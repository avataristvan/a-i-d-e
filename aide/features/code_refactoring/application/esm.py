"""ES-module reference model for TypeScript/JavaScript refactorings.

Scans a source text for every module specifier (static imports, re-exports, dynamic
`import()`, `require()`, `vi.mock()`/`jest.mock()` and friends), resolves specifiers
against relative paths and tsconfig `paths`/`baseUrl`, and computes the specifier a
moved target needs while keeping the importer's style (alias vs. relative, extension,
`/index` elision, quote character stays untouched because only the inner text is edited).
"""
import json
import os
import re
from dataclasses import dataclass, field
from typing import Literal

from aide.core.domain.ports import FileSystemPort

ESM_EXTENSIONS = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
_RESOLVE_EXTENSIONS = (".ts", ".tsx", ".d.ts", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
_JS_TO_TS = {".js": (".ts", ".tsx"), ".jsx": (".tsx",), ".mjs": (".mts",), ".cjs": (".cts",)}


# --------------------------------------------------------------------------- scanning

_COMMENT_OR_STRING = re.compile(r"""//[^\n]*|/\*[\s\S]*?(?:\*/|$)|'(?:\\.|[^'\\\n])*'|"(?:\\.|[^"\\\n])*"|`(?:\\.|[^`\\])*`""")


def blank(text: str) -> str:
    """Same-length text with everything but newlines replaced by spaces."""
    return re.sub(r"[^\n]", " ", text)


def blank_ranges(text: str, ranges: list[tuple[int, int]]) -> str:
    for a, b in sorted(ranges):
        text = text[:a] + blank(text[a:b]) + text[b:]
    return text


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def line_span(text: str, start: int, end: int) -> tuple[int, int]:
    """Expand [start, end) to whole lines including the trailing newline."""
    ls = text.rfind("\n", 0, start) + 1
    le = text.find("\n", end)
    return ls, len(text) if le == -1 else le + 1


def mask_comments(text: str) -> str:
    """Return text with comment bodies replaced by spaces (offsets and newlines preserved)."""
    if "//" not in text and "/*" not in text:
        return text
    return _COMMENT_OR_STRING.sub(lambda m: blank(m.group()) if m.group().startswith("/") else m.group(), text)


def mask_code(text: str) -> str:
    """Blank comments and string/template literal contents (quotes and `${...}` code kept)."""
    out = list(text)
    i, n = 0, len(text)
    stack: list[str] = []  # "`" for template text, "{" for code braces inside `${`

    def blank_at(a: int, b: int) -> None:
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        c = text[i]
        if stack and stack[-1] == "`":
            if c == "\\":
                blank_at(i, min(i + 2, n)); i += 2; continue
            if c == "`":
                stack.pop(); i += 1; continue
            if text.startswith("${", i):
                stack.append("{"); i += 2; continue
            blank_at(i, i + 1); i += 1; continue
        if c in "'\"":
            j = i + 1
            while j < n and text[j] != c and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            blank_at(i + 1, min(j, n)); i = j + 1; continue
        if c == "`":
            stack.append("`"); i += 1; continue
        if text.startswith("//", i):
            j = text.find("\n", i); j = n if j == -1 else j
            blank_at(i, j); i = j; continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2); j = n if j == -1 else j + 2
            blank_at(i, j); i = j; continue
        if c == "{" and stack:
            stack.append("{")
        elif c == "}" and stack and stack[-1] == "{":
            stack.pop()
            if stack and stack[-1] == "`":
                i += 1; continue
        i += 1
    return "".join(out)


_IDENT = re.compile(r"[A-Za-z_$][\w$]*")


def identifiers(masked: str, start: int = 0, end: int | None = None) -> set[str]:
    """Identifiers referenced in masked[start:end], skipping `.prop` member names (not `...spread`)."""
    end = len(masked) if end is None else end
    out = set()
    for m in _IDENT.finditer(masked, start, end):
        a = m.start()
        if a > 0 and (masked[a - 1].isalnum() or masked[a - 1] in "_$"):
            continue
        k = a - 1
        while k >= 0 and masked[k] in " \t":
            k -= 1
        if k >= 0 and masked[k] == "." and not (k >= 2 and masked[k - 2:k + 1] == "..."):
            continue
        out.add(m.group())
    return out


@dataclass
class Binding:
    imported: str   # name exported by the target module
    local: str      # local name in the importing file
    is_type: bool   # inline `type` modifier or whole statement `import type`
    text: str = ""  # source text of this binding, e.g. `type B as C`


RefKind = Literal["import", "export", "side-effect", "call"]


@dataclass
class ModuleRef:
    kind: RefKind
    spec: str
    spec_start: int           # offsets of the specifier text inside the quotes
    spec_end: int
    start: int                # offsets of the whole statement / call head
    end: int
    quote: str = "'"
    type_only: bool = False   # `import type {..}` / `export type {..}`
    default: str | None = None
    namespace: str | None = None
    star: bool = False        # `export * from` (no namespace name)
    named: list[Binding] = field(default_factory=list)
    callee: str | None = None  # for kind == "call"
    braces: tuple[int, int] | None = None  # offsets of `{` .. `}` (inclusive) of the named clause


_STATIC_IMPORT = re.compile(
    r"(?m)^[ \t]*import\s+(?!\()(?P<type>type\s+(?=[\w{*]))?(?P<clause>[^;'\"]*?)\s*from\s*(?P<q>['\"])(?P<spec>[^'\"\n]+)(?P=q)[ \t]*;?")
_SIDE_EFFECT_IMPORT = re.compile(r"(?m)^[ \t]*import\s*(?P<q>['\"])(?P<spec>[^'\"\n]+)(?P=q)[ \t]*;?")
_EXPORT_FROM = re.compile(
    r"(?m)^[ \t]*export\s+(?P<type>type\s+)?(?P<clause>\*(?:\s+as\s+[\w$]+)?|\{[^}]*\})\s*from\s*(?P<q>['\"])(?P<spec>[^'\"\n]+)(?P=q)[ \t]*;?")
_CALL = re.compile(
    r"(?P<callee>(?<![\w$.])import|(?<![\w$.])require|\bvi\.(?:mock|doMock|unmock|doUnmock|importActual|importMock)"
    r"|\bjest\.(?:mock|doMock|unmock|requireActual|requireMock))\s*\(\s*(?P<q>['\"])(?P<spec>[^'\"\n]+)(?P=q)")


def _parse_named(text: str, masked: str, start: int, end: int, all_type: bool) -> list[Binding]:
    """Parse the bindings between offsets start/end (exclusive of the braces)."""
    out = []
    pos = start
    for chunk in masked[start:end].split(","):
        part = chunk.strip()
        lead = len(chunk) - len(chunk.lstrip())
        original = text[pos + lead:pos + lead + len(part)]  # masked span, so comments are not attached
        pos += len(chunk) + 1
        if not part:
            continue
        is_type = all_type
        if re.match(r"type\s+[\w$]", part):
            is_type = True
            part = part[4:].strip()
        m = re.match(r"([\w$]+|'[^']*'|\"[^\"]*\")(?:\s+as\s+([\w$]+))?$", part)
        if not m:
            continue
        imported = m.group(1).strip("'\"")
        out.append(Binding(imported, m.group(2) or imported, is_type, original))
    return out


def _parse_import_clause(ref: ModuleRef, text: str, masked: str, clause: str, clause_start: int) -> None:
    brace = re.search(r"\{([^}]*)\}", clause)
    if brace:
        ref.braces = (clause_start + brace.start(), clause_start + brace.end())
        ref.named = _parse_named(text, masked, ref.braces[0] + 1, ref.braces[1] - 1, ref.type_only)
        clause = (clause[:brace.start()] + clause[brace.end():]).strip()
    clause = clause.strip()
    ns = re.search(r"\*\s+as\s+([\w$]+)", clause)
    if ns:
        ref.namespace = ns.group(1)
        clause = (clause[:ns.start()] + clause[ns.end():]).strip()
    default = clause.strip().strip(",").strip()
    if default and re.fullmatch(r"[\w$]+", default):
        ref.default = default


def scan(text: str) -> list[ModuleRef]:
    masked = mask_comments(text)
    refs: list[ModuleRef] = []
    taken: list[tuple[int, int]] = []

    def free(a: int, b: int) -> bool:
        return all(b <= s or a >= e for s, e in taken)

    for m in _STATIC_IMPORT.finditer(masked):
        ref = ModuleRef("import", m.group("spec"), m.start("spec"), m.end("spec"), m.start(), m.end(),
                        quote=m.group("q"), type_only=bool(m.group("type")))
        _parse_import_clause(ref, text, masked, m.group("clause"), m.start("clause"))
        refs.append(ref)
        taken.append((m.start(), m.end()))
    for m in _SIDE_EFFECT_IMPORT.finditer(masked):
        if free(m.start(), m.end()):
            refs.append(ModuleRef("side-effect", m.group("spec"), m.start("spec"), m.end("spec"), m.start(), m.end(), quote=m.group("q")))
            taken.append((m.start(), m.end()))
    for m in _EXPORT_FROM.finditer(masked):
        ref = ModuleRef("export", m.group("spec"), m.start("spec"), m.end("spec"), m.start(), m.end(),
                        quote=m.group("q"), type_only=bool(m.group("type")))
        clause = m.group("clause")
        if clause.startswith("{"):
            ref.braces = (m.start("clause"), m.end("clause"))
            ref.named = _parse_named(text, masked, ref.braces[0] + 1, ref.braces[1] - 1, ref.type_only)
        else:
            ns = re.search(r"as\s+([\w$]+)", clause)
            ref.namespace = ns.group(1) if ns else None
            ref.star = ns is None
        refs.append(ref)
        taken.append((m.start(), m.end()))
    for m in _CALL.finditer(masked):
        if free(m.start(), m.end()):
            refs.append(ModuleRef("call", m.group("spec"), m.start("spec"), m.end("spec"), m.start(), m.end(),
                                  quote=m.group("q"), callee=m.group("callee")))
    refs.sort(key=lambda r: r.start)
    return refs


# --------------------------------------------------------------------------- resolution

def _load_jsonc(text: str) -> dict:
    text = mask_comments(text)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


@dataclass
class PathAlias:
    prefix: str        # part of the key before '*'
    suffix: str        # part of the key after '*' ("" for most configs)
    wildcard: bool
    targets: list[str]  # absolute target patterns, '*' kept


class ModuleResolver:
    def __init__(self, file_system: FileSystemPort, root: str):
        self.fs = file_system
        self.root = os.path.abspath(root)
        self.aliases: list[PathAlias] = []
        self.base_url: str | None = None
        self._cache: dict[tuple[str, str], str | None] = {}
        self._load_tsconfig(os.path.join(self.root, "tsconfig.json"), set())

    def _load_tsconfig(self, path: str, seen: set[str]) -> None:
        if path in seen or not self.fs.path_exists(path):
            return
        seen.add(path)
        try:
            cfg = _load_jsonc(self.fs.read_file(path))
        except (ValueError, OSError):
            return
        ext = cfg.get("extends")
        if isinstance(ext, str) and ext.startswith("."):
            parent = os.path.normpath(os.path.join(os.path.dirname(path), ext))
            if not parent.endswith(".json"):
                parent += ".json"
            self._load_tsconfig(parent, seen)
        opts = cfg.get("compilerOptions") or {}
        cfg_dir = os.path.dirname(path)
        if "baseUrl" in opts:
            self.base_url = os.path.normpath(os.path.join(cfg_dir, opts["baseUrl"]))
        if "paths" in opts:
            base = self.base_url or cfg_dir
            self.aliases = []
            for key, targets in opts["paths"].items():
                prefix, star, suffix = key.partition("*")
                self.aliases.append(PathAlias(prefix, suffix, bool(star),
                                              [os.path.normpath(os.path.join(base, t)) for t in targets]))
            # most specific (longest prefix) first, as TypeScript does
            self.aliases.sort(key=lambda a: len(a.prefix), reverse=True)

    # ---- specifier -> file
    def _probe(self, base: str) -> str | None:
        if self.fs.path_exists(base) and os.path.isfile(base):
            return base
        stem, ext = os.path.splitext(base)
        for alt in _JS_TO_TS.get(ext, ()):
            if self.fs.path_exists(stem + alt):
                return stem + alt
        for e in _RESOLVE_EXTENSIONS:
            if self.fs.path_exists(base + e):
                return base + e
        for e in _RESOLVE_EXTENSIONS:
            cand = os.path.join(base, "index" + e)
            if self.fs.path_exists(cand):
                return cand
        return None

    def resolve(self, spec: str, from_file: str) -> str | None:
        key = (os.path.dirname(from_file) if spec.startswith(".") else "", spec)
        if key not in self._cache:
            self._cache[key] = self._resolve(spec, from_file)
        return self._cache[key]

    def _resolve(self, spec: str, from_file: str) -> str | None:
        if spec.startswith("."):
            return self._probe(os.path.normpath(os.path.join(os.path.dirname(from_file), spec)))
        for alias in self.aliases:
            hit = self._match_alias(alias, spec)
            if hit is None:
                continue
            for target in alias.targets:
                found = self._probe(target.replace("*", hit, 1))
                if found:
                    return found
        if self.base_url:
            return self._probe(os.path.join(self.base_url, spec))
        return None

    @staticmethod
    def _match_alias(alias: PathAlias, spec: str) -> str | None:
        if not alias.wildcard:
            return "" if spec == alias.prefix else None
        if spec.startswith(alias.prefix) and spec.endswith(alias.suffix) and len(spec) >= len(alias.prefix) + len(alias.suffix):
            return spec[len(alias.prefix):len(spec) - len(alias.suffix)]
        return None

    def classify(self, spec: str) -> Literal["relative", "alias", "bare"]:
        if spec.startswith("."):
            return "relative"
        if any(self._match_alias(a, spec) is not None for a in self.aliases):
            return "alias"
        return "bare"

    # ---- file -> specifier
    def specifier_for(self, target: str, from_file: str, old_spec: str, old_target: str | None = None) -> str:
        """Specifier for `target` as seen from `from_file`, styled like `old_spec`."""
        style = self.classify(old_spec)
        path = self._styled_path(target, old_spec, old_target)
        if style == "alias":
            aliased = self._alias_path(path)
            if aliased:
                return aliased
        if style == "bare" and self.base_url and path.startswith(self.base_url + os.sep):
            return os.path.relpath(path, self.base_url).replace(os.sep, "/")
        return self._relative(path, from_file)

    def relative_specifier(self, target: str, from_file: str) -> str:
        """Extensionless relative specifier, for imports AIDE adds itself."""
        stem = os.path.splitext(target)[0]
        return self._relative(stem[:-2] if stem.endswith(".d") else stem, from_file)

    @staticmethod
    def _relative(path: str, from_file: str) -> str:
        rel = os.path.relpath(path, os.path.dirname(from_file)).replace(os.sep, "/")
        return rel if rel.startswith(".") else "./" + rel

    @staticmethod
    def _styled_path(target: str, old_spec: str, old_target: str | None) -> str:
        """Drop/keep extension and /index the way the old specifier did."""
        stem, ext = os.path.splitext(target)
        if stem.endswith(".d"):
            stem, ext = stem[:-2], ".d" + ext
        old_base = old_spec.rstrip("/").rsplit("/", 1)[-1]
        old_ext = os.path.splitext(old_base)[1]
        old_was_index = (old_target is not None and os.path.splitext(os.path.basename(old_target))[0] == "index"
                         and not old_base.startswith("index"))
        if old_was_index and os.path.basename(stem) == "index":
            return os.path.dirname(stem)
        if old_ext and old_ext in _JS_TO_TS and ext not in _JS_TO_TS:
            return stem + old_ext  # `./foo.js` written for `foo.ts`
        if old_ext:
            return stem + ext
        return stem

    def _alias_path(self, path: str) -> str | None:
        for alias in self.aliases:
            for target in alias.targets:
                head, _, tail = target.partition("*")
                if not alias.wildcard:
                    if os.path.splitext(path)[0] == os.path.splitext(target)[0]:
                        return alias.prefix
                    continue
                if path.startswith(head) and path.endswith(tail):
                    middle = path[len(head):len(path) - len(tail)]
                    return alias.prefix + middle.replace(os.sep, "/") + alias.suffix
        return None


_GENERATED_DIRS = {"dist", "out", "coverage", ".turbo", ".vercel", "storybook-static"}


def iter_esm_files(file_system: FileSystemPort, root: str):
    for path in file_system.walk_files(root):
        rel_parts = os.path.relpath(path, root).split(os.sep)
        if is_esm_file(path) and not _GENERATED_DIRS.intersection(rel_parts[:-1]):
            yield path


def is_esm_file(path: str) -> bool:
    return path.endswith(ESM_EXTENSIONS)


# --------------------------------------------------------------------------- edits

@dataclass
class TextEdit:
    start: int
    end: int
    new_text: str
    reason: str = ""
    summary: str | None = None  # short description used in previews instead of full before/after


class OverlappingEditsError(ValueError):
    pass


def apply_edits(text: str, edits: list[TextEdit]) -> str:
    """Apply offset edits; inserts at the same offset keep their list order."""
    ordered = sorted(enumerate(edits), key=lambda ie: (ie[1].start, ie[1].end, ie[0]))
    for (_, a), (_, b) in zip(ordered, ordered[1:]):
        if b.start < a.end:
            raise OverlappingEditsError(f"overlapping edits at offsets {a.start}-{a.end} and {b.start}-{b.end}")
    out, pos = [], 0
    for _, e in ordered:
        out.append(text[pos:e.start])
        out.append(e.new_text)
        pos = e.end
    out.append(text[pos:])
    return "".join(out)


def describe_edits(text: str, edits: list[TextEdit]) -> list[dict]:
    """Per-edit preview: 1-based line plus summary, inserted/deleted lines, or before/after of the line(s)."""
    out = []
    for e in sorted(edits, key=lambda e: e.start):
        line = line_of(text, e.start)
        if e.summary:
            out.append({"line": line, "reason": e.reason, "summary": e.summary})
            continue
        at_line_start = e.start == 0 or text[e.start - 1] == "\n"
        if e.start == e.end and at_line_start:
            out.append({"line": line, "reason": e.reason, "insert": e.new_text.rstrip("\n")})
            continue
        if not e.new_text and at_line_start and (e.end == len(text) or text[e.end - 1] == "\n"):
            out.append({"line": line, "reason": e.reason, "delete": text[e.start:e.end].rstrip("\n")})
            continue
        ls = text.rfind("\n", 0, e.start) + 1
        le = text.find("\n", e.end)
        le = len(text) if le == -1 else le
        before = text[ls:le]
        after = text[ls:e.start] + e.new_text + text[e.end:le]
        out.append({"line": line, "reason": e.reason, "before": before, "after": after})
    return out


# --------------------------------------------------------------------------- top-level declarations

@dataclass
class Declaration:
    name: str
    kind: str          # function | class | interface | type | enum | const | let | var | namespace
    exported: bool
    default: bool
    start: int         # incl. leading JSDoc/comments/decorators, at line start
    keyword: int       # offset of `export`/keyword on the declaration line
    end: int           # after the trailing newline

    @property
    def is_type(self) -> bool:
        return self.kind in ("interface", "type")


_DECL = re.compile(
    r"(?P<export>export\s+)?(?P<default>default\s+)?(?:declare\s+)?(?:async\s+)?(?:abstract\s+)?"
    r"(?P<kind>function\s*\*?|class|interface|type|const\s+enum|enum|const|let|var|namespace)\s*(?P<name>[A-Za-z_$][\w$]*)")
_BLOCK_KINDS = ("function", "class", "interface", "enum", "namespace")
_CONTINUES_AFTER = set("=,+-*/%&|^!?:<>([{.")
_CONTINUES_BEFORE = set(".?:|&+-*/,)]}=")


def _statement_end(m: str, i: int, block: bool) -> int:
    n = len(m)
    depth = 0
    seen_body = False
    while i < n:
        c = m[i]
        if c in "([{":
            if block and c == "{" and depth == 0:
                seen_body = True
            depth += 1
        elif c in ")]}":
            depth -= 1
            if block and seen_body and depth == 0 and c == "}":
                return i + 1
        elif c == ";" and depth == 0:
            return i + 1
        elif c == "\n" and depth == 0 and not block:
            k = i - 1
            while k >= 0 and m[k] in " \t\r\n":
                k -= 1
            j = i
            while j < n and m[j] in " \t\r\n":
                j += 1
            if k >= 0 and m[k] not in _CONTINUES_AFTER and not m.endswith("=>", 0, k + 1) \
                    and (j == n or m[j] not in _CONTINUES_BEFORE):
                return i
        i += 1
    return n


def top_level_declarations(text: str) -> list[Declaration]:
    m = mask_code(text)
    decls: list[Declaration] = []
    i, n, depth = 0, len(m), 0
    at_line_start = True
    while i < n:
        c = m[i]
        if at_line_start and depth == 0 and c not in " \t\n":
            dm = _DECL.match(m, i)
            if dm:
                kind = re.sub(r"\s+", " ", dm.group("kind")).rstrip("*").strip()
                kind = "enum" if kind == "const enum" else kind
                end = _statement_end(m, dm.end(), kind in _BLOCK_KINDS)
                nl = m.find("\n", end)
                end = n if nl == -1 else nl + 1
                decls.append(Declaration(dm.group("name"), kind, bool(dm.group("export")), bool(dm.group("default")),
                                         _leading_comment_start(text, i), i, end))
                i = end
                at_line_start = True
                continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth = max(0, depth - 1)
        at_line_start = c == "\n" or (at_line_start and c in " \t")
        i += 1
    return decls


def _leading_comment_start(text: str, keyword: int) -> int:
    start = text.rfind("\n", 0, keyword) + 1
    while start > 0:
        prev_start = text.rfind("\n", 0, start - 1) + 1
        line = text[prev_start:start - 1].strip()
        if line.startswith(("//", "/*", "*", "@")) or line.endswith("*/"):
            start = prev_start
        else:
            break
    return start


# --------------------------------------------------------------------------- plans

@dataclass
class EditSet:
    """Text edits per file, all computed against `originals` (read-only until apply)."""
    originals: dict[str, str] = field(default_factory=dict)
    edits: dict[str, list[TextEdit]] = field(default_factory=dict)  # keyed by pre-move abs path
    warnings: list[str] = field(default_factory=list)

    def add(self, path: str, text: str, edit: TextEdit) -> None:
        self.originals.setdefault(path, text)
        self.edits.setdefault(path, []).append(edit)

    @property
    def files_changed(self) -> int:
        return sum(1 for e in self.edits.values() if e)

    @property
    def total_edits(self) -> int:
        return sum(len(e) for e in self.edits.values())

    def warn(self, root: str, path: str, text: str, offset: int, message: str) -> None:
        self.warnings.append(f"{os.path.relpath(path, root)}:{line_of(text, offset)}: {message}")

    def preview(self, root: str) -> dict:
        return {
            "edits": {os.path.relpath(p, root): describe_edits(self.originals[p], e)
                      for p, e in sorted(self.edits.items()) if e},
            "warnings": self.warnings,
        }

    def apply(self, fs: FileSystemPort) -> None:
        for path, edits in self.edits.items():
            if edits:
                fs.write_file(path, apply_edits(self.originals[path], edits))

"""move-symbol for TypeScript/JavaScript (ES modules).

Moves top-level declarations (function, class, interface, type, enum, const, let, var)
plus the non-exported helpers only they use, copies exactly the import bindings the moved
code needs, adds a back-import where the source still uses a moved name, and rewrites
every importer/re-exporter in the project (aliases, relative paths, multi-symbol lines,
`type` modifiers), splitting statements that also import names which stay behind.
"""
import os
import re
from dataclasses import dataclass, field

from aide.core.domain.ports import FileSystemPort
from aide.features.code_refactoring.application.esm import (
    Declaration, EditSet, ModuleRef, ModuleResolver, TextEdit, apply_edits, blank_ranges, identifiers,
    iter_esm_files, line_of, line_span, mask_code, scan, top_level_declarations,
)


class MoveSymbolError(ValueError):
    pass


@dataclass
class SymbolMovePlan(EditSet):
    symbols: list[str] = field(default_factory=list)
    helpers: list[str] = field(default_factory=list)  # non-exported declarations moved along


def _parts(r: ModuleRef, keep=lambda b: True) -> list[str]:
    return [b.text for b in r.named if keep(b)]


def _render_braces(text: str, ref: ModuleRef, parts: list[str]) -> str:
    """Re-render a `{ ... }` clause, keeping single- or multi-line layout."""
    assert ref.braces is not None
    a, b = ref.braces
    inner = text[a + 1:b - 1]
    if "\n" in inner:
        indent = re.search(r"\n([ \t]*)\S", inner)
        ind = indent.group(1) if indent else "  "
        closing = re.search(r"\n([ \t]*)$", inner)
        return "{\n" + "".join(f"{ind}{p},\n" for p in parts) + (closing.group(1) if closing else "") + "}"
    return "{ " + ", ".join(parts) + " }"


def _render_import(kind: str, type_only: bool, default: str | None, namespace: str | None,
                   parts: list[str], spec: str, quote: str) -> str:
    clause = [x for x in (default, f"* as {namespace}" if namespace else None) if x]
    if parts:
        clause.append("{ " + ", ".join(parts) + " }")
    head = f"{kind} type " if type_only else f"{kind} "
    return f"{head}{', '.join(clause)} from {quote}{spec}{quote};"


def _names_import(names: list[str], by_name: dict[str, list[Declaration]], spec: str, quote: str) -> str:
    """`import { A, type B }` with inline `type` for interfaces/type aliases (isolatedModules-safe)."""
    parts = [("type " if all(d.is_type for d in by_name[n]) else "") + n for n in names]
    return _render_import("import", False, None, None, parts, spec, quote)


def _quote_of(refs: list[ModuleRef], fallback: str = "'") -> str:
    return next((r.quote for r in refs if r.kind != "call"), fallback)


def _insertion_point(text: str, refs: list[ModuleRef]) -> int:
    """After the last static import, else after leading comments/directives ('use client'), else 0."""
    imports = [r for r in refs if r.kind in ("import", "side-effect")]
    if imports:
        return line_span(text, imports[-1].start, imports[-1].end)[1]
    m = re.match(r"(?:\s*(?://[^\n]*|/\*[\s\S]*?\*/)\s*)*(?:\s*['\"]use [\w ]+['\"];?[ \t]*\n)*", text)
    return m.end() if m else 0


def _remove_bindings(text: str, r: ModuleRef, locals_: set[str], reason: str) -> TextEdit:
    keep_parts = _parts(r, lambda b: b.local not in locals_)
    keep_default = r.default if r.default not in locals_ else None
    keep_ns = r.namespace if r.namespace not in locals_ else None
    if not (keep_parts or keep_default or keep_ns):
        a, b = line_span(text, r.start, r.end)
        return TextEdit(a, b, "", reason)
    if r.braces and r.default is None and r.namespace is None:
        return TextEdit(r.braces[0], r.braces[1], _render_braces(text, r, keep_parts), reason)
    head = text[r.start:r.end]
    indent = head[:len(head) - len(head.lstrip(" \t"))]
    return TextEdit(r.start, r.end, indent + _render_import(r.kind, r.type_only, keep_default, keep_ns, keep_parts, r.spec, r.quote), reason)


class MoveEsmSymbolUseCase:
    def __init__(self, file_system: FileSystemPort) -> None:
        self.fs = file_system

    def plan(self, source: str, symbols: list[str], dest: str, root: str = ".") -> SymbolMovePlan:
        root_abs = os.path.abspath(root)
        src = os.path.abspath(os.path.join(root_abs, source))
        dst = os.path.abspath(os.path.join(root_abs, dest))
        if not self.fs.path_exists(src):
            raise MoveSymbolError(f"Source file not found: {source}")
        if src == dst:
            raise MoveSymbolError("Source and destination are the same file")

        resolver = ModuleResolver(self.fs, root_abs)
        text = self.fs.read_file(src)
        masked = mask_code(text)
        refs = scan(text)
        decls = top_level_declarations(text)
        by_name: dict[str, list[Declaration]] = {}
        for d in decls:
            by_name.setdefault(d.name, []).append(d)

        requested = list(dict.fromkeys(symbols))
        for name in requested:
            if name not in by_name:
                raise MoveSymbolError(f"Top-level declaration '{name}' not found in {source}")
            if any(d.default for d in by_name[name]):
                raise MoveSymbolError(f"'{name}' is a default export; moving default exports is not supported")

        dest_text = self.fs.read_file(dst) if self.fs.path_exists(dst) else None
        dest_body = dest_text or ""
        dest_refs = scan(dest_body)
        dest_decl_names = {d.name for d in top_level_declarations(dest_body)}

        # identifier usage: per declaration, plus everything outside declarations and imports
        ids_of = {n: set().union(*(identifiers(masked, d.start, d.end) for d in ds)) for n, ds in by_name.items()}
        import_ranges = [(r.start, r.end) for r in refs if r.kind != "call"]
        rest_ids = identifiers(blank_ranges(masked, [(d.start, d.end) for d in decls] + import_ranges))

        def ids_inside(names: set[str]) -> set[str]:
            return set().union(*(ids_of[n] for n in names))

        def ids_outside(names: set[str]) -> set[str]:
            return rest_ids | ids_inside(by_name.keys() - names)

        # non-exported helpers used only by the moved code travel with it
        moving = set(requested)
        helpers: list[str] = []
        changed = True
        while changed:
            changed = False
            for h in sorted(ids_inside(moving) & by_name.keys() - moving):
                if not any(d.exported for d in by_name[h]) and h not in ids_outside(moving | {h}):
                    moving.add(h)
                    helpers.append(h)
                    changed = True

        clash = sorted(moving & dest_decl_names)
        if clash:
            raise MoveSymbolError(f"Destination already declares: {', '.join(clash)}")

        plan = SymbolMovePlan(symbols=requested, helpers=helpers)
        moving_decls = sorted((d for n in moving for d in by_name[n]), key=lambda d: d.start)
        used_by_moved = ids_inside(moving)
        used_by_rest = ids_outside(moving)
        stays_needed = sorted(used_by_moved & by_name.keys() - moving)
        dest_locals = dest_decl_names | {b.local for r in dest_refs for b in r.named} | {
            x for r in dest_refs for x in (r.default, r.namespace) if x}
        src_edits: list[TextEdit] = []
        dest_edits: list[TextEdit] = []
        dest_import_lines: list[str] = []
        quote = _quote_of(dest_refs, _quote_of(refs))

        # 1. moved blocks: requested symbols get `export`, relative dynamic imports re-pointed
        blocks = []
        for d in moving_decls:
            inner = [TextEdit(r.spec_start - d.start, r.spec_end - d.start, resolver.specifier_for(t, dst, r.spec, old_target=t))
                     for r in refs if r.kind == "call" and d.start <= r.start < d.end and r.spec.startswith(".")
                     and (t := resolver.resolve(r.spec, src))]
            block = apply_edits(text[d.start:d.end], inner)
            if d.name in requested and not d.exported:
                k = d.keyword - d.start
                block = block[:k] + "export " + block[k:]
            blocks.append(block.rstrip("\n") + "\n")
            span_end = d.end
            if text[span_end:span_end + 1] == "\n" and (d.start == 0 or text[d.start - 2:d.start] == "\n\n"):
                span_end += 1  # swallow one blank line so no double gap remains
            src_edits.append(TextEdit(d.start, span_end, "", "moved declaration",
                                      summary=f"remove {d.kind} {d.name} (lines {line_of(text, d.start)}-{line_of(text, d.end - 1)})"))

        # 2. imports the moved code needs: only its bindings; drop them from the source if nothing else uses them
        merges: dict[int, tuple[ModuleRef, list[str]]] = {}
        for r in (r for r in refs if r.kind == "import"):
            needed = {x for x in (r.default, r.namespace) if x in used_by_moved} | {b.local for b in r.named if b.local in used_by_moved}
            if not needed:
                continue
            removable = needed - used_by_rest
            if removable:
                src_edits.append(_remove_bindings(text, r, removable, "import only used by moved code"))
            target = resolver.resolve(r.spec, src)
            new = needed - dest_locals
            if target == dst or not new:
                continue
            default = r.default if r.default in new else None
            namespace = r.namespace if r.namespace in new else None
            parts = _parts(r, lambda b: b.local in new)
            existing = None if default or namespace else self._existing_import(dest_refs, resolver, dst, target, r)
            if existing:
                merges.setdefault(existing.start, (existing, _parts(existing)))[1].extend(parts)
            else:
                spec = resolver.specifier_for(target, dst, r.spec, old_target=target) if target else r.spec
                dest_import_lines.append(_render_import("import", r.type_only, default, namespace, parts, spec, quote))
        for existing, parts in merges.values():
            assert existing.braces is not None
            dest_edits.append(TextEdit(existing.braces[0], existing.braces[1], _render_braces(dest_body, existing, parts),
                                       "import needed by moved code (merged)"))

        # declarations that stay in the source but are used by moved code
        if stays_needed:
            dest_import_lines.append(_names_import(stays_needed, by_name, resolver.relative_specifier(src, dst), quote))
            src_edits += [TextEdit(d.keyword, d.keyword, "export ", "now imported by destination")
                          for n in stays_needed for d in by_name[n] if not d.exported]
            plan.warnings.append(f"{os.path.relpath(dst, root_abs)} imports {', '.join(stays_needed)} from the source: "
                                 "circular import between source and destination")

        # 3. back-import where the source still uses moved names
        back = [n for n in requested if n in used_by_rest]
        if back:
            at = _insertion_point(text, refs)
            line = _names_import(back, by_name, resolver.relative_specifier(dst, src), _quote_of(refs)) + "\n"
            src_edits.append(TextEdit(at, at, line, "back-import of moved symbol still used here"))

        # 4. destination
        import_block = "".join(line + "\n" for line in dest_import_lines)
        what = ", ".join(f"{d.kind} {d.name}" for d in moving_decls)
        if dest_text is not None:
            if import_block:
                at = _insertion_point(dest_body, dest_refs)
                dest_edits.append(TextEdit(at, at, import_block, "import needed by moved code"))
            tail = ("\n" if dest_body and not dest_body.endswith("\n") else "") + ("\n" if dest_body else "") + "\n".join(blocks)
            dest_edits.append(TextEdit(len(dest_body), len(dest_body), tail, "moved declarations", summary=f"append {what}"))
        else:
            body = (import_block + "\n" if import_block else "") + "\n".join(blocks)
            dest_edits.append(TextEdit(0, 0, body, "new file", summary=f"create with {what}"
                                       + (f" and {len(dest_import_lines)} import(s)" if dest_import_lines else "")))
        for e in src_edits:
            plan.add(src, text, e)
        for e in dest_edits:
            plan.add(dst, dest_body, e)

        # 5. importers / re-exporters across the project
        exported_moved = {n for n in requested if any(d.exported for d in by_name[n])}
        if exported_moved:
            for path in iter_esm_files(self.fs, root_abs):
                if path != src:
                    self._plan_importer(plan, resolver, root_abs, path, dest_body if path == dst else self.fs.read_file(path),
                                        src, dst, exported_moved)
        return plan

    @staticmethod
    def _existing_import(dest_refs: list[ModuleRef], resolver: ModuleResolver, dst: str, target: str | None,
                         r: ModuleRef) -> ModuleRef | None:
        """A plain `import { .. }` in the destination of the same module, to merge new bindings into."""
        for d in dest_refs:
            if d.kind == "import" and d.braces and d.type_only == r.type_only and not d.namespace:
                if (resolver.resolve(d.spec, dst) == target) if target else d.spec == r.spec:
                    return d
        return None

    @staticmethod
    def _plan_importer(plan: SymbolMovePlan, resolver: ModuleResolver, root: str, path: str, text: str,
                       src: str, dst: str, moved: set[str]) -> None:
        masked = None
        for r in scan(text):
            if resolver.resolve(r.spec, path) != src:
                continue
            if r.kind == "call":
                plan.warn(root, path, text, r.start, f"{r.callee}('{r.spec}') targets the source module; check whether it must also cover the destination")
                continue
            if r.star:
                plan.warn(root, path, text, r.start, "`export *` from the source no longer re-exports the moved symbols")
            if r.namespace:
                masked = masked or mask_code(text)
                if moved & {m.group(1) for m in re.finditer(rf"\b{re.escape(r.namespace)}\.([\w$]+)", masked)}:
                    plan.warn(root, path, text, r.start, f"namespace import '{r.namespace}' uses moved symbols; not rewritten")
            moved_b = [b for b in r.named if b.imported in moved]
            if not moved_b:
                continue
            if path == dst:
                plan.add(path, text, _remove_bindings(text, r, {b.local for b in moved_b}, "symbol is now local"))
                continue
            new_spec = resolver.specifier_for(dst, path, r.spec, old_target=src)
            if len(moved_b) == len(r.named) and not r.default and not r.namespace:
                plan.add(path, text, TextEdit(r.spec_start, r.spec_end, new_spec, f"{r.kind} of moved symbol"))
                continue
            plan.add(path, text, _remove_bindings(text, r, {b.local for b in moved_b}, "split: moved symbols leave this statement"))
            line_end = line_span(text, r.start, r.end)[1]
            stmt = _render_import(r.kind, r.type_only, None, None, [b.text for b in moved_b], new_spec, r.quote)
            plan.add(path, text, TextEdit(line_end, line_end, stmt + "\n", f"split: {r.kind} of moved symbol"))

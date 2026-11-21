import difflib
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlparse

from aide.core.domain.ports import FileSystemPort


def path_to_uri(file_path: str) -> str:
    return Path(os.path.abspath(file_path)).as_uri()


def uri_to_path(uri: str) -> str:
    return unquote(urlparse(uri).path)


class WorkspaceEditError(ValueError):
    pass


@dataclass
class FileOperation:
    kind: str  # "write" | "create" | "rename" | "delete"
    path: str
    content: str | None = None   # full new content for write/create
    new_path: str | None = None  # target for rename


@dataclass
class EditPlan:
    operations: list[FileOperation]
    originals: dict[str, str | None] = field(default_factory=dict)  # disk content before; None = did not exist
    finals: dict[str, str | None] = field(default_factory=dict)     # content after; None = gone

    @property
    def changed_files(self) -> list[str]:
        return sorted(p for p in self.finals if self.finals[p] != self.originals.get(p))

    @property
    def replacements(self) -> int:
        return sum(1 for op in self.operations if op.kind == "write")

    def diff(self, relative_to: str | None = None) -> str:
        def label(path: str) -> str:
            return os.path.relpath(path, relative_to) if relative_to else path

        chunks = []
        for path in self.changed_files:
            before, after = self.originals.get(path), self.finals[path]
            chunks.extend(difflib.unified_diff(
                (before or "").splitlines(keepends=True), (after or "").splitlines(keepends=True),
                fromfile="/dev/null" if before is None else f"a/{label(path)}",
                tofile="/dev/null" if after is None else f"b/{label(path)}",
            ))
        return "".join(line if line.endswith("\n") else line + "\n" for line in chunks)


class WorkspaceEditApplier:
    """Turns an LSP WorkspaceEdit into file operations on a FileSystemPort.

    plan() reads only and validates the whole edit up front; apply() writes. Callers should
    apply inside a FileSystemPort transaction so a failure mid-way can be rolled back.
    Positions are interpreted as UTF-16 code units (the LSP default encoding).
    """

    def __init__(self, file_system: FileSystemPort):
        self._fs = file_system

    def plan(self, edit: dict) -> EditPlan:
        state: dict[str, str | None] = {}
        originals: dict[str, str | None] = {}
        operations: list[FileOperation] = []

        def current(path: str) -> str | None:
            if path not in state:
                state[path] = self._fs.read_file(path) if self._fs.path_exists(path) else None
                originals[path] = state[path]
            return state[path]

        for change in _document_changes(edit):
            kind = change.get("kind")
            if kind is None:
                path = uri_to_path(change["textDocument"]["uri"])
                text = current(path)
                if text is None:
                    raise WorkspaceEditError(f"Edit targets a missing file: {path}")
                state[path] = apply_text_edits(text, change.get("edits", []))
                operations.append(FileOperation("write", path, content=state[path]))
            elif kind == "create":
                path = uri_to_path(change["uri"])
                options = change.get("options") or {}
                if current(path) is not None and not options.get("overwrite"):
                    if options.get("ignoreIfExists"):
                        continue
                    raise WorkspaceEditError(f"Create target already exists: {path}")
                state[path] = ""
                operations.append(FileOperation("create", path, content=""))
            elif kind == "rename":
                old, new = uri_to_path(change["oldUri"]), uri_to_path(change["newUri"])
                options = change.get("options") or {}
                text = current(old)
                if text is None:
                    raise WorkspaceEditError(f"Rename source is missing: {old}")
                if current(new) is not None and not options.get("overwrite"):
                    if options.get("ignoreIfExists"):
                        continue
                    raise WorkspaceEditError(f"Rename target already exists: {new}")
                state[new], state[old] = text, None
                operations.append(FileOperation("rename", old, new_path=new))
            elif kind == "delete":
                path = uri_to_path(change["uri"])
                if os.path.isdir(path):
                    raise WorkspaceEditError(f"Deleting directories is not supported: {path}")
                if current(path) is None:
                    if (change.get("options") or {}).get("ignoreIfNotExists"):
                        continue
                    raise WorkspaceEditError(f"Delete target is missing: {path}")
                state[path] = None
                operations.append(FileOperation("delete", path))
            else:
                raise WorkspaceEditError(f"Unknown resource operation: {kind}")

        return EditPlan(operations, originals, dict(state))

    def apply(self, plan: EditPlan) -> None:
        for op in plan.operations:
            if op.kind in ("write", "create"):
                self._fs.write_file(op.path, op.content or "")
            elif op.kind == "rename":
                assert op.new_path is not None
                self._fs.move_path(op.path, op.new_path)
            elif op.kind == "delete":
                self._fs.delete_path(op.path)


def _document_changes(edit: dict) -> list[dict]:
    """documentChanges takes precedence over changes, as the LSP spec requires."""
    if edit.get("documentChanges") is not None:
        return edit["documentChanges"]
    return [{"textDocument": {"uri": uri}, "edits": edits} for uri, edits in (edit.get("changes") or {}).items()]


def apply_text_edits(text: str, edits: list[dict]) -> str:
    """Applies LSP TextEdits (all relative to the original text). Overlapping edits are rejected;
    inserts at the same position keep their array order."""
    line_starts = _line_starts(text)
    resolved = []
    for index, edit in enumerate(edits):
        start = _offset(text, line_starts, edit["range"]["start"])
        end = _offset(text, line_starts, edit["range"]["end"])
        if end < start:
            raise WorkspaceEditError(f"Edit range ends before it starts: {edit['range']}")
        resolved.append((start, end, index, edit.get("newText", "")))

    resolved.sort(key=lambda e: (e[0], e[2]))
    for prev, nxt in zip(resolved, resolved[1:]):
        if nxt[0] < prev[1]:
            raise WorkspaceEditError(f"Overlapping edits at offsets {prev[0]}-{prev[1]} and {nxt[0]}-{nxt[1]}")

    for start, end, _, new_text in reversed(resolved):
        text = text[:start] + new_text + text[end:]
    return text


def _line_starts(text: str) -> list[int]:
    starts, pos = [0], 0
    for line in text.splitlines(keepends=True):
        pos += len(line)
        starts.append(pos)
    return starts  # last entry is len(text): the (possibly empty) line after the final newline


def _offset(text: str, line_starts: list[int], position: dict) -> int:
    line, units = position["line"], position["character"]
    if line >= len(line_starts):
        return len(text)
    start = line_starts[line]
    end = line_starts[line + 1] if line + 1 < len(line_starts) else len(text)
    content = text[start:end].rstrip("\r\n")
    index = 0
    while index < len(content) and units > 0:
        units -= 2 if ord(content[index]) > 0xFFFF else 1
        index += 1
    return start + index  # characters past the line end clamp to the line end, per spec

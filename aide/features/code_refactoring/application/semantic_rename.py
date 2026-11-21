import os
import re
from dataclasses import dataclass, field
from typing import Callable

from aide.core.domain.ports import FileSystemPort
from aide.core.domain.workspace_edit import WorkspaceEditApplier, path_to_uri

TS_JS_EXTENSIONS = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
_IDENTIFIER = re.compile(r"^[A-Za-z_$][\w$]*$")


def is_ts_js_file(path: str) -> bool:
    return path.endswith(TS_JS_EXTENSIONS)


@dataclass
class SemanticRenameResult:
    success: bool
    message: str
    files_changed: int = 0
    total_replacements: int = 0
    changes: list[dict] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    engine: str = ""


class SemanticRenameUseCase:
    """Renames the symbol at (file, name[, line]) and every reference that TypeScript resolves to it.
    Same-named identifiers of other symbols, strings and comments stay unless asked for."""

    def __init__(self, file_system: FileSystemPort, find_rename_locations: Callable[..., dict]):
        self.file_system = file_system
        self._find_rename_locations = find_rename_locations

    def execute(self, root: str, file: str, old_name: str, new_name: str, line: int | None = None,
                in_strings: bool = False, in_comments: bool = False, dry_run: bool = False) -> SemanticRenameResult:
        if not _IDENTIFIER.match(new_name):
            return SemanticRenameResult(False, f"'{new_name}' is not a valid identifier")
        if old_name == new_name:
            return SemanticRenameResult(False, "Old and new name are identical")
        try:
            payload = self._find_rename_locations(root, file, old_name, line, in_strings, in_comments)
        except Exception as e:
            return SemanticRenameResult(False, str(e))

        by_file: dict[str, list[dict]] = {}
        changes = []
        root_abs = os.path.abspath(root)
        for loc in payload["locations"]:
            text = f"{loc['prefix']}{new_name}{loc['suffix']}"
            by_file.setdefault(loc["file"], []).append({
                "range": {"start": {"line": loc["line"], "character": loc["character"]},
                          "end": {"line": loc["line"], "character": loc["character"] + loc["length"]}},
                "newText": text,
            })
            changes.append({"file": os.path.relpath(loc["file"], root_abs), "line": loc["line"] + 1,
                            "column": loc["character"] + 1, "new_text": text})

        engine = f"typescript {payload['typescript']}"
        if not by_file:
            return SemanticRenameResult(False, f"No rename locations found for '{old_name}'", engine=engine)

        try:
            applier = WorkspaceEditApplier(self.file_system)
            plan = applier.plan({"changes": {path_to_uri(f): edits for f, edits in by_file.items()}})
            if not dry_run:
                applier.apply(plan)
        except Exception as e:
            return SemanticRenameResult(False, str(e), engine=engine)

        return SemanticRenameResult(
            True, "Success", files_changed=len(plan.changed_files), total_replacements=len(changes),
            changes=changes, skipped=[os.path.relpath(p, root_abs) for p in payload["skipped"]], engine=engine,
        )

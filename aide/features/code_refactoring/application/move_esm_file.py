import os
from dataclasses import dataclass, field

from aide.core.domain.ports import FileSystemPort
from aide.features.code_refactoring.application.esm import (
    EditSet, ModuleResolver, TextEdit, iter_esm_files, scan,
)


@dataclass
class FileMovePlan(EditSet):
    moves: dict[str, str] = field(default_factory=dict)  # old abs path -> new abs path
    errors: list[str] = field(default_factory=list)

    def preview(self, root: str) -> dict:
        moves = [{"from": os.path.relpath(a, root), "to": os.path.relpath(b, root)} for a, b in self.moves.items()]
        return {"moves": moves, **super().preview(root)}

    def apply(self, fs: FileSystemPort) -> None:
        super().apply(fs)
        for old, new in self.moves.items():
            fs.move_path(old, new)


def plan_reference_updates(fs: FileSystemPort, resolver: ModuleResolver, root: str, plan: FileMovePlan) -> None:
    """Add specifier edits for every ESM reference whose importer or target moves."""
    for path in iter_esm_files(fs, root):
        text = fs.read_file(path)
        new_from = plan.moves.get(path, path)
        for ref in scan(text):
            target = resolver.resolve(ref.spec, path)
            if target is None:
                continue
            new_target = plan.moves.get(target, target)
            if new_from == path and new_target == target:
                continue
            new_spec = resolver.specifier_for(new_target, new_from, ref.spec, old_target=target)
            if new_spec != ref.spec:
                reason = "moved file's own import" if path in plan.moves else f"{ref.kind} of moved file"
                plan.add(path, text, TextEdit(ref.spec_start, ref.spec_end, new_spec, reason))


class MoveEsmFileUseCase:
    """move-file for TypeScript/JavaScript: module paths, not JVM packages."""

    def __init__(self, file_system: FileSystemPort) -> None:
        self.fs = file_system

    def plan(self, sources: list[str], dest: str, root: str = ".") -> FileMovePlan:
        root_abs = os.path.abspath(root)
        dest_abs = os.path.abspath(os.path.join(root_abs, dest))
        dest_is_file = len(sources) == 1 and os.path.splitext(dest_abs)[1] != "" and not os.path.isdir(dest_abs)

        plan = FileMovePlan()
        for src in sources:
            src_abs = os.path.abspath(os.path.join(root_abs, src))
            target = dest_abs if dest_is_file else os.path.join(dest_abs, os.path.basename(src_abs))
            if not os.path.isfile(src_abs):
                plan.errors.append(f"Source file not found: {src}")
            elif self.fs.path_exists(target) or target in plan.moves.values():
                plan.errors.append(f"Destination already taken: {os.path.relpath(target, root_abs)}")
            else:
                plan.moves[src_abs] = target
        if plan.moves and not plan.errors:
            plan_reference_updates(self.fs, ModuleResolver(self.fs, root_abs), root_abs, plan)
        return plan

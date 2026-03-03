import os
from dataclasses import dataclass
from aide.core.domain.ports import FileSystemPort
from aide.features.code_refactoring.application.smart_rename import SmartRenameUseCase


@dataclass
class MovePackageResult:
    success: bool
    message: str
    files_changed: int
    total_replacements: int
    old_package: str
    new_package: str


class MovePackageUseCase:
    def __init__(self, file_system: FileSystemPort):
        self.file_system = file_system

    def execute(
        self,
        src: str,
        dest_package: str,
        root: str = ".",
        src_root: str = "app/src/main/java",
        dry_run: bool = False,
    ) -> MovePackageResult:
        abs_src_root = os.path.abspath(os.path.join(root, src_root))

        # Try path relative to src_root first, fall back to path relative to root
        src_path = os.path.abspath(os.path.join(abs_src_root, src))
        if not os.path.exists(src_path):
            src_path = os.path.abspath(os.path.join(root, src))

        if not os.path.exists(src_path):
            return MovePackageResult(
                success=False,
                message=f"Source path does not exist: {src_path}",
                files_changed=0,
                total_replacements=0,
                old_package="",
                new_package=dest_package,
            )

        rel_path = os.path.relpath(src_path, abs_src_root)
        if rel_path.startswith(".."):
            return MovePackageResult(
                success=False,
                message=f"Source path must be inside src-root: {abs_src_root}",
                files_changed=0,
                total_replacements=0,
                old_package="",
                new_package=dest_package,
            )

        old_package = rel_path.replace(os.sep, ".")
        dest_path = os.path.join(abs_src_root, dest_package.replace(".", os.sep))

        if not dry_run:
            try:
                self.file_system.move_path(src_path, dest_path)
                self.file_system.delete_empty_parents(src_path, abs_src_root)
            except Exception as e:
                return MovePackageResult(
                    success=False,
                    message=f"Failed to move files: {e}",
                    files_changed=0,
                    total_replacements=0,
                    old_package=old_package,
                    new_package=dest_package,
                )

        rename_use_case = SmartRenameUseCase(self.file_system)
        res = rename_use_case.execute(root, old_package, dest_package, dry_run=dry_run)

        return MovePackageResult(
            success=res.success,
            message="Move complete." if res.success else res.message,
            files_changed=res.files_changed,
            total_replacements=res.total_replacements,
            old_package=old_package,
            new_package=dest_package,
        )

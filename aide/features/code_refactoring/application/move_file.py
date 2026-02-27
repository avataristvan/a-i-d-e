import os
import re
from typing import Any, Tuple, Callable, Generator
from aide.core.domain.ports import FileSystemPort
from aide.core.domain.models import OperationResult
from aide.features.code_refactoring.application.update_refs import UpdateReferencesUseCase

class MoveFileUseCase:
    def __init__(self, file_system: FileSystemPort, strategy_provider):
        self.file_system = file_system
        self.strategy_provider = strategy_provider
        self.update_refs_use_case = UpdateReferencesUseCase(file_system)

    def execute(self, source_paths: list[str], dest_dir: str, root_path: str = ".", src_root: str = "app/src/main/java", dry_run: bool = False) -> OperationResult:
        files_moved = 0
        total_replacements = 0
        errors = []

        try:
            dest_dir_abs = os.path.abspath(os.path.join(root_path, dest_dir))
            src_root_abs = os.path.abspath(os.path.join(root_path, src_root))

            if not os.path.exists(dest_dir_abs) and not dry_run:
                os.makedirs(dest_dir_abs, exist_ok=True)

            for src_rel in source_paths:
                src_path = os.path.abspath(os.path.join(root_path, src_rel.strip()))
                
                if not os.path.exists(src_path):
                    errors.append(f"Source file not found: {src_rel}")
                    continue
                
                if not os.path.isfile(src_path):
                    # For now, we only handle explicit files, not directories in this loop natively
                    errors.append(f"Source must be a file, not a directory: {src_rel}")
                    continue

                filename = os.path.basename(src_path)
                new_path = os.path.join(dest_dir_abs, filename)
                
                # Check if moving within the same src_root boundary
                if not src_path.startswith(src_root_abs) or not new_path.startswith(src_root_abs):
                    # We can still move the file, but we can't reliably infer JVM package changes
                    if not dry_run:
                        self.file_system.move_path(src_path, new_path)
                    files_moved += 1
                    continue

                # JVM/Namespaced Logic: Calculate old and new packages
                old_rel = os.path.relpath(os.path.dirname(src_path), src_root_abs)
                new_rel = os.path.relpath(dest_dir_abs, src_root_abs)
                
                old_package = old_rel.replace(os.sep, ".")
                new_package = new_rel.replace(os.sep, ".")
                
                # Read content before move
                content = self.file_system.read_file(src_path)
                strategy = self.strategy_provider.get_strategy(src_path)
                
                # Update package declaration inside the file
                if old_package != new_package:
                    # e.g., Replace 'package com.example.old' with 'package com.example.new'
                    package_stmt_old = strategy.get_package_header(src_path) # Might need to synthesize if None
                    if not package_stmt_old:
                        package_stmt_old = f"package {old_package}" 
                        
                    package_stmt_new = package_stmt_old.replace(old_package, new_package)
                    
                    if package_stmt_old in content:
                        content = content.replace(package_stmt_old, package_stmt_new)
                    else:
                        # Fallback regex for package replacement
                        content = re.sub(rf"^package\s+{re.escape(old_package)}", f"package {new_package}", content, flags=re.MULTILINE)

                # Collect symbols exposed by this file to update project-wide imports
                # In Kotlin/Java, a file might expose a class matching the filename, or multiple things.
                # For simplicity, we assume the filename (without extension) corresponds to the primary class
                base_name, _ = os.path.splitext(filename)
                
                old_fqdn = f"{old_package}.{base_name}" if old_package != "." else base_name
                new_fqdn = f"{new_package}.{base_name}" if new_package != "." else base_name

                # Write changes and move
                if not dry_run:
                    self.file_system.write_file(src_path, content) # Save updated package first
                    self.file_system.move_path(src_path, new_path)
                    # Cleanup old empty parent folders if any
                    self.file_system.delete_empty_parents(src_path, src_root_abs)
                
                files_moved += 1
                
                # Update project-wide references
                if old_fqdn != new_fqdn:
                    ref_res = self.update_refs_use_case.execute(root_path, old_fqdn, new_fqdn, dry_run=dry_run)
                    total_replacements += ref_res.total_replacements

            if errors and files_moved == 0:
                 return OperationResult(False, "\n".join(errors), 0, 0)
                 
            return OperationResult(True, "Success" if not errors else "Partial Success:\n" + "\n".join(errors), files_moved, total_replacements)
            
        except Exception as e:
            return OperationResult(False, str(e), 0, 0)

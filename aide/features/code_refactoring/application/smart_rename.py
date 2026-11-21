import os
import re
from aide.core.domain.ports import FileSystemPort
from aide.core.domain.models import OperationResult
from typing import Callable

class SmartRenameUseCase:
    def __init__(self, file_system: FileSystemPort,
                 file_filter: Callable[[str, list[str]], tuple[list[str], list[str]]] | None = None):
        self.file_system = file_system
        self._file_filter = file_filter

    def execute(self, root_path: str, old_text: str, new_text: str, use_word_boundary: bool = False, dry_run: bool = False) -> OperationResult:
        files_changed = 0
        total_replacements = 0
        
        try:
            # Prepare pattern
            if use_word_boundary:
                pattern = re.compile(rf"\b{re.escape(old_text)}\b")
            else:
                pattern = re.compile(re.escape(old_text))
            
            # Nested worktrees (e.g. .claude/worktrees/agent-*) and gitignored files are not part of the project.
            files = list(self.file_system.walk_files(root_path))
            if self._file_filter:
                files, _ = self._file_filter(root_path, files)
            for file_path in files:
                # Only check relevant file types
                if not file_path.endswith((".kt", ".java", ".xml", ".gradle", ".gradle.kts", ".toml", ".py", ".md", ".ts", ".tsx", ".js", ".jsx", ".cs", ".rs", ".go", ".c", ".cpp", ".cc", ".h", ".hpp", ".scala", ".rb")):
                    continue
                    
                content = self.file_system.read_file(file_path)
                if old_text in content:
                    new_content, count = pattern.subn(new_text, content)
                    if count > 0:
                        if not dry_run:
                            self.file_system.write_file(file_path, new_content)
                        files_changed += 1
                        total_replacements += count
                    
            return OperationResult(True, "Success", files_changed, total_replacements)
        except Exception as e:
            return OperationResult(False, str(e), 0, 0)

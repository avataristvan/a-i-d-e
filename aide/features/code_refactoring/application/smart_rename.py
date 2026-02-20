import os
import re
from aide.core.domain.ports import FileSystemPort
from aide.core.domain.models import OperationResult

class SmartRenameUseCase:
    def __init__(self, file_system: FileSystemPort):
        self.file_system = file_system

    def execute(self, root_path: str, old_text: str, new_text: str, use_word_boundary: bool = False, dry_run: bool = False) -> OperationResult:
        files_changed = 0
        total_replacements = 0
        
        try:
            # Prepare pattern
            if use_word_boundary:
                pattern = re.compile(rf"\b{re.escape(old_text)}\b")
            else:
                pattern = re.compile(re.escape(old_text))
            
            for file_path in self.file_system.walk_files(root_path):
                # Only check relevant file types
                if not file_path.endswith((".kt", ".java", ".xml", ".gradle", ".toml", ".py", ".md", ".ts", ".tsx", ".js", ".jsx", ".cs", ".rs", ".go", ".c", ".cpp", ".cc", ".h", ".hpp", ".scala", ".rb")):
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

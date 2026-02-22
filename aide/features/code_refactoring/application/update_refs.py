import os
import re
from aide.core.domain.ports import FileSystemPort
from aide.core.domain.models import OperationResult

class UpdateReferencesUseCase:
    def __init__(self, file_system: FileSystemPort):
        self.file_system = file_system

    def execute(self, root_path: str, old_fqdn: str, new_fqdn: str, dry_run: bool = False) -> OperationResult:
        files_changed = 0
        total_replacements = 0
        
        try:
            # We must be careful to match exact fully qualified names to avoid partial substring replacements.
            # In Kotlin/Java: import com.example.old.MyClass -> import com.example.new.MyClass
            # In XML: <com.example.old.MyClass> -> <com.example.new.MyClass>
            
            # Use negative lookbehind and lookahead to ensure we match the whole FQDN
            # Note: We don't use \b here because dots are word boundaries in regex, so \bcom.example\b would match "com.example" in "foo.com.example.bar".
            # Instead, we want to match exactly the string, not preceded or followed by word characters.
            pattern_str = r'(?<![\w\.])' + re.escape(old_fqdn) + r'(?![\w\.])'
            pattern = re.compile(pattern_str)
            
            for file_path in self.file_system.walk_files(root_path):
                # Only check relevant file types
                if not file_path.endswith((".kt", ".java", ".xml", ".gradle", ".gradle.kts", ".toml", ".py", ".md", ".ts", ".tsx", ".js", ".jsx", ".cs", ".rs", ".go", ".c", ".cpp", ".cc", ".h", ".hpp", ".scala", ".rb")):
                    continue
                    
                content = self.file_system.read_file(file_path)
                if old_fqdn in content:
                    new_content, count = pattern.subn(new_fqdn, content)
                    if count > 0:
                        if not dry_run:
                            self.file_system.write_file(file_path, new_content)
                        files_changed += 1
                        total_replacements += count
                    
            return OperationResult(True, "Success", files_changed, total_replacements)
        except Exception as e:
            return OperationResult(False, str(e), 0, 0)

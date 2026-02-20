import os
from aide.core.domain.ports import FileSystemPort
from aide.parsing.domain.ports import LanguageParserPort

class AuditKotlinUseCase:
    """Audits a Kotlin codebase for Clean Architecture violations."""
    
    def __init__(self, file_system: FileSystemPort, language_parser: LanguageParserPort):
        self.file_system = file_system
        self.language_parser = language_parser

    def execute(self, src_path: str) -> dict:
        violations = []
        
        # Use secure file_system walk instead of raw os.walk
        try:
            files = list(self.file_system.walk_files(src_path))
        except Exception as e:
             return {"success": False, "error": f"Failed to traverse path: {e}"}

        for full_path in files:
            if not full_path.endswith(".kt"):
                continue
            
            # Since walk_files returns absolute paths, we calculate rel_path based on src_path 
            # (which itself is resolved relative to the jail in FileSystem, but we can just use string matching for the audit rules)
            # The original code used os.path.relpath(full_path, base_path).
            # We must be careful here since full_path is an absolute path.
            # Let's derive a relative path for the rules to work.
            try:
                # Assuming src_path is relative to the current working directory, 
                # we can find the relative path from the absolute full_path and absolute src_path
                abs_src = os.path.abspath(src_path)
                rel_path = os.path.relpath(full_path, abs_src)
            except ValueError:
                rel_path = full_path

            # Check file line count (God Class detection)
            try:
                content = self.file_system.read_file(full_path)
                lines = content.splitlines()
                if len(lines) > 400:
                    violations.append(f"{rel_path}: File too large ({len(lines)} lines). Consider splitting.")
                
                # Use Parser for Imports
                imports = self.language_parser.parse_imports(content, ".kt")
                
                for imp in imports:
                    # Rule 1: Domain Purity
                    if "/domain/" in rel_path or rel_path.startswith("domain/"):
                        if "android." in imp and "android.util" not in imp: 
                            violations.append(f"{rel_path}: Domain purity violation (imports '{imp}')")
                        
                        if ".infrastructure" in imp:
                            violations.append(f"{rel_path}: Domain cannot import Infrastructure (imports '{imp}')")
                            
                    # Rule 2: Application Layer
                    if "/application/" in rel_path or rel_path.startswith("application/"):
                        if ".infrastructure" in imp:
                            violations.append(f"{rel_path}: Application cannot import Infrastructure (imports '{imp}')")

                    # Rule 3: Feature Isolation
                    if "features/" in rel_path and ".features." in imp:
                        current_feature = rel_path.split("features/")[1].split("/")[0]
                        if f".features.{current_feature}" not in imp and "core." not in imp:
                             pass 
                             
            except Exception as e:
                violations.append(f"{rel_path}: Error reading file: {e}")

        success = len(violations) == 0
        message = "Kotlin Architecture is Clean!" if success else f"Found {len(violations)} Violations"
        
        return {
            "success": success,
            "message": message,
            "data": {
                "violations": violations
            }
        }

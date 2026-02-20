import json
from argparse import _SubParsersAction
import re
from aide.core.context import Context
from aide.core.domain.models import OperationResult

class CleanupPlugin:
    def register(self, subparsers: _SubParsersAction, context: Context) -> None:
        parser = subparsers.add_parser("cleanup", help="Run code cleanup tasks")
        parser.add_argument("--path", default=".", help="Root path to cleanup")
        parser.set_defaults(func=lambda args: self.run(args, context))

    def run(self, args, context: Context):
        unused_result = self.remove_unused_imports(args.path, context)
        duplicate_result = self.remove_duplicate_imports(args.path, context)
        
        result = {
            "success": True,
            "message": "Cleanup Complete.",
            "data": {
                "unused_imports_removed": unused_result,
                "duplicate_imports_removed": duplicate_result
            }
        }
        
        print(json.dumps(result, indent=2))

    def remove_unused_imports(self, root_path: str, context: Context) -> dict:
        files_cleaned = 0
        total_removed = 0
        details = []
        
        for file_path in context.file_system.walk_files(root_path):
            if file_path.endswith((".txt", ".md", ".json", ".ini", ".toml")):
                continue
                
            content = context.file_system.read_file(file_path)
            lines = content.split('\n')
            
            # Fetch the strategy for the current language
            strategy = context.strategy_provider.get_strategy(file_path)
            
            # extract_imports_and_header returns the full lines
            # This is tricky because we need to know WHICH line it was to remove it.
            # And we have to extract the symbol to check if it's used.
            # Let's fallback to the LanguageParser to get the exact imports, or just regex it.
            # The original logic used regex. Let's adapt it slightly.
            
            # Given that extract_unused_imports is hard to generalize perfectly without AST,
            # we will rely on a language-agnostic heuristic:
            # 1. Look for 'import ' or 'from ' or 'use '
            # 2. Extract the last word as the symbol
            # 3. Check if that word exists elsewhere in the file.
            
            original_content = content
            imports_to_remove = []
            
            # Pass 1: Identify imports
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith(("import ", "from ", "use ")) and not stripped.startswith(("import //", "use //")):
                    parts = stripped.replace(';', '').split()
                    if len(parts) >= 2:
                        path = parts[1] if not stripped.startswith("from ") else parts[3] if len(parts) > 3 else parts[-1]
                        if path.endswith("*"): continue
                        
                        symbol = path.split('.')[-1].split('::')[-1].split('/')[-1]
                        if " as " in stripped: symbol = parts[-1]
                            
                        is_used = False
                        for j, check_line in enumerate(lines):
                            if i == j: continue 
                            params = re.escape(symbol)
                            pattern = f"\\b{params}\\b"
                            if re.search(pattern, check_line):
                                is_used = True
                                break
                        
                        if not is_used:
                            imports_to_remove.append(i)

            if imports_to_remove:
                new_lines = [line for i, line in enumerate(lines) if i not in imports_to_remove]
                new_content = '\n'.join(new_lines)
                context.file_system.write_file(file_path, new_content)
                files_cleaned += 1
                total_removed += len(imports_to_remove)
                details.append({"file": file_path, "removed_count": len(imports_to_remove)})

        return {
            "files_cleaned": files_cleaned,
            "total_removed": total_removed,
            "details": details
        }

    def remove_duplicate_imports(self, root_path: str, context: Context) -> dict:
        files_cleaned = 0
        total_removed = 0
        details = []
        
        for file_path in context.file_system.walk_files(root_path):
            if file_path.endswith((".txt", ".md", ".json", ".ini", ".toml")):
                continue
                
            content = context.file_system.read_file(file_path)
            lines = content.split('\n')
            
            seen_imports = set()
            new_lines = []
            duplicates_found = 0
            
            for line in lines:
                stripped = line.strip()
                # Unified heuristic for imports across languages
                is_import = stripped.startswith(("import ", "from ", "use "))
                
                if is_import:
                    if stripped in seen_imports:
                        duplicates_found += 1
                        continue # Skip duplicate
                    seen_imports.add(stripped)
                
                new_lines.append(line)

            if duplicates_found > 0:
                new_content = '\n'.join(new_lines)
                context.file_system.write_file(file_path, new_content)
                files_cleaned += 1
                total_removed += duplicates_found
                details.append({"file": file_path, "removed_count": duplicates_found})

        return {
            "files_cleaned": files_cleaned,
            "total_removed": total_removed,
            "details": details
        }

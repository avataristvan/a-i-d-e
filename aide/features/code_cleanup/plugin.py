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
        print(f"🧹 Running cleanup on {args.path}...")
        self.remove_unused_imports(args.path, context)
        self.remove_duplicate_imports(args.path, context)
        print("✅ Cleanup Complete.")

    def remove_unused_imports(self, root_path: str, context: Context):
        print("   - Scanning for unused imports...")
        files_cleaned = 0
        total_removed = 0
        
        for file_path in context.file_system.walk_files(root_path):
            if not file_path.endswith(".kt"):
                continue
                
            content = context.file_system.read_file(file_path)
            lines = content.split('\n')
            
            original_content = content
            imports_to_remove = []
            
            # Pass 1: Identify imports
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("import ") and not stripped.startswith("import //"):
                    parts = stripped.split()
                    if len(parts) >= 2:
                        path = parts[1]
                        if path.endswith("*"): continue
                        
                        symbol = path.split('.')[-1]
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
                print(f"     - Cleaned {len(imports_to_remove)} imports in {file_path}")

        print(f"   Files cleaned: {files_cleaned}")
        print(f"   Unused imports removed: {total_removed}")

    def remove_duplicate_imports(self, root_path: str, context: Context):
        print("   - Scanning for duplicate imports...")
        files_cleaned = 0
        total_removed = 0
        
        for file_path in context.file_system.walk_files(root_path):
            if not file_path.endswith((".kt", ".ts", ".js", ".py")):
                continue
                
            content = context.file_system.read_file(file_path)
            lines = content.split('\n')
            
            seen_imports = set()
            new_lines = []
            duplicates_found = 0
            
            for line in lines:
                stripped = line.strip()
                # Unified heuristic for imports across languages
                is_import = stripped.startswith(("import ", "from "))
                
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
                print(f"     - Removed {duplicates_found} duplicates in {file_path}")

        print(f"   Files cleaned: {files_cleaned}")
        print(f"   Duplicate imports removed: {total_removed}")

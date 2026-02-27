import os
import re
from typing import Any, Tuple, Callable, Generator

class MoveSymbolUseCase:
    def __init__(self, file_system, language_parser, strategy_provider):
        self.file_system = file_system
        self.language_parser = language_parser
        self.strategy_provider = strategy_provider

    def execute(self, source_file: str, symbol_names_str: str, dest_file: str, dry_run: bool = False, root_path: str = ".") -> bool:
        try:
            source_path = os.path.abspath(source_file)
            dest_path = os.path.abspath(dest_file)
            
            if not os.path.exists(source_path):
                return False

            # Batch processing
            symbols = [s.strip() for s in symbol_names_str.split(",") if s.strip()]
            
            # Get language-specific strategy
            strategy = self.strategy_provider.get_strategy(source_path)
            
            # Read source
            content = self.file_system.read_file(source_path)
            lines = content.splitlines()
            source_imports, source_header = strategy.extract_imports_and_header(lines)
            
            # 1. Prepare Destination Content
            dest_content = ""
            existing_dest_lines = []
            dest_imports = []
            dest_package = ""
            
            if os.path.exists(dest_path):
                dest_content = self.file_system.read_file(dest_path)
                existing_dest_lines = dest_content.splitlines()
                dest_imports, dest_header = strategy.extract_imports_and_header(existing_dest_lines)
            else:
                # Infer package header (if any)
                dest_header = strategy.get_package_header(dest_path)
                if not dest_header:
                     dest_header = source_header
                
                if dest_header:
                    dest_content = f"{dest_header}\n\n"
                if not dry_run:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # 2. Find and Extract Symbols
            ranges = []
            for symbol in symbols:
                start, end = strategy.find_symbol_range(lines, symbol)
                if start:
                    ranges.append((start, end, symbol))

            # Sort ranges by start line descending for safe deletion
            ranges.sort(key=lambda x: x[0], reverse=True)
            
            moved_blocks = []
            symbols_actually_moved = []
            
            for start, end, symbol in ranges:
                symbol_lines = lines[start - 1 : end]
                symbol_content = "\n".join(symbol_lines)
                symbol_content = strategy.adjust_visibility(symbol_content)
                symbol_content = symbol_content.rstrip()
                
                moved_blocks.append(symbol_content)
                symbols_actually_moved.append(symbol)
                
                # Delete from source buffer
                del lines[start - 1 : end]

            if not moved_blocks:
                return False

            # 3. Smart Import Merging
            # Identify which source imports are needed by the moved symbols
            needed_imports = []
            for block in moved_blocks:
                for imp in source_imports:
                    # Improved heuristic: matches 'Symbol' in 'from x import Symbol' 
                    # or 'import Symbol' or 'import pkg.Symbol'
                    parts = re.split(r'[ ,.]', imp)
                    # Filter out keywords and empty strings
                    symbols_in_import = [p.strip() for p in parts if p.strip() and p.strip() not in {"from", "import", "as"}]
                    
                    match_found = False
                    for s in symbols_in_import:
                        if re.search(rf"\b{re.escape(s)}\b", block):
                            match_found = True
                            break
                    
                    if match_found:
                        if imp not in dest_imports and imp not in needed_imports:
                            needed_imports.append(imp)

            # 4. Integrate into Destination
            # If file exists, find the best place for new imports
            if existing_dest_lines:
                # Append symbols at the end
                if not dest_content.endswith("\n\n") and dest_content.strip():
                    dest_content = dest_content.rstrip() + "\n\n"
                
                for block in reversed(moved_blocks):
                    dest_content += block + "\n\n"
                
                # Insert missing imports
                if needed_imports:
                    import_block = "\n".join(needed_imports) + "\n"
                    # Find last import line or package line
                    last_imp_idx = -1
                    pkg_idx = -1
                    dest_lines = dest_content.splitlines()
                    for i, line in enumerate(dest_lines):
                        if line.startswith("import ") or line.startswith("from "): last_imp_idx = i
                        if dest_header and line.startswith(dest_header.split()[0]): 
                            pkg_idx = i
                    
                    if last_imp_idx != -1:
                        dest_lines.insert(last_imp_idx + 1, import_block)
                    elif pkg_idx != -1:
                        dest_lines.insert(pkg_idx + 1, "\n" + import_block)
                    else:
                        dest_lines.insert(0, import_block + "\n")
                    dest_content = "\n".join(dest_lines)
            else:
                # New file
                dest_content += "\n".join(needed_imports) + "\n\n"
                for block in reversed(moved_blocks):
                    dest_content += block + "\n\n"

            # 5. Project-wide Reference Updates
            source_pkg_name = strategy.get_module_path(source_path)
            dest_pkg_name = strategy.get_module_path(dest_path)
            
            if source_pkg_name != dest_pkg_name:
                for symbol in symbols_actually_moved:
                    old_import = strategy.get_import_statement(source_pkg_name, symbol)
                    new_import = strategy.get_import_statement(dest_pkg_name, symbol)
                    self._update_references(old_import, new_import, dry_run, root_path)

            # 6. Write Files
            if moved_blocks:
                if not dry_run:
                    self.file_system.write_file(dest_path, dest_content.strip() + "\n")
                    self.file_system.write_file(source_path, "\n".join(lines).strip() + "\n")
                return True
            
            return False

        except Exception as e:
            return False

    def _update_references(self, old_text: str, new_text: str, dry_run: bool, root: str = "."):
        # Scan all supported files in project
        extensions = (".kt", ".java", ".py", ".ts", ".tsx", ".js", ".jsx", ".xml")
        for file_path in self.file_system.walk_files(root):
            if file_path.endswith(extensions):
                content = self.file_system.read_file(file_path)
                if old_text in content:
                    if new_text in content:
                        # If the new import already exists, just remove the old one (to avoid duplicates)
                        # We need to be careful with line breaks.
                        new_content = content.replace(old_text + "\n", "").replace(old_text, "")
                    else:
                        new_content = content.replace(old_text, new_text)
                    
                    if not dry_run:
                        self.file_system.write_file(file_path, new_content)


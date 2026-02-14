import os
import re
from typing import List
from aide.features.code_inspection.application.find_usages import FindUsagesUseCase

class ChangeSignatureUseCase:
    def __init__(self, file_system, language_parser, strategy_provider):
        self.file_system = file_system
        self.language_parser = language_parser
        self.strategy_provider = strategy_provider
        self.find_usages = FindUsagesUseCase(file_system, language_parser)

    def execute(self, root_path: str, symbol_name: str, new_param_def: str, default_value: str, dry_run: bool = False) -> bool:
        # 1. Find all usages (including definition!)
        # Note: FindUsages might define "definition" as a usage depending on regex.
        # But usually we want to distinguish.
        
        # New approach: 
        # 1. Find the definition file and line.
        # 2. Find all call sites.
        
        print(f"🔎 Scanning for '{symbol_name}'...")
        locations = self.find_usages.execute(root_path, symbol_name)
        
        if not locations:
            print(f"❌ Symbol '{symbol_name}' not found.")
            return False

        # Group by file to minimize IO
        files_map = {}
        for loc in locations:
            path, line, col = loc.split(":")
            if path not in files_map:
                files_map[path] = []
            files_map[path].append((int(line), int(col)))

        total_updates = 0
        
        for relative_path, hits in files_map.items():
            full_path = os.path.join(root_path, relative_path)
            try:
                content = self.file_system.read_file(full_path)
                lines = content.splitlines()
                strategy = self.strategy_provider.get_strategy(full_path)
                
                # Sort hits in reverse so we don't mess up offsets if multiple per line (though usually 1 func call per line)
                # But here we are processing line by line.
                
                updated_lines_indices = set()
                
                for line_idx, col_idx in hits:
                     # 0-indexed line
                     idx = line_idx - 1
                     line = lines[idx]
                     
                     is_definition = strategy.is_definition(line, symbol_name)
                     
                     if idx in updated_lines_indices:
                         continue # Already touched this line
                         
                     if is_definition:
                         # Update Definition
                         # Replace ")" with ", new_param)"
                         # Needs careful regex to find the matching closing paren of the signature.
                         # Simplified: find the last ')' on the line? 
                         # Danger: fun foo(a: (Int)->Unit)
                         
                         # Let's try simple regex replacement for V1
                         # pattern: symbol_name\s*\( ... \)
                         
                         # Regex to find arguments: `symbol_name\s*\((.*)\)`
                         # We want to insert before the last `)` that closes the arguments.
                         
                         # V1 Hack: Replace `)` with `, new_param)` 
                         # BUT only the one corresponding to the function.
                         
                         new_line = strategy.update_signature_string(line, symbol_name, is_definition=True, insertion=new_param_def)
                         if new_line != line:
                             if dry_run:
                                 print(f"   [Dry Run] Would update definition in {relative_path}:{line_idx}")
                             else:
                                 lines[idx] = new_line
                                 updated_lines_indices.add(idx)
                                 total_updates += 1
                                 print(f"   Updated definition in {relative_path}:{line_idx}")

                     else:
                         # Update Call Site
                         # append default_value
                         if default_value:
                             new_line = strategy.update_signature_string(line, symbol_name, is_definition=False, insertion=default_value)
                             if new_line != line:
                                 if dry_run:
                                     print(f"   [Dry Run] Would update call in {relative_path}:{line_idx}")
                                 else:
                                     lines[idx] = new_line
                                     updated_lines_indices.add(idx)
                                     total_updates += 1
                                     print(f"   Updated call in {relative_path}:{line_idx}")

                if not dry_run:
                    self.file_system.write_file(full_path, "\n".join(lines))

            except Exception as e:
                print(f"❌ Failed to update {relative_path}: {e}")

        print(f"✅ Updated {total_updates} locations.")
        return True


import os
import re
from typing import List, Tuple

class FindUsagesUseCase:
    def __init__(self, file_system, language_parser):
        self.file_system = file_system
        self.language_parser = language_parser

    def execute(self, root_path: str, symbol_name: str) -> List[str]:
        usages = []
        try:
            # 1. Walk through all files in root_path
            for dirpath, _, filenames in os.walk(root_path):
                for filename in filenames:
                    # Filter for source files (e.g. .kt, .java, .py)
                    if not filename.endswith(('.kt', '.java', '.py')):
                        continue
                        
                    file_path = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(file_path, root_path)
                    
                    try:
                        content = self.file_system.read_file(file_path)
                        lines = content.splitlines()
                        
                        for i, line in enumerate(lines):
                            # Simple regex match for the symbol
                            # We want whole word matches
                            matches = list(re.finditer(rf"\b{re.escape(symbol_name)}\b", line))
                            
                            for match in matches:
                                # Context Check: Is it a comment?
                                # Naive check: if // or # appears before the match
                                pre_match = line[:match.start()]
                                if '//' in pre_match or '#' in pre_match:
                                    continue # Skip likely comments
                                    
                                # Context Check: Is it an import?
                                if line.strip().startswith("import ") or line.strip().startswith("package "):
                                    continue # Skip imports/package decls
                                    
                                # Found a usage!
                                usage_str = f"{relative_path}:{i+1}:{match.start()+1}"
                                usages.append(usage_str)
                                
                    except Exception as e:
                        # Skip files we can't read
                        continue
                        
            return usages

        except Exception as e:
            print(f"❌ Find usages failed: {e}")
            return []

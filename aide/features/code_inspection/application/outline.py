import os
import fnmatch
from typing import List
from aide.core.domain.ports import FileSystemPort
from aide.parsing.domain.ports import LanguageParserPort

class OutlineUseCase:
    def __init__(self, file_system: FileSystemPort, parser: LanguageParserPort):
        self.file_system = file_system
        self.parser = parser

    def execute(self, file_pattern: str) -> str:
        output = []
        found_files = False
        
        # Start from root (which is where aide.py runs)
        for file_path in self.file_system.walk_files("."): 
            if fnmatch.fnmatch(os.path.basename(file_path), file_pattern) or fnmatch.fnmatch(file_path, file_pattern):
                found_files = True
                output.append(f"## File: {file_path}")
                
                content = self.file_system.read_file(file_path)
                ext = os.path.splitext(file_path)[1]
                
                symbols = self.parser.parse(content, ext)
                if symbols:
                    for symbol in symbols:
                        icon = "?"
                        k = symbol.kind.lower()
                        if "class" in k: icon = "C"
                        elif "function" in k or "method" in k: icon = "f"
                        elif "interface" in k: icon = "I"
                        elif "type" in k: icon = "T"
                        elif "enum" in k: icon = "E"
                        elif "component" in k: icon = "R" # React
                        elif "hook" in k: icon = "h" # Hook
                        
                        output.append(f"- [{icon}] {symbol.name} (L{symbol.line_number})")
                else:
                    output.append("  (No symbols found)")
                
                output.append("") # Empty line
        
        if not found_files:
            return f"No files found matching pattern: {file_pattern}"
            
        return "\n".join(output)

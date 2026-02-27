import re
import os
from typing import Any, Tuple, Callable, Generator
from aide.core.domain.ports import LanguageStrategy

class GoLanguageStrategy(LanguageStrategy):
    """
    Go-specific refactoring strategy.
    Handles 'package', 'import', and bracket-based block detection.
    """
    def extract_imports_and_header(self, lines: list[str]) -> tuple[list[str], str | None]:
        """Extracts 'package' and 'import' statements."""
        imports = []
        header = None
        in_import_block = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("package ") and header is None:
                header = stripped
            elif stripped.startswith("import ("):
                in_import_block = True
            elif in_import_block:
                if stripped == ")":
                    in_import_block = False
                elif stripped:
                    imports.append(f"import {stripped}")
            elif stripped.startswith("import "):
                imports.append(stripped)
                
        return imports, header

    def get_package_header(self, file_path: str) -> str | None:
        pkg = self.get_module_path(file_path)
        # In Go, the package name is usually the directory name.
        pkg_name = pkg.split("/")[-1] if pkg else "main"
        return f"package {pkg_name}"

    def get_module_path(self, file_path: str) -> str:
        """Returns the package path relative to the current directory."""
        rel_path = os.path.relpath(file_path, ".")
        return os.path.dirname(rel_path).replace(os.sep, "/")

    def adjust_visibility(self, content: str) -> str:
        """Adjusts visibility by capitalizing the first letter of the symbol definition."""
        # This is a bit tricky with regex for all cases, but we'll try for common ones.
        # e.g. 'func myFunc' -> 'func MyFunc'
        def capitalize(match):
            keyword = match.group(1)
            name = match.group(2)
            return f"{keyword} {name[0].upper()}{name[1:]}"

        return re.sub(r'\b(func|type|struct|interface|const|var)\s+([a-z][a-zA-Z0-9_]*)\b', capitalize, content)

    def find_symbol_range(self, lines: list[str], symbol: str) -> tuple[int | None, int | None]:
        """Finds the start and end lines of a Go symbol using bracket matching."""
        # Matches: func [receiver] SymbolName(...)
        # Or type SymbolName ...
        pattern = re.compile(rf"\b(func|type|const|var)\s+(\([^)]+\)\s+)?{re.escape(symbol)}\b")
        
        start_line = -1
        for i, line in enumerate(lines):
            if pattern.search(line):
                start_line = i + 1
                break
        
        if start_line == -1:
            return None, None

        # Include comments above
        curr = start_line - 1
        while curr > 0:
            prev_line = lines[curr - 1].strip()
            if prev_line.startswith("//") or prev_line.startswith("/*") or prev_line.endswith("*/") or prev_line == "":
                start_line = curr
                curr -= 1
            else:
                break

        balance = 0
        found_open = False
        end_line = -1
        
        for i in range(start_line - 1, len(lines)):
            line = lines[i]
            for char in line:
                if char == '{':
                    balance += 1
                    found_open = True
                elif char == '}':
                    balance -= 1
            
            if found_open and balance == 0:
                end_line = i + 1
                break
        
        # Handle cases without blocks (e.g. simple types, vars)
        if not found_open:
            if "(" in lines[start_line-1]: # Multi-line const/var block?
                 balance = 0
                 for i in range(start_line-1, len(lines)):
                     for char in lines[i]:
                         if char == '(': balance += 1
                         elif char == ')': balance -= 1
                     if balance == 0:
                         end_line = i + 1
                         break
            else:
                end_line = start_line
                    
        if end_line == -1:
             return None, None
             
        return start_line, end_line

    def get_import_statement(self, package: str, symbol: str) -> str:
        # Go usually imports by package path, and then uses PackageName.Symbol
        return f'import "{package}"'

    def find_variables(self, text: str) -> set[str]:
        keywords = {
            "break", "default", "func", "interface", "select", "case", "defer", "go", "map", "struct", "chan", "else", "goto", "package", "switch", "const", "fallthrough", "if", "range", "type", "continue", "for", "import", "return", "var", "nil", "true", "false", "iota", "make", "new", "len", "cap", "append", "copy", "close", "delete", "complex", "real", "imag", "panic", "recover", "print", "println"
        }
        matches = re.findall(r'\b[a-z_][a-zA-Z0-9_]*\b', text)
        return set([m for m in matches if m not in keywords])

    def is_defined_in_outer_scope(self, var_name: str, context_text: str) -> bool:
        # Check for := or var
        patterns = [
            rf"\b{var_name}\s*:=\s*",
            rf"\bvar\s+{var_name}\b",
            rf"func\s+.*\(.*\b{var_name}\b"
        ]
        return any(re.search(p, context_text) for p in patterns)

    def infer_types(self, parameters: list[str], context_text: str) -> list[tuple[str, str]]:
        typed = []
        for var in parameters:
            # Match "var Type"
            match = re.search(rf"\b{var}\s+([\w\.\*\[\]]+)", context_text)
            typed.append((var, match.group(1).strip() if match else "interface{}"))
        return typed

    def get_function_template(self, name: str, params_str: str, body: list[str], scope: str, indent: str) -> str:
        actual_name = f"{name[0].upper()}{name[1:]}" if scope in {"public", "internal"} else name
        code = f"\n\n{indent}func {actual_name}({params_str}) {{\n"
        for line in body:
            code += line + "\n"
        code += f"{indent}}}\n"
        return code

    def get_function_call(self, name: str, args_str: str, indent: str) -> str:
        return f"{indent}{name}({args_str})"

    def is_definition(self, line: str, symbol: str) -> bool:
        return re.search(rf"\b(func|type|const|var)\s+(\([^)]+\)\s+)?{symbol}\b", line) is not None

    def update_signature_string(self, line: str, symbol: str, is_definition: bool, insertion: str) -> str:
        match = re.search(rf"\b{re.escape(symbol)}\s*\(", line)
        if not match:
            return line
            
        start_paren_index = match.end() - 1
        balance = 1
        i = start_paren_index + 1
        last_paren_index = -1
        
        while i < len(line):
            char = line[i]
            if char == '(': balance += 1
            elif char == ')': balance -= 1
            if balance == 0:
                last_paren_index = i
                break
            i += 1
            
        if last_paren_index != -1:
            args_content = line[start_paren_index+1:last_paren_index].strip()
            prefix = ", " if args_content else ""
            return line[:last_paren_index] + prefix + insertion + line[last_paren_index:]
            
        return line

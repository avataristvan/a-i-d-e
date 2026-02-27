import re
import os
from typing import Any, Tuple, Callable, Generator
from aide.core.domain.ports import LanguageStrategy

class KotlinLanguageStrategy(LanguageStrategy):
    def extract_imports_and_header(self, lines: list[str]) -> tuple[list[str], str | None]:
        imports = []
        header = None
        for line in lines:
            if line.strip().startswith("package "):
                header = line.strip()
            elif line.strip().startswith("import "):
                imports.append(line.strip())
        return imports, header

    def get_package_header(self, file_path: str) -> str | None:
        pkg = self.get_module_path(file_path)
        return f"package {pkg}" if pkg else None

    def get_module_path(self, file_path: str) -> str:
        parts = file_path.split(os.sep)
        try:
            if "java" in parts:
                idx = parts.index("java")
                pkg_parts = parts[idx+1:-1]
                return ".".join(pkg_parts)
            elif "kotlin" in parts:
                idx = parts.index("kotlin")
                pkg_parts = parts[idx+1:-1]
                return ".".join(pkg_parts)
        except:
            pass
        return ""

    def adjust_visibility(self, content: str) -> str:
        return re.sub(r'\bprivate\s+(fun|class|object|interface|val|var)\b', r'\1', content)

    def find_symbol_range(self, lines: list[str], symbol: str) -> tuple[int | None, int | None]:
        pattern = re.compile(rf"\b(fun|class|interface|object)\s+([\w\.]+\.)?{re.escape(symbol)}\b")
        start_line = -1
        for i, line in enumerate(lines):
            if pattern.search(line):
                 start_line = i + 1
                 break
        
        if start_line == -1:
            return None, None
            
        curr = start_line - 1
        while curr > 0:
            prev_line = lines[curr - 1].strip()
            if prev_line.startswith("@") or prev_line.startswith("//") or prev_line == "":
                if prev_line.startswith("@"):
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
                
        if end_line == -1:
             return None, None
             
        return start_line, end_line

    def get_import_statement(self, package: str, symbol: str) -> str:
        pkg_name = package.replace("package ", "").strip()
        return f"import {pkg_name}.{symbol}"

    def find_variables(self, text: str) -> set:
        keywords = {"val", "var", "if", "else", "for", "while", "return", "fun", "class", "true", "false", "null", "this", "super", "in", "is", "as", "package", "import"}
        matches = re.findall(r'\b[a-z][a-zA-Z0-9_]*\b', text)
        return set([m for m in matches if m not in keywords])

    def is_defined_in_outer_scope(self, var_name: str, context_text: str) -> bool:
        patterns = [rf"\bval\s+{var_name}\b", rf"\bvar\s+{var_name}\b", rf"\b{var_name}\s*:"]
        return any(re.search(p, context_text) for p in patterns)

    def infer_types(self, parameters: list[str], context_text: str) -> list[tuple[str, str]]:
        typed = []
        for var in parameters:
            match = re.search(rf"\b(?:val|var)\s+{var}\s*:\s*([\w<>?]+)", context_text)
            if not match:
                match = re.search(rf"\b{var}\s*:\s*([\w<>?]+)", context_text)
            typed.append((var, match.group(1) if match else "Any"))
        return typed

    def get_function_template(self, name: str, params_str: str, body: list[str], scope: str, indent: str) -> str:
        code = f"\n\n{indent}{scope} fun {name}({params_str}) {{\n"
        for line in body:
            code += line + "\n"
        code += f"{indent}}}\n"
        return code

    def get_function_call(self, name: str, args_str: str, indent: str) -> str:
        return f"{indent}{name}({args_str})"

    def is_definition(self, line: str, symbol: str) -> bool:
        return f"fun {symbol}" in line or f"def {symbol}" in line

    def update_signature_string(self, line: str, symbol: str, is_definition: bool, insertion: str) -> str:
        # Find the "symbol(" start
        match = re.search(rf"\b{re.escape(symbol)}\s*\(", line)
        if not match:
            return line
            
        start_paren_index = match.end() - 1
        
        # Scan for balancing paren
        balance = 1
        i = start_paren_index + 1
        last_paren_index = -1
        
        while i < len(line):
            char = line[i]
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1
                
            if balance == 0:
                last_paren_index = i
                break
            i += 1
            
        if last_paren_index != -1:
            # Check if empty args "()"
            args_content = line[start_paren_index+1:last_paren_index].strip()
            
            prefix = ", " if args_content else ""
            
            # Insert before last paren
            return line[:last_paren_index] + prefix + insertion + line[last_paren_index:]
            
        return line

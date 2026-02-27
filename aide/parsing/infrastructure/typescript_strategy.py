import re
import os
from typing import Any, Tuple, Callable, Generator
from aide.core.domain.ports import LanguageStrategy

class TypeScriptLanguageStrategy(LanguageStrategy):
    def extract_imports_and_header(self, lines: list[str]) -> tuple[list[str], str | None]:
        imports = []
        header = None 
        
        # Heuristic for ESM imports (supports both single and multi-line)
        in_multiline_import = False
        current_import = ""
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("import ") or in_multiline_import:
                current_import += line + "\n"
                if "from " in stripped:
                    imports.append(current_import.strip())
                    current_import = ""
                    in_multiline_import = False
                else:
                    in_multiline_import = True
                    
        return imports, header

    def get_package_header(self, file_path: str) -> str | None:
        return None # TS is header-less

    def get_module_path(self, file_path: str) -> str:
        # TS usually uses relative or absolute paths. 
        # For simplicity, we'll use same relative-from-root as Python/Kotlin
        rel_path = os.path.relpath(file_path, ".")
        module_path = os.path.splitext(rel_path)[0]
        return module_path

    def adjust_visibility(self, content: str) -> str:
        stripped = content.strip()
        if not stripped.startswith("export "):
            return "export " + stripped
        return stripped

    def find_symbol_range(self, lines: list[str], symbol: str) -> tuple[int | None, int | None]:
        pattern = re.compile(rf"\b(export\s+)?(async\s+)?(function|class|interface|type|enum|const)\s+{re.escape(symbol)}\b")
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
            if prev_line.startswith("/*") or prev_line.startswith("*") or prev_line.startswith("//") or prev_line.startswith("@") or prev_line == "":
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
                
        if not found_open and start_line != -1:
            for i in range(start_line - 1, len(lines)):
                if ";" in lines[i]:
                    end_line = i + 1
                    break
            if end_line == -1: end_line = start_line
                
        return start_line, end_line

    def get_import_statement(self, package: str, symbol: str) -> str:
        return f"import {{ {symbol} }} from '{package}';"

    def find_variables(self, text: str) -> set[str]:
        keywords = {"const", "let", "var", "function", "class", "interface", "type", "enum", "if", "else", "for", "while", "return", "true", "false", "null", "this", "super", "export", "import", "async", "await", "yield", "from", "as"}
        matches = re.findall(r'\b[a-z][a-zA-Z0-9_]*\b', text)
        return set([m for m in matches if m not in keywords])

    def is_defined_in_outer_scope(self, var_name: str, context_text: str) -> bool:
        patterns = [rf"\bconst\s+{var_name}\b", rf"\blet\s+{var_name}\b", rf"\bvar\s+{var_name}\b", rf"\bfunction\s+{var_name}\b", rf"\b{var_name}\s*:"]
        return any(re.search(p, context_text) for p in patterns)

    def infer_types(self, parameters: list[str], context_text: str) -> list[tuple[str, str]]:
        typed = []
        for var in parameters:
            match = re.search(rf"\b{var}\s*:\s*([\w<>?\[\]]+)", context_text)
            typed.append((var, match.group(1) if match else "any"))
        return typed

    def get_function_template(self, name: str, params_str: str, body: list[str], scope: str, indent: str) -> str:
        visibility = "export " if scope in {"public", "internal"} else ""
        code = f"\n\n{indent}{visibility}function {name}({params_str}) {{\n"
        for line in body:
            code += line + "\n"
        code += f"{indent}}}\n"
        return code

    def get_function_call(self, name: str, args_str: str, indent: str) -> str:
        return f"{indent}{name}({args_str});"

    def is_definition(self, line: str, symbol: str) -> bool:
        return f"function {symbol}" in line or f"const {symbol}" in line or f"class {symbol}" in line

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

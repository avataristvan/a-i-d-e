import re
import os
from typing import Any, Tuple, Callable, Generator
from aide.core.domain.ports import LanguageStrategy

class ScalaLanguageStrategy(LanguageStrategy):
    """
    Scala-specific refactoring strategy.
    Handles 'package', 'import', and bracket-based block detection.
    """
    def extract_imports_and_header(self, lines: list[str]) -> tuple[list[str], str | None]:
        """Extracts 'package' and 'import' statements."""
        imports = []
        header = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("package ") and header is None:
                header = stripped
            elif stripped.startswith("import "):
                imports.append(stripped)
        return imports, header

    def get_package_header(self, file_path: str) -> str | None:
        pkg = self.get_module_path(file_path)
        return f"package {pkg}" if pkg else None

    def get_module_path(self, file_path: str) -> str:
        """Returns the dot-notated package path based on folder structure."""
        rel_path = os.path.relpath(file_path, ".")
        parts = os.path.dirname(rel_path).split(os.sep)
        # Often Scala projects have src/main/scala prefix
        if "scala" in parts:
            idx = parts.index("scala")
            parts = parts[idx+1:]
        
        parts = [p for p in parts if p and p != "."]
        return ".".join(parts)

    def adjust_visibility(self, content: str) -> str:
        """Removes private/protected modifiers for moved symbols."""
        return re.sub(r'\b(private|protected)(\[[^\]]+\])?\s+', '', content)

    def find_symbol_range(self, lines: list[str], symbol: str) -> tuple[int | None, int | None]:
        """Finds the start and end lines of a Scala symbol using bracket matching."""
        # Matches: class/object/trait/def [modifiers] SymbolName
        pattern = re.compile(rf"\b(class|object|trait|def|type|val|var)\s+{re.escape(symbol)}\b")
        
        start_line = -1
        for i, line in enumerate(lines):
            if pattern.search(line):
                start_line = i + 1
                break
        
        if start_line == -1:
            return None, None

        # Include annotations and comments above
        curr = start_line - 1
        while curr > 0:
            prev_line = lines[curr - 1].strip()
            if prev_line.startswith("@") or prev_line.startswith("//") or prev_line.startswith("/*") or prev_line.startswith("*") or prev_line == "":
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
        
        # Handle cases without blocks (one-liners or val/var/type definitions)
        if not found_open:
            # If it's a def/val/var on one line
            end_line = start_line
                    
        if end_line == -1:
             return None, None
             
        return start_line, end_line

    def get_import_statement(self, package: str, symbol: str) -> str:
        pkg_name = package.replace("package ", "").strip()
        return f"import {pkg_name}.{symbol}"

    def find_variables(self, text: str) -> set[str]:
        keywords = {
            "abstract", "case", "catch", "class", "def", "do", "else", "extends", "false", "final", "finally", "for", "forSome", "if", "implicit", "import", "lazy", "match", "new", "null", "object", "override", "package", "private", "protected", "return", "sealed", "super", "this", "throw", "trait", "true", "try", "type", "val", "var", "while", "with", "yield"
        }
        matches = re.findall(r'\b[a-z_][a-zA-Z0-9_]*\b', text)
        return set([m for m in matches if m not in keywords])

    def is_defined_in_outer_scope(self, var_name: str, context_text: str) -> bool:
        # Check for val, var or def
        patterns = [
            rf"\bval\s+{var_name}\b",
            rf"\bvar\s+{var_name}\b",
            rf"\bdef\s+{var_name}\b",
            rf"\b{var_name}\s*:"
        ]
        return any(re.search(p, context_text) for p in patterns)

    def infer_types(self, parameters: list[str], context_text: str) -> list[tuple[str, str]]:
        typed = []
        for var in parameters:
            # Match "var: Type"
            match = re.search(rf"\b{var}\s*:\s*([\w\[\],\. ]+)", context_text)
            typed.append((var, match.group(1).strip() if match else "Any"))
        return typed

    def get_function_template(self, name: str, params_str: str, body: list[str], scope: str, indent: str) -> str:
        # scope is ignored for now as Scala uses private/protected keywords handled in adjust_visibility
        code = f"\n\n{indent}def {name}({params_str}): Unit = {{\n"
        for line in body:
            code += line + "\n"
        code += f"{indent}}}\n"
        return code

    def get_function_call(self, name: str, args_str: str, indent: str) -> str:
        return f"{indent}{name}({args_str})"

    def is_definition(self, line: str, symbol: str) -> bool:
        return re.search(rf"\b(class|object|trait|def|val|var|type)\s+{symbol}\b", line) is not None

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

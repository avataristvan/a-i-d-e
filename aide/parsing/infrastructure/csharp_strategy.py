import re
import os
from typing import List, Tuple, Optional, Set
from aide.core.domain.ports import LanguageStrategy

class CSharpLanguageStrategy(LanguageStrategy):
    """
    C#-specific refactoring strategy.
    Handles imports (using), namespaces, and bracket-based block detection.
    """
    def extract_imports_and_header(self, lines: List[str]) -> Tuple[List[str], Optional[str]]:
        """Extracts all 'using' statements and the 'namespace' declaration."""
        imports = []
        header = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("using ") and ";" in stripped:
                imports.append(stripped)
            elif stripped.startswith("namespace ") and header is None:
                header = stripped.rstrip("{;").strip()
        return imports, header

    def get_package_header(self, file_path: str) -> Optional[str]:
        """Returns the namespace line for a new file based on its path."""
        pkg = self._get_namespace(file_path)
        return f"namespace {pkg}" if pkg else None

    def get_module_path(self, file_path: str) -> str:
        """Returns the C# namespace based on file path."""
        return self._get_namespace(file_path)

    def _get_namespace(self, file_path: str) -> str:
        """Helper to infer namespace from file path."""
        rel_path = os.path.relpath(file_path, ".")
        parts = os.path.dirname(rel_path).split(os.sep)
        # Filter out empty parts or '.'
        parts = [p for p in parts if p and p != "."]
        return ".".join(parts)

    def adjust_visibility(self, content: str) -> str:
        """C# visibility adjustment (e.g. ensuring internal/public)."""
        # Very simple heuristic: if it starts with private, make it internal or leave as is?
        # Standard approach in these strategies seems to be removing 'private'
        return re.sub(r'\bprivate\s+(class|interface|struct|enum|delegate|void|int|string|bool)\b', r'internal \1', content)

    def find_symbol_range(self, lines: List[str], symbol: str) -> Tuple[Optional[int], Optional[int]]:
        """Finds the start and end lines of a class, method, or interface using bracket matching."""
        # Pattern for class, interface, struct, enum or method definitions
        # Matches: [visibility] [modifiers] [type] SymbolName [inheritance/constraints]
        pattern = re.compile(rf"\b(class|interface|struct|enum|void|[\w<>[\]]+)\s+{re.escape(symbol)}\b")
        
        start_line = -1
        for i, line in enumerate(lines):
            if pattern.search(line):
                # Ensure it's not a call (simple check: no ';' right after if it's a method-like thing)
                # But for class/interface it's safer.
                # In C#, methods usually have '(' after Name.
                if "(" in line and ";" in line and not "{" in line:
                    # Likely a call or abstract/interface method declaration without body if in interface
                    # For now, let's assume definitions have '{' on same or next line.
                    pass
                
                start_line = i + 1
                break
        
        if start_line == -1:
            return None, None

        # Include attributes/comments above
        curr = start_line - 1
        while curr > 0:
            prev_line = lines[curr - 1].strip()
            if prev_line.startswith("[") or prev_line.startswith("//") or prev_line.startswith("/*") or prev_line.startswith("*") or prev_line == "":
                start_line = curr
                curr -= 1
            else:
                break

        balance = 0
        found_open = False
        end_line = -1
        
        for i in range(start_line - 1, len(lines)):
            line = lines[i]
            # Simple bracket counting
            for char in line:
                if char == '{':
                    balance += 1
                    found_open = True
                elif char == '}':
                    balance -= 1
            
            if found_open and balance == 0:
                end_line = i + 1
                break
        
        # Handle file-scoped namespaces if the symbol is the namespace itself? 
        # Usually we look for classes/methods.
        
        if end_line == -1:
             return None, None
             
        return start_line, end_line

    def get_import_statement(self, package: str, symbol: str) -> str:
        # package here is expected to be the namespace
        pkg_name = package.replace("namespace ", "").strip()
        return f"using {pkg_name};"

    def find_variables(self, text: str) -> Set[str]:
        keywords = {
            "abstract", "as", "base", "bool", "break", "byte", "case", "catch", "char", "checked", "class", "const", "continue", "decimal", "default", "delegate", "do", "double", "else", "enum", "event", "explicit", "extern", "false", "finally", "fixed", "float", "for", "foreach", "goto", "if", "implicit", "in", "int", "interface", "internal", "is", "lock", "long", "namespace", "new", "null", "object", "operator", "out", "override", "params", "private", "protected", "public", "readonly", "ref", "return", "sbyte", "sealed", "short", "sizeof", "stackalloc", "static", "string", "struct", "switch", "this", "throw", "true", "try", "typeof", "uint", "ulong", "unchecked", "unsafe", "ushort", "using", "virtual", "void", "volatile", "while", "var", "async", "await", "get", "set"
        }
        # C# allows @ prefix for identifiers
        matches = re.findall(r'\b[a-z_][a-zA-Z0-9_]*\b', text)
        return set([m for m in matches if m not in keywords])

    def is_defined_in_outer_scope(self, var_name: str, context_text: str) -> bool:
        # Check for assignment or declaration: Type var = ... or var var = ...
        patterns = [
            rf"\b(var|[\w<>[\]]+)\s+{var_name}\s*[=;]", 
            rf"\b{var_name}\s*="
        ]
        return any(re.search(p, context_text) for p in patterns)

    def infer_types(self, parameters: List[str], context_text: str) -> List[Tuple[str, str]]:
        typed = []
        for var in parameters:
            # Match "Type var" or "var var = (Type)..."
            match = re.search(rf"\b([\w<>[\]]+)\s+{var}\b", context_text)
            type_name = match.group(1) if match and match.group(1) != "var" else "object"
            typed.append((var, type_name))
        return typed

    def get_function_template(self, name: str, params_str: str, body: List[str], scope: str, indent: str) -> str:
        visibility = scope if scope else "public"
        code = f"\n\n{indent}{visibility} void {name}({params_str})\n{indent}{{\n"
        for line in body:
            code += line + "\n"
        code += f"{indent}}}\n"
        return code

    def get_function_call(self, name: str, args_str: str, indent: str) -> str:
        return f"{indent}{name}({args_str});"

    def is_definition(self, line: str, symbol: str) -> bool:
        # Simple check for method or class definition
        return re.search(rf"\b(class|interface|void|[\w<>[\]]+)\s+{symbol}\s*\(?", line) is not None

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

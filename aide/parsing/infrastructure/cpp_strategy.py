import re
import os
from typing import List, Tuple, Optional, Set
from aide.core.domain.ports import LanguageStrategy

class CppLanguageStrategy(LanguageStrategy):
    """
    C++-specific refactoring strategy.
    Handles #include, namespaces, and bracket-based block detection.
    """
    def extract_imports_and_header(self, lines: List[str]) -> Tuple[List[str], Optional[str]]:
        """Extracts #include and namespace declarations."""
        imports = []
        header = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#include"):
                imports.append(stripped)
            elif stripped.startswith("namespace ") and header is None:
                header = stripped.rstrip("{").strip()
        return imports, header

    def get_package_header(self, file_path: str) -> Optional[str]:
        ns = self.get_module_path(file_path)
        return f"namespace {ns} {{" if ns else None

    def get_module_path(self, file_path: str) -> str:
        """Returns the namespace based on folder structure."""
        rel_path = os.path.relpath(file_path, ".")
        parts = os.path.dirname(rel_path).split(os.sep)
        parts = [p for p in parts if p and p != "."]
        return "::".join(parts)

    def adjust_visibility(self, content: str) -> str:
        """C++ visibility is handled via public/private labels in classes."""
        # Simple heuristic: if we are moving to a class, we might need 'public:'
        return content

    def find_symbol_range(self, lines: List[str], symbol: str) -> Tuple[Optional[int], Optional[int]]:
        """Finds the start and end lines of a C++ symbol using bracket matching."""
        # Matches: class/struct/void/... SymbolName
        pattern = re.compile(rf"\b(class|struct|enum|void|[\w:<>[\]\*&]+)\s+{re.escape(symbol)}\b")
        
        start_line = -1
        for i, line in enumerate(lines):
            if pattern.search(line):
                # Ensure it's not a forward declaration
                if ";" in line and not "{" in line:
                    continue
                start_line = i + 1
                break
        
        if start_line == -1:
            return None, None

        # Include comments above
        curr = start_line - 1
        while curr > 0:
            prev_line = lines[curr - 1].strip()
            if prev_line.startswith("//") or prev_line.startswith("/*") or prev_line.startswith("*") or prev_line == "":
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
        
        # Handle cases without blocks (e.g. enum declarations on one line, variables)
        if not found_open:
            for i in range(start_line - 1, len(lines)):
                if ";" in lines[i]:
                    end_line = i + 1
                    break
                    
        if end_line == -1:
             return None, None
             
        return start_line, end_line

    def get_import_statement(self, package: str, symbol: str) -> str:
        # C++ uses #include. Assuming package is the header path here for simplicity.
        return f'#include "{package}.hpp"'

    def find_variables(self, text: str) -> Set[str]:
        keywords = {
            "alignas", "alignof", "and", "and_eq", "asm", "atomic_cancel", "atomic_commit", "atomic_noexcept", "auto", "bitand", "bitor", "bool", "break", "case", "catch", "char", "char8_t", "char16_t", "char32_t", "class", "compl", "concept", "const", "consteval", "constexpr", "constinit", "const_cast", "continue", "co_await", "co_return", "co_yield", "decltype", "default", "delete", "do", "double", "dynamic_cast", "else", "enum", "explicit", "export", "extern", "false", "float", "for", "friend", "goto", "if", "inline", "int", "long", "mutable", "namespace", "new", "noexcept", "not", "not_eq", "nullptr", "operator", "or", "or_eq", "private", "protected", "public", "reflexpr", "register", "reinterpret_cast", "requires", "return", "short", "signed", "sizeof", "static", "static_assert", "static_cast", "struct", "switch", "synchronized", "template", "this", "thread_local", "throw", "true", "try", "typedef", "typeid", "typename", "union", "unsigned", "using", "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq"
        }
        matches = re.findall(r'\b[a-z_][a-zA-Z0-9_]*\b', text)
        return set([m for m in matches if m not in keywords])

    def is_defined_in_outer_scope(self, var_name: str, context_text: str) -> bool:
        # Check for Type var = ... or auto var = ...
        patterns = [
            rf"\b(auto|[\w:<>[\]\*&]+)\s+{var_name}\s*[=;]", 
            rf"\b{var_name}\s*="
        ]
        return any(re.search(p, context_text) for p in patterns)

    def infer_types(self, parameters: List[str], context_text: str) -> List[Tuple[str, str]]:
        typed = []
        for var in parameters:
            # Match "Type var"
            match = re.search(rf"\b([\w:<>[\]\*&]+)\s+{var}\b", context_text)
            typed.append((var, match.group(1).strip() if match else "auto"))
        return typed

    def get_function_template(self, name: str, params_str: str, body: List[str], scope: str, indent: str) -> str:
        code = f"\n\n{indent}void {name}({params_str})\n{indent}{{\n"
        for line in body:
            code += line + "\n"
        code += f"{indent}}}\n"
        return code

    def get_function_call(self, name: str, args_str: str, indent: str) -> str:
        return f"{indent}{name}({args_str});"

    def is_definition(self, line: str, symbol: str) -> bool:
        return re.search(rf"\b(class|struct|enum|void|[\w:<>[\]\*&]+)\s+{symbol}\s*\(?", line) is not None

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

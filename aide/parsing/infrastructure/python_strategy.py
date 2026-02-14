import re
import os
from typing import List, Tuple, Optional, Set
from aide.core.domain.ports import LanguageStrategy

class PythonLanguageStrategy(LanguageStrategy):
    """
    Python-specific refactoring strategy.
    Uses indentation-based block detection for symbols.
    """
    def extract_imports_and_header(self, lines: List[str]) -> Tuple[List[str], Optional[str]]:
        """Extracts all 'import' and 'from ... import' statements."""
        imports = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                imports.append(stripped)
        return imports, None # Python has no package header in the file content

    def get_package_header(self, file_path: str) -> Optional[str]:
        """Python files do not require a package header."""
        return None

    def get_module_path(self, file_path: str) -> str:
        """Converts a file path to a logical Python module path (e.g. aide.core.context)."""
        rel_path = os.path.relpath(file_path, ".")
        module_path = os.path.splitext(rel_path)[0].replace(os.sep, ".")
        return module_path

    def adjust_visibility(self, content: str) -> str:
        """Python visibility is convention-based; no changes needed during move."""
        return content

    def find_symbol_range(self, lines: List[str], symbol: str) -> Tuple[Optional[int], Optional[int]]:
        """Finds the start and end lines of a class or function using indentation."""
        pattern = re.compile(rf"^(async\s+)?(def|class)\s+{re.escape(symbol)}\b")
        start_line = -1
        for i, line in enumerate(lines):
            if pattern.match(line.strip()):
                 start_line = i + 1
                 break
        
        if start_line == -1:
            return None, None

        start_line_orig = start_line
            
        # Include decorators above
        curr = start_line - 1
        while curr > 0:
            prev_line = lines[curr - 1].strip()
            if prev_line.startswith("@") or prev_line.startswith("#") or prev_line == "":
                start_line = curr
                curr -= 1
            else:
                break
                
        # Find end by indentation
        # CRITICAL: base_indent MUST be calculated from the def/class line, not decorators/empty lines above
        def_line = lines[start_line_orig - 1]
        base_indent = len(def_line) - len(def_line.lstrip())
        
        end_line = start_line_orig
        for i in range(start_line_orig, len(lines)):
            line = lines[i]
            if line.strip() == "":
                 continue
            indent = len(line) - len(line.lstrip())
            if indent <= base_indent:
                break
            end_line = i + 1
            
        return start_line, end_line

    def get_import_statement(self, package: str, symbol: str) -> str:
        return f"from {package} import {symbol}"

    def find_variables(self, text: str) -> Set[str]:
        keywords = {"def", "class", "if", "else", "elif", "for", "while", "return", "import", "from", "async", "await", "yield", "as", "with", "try", "except", "finally", "None", "True", "False", "and", "or", "not", "is", "in"}
        matches = re.findall(r'\b[a-z_][a-zA-Z0-9_]*\b', text)
        return set([m for m in matches if m not in keywords])

    def is_defined_in_outer_scope(self, var_name: str, context_text: str) -> bool:
        # Check for assignment or def
        patterns = [rf"^{var_name}\s*=", rf"\bdef\s+{var_name}\b", rf"\bclass\s+{var_name}\b"]
        return any(re.search(p, context_text, re.MULTILINE) for p in patterns)

    def infer_types(self, parameters: List[str], context_text: str) -> List[Tuple[str, str]]:
        typed = []
        for var in parameters:
            # Look for type hints: var: Type
            match = re.search(rf"\b{var}\s*:\s*([\w\[\], ]+)", context_text)
            typed.append((var, match.group(1) if match else "Any"))
        return typed

    def get_function_template(self, name: str, params_str: str, body: List[str], scope: str, indent: str) -> str:
        # scope isn't strictly used in top-level python functions as much as underscores
        prefix = "_" if scope == "private" else ""
        code = f"\n\ndef {prefix}{name}({params_str}):\n"
        for line in body:
            code += line + "\n"
        return code

    def get_function_call(self, name: str, args_str: str, indent: str) -> str:
        return f"{indent}{name}({args_str})"

    def is_definition(self, line: str, symbol: str) -> bool:
        return line.strip().startswith(f"def {symbol}(") or line.strip().startswith(f"class {symbol}")

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

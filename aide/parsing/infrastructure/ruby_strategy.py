import re
import os
from typing import Any, Tuple, Callable, Generator
from aide.core.domain.ports import LanguageStrategy

class RubyLanguageStrategy(LanguageStrategy):
    """
    Ruby-specific refactoring strategy.
    Handles 'require', 'module', 'class', 'def' and 'end'-based block detection.
    """
    def extract_imports_and_header(self, lines: list[str]) -> tuple[list[str], str | None]:
        """Extracts 'require' and 'require_relative' statements."""
        imports = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("require ") or stripped.startswith("require_relative "):
                imports.append(stripped)
        return imports, None # Ruby doesn't have a package header

    def get_package_header(self, file_path: str) -> str | None:
        return None

    def get_module_path(self, file_path: str) -> str:
        """Converts file path to Ruby module path (e.g. lib/my_app/utils.rb -> MyApp::Utils)."""
        rel_path = os.path.relpath(file_path, ".")
        parts = os.path.splitext(rel_path)[0].split(os.sep)
        # Remove 'lib' if it's there
        if parts[0] == 'lib':
            parts = parts[1:]
            
        def camelize(s):
            return "".join(word.capitalize() for word in s.split("_"))
            
        return "::".join(camelize(p) for p in parts)

    def adjust_visibility(self, content: str) -> str:
        """Removes private/protected keywords if they appear before a method."""
        return re.sub(r'^\s*(private|protected|public)\s*$', '', content, flags=re.MULTILINE)

    def find_symbol_range(self, lines: list[str], symbol: str) -> tuple[int | None, int | None]:
        """Finds the range using 'end' keyword matching."""
        # Pattern for class, module or def
        pattern = re.compile(rf"^\s*(class|module|def)\s+{re.escape(symbol)}\b")
        
        start_line = -1
        for i, line in enumerate(lines):
            if pattern.match(line):
                start_line = i + 1
                break
        
        if start_line == -1:
            return None, None

        # Include comments above
        curr = start_line - 1
        while curr > 0:
            prev_line = lines[curr - 1].strip()
            if prev_line.startswith("#") or prev_line == "":
                start_line = curr
                curr -= 1
            else:
                break

        # Find the matching 'end'
        # We need to count nested blocks: class, module, def, if, unless, case, for, while, until, begin, do
        block_starts = {"class", "module", "def", "if", "unless", "case", "for", "while", "until", "begin", "do"}
        
        balance = 0
        found_start = False
        end_line = -1
        
        for i in range(start_line - 1, len(lines)):
            line_content = lines[i]
            # Split into words to avoid matching inside strings/comments (simplified)
            words = re.findall(r'\b\w+\b', re.sub(r'#.*$', '', line_content))
            
            for word in words:
                if word in block_starts:
                    # 'if', 'while' etc. can be used as modifiers without 'end'
                    # Simplified: if it's at the start of the line it's likely a block start
                    if word == words[0]:
                        balance += 1
                        found_start = True
                elif word == "end":
                    balance -= 1
            
            if found_start and balance == 0:
                end_line = i + 1
                break
                
        if end_line == -1:
             return None, None
             
        return start_line, end_line

    def get_import_statement(self, package: str, symbol: str) -> str:
        # Simplified: assumes package is the file name to require
        return f"require '{package}'"

    def find_variables(self, text: str) -> set[str]:
        keywords = {
            "BEGIN", "END", "alias", "and", "begin", "break", "case", "class", "def", "defined?", "do", "else", "elsif", "end", "ensure", "false", "for", "if", "in", "module", "next", "nil", "not", "or", "redo", "rescue", "retry", "return", "self", "super", "then", "true", "undef", "unless", "until", "when", "while", "yield"
        }
        # Ruby local variables start with lower case or underscore
        matches = re.findall(r'\b[a-z_][a-zA-Z0-9_]*\b', text)
        return set([m for m in matches if m not in keywords])

    def is_defined_in_outer_scope(self, var_name: str, context_text: str) -> bool:
        # Look for assignment: var = ...
        return re.search(rf"\b{var_name}\s*=", context_text) is not None

    def infer_types(self, parameters: list[str], context_text: str) -> list[tuple[str, str]]:
        # Ruby is dynamically typed, so we just return 'Object' or guess from YARD comments if present
        typed = []
        for var in parameters:
            match = re.search(rf"@param\s+{var}\s+\[([\w:]+)\]", context_text)
            typed.append((var, match.group(1) if match else "Object"))
        return typed

    def get_function_template(self, name: str, params_str: str, body: list[str], scope: str, indent: str) -> str:
        # scope is ignored for Ruby top-level/class methods usually handled by private
        code = f"\n\n{indent}def {name}({params_str})\n"
        for line in body:
            code += line + "\n"
        code += f"{indent}end\n"
        return code

    def get_function_call(self, name: str, args_str: str, indent: str) -> str:
        return f"{indent}{name}({args_str})"

    def is_definition(self, line: str, symbol: str) -> bool:
        return re.search(rf"^\s*(class|module|def)\s+{symbol}\b", line) is not None

    def update_signature_string(self, line: str, symbol: str, is_definition: bool, insertion: str) -> str:
        # Ruby methods can have optional parenthesies
        match = re.search(rf"\b{re.escape(symbol)}\s*\(?", line)
        if not match:
            return line
            
        if "(" in match.group(0):
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
        else:
            # Handle 'def method arg1, arg2'
            # We insert at the end of the line for simplicity in this strategy
            prefix = ", " if re.search(rf"\b{re.escape(symbol)}\s+\w+", line) else " "
            return line.rstrip() + prefix + insertion
            
        return line

import re
import os
from typing import Any, Tuple, Callable, Generator
from aide.core.domain.ports import LanguageStrategy

class RustLanguageStrategy(LanguageStrategy):
    def adjust_visibility(self, content: str) -> str:
        # In Rust, everything is private by default. 
        # Making it public involves adding `pub` or `pub(crate)`.
        return content

    def extract_imports_and_header(self, lines: list[str]) -> tuple[list[str], str]:
        imports = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("use "):
                imports.append(line)
            elif stripped.startswith(("struct", "enum", "trait", "fn ", "pub ", "impl")):
                break # We hit the body of the file
        
        # Rust doesn't really have a file-level "package" header like Java/C#. It uses `mod` declarations in lib.rs/mod.rs.
        return imports, ""

    def find_symbol_range(self, lines: list[str], symbol: str) -> tuple[int | None, int | None]:
        """
        Naive brace counting to find a symbol block.
        """
        start_line = None
        end_line = None
        brace_count = 0
        in_symbol = False
        
        pattern = re.compile(rf"\b(?:struct|enum|trait|fn)\s+{re.escape(symbol)}\b")

        for i, line in enumerate(lines):
            if not in_symbol:
                if pattern.search(line):
                    # Backtrack for attributes (e.g., #[derive(...)])
                    start_line_idx = i
                    while start_line_idx > 0 and lines[start_line_idx - 1].strip().startswith("#["):
                        start_line_idx -= 1
                    
                    start_line = start_line_idx + 1
                    in_symbol = True
                    brace_count += line.count('{') - line.count('}')
                    
                    if line.strip().endswith(';'):
                        end_line = i + 1
                        break
            else:
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0 and ('{' in line or '}' in line or brace_count < 0):
                    end_line = i + 1
                    break
        
        return start_line, end_line

    def get_module_path(self, file_path: str) -> str:
        """
        In Rust, module paths are dictated by the file hierarchy relative to src/.
        """
        try:
            abs_path = os.path.abspath(file_path)
            if "src/" in abs_path:
                parts = abs_path.split("src/")
                rel_path = parts[1]
                module_path = rel_path.replace(".rs", "").replace(os.sep, "::")
                # Handle mod.rs which represents the directory's module itself
                if module_path.endswith("::mod"):
                    module_path = module_path[:-5]
                return "crate::" + module_path
        except Exception:
            pass
            
        base_dir = os.path.dirname(file_path)
        return os.path.basename(base_dir)

    def get_import_statement(self, module_path: str, symbol: str) -> str:
        """
        Returns the Rust use statement.
        """
        if module_path:
            return f"use {module_path}::{symbol};"
        return f"use {symbol};"

    def get_package_header(self, file_path: str) -> str | None:
        # Rust files don't declare their own package header like Java.
        return None

    def find_variables(self, text: str) -> set[str]:
        keywords = {"let", "mut", "fn", "struct", "enum", "trait", "impl", "use", "mod", "pub", "crate", "self", "Self", "match", "if", "else", "loop", "while", "for", "in", "return", "break", "continue", "async", "await", "unsafe", "where", "type", "as", "const", "static"}
        matches = re.findall(r'\b[a-z_][a-zA-Z0-9_]*\b', text)
        return set([m for m in matches if m not in keywords])

    def is_defined_in_outer_scope(self, var_name: str, context_text: str) -> bool:
        patterns = [rf"\blet\s+(?:mut\s+)?{var_name}\b", rf"\bfn\s+{var_name}\b"]
        return any(re.search(p, context_text) for p in patterns)

    def infer_types(self, parameters: list[str], context_text: str) -> list[tuple[str, str]]:
        typed = []
        for var in parameters:
            match = re.search(rf"\b{var}\s*:\s*([\w<>: &]+)", context_text)
            typed.append((var, match.group(1).strip() if match else "&str")) # default to &str as a guess
        return typed

    def get_function_template(self, name: str, params_str: str, body: list[str], scope: str, indent: str) -> str:
        visibility = "pub " if scope != "private" else ""
        code = f"\n\n{indent}{visibility}fn {name}({params_str}) {{\n"
        for line in body:
            code += line + "\n"
        code += f"{indent}}}\n"
        return code

    def get_function_call(self, name: str, args_str: str, indent: str) -> str:
        return f"{indent}{name}({args_str});"

    def is_definition(self, line: str, symbol: str) -> bool:
        return f"fn {symbol}" in line

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

import re
import os
from typing import List, Tuple, Optional, Set
from aide.core.domain.ports import LanguageStrategy

class RustLanguageStrategy(LanguageStrategy):
    """
    Rust-specific refactoring strategy.
    Handles 'use', 'mod', and bracket-based block detection.
    """
    def extract_imports_and_header(self, lines: List[str]) -> Tuple[List[str], Optional[str]]:
        """Extracts 'use' and 'mod' statements."""
        imports = []
        header = None
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith("use ") or stripped.startswith("pub use ")) and ";" in stripped:
                imports.append(stripped)
            elif (stripped.startswith("mod ") or stripped.startswith("pub mod ")) and header is None:
                # In Rust, 'mod' can be a declaration or a block.
                # If it ends with ';', it's a declaration.
                if ";" in stripped:
                    header = stripped
        return imports, header

    def get_package_header(self, file_path: str) -> Optional[str]:
        # Rust doesn't use package headers in the same way Kotlin/C# do.
        # It uses the file system and 'mod' declarations in parent files.
        return None

    def get_module_path(self, file_path: str) -> str:
        """Returns the logical Rust module path."""
        rel_path = os.path.relpath(file_path, ".")
        module_path = os.path.splitext(rel_path)[0].replace(os.sep, "::")
        # Standard Rust convention: src/main.rs or src/lib.rs are the root.
        module_path = module_path.replace("src::", "")
        if module_path.endswith("::mod"):
            module_path = module_path[:-5]
        return module_path

    def adjust_visibility(self, content: str) -> str:
        """Adjusts visibility to public for moved symbols."""
        return re.sub(r'\b(pub\(crate\)|pub\(super\)|pub\(self\))?\s*(fn|struct|enum|const|static|type|trait|mod)\b', r'pub \2', content)

    def find_symbol_range(self, lines: List[str], symbol: str) -> Tuple[Optional[int], Optional[int]]:
        """Finds the start and end lines of a Rust symbol using bracket matching."""
        # Matches: [pub] [async] [unsafe] fn/struct/enum... SymbolName
        pattern = re.compile(rf"\b(fn|struct|enum|type|trait|impl|mod)\s+{re.escape(symbol)}\b")
        
        start_line = -1
        for i, line in enumerate(lines):
            if pattern.search(line):
                start_line = i + 1
                break
        
        if start_line == -1:
            return None, None

        # Include attributes (#[...]) and comments above
        curr = start_line - 1
        while curr > 0:
            prev_line = lines[curr - 1].strip()
            if prev_line.startswith("#[") or prev_line.startswith("//") or prev_line.startswith("///") or prev_line.startswith("/*") or prev_line == "":
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
        
        # Some Rust items don't have blocks (e.g. type aliases, unit structs, constants)
        if not found_open:
            for i in range(start_line - 1, len(lines)):
                if ";" in lines[i]:
                    end_line = i + 1
                    break
                    
        if end_line == -1:
             return None, None
             
        return start_line, end_line

    def get_import_statement(self, package: str, symbol: str) -> str:
        return f"use {package}::{symbol};"

    def find_variables(self, text: str) -> Set[str]:
        keywords = {
            "as", "break", "const", "continue", "crate", "else", "enum", "extern", "false", "fn", "for", "if", "impl", "in", "let", "loop", "match", "mod", "move", "mut", "pub", "ref", "return", "self", "Self", "static", "struct", "super", "trait", "true", "type", "unsafe", "use", "where", "while", "async", "await", "dyn", "abstract", "become", "box", "do", "final", "macro", "override", "priv", "try", "typeof", "unsized", "virtual", "yield"
        }
        matches = re.findall(r'\b[a-z_][a-zA-Z0-9_]*\b', text)
        return set([m for m in matches if m not in keywords])

    def is_defined_in_outer_scope(self, var_name: str, context_text: str) -> bool:
        # Check for let binding or fn parameter
        patterns = [
            rf"\blet\s+(mut\s+)?{var_name}\b",
            rf"\bfn\s+\w+\s*\([^)]*\b{var_name}\b"
        ]
        return any(re.search(p, context_text) for p in patterns)

    def infer_types(self, parameters: List[str], context_text: str) -> List[Tuple[str, str]]:
        typed = []
        for var in parameters:
            # Match "var: Type"
            match = re.search(rf"\b{var}\s*:\s*([\w<>: &]+)", context_text)
            typed.append((var, match.group(1).strip() if match else "()"))
        return typed

    def get_function_template(self, name: str, params_str: str, body: List[str], scope: str, indent: str) -> str:
        visibility = "pub " if scope in {"public", "internal"} else ""
        code = f"\n\n{indent}{visibility}fn {name}({params_str}) {{\n"
        for line in body:
            code += line + "\n"
        code += f"{indent}}}\n"
        return code

    def get_function_call(self, name: str, args_str: str, indent: str) -> str:
        return f"{indent}{name}({args_str});"

    def is_definition(self, line: str, symbol: str) -> bool:
        return re.search(rf"\b(fn|struct|enum|trait|type|mod)\s+{symbol}\b", line) is not None

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

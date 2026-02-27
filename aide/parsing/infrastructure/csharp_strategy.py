import re
import os
from typing import Any, Tuple, Callable, Generator
from aide.core.domain.ports import LanguageStrategy

class CSharpLanguageStrategy(LanguageStrategy):
    def adjust_visibility(self, content: str) -> str:
        # For simple code-block extraction, we don't automatically rewrite visibility in C#
        # C# is explicit, changing `public` to `private` requires AST or complex regex
        return content

    def extract_imports_and_header(self, lines: list[str]) -> tuple[list[str], str]:
        imports = []
        header = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("using ") and not stripped.startswith("using ("):
                # Captures `using System;` but ignores `using (var x = ...)`
                imports.append(line)
            elif stripped.startswith("namespace "):
                header.append(line)
            elif stripped.startswith(("class", "record", "struct", "interface", "enum", "public", "private", "internal", "protected")):
                break # We hit the body of the file
        
        return imports, "\n".join(header)

    def find_symbol_range(self, lines: list[str], symbol: str) -> tuple[int | None, int | None]:
        """
        Extremely naive brace counting to find a symbol block.
        Real AST-based splicing belongs in a future `AstSplicer` port.
        For now, this maintains compatibility with the legacy `RegexLanguageParser` splicing mechanism.
        """
        start_line = None
        end_line = None
        brace_count = 0
        in_symbol = False
        
        # We need a robust regex to find the start
        pattern = re.compile(rf"\b(?:class|struct|interface|record|enum)\s+{re.escape(symbol)}\b|\b(?:[a-zA-Z0-9_<>\[\]]+\s+){re.escape(symbol)}\s*\(")

        for i, line in enumerate(lines):
            if not in_symbol:
                if pattern.search(line):
                    # We might have attributes above the class/method e.g. [Route("api/[controller]")]
                    # We backtrack to find attributes
                    start_line_idx = i
                    while start_line_idx > 0 and lines[start_line_idx - 1].strip().startswith("["):
                        start_line_idx -= 1
                    
                    start_line = start_line_idx + 1
                    in_symbol = True
                    brace_count += line.count('{') - line.count('}')
                    
                    # It might be a one-liner without braces (e.g. abstract method or auto-property)
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
        Extract the namespace from the file if possible, otherwise guess from directory structure.
        In C#, package structure isn't strictly tied to directory path like Java.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.search(r'^\s*namespace\s+([\w\.]+)', content, re.MULTILINE)
            if match:
                return match.group(1)
        except Exception:
            pass
            
        # Fallback to directory structure guessing
        base_dir = os.path.dirname(file_path)
        return  os.path.basename(base_dir) # Very simplistic fallback

    def get_import_statement(self, module_path: str, symbol: str) -> str:
        """
        Returns the C# using statement. C# imports namespaces, not individual symbols.
        """
        return f"using {module_path};"

    def get_package_header(self, file_path: str) -> str | None:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # File-scoped namespaces (C# 10) or traditional
            match = re.search(r'^\s*namespace\s+([\w\.]+)\s*;?', content, re.MULTILINE)
            if match:
                 return match.group(0).strip()
        except:
            pass
        return None

    def find_variables(self, text: str) -> set[str]:
        # C# keywords
        keywords = {"var", "int", "string", "bool", "double", "float", "long", "byte", "char", "decimal", "object", "dynamic", "if", "else", "for", "foreach", "while", "return", "new", "this", "base", "true", "false", "null", "class", "struct", "interface", "enum", "namespace", "using", "public", "private", "protected", "internal", "static", "readonly", "volatile", "const", "async", "await", "yield", "params", "ref", "out", "in"}
        matches = re.findall(r'\b[a-z_][a-zA-Z0-9_]*\b', text)
        return set([m for m in matches if m not in keywords])

    def is_defined_in_outer_scope(self, var_name: str, context_text: str) -> bool:
        patterns = [rf"\b(?:var|int|string|bool|double|float|long|byte|char|decimal|object|dynamic|\w+)\s+{var_name}\b", rf"\b{var_name}\s*="]
        return any(re.search(p, context_text) for p in patterns)

    def infer_types(self, parameters: list[str], context_text: str) -> list[tuple[str, str]]:
        typed = []
        for var in parameters:
            # Match "Type var" or "Type var ="
            match = re.search(rf"\b([\w<>, \[\]]+)\s+{var}\b", context_text)
            typed.append((var, match.group(1) if match else "object"))
        return typed

    def get_function_template(self, name: str, params_str: str, body: list[str], scope: str, indent: str) -> str:
        # Map scope to C# access modifiers
        modifier = "private" if scope == "private" else "public"
        # We assume `void` for now as type inference is limited
        code = f"\n\n{indent}{modifier} void {name}({params_str}) {{\n"
        for line in body:
            code += line + "\n"
        code += f"{indent}}}\n"
        return code

    def get_function_call(self, name: str, args_str: str, indent: str) -> str:
        return f"{indent}{name}({args_str});"

    def is_definition(self, line: str, symbol: str) -> bool:
        return f" {symbol}(" in line and ("void" in line or "class" in line or "int" in line or "string" in line)

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

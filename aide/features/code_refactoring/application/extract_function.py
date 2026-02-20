import re
from typing import List, Tuple, Set

class ExtractFunctionUseCase:
    def __init__(self, file_system, strategy_provider):
        self.file_system = file_system
        self.strategy_provider = strategy_provider

    def execute(self, file_path: str, selection: str, function_name: str, scope: str = "private", dry_run: bool = False) -> bool:
        try:
            # 1. Read File
            content = self.file_system.read_file(file_path)
            lines = content.splitlines()
            strategy = self.strategy_provider.get_strategy(file_path)

            # 2. Parse Selection (start_line:end_line) 1-based
            try:
                start_line_str, end_line_str = selection.split(":")
                start_line = int(start_line_str)
                end_line = int(end_line_str)
            except ValueError:
                return False

            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                return False

            # Extract lines (0-indexed for list access)
            selected_lines = lines[start_line - 1 : end_line]
            selected_text = "\n".join(selected_lines)

            # 3. Analyze Variables (Naive Approach for V1)
            # Find all words that look like variables in the selection
            # Then check if they are defined BEFORE the selection in the original file
            
            used_Variables = strategy.find_variables(selected_text)
            preceeding_text = "\n".join(lines[:start_line - 1])
            
            # Identify which used variables are actually defined in outer scope
            parameters = []
            for var in used_Variables:
                if strategy.is_defined_in_outer_scope(var, preceeding_text):
                     parameters.append(var)

            # 4. Generate Function Signature
            # We don't know types easily with regex, so we might need user input or heuristic
            # For Kotlin, we can try to guess or use "Any" as placeholder if unsure, 
            # OR just generate the names and let the user fill types. 
            # Ideally, we look for 'val x: Type' in preceeding text.
            
            typed_parameters = strategy.infer_types(parameters, preceeding_text)
            
            params_parts = []
            for name, tipo in typed_parameters:
                if tipo and tipo != "Any" and tipo != "any":
                    params_parts.append(f"{name}: {tipo}")
                else:
                    params_parts.append(name)
            params_str = ", ".join(params_parts)
            
            # Indentation
            indent = self._get_indentation(lines[start_line - 1])

            # 5. Generate New Function
            new_function_code = strategy.get_function_template(function_name, params_str, selected_lines, scope, indent)

            # 6. Replace Selection with Call
            call_args = ", ".join(parameters)
            call_stmt = strategy.get_function_call(function_name, call_args, indent)
            
            # Apply edits
            # We replace lines[start-1 : end] with [call_stmt]
            # And append new_function_code at the end of the class/file?
            # For simplicity, append to end of file for now, user can move it.
            # OR better: insert after the current method? Hard to find end of method without parser.
            # Let's append to end of file.
            
            new_lines = lines[:start_line - 1] + [call_stmt] + lines[end_line:] + new_function_code.splitlines()
            
            new_content = "\n".join(new_lines)
            
            if not dry_run:
                self.file_system.write_file(file_path, new_content)
            
            return True

        except Exception as e:
            return False

    def _get_indentation(self, line: str) -> str:
        return line[:len(line) - len(line.lstrip())]

import os

class RegisterDependencyUseCase:
    def __init__(self, file_system, language_parser, strategy_provider):
        self.file_system = file_system
        self.language_parser = language_parser
        self.strategy_provider = strategy_provider

    def execute(self, file_path: str, import_path: str, binding: str) -> bool:
        try:
            content = self.file_system.read_file(file_path)
            lines = content.splitlines()
            
            # Simple heuristic since DI containers vary wildly in structure:
            # 1. Inject the import safely at the top
            
            # Build the import string
            import_str = ""
            if file_path.endswith(".py"):
                # Simplistic: from <path> import <class>
                # Using standard syntax if provided
                import_str = f"import {import_path}" if " " not in import_path else import_path
            elif file_path.endswith((".kt", ".java")):
                import_str = f"import {import_path}"
                
            has_import = any(import_str in line for line in lines)
            
            if import_str and not has_import:
                # Find last import or just put it after package declaration
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith("import "):
                        insert_idx = i + 1
                    elif line.startswith("package ") and insert_idx == 0:
                        insert_idx = i + 1
                        
                if insert_idx == 0 and len(lines) > 0:
                     # It's python or something without standard package headers, drop it at top
                     pass
                     
                lines.insert(insert_idx, import_str)
                
            # 2. Inject the binding statement
            # The safest deterministic approach without AST for a generic container 
            # is to splice it at the end of the file or just inside the main class block.
            
            # For this basic implementation, we just append it safely if it doesn't exist
            if not any(binding in line for line in lines):
                if file_path.endswith((".kt", ".java", ".ts")):
                    # Naively insert before the last closing brace in the file
                    # To assume it goes inside the module block
                    for i in reversed(range(len(lines))):
                        if "}" in lines[i]:
                            # Inject right before it
                            lines.insert(i, f"    {binding}")
                            break
                    else:
                        # Fallback append
                        lines.append(binding)
                else:
                    # Python fallback append
                    lines.append(binding)

            new_content = "\n".join(lines) + "\n"
            self.file_system.write_file(file_path, new_content)
            
            print(f"✅ Registered dependency '{binding}'.")
            return True

        except Exception as e:
            print(f"❌ Failed to register dependency: {e}")
            return False

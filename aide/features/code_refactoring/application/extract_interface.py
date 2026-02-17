import os
import re
from typing import List, Tuple

class ExtractInterfaceUseCase:
    def __init__(self, file_system, language_parser, strategy_provider):
        self.file_system = file_system
        self.language_parser = language_parser
        self.strategy_provider = strategy_provider

    def execute(self, file_path: str, class_name: str, interface_name: str = None, dry_run: bool = False) -> bool:
        try:
            file_path = os.path.abspath(file_path)
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                return False

            if not interface_name:
                interface_name = class_name # User might want IClass or similar later

            strategy = self.strategy_provider.get_strategy(file_path)
            content = self.file_system.read_file(file_path)
            lines = content.splitlines()

            # 1. Find Class and extract public members
            start, end = strategy.find_symbol_range(lines, class_name)
            if not start:
                print(f"❌ Class '{class_name}' not found in {file_path}")
                return False

            class_lines = lines[start-1:end]
            class_content = "\n".join(class_lines)

            # Heuristic: Find public fun/val/var in class body
            # We look for lines starting with 'fun ' or 'val ' or 'var ' inside the class
            # excluding those that have 'private' or 'internal'
            members = []
            for line in class_lines:
                stripped = line.strip()
                if (stripped.startswith("fun ") or stripped.startswith("val ") or stripped.startswith("var ")) \
                   and "private" not in stripped and "internal" not in stripped and "override" not in stripped:
                    # Strip implementation for interface
                    if stripped.startswith("fun "):
                        # Convert 'fun name(params) { ... }' to 'fun name(params)'
                        member = stripped.split("{")[0].strip()
                        members.append(member)
                    else:
                        # Convert 'val name: Type = ...' to 'val name: Type'
                        member = stripped.split("=")[0].strip()
                        members.append(member)

            if not members:
                print(f"⚠️ No public non-override members found in class {class_name}")

            # 2. Create Interface Content
            package_header = strategy.get_package_header(file_path)
            interface_content = f"{package_header}\n\n" if package_header else ""
            interface_content += f"interface {interface_name} {{\n"
            for member in members:
                interface_content += f"    {member}\n"
            interface_content += "}\n"

            # 3. Update Class to implement interface
            # Find the class declaration line
            decl_line_idx = -1
            for i, line in enumerate(class_lines):
                if f"class {class_name}" in line:
                    decl_line_idx = i
                    break
            
            if decl_line_idx != -1:
                original_decl = class_lines[decl_line_idx]
                if ":" in original_decl:
                    new_decl = original_decl.replace(":", f": {interface_name},")
                else:
                    # Attach to the end of class declaration
                    if "{" in original_decl:
                         new_decl = original_decl.replace("{", f": {interface_name} {{")
                    else:
                         new_decl = original_decl + f" : {interface_name}"
                
                class_lines[decl_line_idx] = new_decl
            
            modified_class_content = "\n".join(class_lines)
            new_original_content = "\n".join(lines[:start-1] + [modified_class_content] + lines[end:])

            # 4. Write Files
            interface_file = os.path.join(os.path.dirname(file_path), f"{interface_name}.kt")
            
            if dry_run:
                print(f"🔍 [Dry Run] Would create {interface_file}")
                print(f"🔍 [Dry Run] Would modify {file_path}")
            else:
                self.file_system.write_file(interface_file, interface_content)
                self.file_system.write_file(file_path, new_original_content)
                print(f"✅ Extracted interface {interface_name} to {interface_file}")
                print(f"✅ Updated {class_name} to implement {interface_name}")

            return True

        except Exception as e:
            print(f"❌ Interface extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return False

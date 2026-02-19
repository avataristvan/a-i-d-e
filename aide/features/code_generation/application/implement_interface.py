import re
from typing import Optional

class ImplementInterfaceUseCase:
    def __init__(self, file_system, language_parser, strategy_provider):
        self.file_system = file_system
        self.language_parser = language_parser
        self.strategy_provider = strategy_provider

    def execute(self, file_path: str, class_name: str, interface_name: str) -> bool:
        try:
            content = self.file_system.read_file(file_path)
            lines = content.splitlines()
            
            strategy = self.strategy_provider.get_strategy(file_path)
            
            # Find the interface bounds
            iface_start, iface_end = strategy.find_symbol_range(lines, interface_name)
            if not iface_start:
                print(f"❌ Interface '{interface_name}' not found.")
                return False
                
            # Find the target class bounds
            class_start, class_end = strategy.find_symbol_range(lines, class_name)
            if not class_start:
                print(f"❌ Class '{class_name}' not found.")
                return False

            # Extract the interface body
            iface_body = "\n".join(lines[iface_start-1:iface_end])
            
            # Determine methods the interface requires
            # Here we do naive regex extraction since we lack a full AST
            methods = self._extract_method_signatures(iface_body, file_path)
            
            if not methods:
                print(f"⚠️ No methods found in interface '{interface_name}'.")
                return False
                
            # See which ones are missing from the concrete class
            class_body = "\n".join(lines[class_start-1:class_end])
            missing_methods = []
            for method_sig, method_name in methods:
                 # Very naive check: does the string "def method_name" or "fun method_name" exist in class body?
                 if method_name not in class_body:
                     missing_methods.append((method_sig, method_name))
                     
            if not missing_methods:
                print(f"✅ Class '{class_name}' already implements all methods of '{interface_name}'.")
                return True
                
            # Inject missing methods at the bottom of the class
            stubbed_lines = self._generate_stubs(missing_methods, file_path)
            
            # Splice into final file (just before the class ends, or at the end of class block)
            # Find the indentation of the class to inject safely.
            # Here we assume standard formatting
            indent = "    "
            if file_path.endswith(".kt") or file_path.endswith(".java") or file_path.endswith(".ts"):
                # Insert just before the last brace of the class
                # This is a naive heuristic
                new_class_content = "\n".join(lines[class_start-1:class_end-1]) + "\n"
                for stub in stubbed_lines:
                    new_class_content += indent + stub + "\n"
                new_class_content += lines[class_end-1] # the closing brace
                
                lines[class_start-1:class_end] = new_class_content.splitlines()
            else:
                # Python: insert at the end of the class range with one indent
                for stub in stubbed_lines:
                    lines.insert(class_end, indent + stub)
                    class_end += 1

            new_content = "\n".join(lines) + "\n"
            self.file_system.write_file(file_path, new_content)
            
            print(f"✅ Implemented {len(missing_methods)} methods for '{class_name}'.")
            return True

        except Exception as e:
            print(f"❌ Failed to implement interface: {e}")
            return False

    def _extract_method_signatures(self, body: str, file_path: str):
        methods = []
        if file_path.endswith(".py"):
            # Ex: def do_something(self, id: str) -> None:
            matches = re.finditer(r'def\s+(\w+)\s*\(.*?\)(\s*->\s*[^{:\n]+)?\s*:', body)
            for m in matches:
                sig = m.group(0).strip()
                if sig.endswith(":"):
                    sig = sig[:-1] # Remove trailing colon for injection
                name = m.group(1)
                methods.append((sig + ":", name))
                
        elif file_path.endswith(".kt"):
            # Ex: fun doSomething(id: String): Unit
            matches = re.finditer(r'fun\s+(\w+)\s*\(.*?\)(\s*:\s*[^{:\n]+)?', body)
            for m in matches:
                sig = m.group(0).strip()
                name = m.group(1)
                methods.append((sig, name))
        return methods

    def _generate_stubs(self, methods, file_path: str):
        stubs = []
        for sig, name in methods:
            if file_path.endswith(".py"):
                # def do_something(self, a): -> def do_something(self, a):\n    pass
                stubs.append(sig)
                stubs.append("    pass\n")
            elif file_path.endswith(".kt"):
                # fun doSomething() -> fun doSomething() { TODO("Not yet implemented") }
                stubs.append(sig + " {")
                stubs.append("    TODO(\"Not yet implemented\")")
                stubs.append("}\n")
        return stubs

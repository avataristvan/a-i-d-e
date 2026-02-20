import os
from aide.core.domain.ports import FileSystemPort
from aide.parsing.domain.ports import LanguageParserPort

class AuditNextjsUseCase:
    """Audits a Next.js codebase for Hexagonal Architecture violations."""
    
    def __init__(self, file_system: FileSystemPort, language_parser: LanguageParserPort):
        self.file_system = file_system
        self.language_parser = language_parser

    def execute(self, src_path: str) -> dict:
        violations = []
        
        try:
            files = list(self.file_system.walk_files(src_path))
        except Exception as e:
            return {"success": False, "error": f"Failed to traverse path: {e}"}

        for full_path in files:
            if not full_path.endswith(".ts") and not full_path.endswith(".tsx"):
                continue
            
            try:
                abs_src = os.path.abspath(src_path)
                rel_path = os.path.relpath(full_path, abs_src)
            except ValueError:
                rel_path = full_path

            filename = os.path.basename(full_path)
            
            try:
                content = self.file_system.read_file(full_path)
                # Instead of raw regex lines, use parse_imports
                imports = self.language_parser.parse_imports(content, ".ts" if full_path.endswith(".ts") else ".tsx")
                
                # --- Rule Set 1: High-Level Module Boundaries ---
                
                # Rule 1.1: Shared cannot import Feature Modules
                if rel_path.startswith("shared/"):
                    for imp in imports:
                        if "modules/" in imp:
                            violations.append(f"{filename} : Shared cannot import Feature Modules (imports '{imp}')")
                
                # Rule 1.2: Feature Modules should not import App Layer (Next.js pages)
                if rel_path.startswith("modules/") or rel_path.startswith("features/"):
                     for imp in imports:
                        if "app/" in imp:
                            violations.append(f"{filename} : Features cannot import App Layer (imports '{imp}')")

                # --- Rule Set 2: Hexagonal/DDD Layer Constraints ---
                
                # Rule 2.1: Domain Layer Purity (The Core)
                if "/domain/" in rel_path or rel_path.startswith("domain/"):
                    for imp in imports:
                        if "react" in imp:
                            violations.append(f"{filename} : Domain: Must be pure (No React) (imports '{imp}')")
                        if "../infrastructure" in imp or "infrastructure/" in imp:
                            violations.append(f"{filename} : Domain: Cannot import Infrastructure (imports '{imp}')")
                        if "../application" in imp or "application/" in imp:
                            violations.append(f"{filename} : Domain: Cannot import Application (imports '{imp}')")

                # Rule 2.2: Infrastructure Layer
                if "/infrastructure/" in rel_path or rel_path.startswith("infrastructure/"):
                     for imp in imports:
                        if "../application" in imp or "application/" in imp:
                            violations.append(f"{filename} : Infrastructure: Cannot import Application (imports '{imp}')")

                # --- Rule Set 3: Okkularion Critical Path (Low-Latency) ---
                
                if (filename.endswith("Engine.ts") or filename.endswith("Controller.ts")) and not filename.endswith(".tsx"):
                     for imp in imports:
                        if "react" in imp:
                            violations.append(f"{filename} : Critical Path: Engines/Controllers should NOT import React (imports '{imp}')")

            except Exception as e:
                violations.append(f"{rel_path}: Error reading file: {e}")

        success = len(violations) == 0
        message = "Next.js/Okkularion Architecture is Clean!" if success else f"Found {len(violations)} Violations"
        
        return {
            "success": success,
            "message": message,
            "data": {
                "violations": violations
            }
        }

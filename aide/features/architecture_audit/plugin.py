from argparse import _SubParsersAction
import os
from aide.core.context import Context

class ArchitectureAuditPlugin:
    def register(self, subparsers: _SubParsersAction, context: Context) -> None:
        parser = subparsers.add_parser("audit", help="Audit codebase for architecture violations")
        parser.add_argument("--stack", choices=['kotlin', 'nextjs'], required=True, help="Technology stack to audit")
        parser.add_argument("--src", default=".", help="Source root directory")
        parser.set_defaults(func=lambda args: self.run_audit(args, context))

    def run_audit(self, args, context):
        if args.stack == 'kotlin':
            self.audit_kotlin(args, context)
        elif args.stack == 'nextjs':
            self.audit_nextjs(args, context)

    def audit_kotlin(self, args, context):
        print(f"🔍 Auditing Kotlin/Android Architecture in {args.src}...")
        violations = []
        base_path = os.path.abspath(args.src)
        
        if not os.path.exists(base_path):
            print(f"❌ Source path not found: {base_path}")
            return

        for root, dirs, files in os.walk(base_path):
            for file in files:
                if not file.endswith(".kt"):
                    continue
                
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_path)
                filename = os.path.basename(file)
                
                # Check file line count (God Class detection)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.splitlines()
                        if len(lines) > 400:
                            violations.append(f"{rel_path}: File too large ({len(lines)} lines). Consider splitting.")
                        
                        # Use Parser for Imports
                        imports = context.language_parser.parse_imports(content, ".kt")
                        
                        for imp in imports:
                            # Rule 1: Domain Purity
                            if "/domain/" in rel_path:
                                if "android." in imp and "android.util" not in imp: 
                                    violations.append(f"{rel_path}: Domain purity violation (imports '{imp}')")
                                
                                if ".infrastructure" in imp:
                                    violations.append(f"{rel_path}: Domain cannot import Infrastructure (imports '{imp}')")
                                    
                            # Rule 2: Application Layer
                            if "/application/" in rel_path:
                                if ".infrastructure" in imp:
                                    violations.append(f"{rel_path}: Application cannot import Infrastructure (imports '{imp}')")

                            # Rule 3: Feature Isolation
                            if "features/" in rel_path and ".features." in imp:
                                current_feature = rel_path.split("features/")[1].split("/")[0]
                                if f".features.{current_feature}" not in imp and "core." not in imp:
                                     # This is a cross-feature import. 
                                     # We might want to allow it for now, or flag it.
                                     pass 
                                     
                except Exception as e:
                    print(f"Error reading {full_path}: {e}")

        if violations:
            print(f"❌ Found {len(violations)} Violations:")
            for v in violations:
                 print(f"  - {v}")
        else:
            print("✅ Kotlin Architecture is Clean!")

    def audit_nextjs(self, args, context):
        print(f"🔍 Auditing Next.js/React Architecture in {args.src}...")
        violations = []
        base_path = os.path.abspath(args.src)
        
        if not os.path.exists(base_path):
            print(f"❌ Source path not found: {base_path}")
            return

        for root, dirs, files in os.walk(base_path):
            for file in files:
                if not file.endswith(".ts") and not file.endswith(".tsx"):
                    continue
                
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_path)
                filename = os.path.basename(file)
                
                # --- Rule Set 1: High-Level Module Boundaries ---
                
                # Rule 1.1: Shared cannot import Feature Modules
                if rel_path.startswith("shared/"):
                    self.check_import_ban(full_path, "modules/", violations, "Shared cannot import Feature Modules")
                
                # Rule 1.2: Feature Modules should not import App Layer (Next.js pages)
                if rel_path.startswith("modules/") or rel_path.startswith("features/"):
                    self.check_import_ban(full_path, "app/", violations, "Features cannot import App Layer")

                # --- Rule Set 2: Hexagonal/DDD Layer Constraints ---
                
                # Rule 2.1: Domain Layer Purity (The Core)
                # Must be pure TypeScript. No React, no Infrastructure, no Application.
                if "/domain/" in rel_path:
                    self.check_import_content(full_path, "react", violations, "Domain: Must be pure (No React)")
                    self.check_import_ban(full_path, "../infrastructure", violations, "Domain: Cannot import Infrastructure")
                    self.check_import_ban(full_path, "../application", violations, "Domain: Cannot import Application")

                # Rule 2.2: Infrastructure Layer
                # adapters only. Should not import Application logic (circular).
                if "/infrastructure/" in rel_path:
                    self.check_import_ban(full_path, "../application", violations, "Infrastructure: Cannot import Application")

                # --- Rule Set 3: Okkularion Critical Path (Low-Latency) ---
                
                # Rule 3.1: Engines & Controllers (The "Real-time" Loop)
                # Files named *Engine.ts or *Controller.ts (excluding React components)
                # should generally NOT be React components or import React, 
                # as they run outside the render cycle (requestAnimationFrame).
                if (filename.endswith("Engine.ts") or filename.endswith("Controller.ts")) and not filename.endswith(".tsx"):
                     self.check_import_content(full_path, "react", violations, "Critical Path: Engines/Controllers should NOT import React")

        if violations:
            print(f"❌ Found {len(violations)} Violations:")
            for v in violations:
                 print(f"  - {v}")
        else:
            print("✅ Next.js/Okkularion Architecture is Clean!")

    def check_import_ban(self, file_path, banned_path_fragment, violations, message):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if line.startswith("import ") or line.startswith("export "):
                        if banned_path_fragment in line:
                            violations.append(f"{os.path.basename(file_path)}:{i+1} : {message} ({line})")
        except Exception:
            pass

    def check_import_content(self, file_path, forbidden_lib, violations, message):
         try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if (line.startswith("import ") or line.startswith("from ")) and forbidden_lib in line:
                         violations.append(f"{os.path.basename(file_path)}:{i+1} : {message} ({line})")
         except Exception:
            pass

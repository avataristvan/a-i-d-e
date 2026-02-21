import os
import re
from typing import Dict, Any, List
from aide.features.code_inspection.application.find_usages import FindUsagesUseCase

class FindImpactUseCase:
    """Identifies files impacted by a symbol change by cross-referencing string matches with actual import/dependency graph structures."""
    
    def __init__(self, file_system, language_parser, strategy_provider):
        self.file_system = file_system
        self.language_parser = language_parser
        self.strategy_provider = strategy_provider
        self.find_usages = FindUsagesUseCase(file_system, language_parser)

    def execute(self, symbol_name: str, source_file: str = None) -> Dict[str, Any]:
        impacted_files = set()
        impacted_tests = set()
        
        try:
            # 1. Broadly find usages
            root_path = "."
            raw_usages = self.find_usages.execute(root_path, symbol_name)
            
            # 2. Determine defining module if source_file is provided
            defining_module = None
            if source_file and os.path.exists(source_file):
                try:
                    strategy = self.strategy_provider.get_strategy(os.path.abspath(source_file))
                    defining_module = strategy.get_module_path(os.path.abspath(source_file))
                except Exception:
                    pass

            for usage in raw_usages:
                file_rel_path = usage.split(":")[0]
                file_path = os.path.abspath(file_rel_path)
                
                # Filter out the source file itself
                if source_file and os.path.abspath(source_file) == file_path:
                    continue

                # Advanced Graph Check: Verify the file imports the defining module
                # (Skip check if defining_module couldn't be resolved or file doesn't exist)
                has_graph_dependency = True
                if defining_module and os.path.exists(file_path):
                    try:
                        content = self.file_system.read_file(file_path)
                        _, ext = os.path.splitext(file_path)
                        imports = self.language_parser.parse_imports(content, ext)
                        
                        # Check if any import references the defining_module
                        # We use simple substring matching for now as imports can be structured differently
                        module_imported = False
                        for imp in imports:
                            if defining_module in imp or imp in defining_module:
                                module_imported = True
                                break
                            # Also check if the symbol itself is explicitly imported
                            if symbol_name in imp:
                                module_imported = True
                                break
                                
                        if not module_imported:
                            # Also check if they are in the exact same package/module
                            # If so, they don't need imports
                            strategy = self.strategy_provider.get_strategy(file_path)
                            local_module = strategy.get_module_path(file_path)
                            if local_module == defining_module:
                                module_imported = True
                                
                        if not module_imported:
                            # It's a false positive (grep match but no actual dependency graph link)
                            has_graph_dependency = False
                    except Exception:
                        pass # proceed if we can't parse it
                        
                if has_graph_dependency:
                    if self._is_test_file(file_rel_path):
                        impacted_tests.add(file_rel_path)
                    else:
                        impacted_files.add(file_rel_path)

            return {
                "impacted_files": sorted(list(impacted_files)),
                "impacted_tests": sorted(list(impacted_tests))
            }

        except Exception as e:
            return {"impacted_files": [], "impacted_tests": []}

    def _is_test_file(self, file_path: str) -> bool:
        lower_path = file_path.lower()
        if "test" in lower_path:
            # Typical conventions
            if "/test" in lower_path or "\\test" in lower_path:
                return True
            if lower_path.endswith("_test.py") or lower_path.endswith("_test.go"):
                return True
            if lower_path.endswith("test.kt") or lower_path.endswith("test.java") or lower_path.endswith("tests.py"):
                return True
            if lower_path.endswith(".spec.ts") or lower_path.endswith(".test.ts"):
                return True
            if lower_path.endswith(".spec.js") or lower_path.endswith(".test.js"):
                return True
            if "test_" in os.path.basename(lower_path):
                return True
            if lower_path.startswith("test") or lower_path.startswith("tests"):
                return True
        return False

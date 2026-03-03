import json
import re
from typing import Optional, Dict, Any
from aide.core.domain.ports import FileSystemPort, StrategyProviderPort
from aide.parsing.domain.ports import LanguageParserPort

class ScaffoldMocksUseCase:
    def __init__(self, file_system: FileSystemPort, language_parser: LanguageParserPort, strategy_provider: StrategyProviderPort) -> None:
        self.file_system = file_system
        self.language_parser = language_parser
        self.strategy_provider = strategy_provider

    def execute(self, file_path: str, class_name: str, output_format: str = "json") -> str | None:
        content = self.file_system.read_file(file_path)
        lines = content.splitlines()
        
        strategy = self.strategy_provider.get_strategy(file_path)
        
        # Find the symbol range 
        start, end = strategy.find_symbol_range(lines, class_name)
        if not start:
            return None
        
        # Extract dependencies (parameters from __init__ or constructor)
        # This is a naive regex-based dependency extraction for demonstration.
        # In a full AST, this would be highly precise.
        
        class_code = "\n".join(lines[start - 1 : end])
        
        dependencies = self._extract_dependencies(class_code, class_name, file_path)
        
        mock_scaffolds = []
        for dep_name, dep_type in dependencies.items():
            mock_scaffolds.append(self._generate_mock_class(dep_name, dep_type, file_path))
            
        context_data: dict[str, Any] = {
            "target_class": class_name,
            "file_path": file_path,
            "dependencies_found": len(dependencies),
            "mock_classes": mock_scaffolds
        }
        
        if output_format == "json":
            return json.dumps(context_data, indent=2)
        elif output_format == "markdown":
            return self._format_markdown(context_data)
        else:
            return json.dumps(context_data)
            

    def _extract_dependencies(self, class_code: str, class_name: str, file_path: str) -> dict[str, str]:
        deps = {}
        if file_path.endswith(".py"):
            # Look for __init__(self, arg1: Type, arg2=...)
            init_match = re.search(r'def __init__\s*\(\s*self\s*(.*?)\)', class_code, re.DOTALL)
            if init_match:
                params_str = init_match.group(1)
                if params_str.startswith(","):
                    params_str = params_str[1:]
                
                # Naive split by comma, ignoring complex typings
                for param in params_str.split(","):
                    param = param.strip()
                    if not param: continue
                    parts = param.split(":")
                    name = parts[0].strip()
                    dep_type = parts[1].split("=")[0].strip() if len(parts) > 1 else "Any"
                    if name != "self":
                        deps[name] = dep_type
                        
        elif file_path.endswith((".kt", ".java")):
             # Look for class Name(val x: Type, ...)
            match = re.search(rf'class\s+{class_name}\s*\((.*?)\)', class_code, re.DOTALL)
            if match:
                params_str = match.group(1)
                for param in params_str.split(","):
                    param = param.strip()
                    if not param: continue
                    # Remove val/var
                    param = re.sub(r'^(val|var)\s+', '', param)
                    parts = param.split(":")
                    name = parts[0].strip()
                    dep_type = parts[1].split("=")[0].strip() if len(parts) > 1 else "Any"
                    deps[name] = dep_type

        return deps

    def _generate_mock_class(self, param_name: str, type_name: str, file_path: str) -> str:
        # Title case the param name if type is unknown
        mock_name = f"Mock{type_name}" if type_name != "Any" else f"Mock{param_name.title().replace('_', '')}"
        
        if file_path.endswith(".py"):
            return f"class {mock_name}:\n    def __init__(self):\n        pass\n"
        elif file_path.endswith(".kt"):
            # Provide an interface mock stub
            if type_name != "Any":
                return f"class {mock_name} : {type_name} {{\n}}\n"
            return f"class {mock_name} {{\n}}\n"
        else:
            return f"class {mock_name} {{\n}}\n"

    def _format_markdown(self, data: dict[str, Any]) -> str:
        md = f"# Mocks for `{data['target_class']}`\n\n"
        md += f"**File:** `{data['file_path']}`\n"
        md += f"**Dependencies Detected:** {data['dependencies_found']}\n\n"
        
        md += "## Boilerplate Mocks\n```\n"
        for mock in data['mock_classes']:
            md += mock + "\n"
        md += "```\n"
        return md

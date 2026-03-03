import json
from typing import Optional, Dict, Any
from aide.core.domain.ports import FileSystemPort, StrategyProviderPort
from aide.parsing.domain.ports import LanguageParserPort

class GenerateTestsUseCase:
    def __init__(self, file_system: FileSystemPort, language_parser: LanguageParserPort, strategy_provider: StrategyProviderPort) -> None:
        self.file_system = file_system
        self.language_parser = language_parser
        self.strategy_provider = strategy_provider

    def execute(self, file_path: str, symbol_name: str, output_format: str = "json") -> str | None:
        content = self.file_system.read_file(file_path)
        lines = content.splitlines()
        
        # 1. Provide strategy for finding the symbol
        strategy = self.strategy_provider.get_strategy(file_path)
        
        # Find the symbol range
        start, end = strategy.find_symbol_range(lines, symbol_name)
        if not start:
            return None
            
        symbol_code = "\n".join(lines[start - 1 : end])
        
        # Extract dependencies (imports)
        imports, header = strategy.extract_imports_and_header(lines)
        
        # We also get the module path if the language supports it
        module_path = strategy.get_module_path(file_path)
        
        import os
        ext = os.path.splitext(file_path)[1].lower()
        
        # Build the context object
        context_data: dict[str, Any] = {
            "language_extension": ext,
            "target_symbol": symbol_name,
            "file_path": file_path,
            "module_path": module_path,
            "header": header,
            "imports": imports,
            "symbol_code": symbol_code
        }
        
        if output_format == "json":
            return json.dumps(context_data, indent=2)
        elif output_format == "markdown":
            return self._format_markdown(context_data)
        else:
            return json.dumps(context_data)
            

    def _format_markdown(self, data: dict[str, Any]) -> str:
        md = f"# Context for `{data['target_symbol']}`\n\n"
        md += f"**File:** `{data['file_path']}`\n"
        md += f"**Module:** `{data['module_path']}`\n\n"
        
        md += "## Dependencies\n```\n"
        if data['header']:
            md += data['header'] + "\n"
        for imp in data['imports']:
            md += imp + "\n"
        md += "```\n\n"
        
        md += "## Target Code\n```\n"
        md += data['symbol_code'] + "\n"
        md += "```\n"
        
        return md

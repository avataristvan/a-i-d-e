import ast
from typing import List
from aide.parsing.domain.ports import LanguageParserPort
from aide.parsing.domain.models import SymbolNode

class AstPythonParser(LanguageParserPort):
    """Uses the native Python `ast` module to deterministically build precise symbol trees, 
    eliminating regex logic flaws for nested classes or multiline definitions."""
    
    def parse(self, content: str, file_extension: str) -> List[SymbolNode]:
        if file_extension != ".py":
            return []
            
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # If the code is completely broken, return empty. Or fallback. 
            # AIDE assumes mostly valid code.
            return []
            
        return self._walk(tree.body)
        
    def _walk(self, nodes: list) -> List[SymbolNode]:
        symbols = []
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                children = self._walk(node.body)
                symbols.append(SymbolNode(
                    name=node.name,
                    kind="class",
                    line_number=node.lineno,
                    children=children
                ))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                children = self._walk(node.body)
                symbols.append(SymbolNode(
                    name=node.name,
                    kind="function",
                    line_number=node.lineno,
                    children=children
                ))
            # We skip ast.Assign (variables) purely because AIDE currently focuses on 
            # top-level structural bounds (classes/functions) for outline and movement.
        return symbols

    def parse_imports(self, content: str, file_extension: str) -> List[str]:
        if file_extension != ".py":
            return []
            
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []
            
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
                    # We could also append node.module + "." + alias.name, but usually 
                    # the module or package origin is sufficient for AIDE dependency checks.
        return imports

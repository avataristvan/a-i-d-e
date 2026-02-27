import ast
from typing import Any, Tuple, Callable, Generator
from aide.parsing.domain.ports import LanguageParserPort
from aide.parsing.domain.models import SymbolNode

class AstPythonParser(LanguageParserPort):
    """Uses the native Python `ast` module to deterministically build precise symbol trees, 
    eliminating regex logic flaws for nested classes or multiline definitions."""
    
    def parse(self, content: str, file_extension: str) -> list[SymbolNode]:
        if file_extension != ".py":
            return []
            
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # If the code is completely broken, return empty. Or fallback. 
            # AIDE assumes mostly valid code.
            return []
            
        return self._walk(tree.body)
        
    def _walk(self, nodes: list) -> list[SymbolNode]:
        symbols = []
        for node in nodes:
            match node:
                case ast.ClassDef(name=name, lineno=lineno, body=body):
                    children = self._walk(body)
                    symbols.append(SymbolNode(
                        name=name,
                        kind="class",
                        line_number=lineno,
                        children=children
                    ))
                case ast.FunctionDef(name=name, lineno=lineno, body=body) | ast.AsyncFunctionDef(name=name, lineno=lineno, body=body):
                    children = self._walk(body)
                    symbols.append(SymbolNode(
                        name=name,
                        kind="function",
                        line_number=lineno,
                        children=children
                    ))
            # We skip ast.Assign (variables) purely because AIDE currently focuses on 
            # top-level structural bounds (classes/functions) for outline and movement.
        return symbols

    def parse_imports(self, content: str, file_extension: str) -> list[str]:
        if file_extension != ".py":
            return []
            
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []
            
        imports = []
        for node in ast.walk(tree):
            match node:
                case ast.Import(names=names):
                    for alias in names:
                        imports.append(alias.name)
                case ast.ImportFrom(module=module) if module is not None:
                    imports.append(module)
                    # We could also append node.module + "." + alias.name, but usually 
                    # the module or package origin is sufficient for AIDE dependency checks.
        return imports

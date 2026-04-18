import ast
import os

from aide.parsing.domain.models import SymbolNode
from aide.parsing.domain.ports import LanguageParserPort


class SymbolNotFoundError(Exception):
    pass


class SymbolLocator:
    """Finds the line range (start, end) of a named symbol within a source file."""

    def __init__(self, language_parser: LanguageParserPort) -> None:
        self.language_parser = language_parser

    def locate(self, file_path: str, content: str, symbol_name: str) -> tuple[int, int]:
        ext = os.path.splitext(file_path)[1]
        if ext == ".py":
            return self._locate_python(content, symbol_name)
        return self._locate_generic(content, ext, symbol_name)

    def _locate_python(self, content: str, symbol_name: str) -> tuple[int, int]:
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            raise SymbolNotFoundError(f"Could not parse file: {e}") from e

        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == symbol_name:
                    return node.lineno, node.end_lineno

        raise SymbolNotFoundError(f"Symbol '{symbol_name}' not found")

    def _locate_generic(self, content: str, ext: str, symbol_name: str) -> tuple[int, int]:
        symbols = self.language_parser.parse(content, ext)
        flat = self._flatten(symbols)
        flat.sort(key=lambda s: s.line_number)

        for i, sym in enumerate(flat):
            if sym.name == symbol_name:
                start = sym.line_number
                end = flat[i + 1].line_number - 1 if i + 1 < len(flat) else content.count("\n") + 1
                return start, end

        raise SymbolNotFoundError(f"Symbol '{symbol_name}' not found")

    def _flatten(self, symbols: list[SymbolNode]) -> list[SymbolNode]:
        result = []
        for sym in symbols:
            result.append(sym)
            result.extend(self._flatten(sym.children))
        return result

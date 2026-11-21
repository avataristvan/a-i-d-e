import os
import tempfile

from aide.core.infrastructure.lsp_client import StdioLspClient
from aide.core.infrastructure.lsp_registry import CLANGD
from aide.parsing.infrastructure.parsers import RegexLanguageParser
from aide.parsing.domain.ports import LanguageParserPort
from aide.parsing.domain.models import SymbolNode

# LSP SymbolKind values relevant for C/C++
_SYMBOL_KIND: dict[int, str] = {
    3: "namespace",
    5: "class",
    6: "function",   # Method
    9: "function",   # Constructor
    10: "enum",
    12: "function",  # Function
    23: "struct",
}

CLANGD_EXTENSIONS = tuple(CLANGD.language_ids)


def is_clangd_available() -> bool:
    return CLANGD.is_available()


class ClangdCppParser(LanguageParserPort):
    """
    C/C++ parser backed by clangd via LSP.
    Starts clangd lazily on first use; degrades silently if unavailable.
    """

    def __init__(self):
        # No root and no background index: each parse is a single in-memory document.
        self._client = StdioLspClient([*CLANGD.command, "--background-index=false"],
                                      language_ids=CLANGD.language_ids, init_timeout=15.0, request_timeout=10.0)
        self._started = False
        self._unavailable = False
        self._fallback = RegexLanguageParser()
        # Use a counter so each parse gets a unique URI, avoiding clangd cache confusion
        self._doc_counter = 0

    def parse(self, content: str, file_extension: str) -> list[SymbolNode]:
        if not self._ensure_started():
            return []
        self._doc_counter += 1
        path = os.path.join(tempfile.gettempdir(), f"aide-parse-{self._doc_counter}{file_extension}")
        try:
            self._client.open_document(path, content)
            try:
                return _convert_symbols(self._client.document_symbols(path))
            finally:
                self._client.close_document(path)
        except Exception:
            # A hung or crashed clangd would otherwise cost a full request timeout per file.
            self._give_up()
            return []

    def parse_imports(self, content: str, file_extension: str) -> list[str]:
        return self._fallback.parse_imports(content, file_extension)

    def _ensure_started(self) -> bool:
        if self._unavailable:
            return False
        if not self._started:
            try:
                self._client.start()
                self._started = True
            except Exception:
                self._give_up()
                return False
        return True

    def _give_up(self) -> None:
        self._unavailable = True
        self._client.stop()


def _convert_symbols(symbols: list[dict]) -> list[SymbolNode]:
    nodes = []
    for sym in symbols:
        kind = _SYMBOL_KIND.get(sym.get("kind", 0))
        if kind is None:
            continue
        sel = sym.get("selectionRange") or sym.get("range") or {}
        line = sel.get("start", {}).get("line", 0) + 1
        children = _convert_symbols(sym.get("children") or [])
        nodes.append(SymbolNode(name=sym["name"], kind=kind, line_number=line, children=children))
    return nodes

from abc import ABC, abstractmethod
from typing import Any, Tuple, Callable, Generator
from aide.parsing.domain.models import SymbolNode

class LanguageParserPort(ABC):
    @abstractmethod
    def parse(self, content: str, file_extension: str) -> list[SymbolNode]:
        """Parses content and returns a list of top-level symbols."""
        pass

    @abstractmethod
    def parse_imports(self, content: str, file_extension: str) -> list[str]:
        """Parses content and returns a list of imported modules/packages."""
        pass

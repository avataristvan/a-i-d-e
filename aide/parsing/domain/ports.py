from abc import ABC, abstractmethod
from typing import List
from aide.parsing.domain.models import SymbolNode

class LanguageParserPort(ABC):
    @abstractmethod
    def parse(self, content: str, file_extension: str) -> List[SymbolNode]:
        """Parses content and returns a list of top-level symbols."""
        pass

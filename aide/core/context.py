from dataclasses import dataclass
from aide.core.domain.ports import FileSystemPort
from aide.parsing.domain.ports import LanguageParserPort
from aide.core.infrastructure.strategy_provider import StrategyProvider

@dataclass
class Context:
    file_system: FileSystemPort
    language_parser: LanguageParserPort
    strategy_provider: StrategyProvider = StrategyProvider()

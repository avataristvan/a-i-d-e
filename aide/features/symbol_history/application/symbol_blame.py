from aide.core.domain.ports import FileSystemPort
from aide.features.symbol_history.domain.ports import GitPort, BlameLine
from aide.features.symbol_history.application.symbol_locator import SymbolLocator
from aide.parsing.domain.ports import LanguageParserPort


class SymbolBlameUseCase:
    def __init__(self, file_system: FileSystemPort, language_parser: LanguageParserPort, git: GitPort) -> None:
        self.file_system = file_system
        self.locator = SymbolLocator(language_parser)
        self.git = git

    def execute(self, file_path: str, symbol_name: str) -> list[BlameLine]:
        content = self.file_system.read_file(file_path)
        start, end = self.locator.locate(file_path, content, symbol_name)
        return self.git.blame(file_path, start, end)

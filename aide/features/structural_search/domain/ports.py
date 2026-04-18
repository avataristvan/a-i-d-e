from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SemgrepMatch:
    file: str
    line: int
    column: int
    end_line: int
    end_column: int
    match_text: str


@dataclass
class SemgrepReplaceResult:
    files_modified: list[str]
    total_fixes: int
    dry_run: bool


class SemgrepRunnerPort(ABC):
    @abstractmethod
    def search(self, pattern: str, lang: str, root: str) -> list[SemgrepMatch]:
        pass

    @abstractmethod
    def replace(self, pattern: str, rewrite: str, lang: str, root: str, dry_run: bool) -> SemgrepReplaceResult:
        pass

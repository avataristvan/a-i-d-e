from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BlameLine:
    line_number: int
    content: str
    commit_hash: str
    author: str
    author_email: str
    timestamp: int
    summary: str


@dataclass
class CommitInfo:
    hash: str
    author: str
    author_email: str
    timestamp: int
    message: str


class GitPort(ABC):
    @abstractmethod
    def blame(self, file_path: str, start_line: int, end_line: int) -> list[BlameLine]:
        pass

    @abstractmethod
    def log(self, file_path: str, start_line: int, end_line: int, limit: int) -> list[CommitInfo]:
        pass

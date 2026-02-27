from dataclasses import dataclass
from typing import Any, Tuple, Callable, Generator

@dataclass
class TextReplacement:
    original_text: str
    new_text: str

@dataclass
class FileChange:
    file_path: str
    replacements: list[TextReplacement]
    
    @property
    def change_count(self) -> int:
        return len(self.replacements)

@dataclass
class OperationResult:
    success: bool
    message: str
    files_changed: int
    total_replacements: int

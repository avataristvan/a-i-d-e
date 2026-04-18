from dataclasses import dataclass
from typing import Any, Tuple, Callable, Generator

@dataclass
class TextReplacement:
    original_text: str
    new_text: str

@dataclass
class OperationResult:
    success: bool
    message: str
    files_changed: int
    total_replacements: int

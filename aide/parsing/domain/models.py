from dataclasses import dataclass
from typing import Any, Tuple, Callable, Generator

@dataclass
class SymbolNode:
    name: str
    kind: str  # "class", "function", "variable"
    line_number: int
    children: list['SymbolNode']

from dataclasses import dataclass
from typing import List

@dataclass
class SymbolNode:
    name: str
    kind: str  # "class", "function", "variable"
    line_number: int
    children: List['SymbolNode']

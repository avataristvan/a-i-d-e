import fnmatch
import os
import re
from dataclasses import dataclass

from aide.core.domain.ports import FileSystemPort
from aide.parsing.domain.ports import LanguageParserPort

_SOURCE_EXTENSIONS = {'.py', '.kt', '.ts', '.tsx', '.js', '.jsx', '.java', '.go', '.rs', '.cs', '.rb'}
_TEST_FILE_PATTERNS = ('test_*.py', '*_test.py', '*Test.kt', '*Spec.ts', '*spec.ts')


@dataclass
class DeadSymbol:
    name: str
    kind: str
    file: str
    line: int


class FindDeadCodeUseCase:
    def __init__(self, file_system: FileSystemPort, language_parser: LanguageParserPort) -> None:
        self.file_system = file_system
        self.language_parser = language_parser

    def execute(self, root: str, ignore_patterns: list[str]) -> list[DeadSymbol]:
        source_files = self._collect_source_files(root)

        # Pass 1: collect all defined top-level symbols (skip test files)
        defined: list[DeadSymbol] = []
        for file_path in source_files:
            if self._is_test_file(file_path):
                continue
            try:
                content = self.file_system.read_file(file_path)
                ext = os.path.splitext(file_path)[1]
                for sym in self.language_parser.parse(content, ext):
                    if not self._should_ignore(sym.name, ignore_patterns):
                        defined.append(DeadSymbol(
                            name=sym.name,
                            kind=sym.kind,
                            file=os.path.relpath(file_path, root),
                            line=sym.line_number,
                        ))
            except Exception:
                continue

        if not defined:
            return []

        # Pass 2: collect all identifier occurrences across all files (single-pass, set lookup)
        symbol_names = {sym.name for sym in defined}
        # symbol_name → set of (rel_file, line) where the name appears
        occurrences: dict[str, set[tuple[str, int]]] = {name: set() for name in symbol_names}

        for file_path in source_files:
            try:
                content = self.file_system.read_file(file_path)
                rel_path = os.path.relpath(file_path, root)
                for i, line in enumerate(content.splitlines(), start=1):
                    for token in re.findall(r'\b\w+\b', line):
                        if token in symbol_names:
                            occurrences[token].add((rel_path, i))
            except Exception:
                continue

        # Dead = defined but referenced nowhere except its own definition line
        dead = [
            sym for sym in defined
            if not (occurrences[sym.name] - {(sym.file, sym.line)})
        ]
        return sorted(dead, key=lambda s: (s.file, s.line))

    def _collect_source_files(self, root: str) -> list[str]:
        return [
            f for f in self.file_system.walk_files(root)
            if os.path.splitext(f)[1] in _SOURCE_EXTENSIONS
        ]

    def _is_test_file(self, file_path: str) -> bool:
        return any(fnmatch.fnmatch(os.path.basename(file_path), pat) for pat in _TEST_FILE_PATTERNS)

    def _should_ignore(self, name: str, user_patterns: list[str]) -> bool:
        if name.startswith('__') or name == 'main':
            return True
        return any(fnmatch.fnmatch(name, pat) for pat in user_patterns)

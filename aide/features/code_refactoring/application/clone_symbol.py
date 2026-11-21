import os
import re
from dataclasses import dataclass, field
from aide.core.domain.declaration_extent import find_declaration_end
from aide.core.domain.ports import FileSystemPort, StrategyProviderPort


@dataclass
class CloneSymbolResult:
    success: bool
    message: str
    cloned_symbols: list[str] = field(default_factory=list)


class CloneSymbolUseCase:
    """Clones a template symbol and its structurally-coupled companions
    (extension functions/properties, prefixed top-level declarations) into a
    new symbol with all references renamed. Kotlin-only for now.
    """

    def __init__(self, file_system: FileSystemPort, strategy_provider: StrategyProviderPort) -> None:
        self.file_system = file_system
        self.strategy_provider = strategy_provider

    def execute(
        self,
        file_path: str,
        template_symbol: str,
        new_symbol: str,
        substitutions: dict[str, str] | None = None,
        dry_run: bool = False,
    ) -> CloneSymbolResult:
        file_path = os.path.abspath(file_path)
        substitutions = substitutions or {}

        if os.path.splitext(file_path)[1] != ".kt":
            return CloneSymbolResult(False, "clone-symbol currently only supports Kotlin (.kt) files.")

        if not self.file_system.path_exists(file_path):
            return CloneSymbolResult(False, f"File not found: {file_path}")

        strategy = self.strategy_provider.get_strategy(file_path)
        content = self.file_system.read_file(file_path)
        newline = "\r\n" if "\r\n" in content else "\n"
        lines = content.splitlines()

        start, end = strategy.find_symbol_range(lines, template_symbol)
        if not start or not end:
            return CloneSymbolResult(False, f"Template symbol '{template_symbol}' not found in {file_path}")

        existing_start, _ = strategy.find_symbol_range(lines, new_symbol)
        if existing_start:
            return CloneSymbolResult(False, f"Symbol '{new_symbol}' already exists in {file_path}")

        ranges: list[tuple[int, int]] = [(start, end)]
        names_cloned = [template_symbol]

        for member_start, member_end, member_name in self._find_related_declarations(lines, template_symbol, ranges):
            ranges.append((member_start, member_end))
            names_cloned.append(f"{template_symbol}.{member_name}")

        ranges.sort(key=lambda r: r[0])

        blocks = []
        for block_start, block_end in ranges:
            block_text = newline.join(lines[block_start - 1 : block_end])
            blocks.append(self._rename(block_text, template_symbol, new_symbol, substitutions))

        insert_after = max(r[1] for r in ranges)
        clone_text = (newline * 2).join(blocks)

        new_lines = lines[:insert_after] + ["", clone_text] + lines[insert_after:]
        new_content = newline.join(new_lines).rstrip() + newline

        if not dry_run:
            self.file_system.write_file(file_path, new_content)

        return CloneSymbolResult(
            True,
            f"Cloned {len(ranges)} symbol(s) from '{template_symbol}' as '{new_symbol}'.",
            names_cloned,
        )

    def _find_related_declarations(self, lines: list[str], template_symbol: str, primary_ranges: list[tuple[int, int]]) -> list[tuple[int, int, str]]:
        """Finds extension members (`fun/val/var Template.member`) and prefixed
        top-level declarations (`TemplatePresets`, `TemplateDefault`, ...) that
        are structurally coupled to the template symbol but declared outside its
        own range."""
        taken_ranges = list(primary_ranges)
        escaped = re.escape(template_symbol)
        extension_pattern = re.compile(rf"^(?:(?:private|internal|public)\s+)?(?:fun|val|var)\s+{escaped}\.(\w+)")
        prefixed_pattern = re.compile(rf"^(?:(?:private|internal|public)\s+)?(?:fun|val|var|object|class)\s+({escaped}[A-Z]\w*)\b")

        found = []
        for i, line in enumerate(lines):
            line_no = i + 1
            if any(rs <= line_no <= re_ for rs, re_ in taken_ranges):
                continue

            match = extension_pattern.match(line)
            member_name = None
            if match:
                member_name = match.group(1)
            else:
                match = prefixed_pattern.match(line)
                if match:
                    member_name = match.group(1)

            if not member_name:
                continue

            member_start, member_end = self._find_declaration_extent(lines, i)
            if member_start is None or member_end is None:
                continue
            if any(rs <= member_start <= re_ or rs <= member_end <= re_ for rs, re_ in taken_ranges):
                continue

            taken_ranges.append((member_start, member_end))
            found.append((member_start, member_end, member_name))

        return found

    def _find_declaration_extent(self, lines: list[str], start_index: int) -> tuple[int | None, int | None]:
        end_index = find_declaration_end(lines, start_index)
        return (None, None) if end_index is None else (start_index + 1, end_index + 1)

    def _rename(self, text: str, template_symbol: str, new_symbol: str, substitutions: dict[str, str]) -> str:
        renamed = re.sub(rf"\b{re.escape(template_symbol)}(?=[A-Z_]|\b)", new_symbol, text)
        for old, new in substitutions.items():
            renamed = re.sub(rf"\b{re.escape(old)}\b", new, renamed)
        return renamed

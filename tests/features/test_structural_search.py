import pytest
from aide.features.structural_search.domain.ports import SemgrepRunnerPort, SemgrepMatch, SemgrepReplaceResult
from aide.features.structural_search.application.structural_search import StructuralSearchUseCase
from aide.features.structural_search.application.structural_replace import StructuralReplaceUseCase


class StubSemgrepRunner(SemgrepRunnerPort):
    def search(self, pattern: str, lang: str, root: str) -> list[SemgrepMatch]:
        return [
            SemgrepMatch(file="src/foo.py", line=5, column=1, end_line=5, end_column=20, match_text="if x: return x")
        ]

    def replace(self, pattern: str, rewrite: str, lang: str, root: str, dry_run: bool) -> SemgrepReplaceResult:
        return SemgrepReplaceResult(files_modified=["src/foo.py"], total_fixes=1, dry_run=dry_run)


class EmptySemgrepRunner(SemgrepRunnerPort):
    def search(self, pattern, lang, root):
        return []

    def replace(self, pattern, rewrite, lang, root, dry_run):
        return SemgrepReplaceResult(files_modified=[], total_fixes=0, dry_run=dry_run)


def test_search_returns_matches():
    matches = StructuralSearchUseCase(StubSemgrepRunner()).execute("if $X: return $X", "python", ".")
    assert len(matches) == 1
    assert matches[0].file == "src/foo.py"
    assert matches[0].line == 5
    assert matches[0].match_text == "if x: return x"


def test_search_returns_empty_when_no_matches():
    matches = StructuralSearchUseCase(EmptySemgrepRunner()).execute("if $X: return $X", "python", ".")
    assert matches == []


def test_replace_dry_run_does_not_apply():
    result = StructuralReplaceUseCase(StubSemgrepRunner()).execute(
        "if $X: return $X", "$X", "python", ".", dry_run=True
    )
    assert result.dry_run is True
    assert result.total_fixes == 1
    assert "src/foo.py" in result.files_modified


def test_replace_live_marks_files_modified():
    result = StructuralReplaceUseCase(StubSemgrepRunner()).execute(
        "if $X: return $X", "$X", "python", ".", dry_run=False
    )
    assert result.dry_run is False
    assert result.files_modified == ["src/foo.py"]


def test_replace_no_matches_returns_empty():
    result = StructuralReplaceUseCase(EmptySemgrepRunner()).execute(
        "if $X: return $X", "$X", "python", ".", dry_run=True
    )
    assert result.total_fixes == 0
    assert result.files_modified == []

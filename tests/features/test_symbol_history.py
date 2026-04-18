import os
import pytest
from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.parsing.infrastructure.ast_parsers import AstPythonParser
from aide.features.symbol_history.domain.ports import GitPort, BlameLine, CommitInfo
from aide.features.symbol_history.application.symbol_blame import SymbolBlameUseCase
from aide.features.symbol_history.application.symbol_history import SymbolHistoryUseCase
from aide.features.symbol_history.application.symbol_locator import SymbolLocator, SymbolNotFoundError

SAMPLE = """\
class Alpha:
    def method(self):
        pass

class Beta:
    pass
"""

_BLAME = [
    BlameLine(1, "class Alpha:", "abc123", "Alice", "a@x.com", 1000, "add Alpha"),
    BlameLine(2, "    def method(self):", "def456", "Bob", "b@x.com", 2000, "add method"),
    BlameLine(3, "        pass", "def456", "Bob", "b@x.com", 2000, "add method"),
]
_COMMITS = [
    CommitInfo("def456abc", "Bob", "b@x.com", 2000, "add method"),
    CommitInfo("abc123def", "Alice", "a@x.com", 1000, "add Alpha"),
]


class StubGit(GitPort):
    def __init__(self, blame=None, commits=None):
        self._blame = blame or _BLAME
        self._commits = commits or _COMMITS

    def blame(self, file_path, start_line, end_line):
        return self._blame

    def log(self, file_path, start_line, end_line, limit):
        return self._commits[:limit]


@pytest.fixture
def fs(temp_dir):
    fs = OsFileSystem(jailed_root=temp_dir)
    fs.write_file(os.path.join(temp_dir, "sample.py"), SAMPLE)
    return fs, temp_dir


def test_blame_returns_lines(fs):
    filesystem, temp_dir = fs
    lines = SymbolBlameUseCase(filesystem, AstPythonParser(), StubGit()).execute(
        os.path.join(temp_dir, "sample.py"), "Alpha"
    )
    assert len(lines) == 3
    assert lines[0].author == "Alice"
    assert lines[1].summary == "add method"


def test_history_returns_commits(fs):
    filesystem, temp_dir = fs
    commits = SymbolHistoryUseCase(filesystem, AstPythonParser(), StubGit()).execute(
        os.path.join(temp_dir, "sample.py"), "Alpha"
    )
    assert len(commits) == 2
    assert commits[0].message == "add method"


def test_history_respects_limit(fs):
    filesystem, temp_dir = fs
    commits = SymbolHistoryUseCase(filesystem, AstPythonParser(), StubGit()).execute(
        os.path.join(temp_dir, "sample.py"), "Alpha", limit=1
    )
    assert len(commits) == 1


def test_unknown_symbol_raises(fs):
    filesystem, temp_dir = fs
    with pytest.raises(SymbolNotFoundError):
        SymbolBlameUseCase(filesystem, AstPythonParser(), StubGit()).execute(
            os.path.join(temp_dir, "sample.py"), "NoSuchSymbol"
        )


def test_locator_finds_method(fs):
    filesystem, temp_dir = fs
    content = filesystem.read_file(os.path.join(temp_dir, "sample.py"))
    start, end = SymbolLocator(AstPythonParser()).locate(
        os.path.join(temp_dir, "sample.py"), content, "method"
    )
    assert start == 2
    assert end == 3


def test_locator_finds_class(fs):
    filesystem, temp_dir = fs
    content = filesystem.read_file(os.path.join(temp_dir, "sample.py"))
    start, end = SymbolLocator(AstPythonParser()).locate(
        os.path.join(temp_dir, "sample.py"), content, "Beta"
    )
    assert start == 5
    assert end == 6

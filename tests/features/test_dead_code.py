import os
import pytest
from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.parsing.infrastructure.ast_parsers import AstPythonParser
from aide.features.code_inspection.application.find_dead_code import FindDeadCodeUseCase


@pytest.fixture
def use_case(temp_dir):
    return FindDeadCodeUseCase(OsFileSystem(jailed_root=temp_dir), AstPythonParser())


def write(temp_dir, name, content):
    path = os.path.join(temp_dir, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    OsFileSystem(jailed_root=temp_dir).write_file(path, content)


def test_finds_unreferenced_class(temp_dir, use_case):
    write(temp_dir, "orphan.py", "class Orphan:\n    pass\n")
    dead = use_case.execute(temp_dir, [])
    assert any(s.name == "Orphan" for s in dead)


def test_referenced_class_is_alive(temp_dir, use_case):
    write(temp_dir, "models.py", "class Active:\n    pass\n")
    write(temp_dir, "main.py", "from models import Active\nActive()\n")
    dead = use_case.execute(temp_dir, [])
    assert all(s.name != "Active" for s in dead)


def test_ignores_dunder_names(temp_dir, use_case):
    write(temp_dir, "module.py", "def __init__():\n    pass\n\ndef __all__():\n    pass\n")
    dead = use_case.execute(temp_dir, [])
    assert all(not s.name.startswith("__") for s in dead)


def test_ignores_main(temp_dir, use_case):
    write(temp_dir, "entry.py", "def main():\n    pass\n")
    dead = use_case.execute(temp_dir, [])
    assert all(s.name != "main" for s in dead)


def test_user_ignore_pattern(temp_dir, use_case):
    write(temp_dir, "plugin.py", "class FooPlugin:\n    pass\n")
    dead = use_case.execute(temp_dir, ["*Plugin"])
    assert all(s.name != "FooPlugin" for s in dead)


def test_skips_test_files(temp_dir, use_case):
    write(temp_dir, "test_things.py", "class TestHelper:\n    pass\n")
    dead = use_case.execute(temp_dir, [])
    assert all(s.name != "TestHelper" for s in dead)


def test_returns_empty_for_clean_codebase(temp_dir, use_case):
    write(temp_dir, "a.py", "class Foo:\n    pass\n")
    write(temp_dir, "b.py", "from a import Foo\nFoo()\n")
    dead = use_case.execute(temp_dir, [])
    assert dead == []


def test_result_sorted_by_file_then_line(temp_dir, use_case):
    write(temp_dir, "a.py", "class Alpha:\n    pass\nclass Beta:\n    pass\n")
    dead = use_case.execute(temp_dir, [])
    files_lines = [(s.file, s.line) for s in dead]
    assert files_lines == sorted(files_lines)

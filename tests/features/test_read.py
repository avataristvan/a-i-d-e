import os
import pytest
from argparse import Namespace
from aide.core.context import Context
from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.parsing.infrastructure.parsers import RegexLanguageParser
from aide.features.code_inspection.plugin import CodeInspectionPlugin

@pytest.fixture
def test_context():
    fs = OsFileSystem()
    parser = RegexLanguageParser()
    return Context(file_system=fs, language_parser=parser)

def test_handle_read_full_file(temp_dir, test_context, capsys):
    test_file = os.path.join(temp_dir, "test.txt")
    test_context.file_system.write_file(test_file, "line 1\nline 2\nline 3\n")
    
    plugin = CodeInspectionPlugin()
    args = Namespace(file=test_file, selection=None)
    
    plugin.handle_read(args, test_context)
    
    captured = capsys.readouterr()
    assert "Total Lines: 3" in captured.out
    assert "1: line 1" in captured.out
    assert "3: line 3" in captured.out

def test_handle_read_with_selection(temp_dir, test_context, capsys):
    test_file = os.path.join(temp_dir, "test.txt")
    test_context.file_system.write_file(test_file, "line 1\nline 2\nline 3\nline 4\n")
    
    plugin = CodeInspectionPlugin()
    args = Namespace(file=test_file, selection="2:3")
    
    plugin.handle_read(args, test_context)
    
    captured = capsys.readouterr()
    assert "Showing lines 2 to 3" in captured.out
    assert "2: line 2" in captured.out
    assert "3: line 3" in captured.out
    assert "1: line 1" not in captured.out
    assert "4: line 4" not in captured.out

def test_handle_read_file_not_found(test_context, capsys):
    plugin = CodeInspectionPlugin()
    args = Namespace(file="nonexistent.txt", selection=None)
    
    plugin.handle_read(args, test_context)
    
    captured = capsys.readouterr()
    assert "❌ File not found" in captured.out

import os
import json
import pytest
from argparse import Namespace
from aide.core.context import Context
from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.parsing.infrastructure.parsers import RegexLanguageParser
from aide.features.code_refactoring.plugin import RefactorPlugin
from aide.core.infrastructure.strategy_provider import StrategyProvider

@pytest.fixture
def test_context(temp_dir):
    fs = OsFileSystem(jailed_root=temp_dir)
    parser = RegexLanguageParser()
    strategy_provider = StrategyProvider()
    return Context(file_system=fs, language_parser=parser, strategy_provider=strategy_provider)

def test_verify_refactor_reverts_on_test_failure(temp_dir, test_context, capsys):
    # Setup initial state
    test_file = os.path.join(temp_dir, "to_rename.py")
    test_context.file_system.write_file(test_file, "def old_func():\n    pass\n")

    # Register a mock TestRunnerPort that simulates test failure
    from aide.core.domain.ports import TestRunnerPort

    class MockFailingRunner(TestRunnerPort):
        def run(self, root_path):
            return {"success": False, "summary": "1 test failed", "failures": [{"test": "test_failure", "error": "AssertionError"}], "is_implemented": True}

    test_context.register(TestRunnerPort, MockFailingRunner())

    plugin = RefactorPlugin()
    
    # Try renaming a symbol with --verify
    args = Namespace(
        old_symbol="old_func",
        new_symbol="new_func",
        root=temp_dir,
        dry_run=False,
        verify=True
    )
    
    plugin.handle_rename_symbol(args, test_context)
    
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    
    assert output["success"] is False
    assert output["data"]["reverted"] is True
    
    # Verify the file was restored to its old state (no renaming occurred on disk permanently)
    file_content = test_context.file_system.read_file(test_file)
    assert "old_func" in file_content
    assert "new_func" not in file_content

def test_verify_refactor_commits_on_test_success(temp_dir, test_context, capsys):
    # Setup initial state
    test_file = os.path.join(temp_dir, "to_rename_success.py")
    test_context.file_system.write_file(test_file, "def old_func():\n    pass\n")

    # Register a mock TestRunnerPort that simulates test success
    from aide.core.domain.ports import TestRunnerPort

    class MockPassingRunner(TestRunnerPort):
        def run(self, root_path):
            return {"success": True, "summary": "1 test passed", "failures": [], "is_implemented": True}

    test_context.register(TestRunnerPort, MockPassingRunner())

    plugin = RefactorPlugin()
    
    args = Namespace(
        old_symbol="old_func",
        new_symbol="new_func",
        root=temp_dir,
        dry_run=False,
        verify=True
    )
    
    plugin.handle_rename_symbol(args, test_context)
    
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    
    assert output["success"] is True
    assert output["data"]["reverted"] is False
    
    # Verify the file was permanently changed
    file_content = test_context.file_system.read_file(test_file)
    assert "new_func" in file_content
    assert "old_func" not in file_content

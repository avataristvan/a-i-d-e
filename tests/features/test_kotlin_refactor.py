import os
import json
import pytest
from unittest.mock import patch, MagicMock
from aide.core.context import Context
from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.features.code_refactoring.plugin import RefactorPlugin
from aide.parsing.infrastructure.parsers import RegexLanguageParser, CompositeLanguageParser

@pytest.fixture
def kotlin_project(tmp_path):
    src_root = tmp_path / "app/src/main/java"
    src_root.mkdir(parents=True)
    
    package_dir = src_root / "com/example/mypackage"
    package_dir.mkdir(parents=True)
    
    kotlin_file = package_dir / "MyClass.kt"
    kotlin_file.write_text("""package com.example.mypackage

class MyClass {
    fun hello() = "world"
}
""")
    
    # Add a gradlew file to make it a Kotlin project
    gradlew = tmp_path / "gradlew"
    gradlew.write_text("""#!/bin/bash
echo "Running gradle tests"
exit 0""")
    gradlew.chmod(0o755)
    
    return tmp_path

def test_move_package_kotlin_verification_skip_on_missing_runner(kotlin_project):
    # When gradle fails, the refactoring should be reverted
    file_system = OsFileSystem(jailed_root=str(kotlin_project))
    context = Context(file_system=file_system, language_parser=CompositeLanguageParser(RegexLanguageParser()))

    from aide.core.domain.ports import TestRunnerPort
    from aide.features.testing_execution.infrastructure.test_runner_adapter import TestRunnerAdapter
    context.register(TestRunnerPort, TestRunnerAdapter(file_system))

    plugin = RefactorPlugin()
    
    class Args:
        root = str(kotlin_project)
        src = "com/example/mypackage"
        src_root = "app/src/main/java"
        dest_package = "com.example.newpackage"
        dry_run = False
        verify = True
    
    with patch("subprocess.run") as mock_run:
        # Mock gradle failure
        mock_run.return_value = MagicMock(returncode=1, stdout="Build failed", stderr="")
        
        # We need to capture stdout
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            plugin.handle_move_package(Args(), context)
        
        output = f.getvalue()
        result = json.loads(output)
        
        assert result["success"] is False
        assert "Tests failed" in result["message"]
        assert result["data"]["reverted"] is True
        
        # Check if file was moved back
        assert os.path.exists(os.path.join(kotlin_project, "app/src/main/java/com/example/mypackage/MyClass.kt"))
        assert not os.path.exists(os.path.join(kotlin_project, "app/src/main/java/com/example/newpackage/MyClass.kt"))

def test_move_package_path_sensitivity(kotlin_project):
    # Test that src can be relative to src-root
    file_system = OsFileSystem(jailed_root=str(kotlin_project))
    context = Context(file_system=file_system, language_parser=CompositeLanguageParser(RegexLanguageParser()))
    plugin = RefactorPlugin()
    
    class Args:
        root = str(kotlin_project)
        src = "com/example/mypackage" # Relative to src-root
        src_root = "app/src/main/java"
        dest_package = "com.example.other"
        dry_run = False
        verify = False
    
    import io
    from contextlib import redirect_stdout
    f = io.StringIO()
    with redirect_stdout(f):
        plugin.handle_move_package(Args(), context)
    
    result = json.loads(f.getvalue())
    assert result["success"] is True
    assert os.path.exists(os.path.join(kotlin_project, "app/src/main/java/com/example/other/MyClass.kt"))

def test_move_package_verification_skipped_on_unsupported(tmp_path):
    # Project with no runner (e.g. just some random files)
    (tmp_path / "other").mkdir()
    (tmp_path / "other/file.txt").write_text("hello")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/mypkg").mkdir()
    (tmp_path / "src/mypkg/main.txt").write_text("content")
    
    file_system = OsFileSystem(jailed_root=str(tmp_path))
    context = Context(file_system=file_system, language_parser=CompositeLanguageParser(RegexLanguageParser()))
    plugin = RefactorPlugin()
    
    class Args:
        root = str(tmp_path)
        src = "mypkg"
        src_root = "src"
        dest_package = "newpkg"
        dry_run = False
        verify = True
        
    import io
    from contextlib import redirect_stdout
    f = io.StringIO()
    with redirect_stdout(f):
        plugin.handle_move_package(Args(), context)
    
    result = json.loads(f.getvalue())
    assert result["success"] is True
    assert "verification was skipped" in result["message"]
    assert result["data"]["reverted"] is False
    assert os.path.exists(os.path.join(tmp_path, "src/newpkg/main.txt"))

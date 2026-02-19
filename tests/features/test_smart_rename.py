import pytest
import os
from aide.features.code_refactoring.application.smart_rename import SmartRenameUseCase
from aide.core.infrastructure.os_file_system import OsFileSystem

def test_smart_rename(temp_dir):
    fs = OsFileSystem(jailed_root=temp_dir)
    test_file = os.path.join(temp_dir, "test.py")
    fs.write_file(test_file, "def old_func():\n    old_func()\n")
    
    use_case = SmartRenameUseCase(fs)
    result = use_case.execute(temp_dir, "old_func", "new_func", use_word_boundary=True, dry_run=False)
    
    assert result.success
    assert result.files_changed == 1
    assert result.total_replacements == 2
    
    content = fs.read_file(test_file)
    assert "def new_func():" in content
    assert "old_func" not in content

def test_smart_rename_dry_run(temp_dir):
    fs = OsFileSystem(jailed_root=temp_dir)
    test_file = os.path.join(temp_dir, "test.kt")
    fs.write_file(test_file, "val oldVar = 1\n")
    
    use_case = SmartRenameUseCase(fs)
    result = use_case.execute(temp_dir, "oldVar", "newVar", dry_run=True)
    
    assert result.success
    assert result.files_changed == 1 # dry_run returns potential files changed
    
    content = fs.read_file(test_file)
    assert "oldVar" in content # Should not be written

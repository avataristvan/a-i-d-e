import pytest
import os
from argparse import Namespace
from aide.core.context import Context
from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.features.code_refactoring.plugin import RefactorPlugin

def test_handle_move_package(temp_dir, capsys):
    fs = OsFileSystem()
    context = Context(file_system=fs, language_parser=None, strategy_provider=None)
    plugin = RefactorPlugin()
    
    java_root = os.path.join(temp_dir, "app/src/main/java")
    src_pkg = os.path.join(java_root, "com/old")
    
    os.makedirs(src_pkg)
    fs.write_file(os.path.join(src_pkg, "Source.kt"), "package com.old\nclass Source {}\n")
    
    # Another file referencing it
    other_pkg = os.path.join(java_root, "com/other")
    os.makedirs(other_pkg)
    fs.write_file(os.path.join(other_pkg, "Other.kt"), "import com.old.Source\n")
    
    args = Namespace(
        src="app/src/main/java/com/old",
        dest_package="com.new",
        root=temp_dir,
        java_root="app/src/main/java",
        dry_run=False
    )
    
    plugin.handle_move_package(args, context)
    
    # Assertions
    assert not os.path.exists(os.path.join(src_pkg, "Source.kt"))
    assert os.path.exists(os.path.join(java_root, "com/new/Source.kt"))
    
    source_content = fs.read_file(os.path.join(java_root, "com/new/Source.kt"))
    assert "package com.new" in source_content
    
    other_content = fs.read_file(os.path.join(other_pkg, "Other.kt"))
    assert "import com.new.Source" in other_content

import pytest
import os
from aide.features.code_refactoring.application.move_symbol import MoveSymbolUseCase
from aide.core.infrastructure.os_file_system import OsFileSystem

class MockParser:
    pass

class MockStrategy:
    def extract_imports_and_header(self, lines):
        imports = [line for line in lines if line.startswith("import ")]
        return imports, "package com.example.src"
    def get_package_header(self, path):
        return "package com.example.dest"
    def find_symbol_range(self, lines, symbol):
        for i, line in enumerate(lines):
            if f"class {symbol}" in line:
                return i + 1, i + 1
        return None, None
    def adjust_visibility(self, content): return content
    def get_module_path(self, path): return "com.example.src" if "src" in path else "com.example.dest"
    def get_import_statement(self, pkg, symbol): return f"import {pkg}.{symbol}"

class MockStrategyProvider:
    def get_strategy(self, path): return MockStrategy()
    def get_strategy_for_extension(self, ext): return MockStrategy()

def test_move_symbol(temp_dir):
    fs = OsFileSystem()
    src_file = os.path.join(temp_dir, "src.kt")
    dest_file = os.path.join(temp_dir, "dest.kt")
    
    fs.write_file(src_file, "package com.example.src\nimport Bar\nclass Foo { val b = Bar() }\nfun other() {}")
    fs.write_file(dest_file, "package com.example.dest\nclass Dest {}\n")
    
    parser = MockParser()
    provider = MockStrategyProvider()
    
    # We also mock SmartRenameUseCase inside MoveSymbol
    use_case = MoveSymbolUseCase(fs, parser, provider)
    success = use_case.execute(src_file, "Foo", dest_file, dry_run=False)
    
    assert success
    assert "class Foo" not in fs.read_file(src_file)
    assert "class Foo" in fs.read_file(dest_file)
    assert "import Bar" in fs.read_file(dest_file)

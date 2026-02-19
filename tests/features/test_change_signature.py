import pytest
import os
from aide.features.code_refactoring.application.change_signature import ChangeSignatureUseCase
from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.parsing.domain.models import SymbolNode

class MockParser:
    def parse(self, content, ext):
        return [SymbolNode(name="foo", kind="function", line_number=1, children=[])]

class MockStrategy:
    def is_definition(self, line, symbol):
        return "def " in line and symbol in line
        
    def update_signature_string(self, line, symbol, is_definition, insertion):
        if is_definition:
            return line.replace("):", f"{insertion}):")
        else:
            return line.replace(")", f"{insertion})")

class MockStrategyProvider:
    def get_strategy(self, path): return MockStrategy()
    def get_strategy_for_extension(self, ext): return MockStrategy()

def test_change_signature(temp_dir):
    fs = OsFileSystem(jailed_root=temp_dir)
    test_file = os.path.join(temp_dir, "test.py")
    fs.write_file(test_file, "def foo():\n    pass\nfoo()\n")
    
    parser = MockParser()
    provider = MockStrategyProvider()
    
    use_case = ChangeSignatureUseCase(fs, parser, provider)
    success = use_case.execute(temp_dir, "foo", "x=0", "0", dry_run=False)
    
    assert success
    content = fs.read_file(test_file)
    assert "def foo(x=0):" in content
    assert "foo(0)" in content

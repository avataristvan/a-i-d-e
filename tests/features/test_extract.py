import pytest
import os
from aide.features.code_refactoring.application.extract_function import ExtractFunctionUseCase

class MockFileSystem:
    def __init__(self, contents):
        self.contents = contents
        
    def read_file(self, path):
        return self.contents[path]
        
    def write_file(self, path, content):
        self.contents[path] = content

class MockStrategy:
    def find_variables(self, text): return ["x"]
    def is_defined_in_outer_scope(self, var, preceeding): return True
    def infer_types(self, params, preceeding): return [("x", "int")]
    def get_function_template(self, name, params, lines, scope, indent): 
        return f"\ndef {name}({params}):\n    pass\n"
    def get_function_call(self, name, args, indent): 
        return f"{indent}{name}({args})"

class MockStrategyProvider:
    def get_strategy(self, path): 
        return MockStrategy()

def test_extract_function():
    fs = MockFileSystem({
        "test.py": "x = 1\nold_stuff()\nmore_stuff()\n"
    })
    provider = MockStrategyProvider()
    
    use_case = ExtractFunctionUseCase(fs, provider)
    success = use_case.execute("test.py", "2:3", "new_func", dry_run=False)
    
    assert success is True
    content = fs.read_file("test.py")
    assert "new_func(x)" in content
    assert "def new_func(x: int):" in content
    assert "old_stuff()" not in content # Replaced by call statement

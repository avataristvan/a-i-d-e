import pytest
import json
from aide.features.test_generation.application.generate_tests import GenerateTestsUseCase

class MockFileSystem:
    def __init__(self, contents): self.contents = contents
    def read_file(self, path): return self.contents[path]

class MockParser:
    pass

class MockStrategy:
    def find_symbol_range(self, lines, symbol):
        if symbol == "Foo":
            return 3, 4 # 1-indexed, meaning lines 3 and 4
        return None, None
    def extract_imports_and_header(self, lines):
        return ["import os"], "package com.example"
    def get_module_path(self, path):
        return "com.example.Foo"

class MockStrategyProvider:
    def get_strategy(self, path): return MockStrategy()

def test_generate_tests_json():
    fs = MockFileSystem({
        "test.kt": "package com.example\nimport os\nclass Foo {\n  fun bar() {}\n}\n"
    })
    
    use_case = GenerateTestsUseCase(fs, MockParser(), MockStrategyProvider())
    result = use_case.execute("test.kt", "Foo", "json")
    
    assert result is not None
    data = json.loads(result)
    assert data["target_symbol"] == "Foo"
    assert data["file_path"] == "test.kt"
    assert data["module_path"] == "com.example.Foo"
    assert data["header"] == "package com.example"
    assert "import os" in data["imports"]
    assert "class Foo {" in data["symbol_code"]

def test_generate_tests_markdown():
    fs = MockFileSystem({
        "test.kt": "package com.example\nimport os\nclass Foo {\n  fun bar() {}\n}\n"
    })
    
    use_case = GenerateTestsUseCase(fs, MockParser(), MockStrategyProvider())
    result = use_case.execute("test.kt", "Foo", "markdown")
    
    assert result is not None
    assert "# Context for `Foo`" in result
    assert "**Module:** `com.example.Foo`" in result
    assert "package com.example" in result
    assert "import os" in result
    assert "class Foo {" in result

def test_generate_tests_not_found():
    fs = MockFileSystem({
        "test.kt": "package com.example\n"
    })
    
    use_case = GenerateTestsUseCase(fs, MockParser(), MockStrategyProvider())
    result = use_case.execute("test.kt", "Missing", "json")
    
    assert result is None

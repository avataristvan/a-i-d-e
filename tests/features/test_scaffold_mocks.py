import pytest
import json
from aide.features.test_generation.application.scaffold_mocks import ScaffoldMocksUseCase

class MockFileSystem:
    def __init__(self, contents): self.contents = contents
    def read_file(self, path): return self.contents[path]

class MockParser:
    pass

class MockStrategy:
    def find_symbol_range(self, lines, symbol):
        if symbol == "MyService":
            return 1, 4 # entire file
        return None, None

class MockStrategyProvider:
    def get_strategy(self, path): return MockStrategy()

def test_scaffold_mocks_python():
    fs = MockFileSystem({
        "service.py": "class MyService:\n    def __init__(self, file_system: FileSystem, parser):\n        pass\n"
    })
    
    use_case = ScaffoldMocksUseCase(fs, MockParser(), MockStrategyProvider())
    result = use_case.execute("service.py", "MyService", "json")
    
    assert result is not None
    data = json.loads(result)
    assert data["target_class"] == "MyService"
    assert data["dependencies_found"] == 2
    
    mocks = data["mock_classes"]
    assert "class MockFileSystem:\n    def __init__(self):\n        pass\n" in mocks
    # Untyped parameter 'parser' defaults to MockParser (title cased param name)
    assert "class MockParser:\n    def __init__(self):\n        pass\n" in mocks

def test_scaffold_mocks_kotlin():
    fs = MockFileSystem({
        "service.kt": "class MyService(val fileSystem: FileSystem, parser: Parser) {\n}\n"
    })
    
    use_case = ScaffoldMocksUseCase(fs, MockParser(), MockStrategyProvider())
    result = use_case.execute("service.kt", "MyService", "json")
    
    assert result is not None
    data = json.loads(result)
    assert data["target_class"] == "MyService"
    assert data["dependencies_found"] == 2
    
    mocks = data["mock_classes"]
    assert "class MockFileSystem : FileSystem {\n}\n" in mocks
    assert "class MockParser : Parser {\n}\n" in mocks

def test_scaffold_mocks_markdown():
    fs = MockFileSystem({
        "service.py": "class MyService:\n    def __init__(self, fs: FileSystem):\n        pass\n"
    })
    
    use_case = ScaffoldMocksUseCase(fs, MockParser(), MockStrategyProvider())
    result = use_case.execute("service.py", "MyService", "markdown")
    
    assert result is not None
    assert "# Mocks for `MyService`" in result
    assert "class MockFileSystem:" in result

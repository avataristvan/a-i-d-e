import pytest
from aide.features.code_generation.application.implement_interface import ImplementInterfaceUseCase

class MockFileSystem:
    def __init__(self, contents): self.contents = contents
    def read_file(self, path): return self.contents[path]
    def write_file(self, path, content): self.contents[path] = content

class MockParser: pass

class MockStrategy:
    def find_symbol_range(self, lines, symbol):
        # Extremely simplified mocking for line ranges
        if symbol == "IRepository":
            return 1, 4 # Lines 1 to 4
        elif symbol == "MyRepo":
            return 5, 6 # Lines 5 to 6
        return None, None

class MockStrategyProvider:
    def get_strategy(self, path): return MockStrategy()


def test_implement_interface_python():
    initial = (
        "class IRepository:\n"
        "    def save(self, entity: str) -> bool:\n"
        "        pass\n"
        "\n"
        "class MyRepo:\n"
        "    def other(self): pass\n"
    )
    
    fs = MockFileSystem({"test.py": initial})
    use_case = ImplementInterfaceUseCase(fs, MockParser(), MockStrategyProvider())
    
    success = use_case.execute("test.py", "MyRepo", "IRepository")
    
    assert success is True
    assert "def save(self, entity: str) -> bool:" in fs.contents["test.py"]
    assert "    pass" in fs.contents["test.py"]


def test_implement_interface_kotlin():
    initial = (
        "interface IRepository {\n"
        "    fun save(entity: String): Boolean\n"
        "}\n"
        "\n"
        "class MyRepo : IRepository {\n"
        "}\n"
    )
    
    fs = MockFileSystem({"test.kt": initial})
    use_case = ImplementInterfaceUseCase(fs, MockParser(), MockStrategyProvider())
    
    success = use_case.execute("test.kt", "MyRepo", "IRepository")
    
    assert success is True
    assert "fun save(entity: String): Boolean {" in fs.contents["test.kt"]
    assert "TODO(\"Not yet implemented\")" in fs.contents["test.kt"]
    assert fs.contents["test.kt"].endswith("}\n")

def test_implement_interface_missing():
    initial = "class Empty:\n    pass\n"
    fs = MockFileSystem({"test.py": initial})
    use_case = ImplementInterfaceUseCase(fs, MockParser(), MockStrategyProvider())
    
    # Should fail because interface doesn't exist in ranges
    success = use_case.execute("test.py", "MyRepo", "IRepository")
    assert success is False

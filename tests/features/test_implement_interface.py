import pytest
import os
from aide.features.code_generation.application.implement_interface import ImplementInterfaceUseCase

class MockFileSystem:
    def __init__(self, contents): self.contents = contents
    def read_file(self, path): return self.contents[path]
    def write_file(self, path, content): self.contents[path] = content
    def path_exists(self, path): return path in self.contents

class MockLlmProvider:
    def __init__(self, response): self.response = response
    def generate(self, system, user): return self.response

class MockBriefingService:
    def get_persona_rules(self): return "Rules"
    def get_dependency_context(self, path=None): return "Deps"

class MockStrategy:
    def find_symbol_range(self, lines, symbol):
        # Simple detection based on the test data
        for i, line in enumerate(lines):
             if symbol in line:
                 if "{" in line:
                     # multi-line block
                     for j in range(i, len(lines)):
                         if "}" in lines[j]:
                             return i + 1, j + 1
                 return i + 1, i + 1
        return None, None

class MockStrategyProvider:
    def get_strategy(self, path): return MockStrategy()

def test_implement_interface_python():
    initial = (
        "class IAuth:\n    def login(self): pass\n\n"
        "class AuthImpl(IAuth):\n    pass\n"
    )
    expected_injection = "    def login(self): return True"
    
    fs = MockFileSystem({"auth.py": initial})
    llm = MockLlmProvider(expected_injection)
    briefing = MockBriefingService()
    
    use_case = ImplementInterfaceUseCase(fs, MockStrategyProvider(), llm, briefing)
    success = use_case.execute("auth.py", "AuthImpl", "IAuth")
    
    assert success is True
    assert "def login(self): return True" in fs.contents["auth.py"]

def test_implement_interface_kotlin():
    initial = (
        "interface IAuth { fun login(): Boolean }\n\n"
        "class AuthImpl : IAuth {\n}\n"
    )
    expected_injection = "    override fun login() = true"
    
    fs = MockFileSystem({"auth.kt": initial})
    llm = MockLlmProvider(expected_injection)
    briefing = MockBriefingService()
    
    use_case = ImplementInterfaceUseCase(fs, MockStrategyProvider(), llm, briefing)
    success = use_case.execute("auth.kt", "AuthImpl", "IAuth")
    
    assert success is True
    assert "override fun login() = true" in fs.contents["auth.kt"]

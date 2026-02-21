import pytest
from aide.features.code_generation.application.register_dependency import RegisterDependencyUseCase

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

def test_register_dependency_kotlin():
    initial = "package com.example\n\nval module = module {\n}\n"
    # Mock LLM returns the whole file as instructed in the UseCase
    expected = "package com.example\n\nimport com.example.Service\n\nval module = module {\n    single { Service() }\n}\n"
    
    fs = MockFileSystem({"temp.kt": initial})
    llm = MockLlmProvider(expected)
    briefing = MockBriefingService()
    
    use_case = RegisterDependencyUseCase(fs, None, llm, briefing)
    success = use_case.execute("temp.kt", "com.example.Service", "single { Service() }")
    
    assert success is True
    assert "import com.example.Service" in fs.contents["temp.kt"]
    assert "single { Service() }" in fs.contents["temp.kt"]

def test_register_dependency_python():
    initial = "di = DI()\n"
    expected = "import Service\ndi = DI()\ndi.register(Service)\n"
    
    fs = MockFileSystem({"temp.py": initial})
    llm = MockLlmProvider(expected)
    briefing = MockBriefingService()
    
    use_case = RegisterDependencyUseCase(fs, None, llm, briefing)
    success = use_case.execute("temp.py", "import Service", "di.register(Service)")
    
    assert success is True
    assert "import Service" in fs.contents["temp.py"]
    assert "di.register(Service)" in fs.contents["temp.py"]

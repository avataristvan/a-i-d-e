import pytest
from aide.features.code_generation.application.register_dependency import RegisterDependencyUseCase

class MockFileSystem:
    def __init__(self, contents): self.contents = contents
    def read_file(self, path): return self.contents[path]
    def write_file(self, path, content): self.contents[path] = content

class MockParser: pass
class MockStrategyProvider: pass

def test_register_dependency_kotlin():
    initial = (
        "package com.example.di\n"
        "\n"
        "import org.koin.dsl.module\n"
        "import com.example.ExistingService\n"
        "\n"
        "val appModule = module {\n"
        "    single<ExistingService> { ExistingServiceImpl() }\n"
        "}\n"
    )
    
    fs = MockFileSystem({"temp.kt": initial})
    use_case = RegisterDependencyUseCase(fs, MockParser(), MockStrategyProvider())
    
    success = use_case.execute("temp.kt", "com.example.NewService", "single<NewService> { NewServiceImpl() }")
    
    assert success is True
    content = fs.contents["temp.kt"]
    assert "import com.example.NewService" in content
    # Ensure it's inside the module block (before the last brace)
    assert "    single<NewService> { NewServiceImpl() }" in content
    assert content.endswith("}\n")

def test_register_dependency_python():
    initial = (
        "from container import DI\n"
        "from services import OldService\n"
        "\n"
        "di = DI()\n"
        "di.register(OldService)\n"
    )
    
    fs = MockFileSystem({"temp.py": initial})
    use_case = RegisterDependencyUseCase(fs, MockParser(), MockStrategyProvider())
    
    success = use_case.execute("temp.py", "from services import NewService", "di.register(NewService)")
    
    assert success is True
    content = fs.contents["temp.py"]
    assert "from services import NewService" in content
    assert "di.register(NewService)" in content

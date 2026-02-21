import pytest
import os
from aide.features.code_generation.application.project_dto import ProjectDtoUseCase
from aide.core.domain.ports import LlmProvider, FileSystemPort

class MockFileSystem(FileSystemPort):
    def __init__(self, contents): 
        self.contents = contents
        self.jailed_root = os.getcwd() # Dummy
        self._in_transaction = False
    def read_file(self, path): return self.contents[path]
    def write_file(self, path, content): self.contents[path] = content
    def path_exists(self, path): return path in self.contents
    def walk_files(self, root_path): yield from self.contents.keys()
    def delete_path(self, path): del self.contents[path]
    def move_path(self, src, dst): self.contents[dst] = self.contents.pop(src)
    def start_transaction(self): pass
    def commit(self): pass
    def rollback(self): pass

class MockLlmProvider(LlmProvider):
    def __init__(self, response): self.response = response
    def generate(self, system, user): return self.response

class MockBriefingService:
    def get_persona_rules(self): return "Rules"
    def get_dependency_context(self, path=None): return "Deps"

class MockStrategy:
    def find_symbol_range(self, lines, symbol):
        return 1, len(lines)
class MockStrategyProvider:
    def get_strategy(self, path): return MockStrategy()

def test_project_dto_kotlin():
    initial = (
        "data class UserEntity(\n"
        "    val id: String,\n"
        "    var email: String?,\n"
        "    val isActive: Boolean\n"
        ")\n"
    )
    # Mock LLM output that matches the old hardcoded template for minimal test changes
    expected_output = (
        "data class UserDTO(\n"
        "    val id: String,\n"
        "    val email: String?,\n"
        "    val isActive: Boolean\n"
        ")\n\n"
        "fun UserEntity.toUserDTO() = UserDTO(\n"
        "    id = this.id,\n"
        "    email = this.email,\n"
        "    isActive = this.isActive\n"
        ")\n"
    )
    
    fs = MockFileSystem({"entity.kt": initial})
    llm = MockLlmProvider(expected_output)
    briefing = MockBriefingService()
    
    use_case = ProjectDtoUseCase(fs, MockStrategyProvider(), llm, briefing)
    
    success = use_case.execute("entity.kt", "UserEntity", "dto.kt", "UserDTO", "kotlin")
    
    assert success is True
    content = fs.contents["dto.kt"]
    assert "data class UserDTO(" in content
    assert "val id: String," in content
    assert "fun UserEntity.toUserDTO() = UserDTO(" in content

def test_project_dto_python():
    initial = (
        "@dataclass\n"
        "class UserEntity:\n"
        "    id: str\n"
        "    email: Optional[str]\n"
        "    is_active: bool\n"
    )
    expected_output = (
        "class UserDTO:\n"
        "    id: str\n"
        "    email: Optional[str]\n"
        "    is_active: bool\n\n"
        "    def from_entity(cls, entity):\n"
        "        return cls(\n"
        "            id=entity.id,\n"
        "            email=entity.email,\n"
        "            is_active=entity.is_active\n"
        "        )\n"
    )
    
    fs = MockFileSystem({"entity.py": initial})
    llm = MockLlmProvider(expected_output)
    briefing = MockBriefingService()
    
    use_case = ProjectDtoUseCase(fs, MockStrategyProvider(), llm, briefing)
    
    success = use_case.execute("entity.py", "UserEntity", "dto.py", "UserDTO", "python")
    
    assert success is True
    content = fs.contents["dto.py"]
    assert "class UserDTO:" in content
    assert "    id: str" in content
    assert "def from_entity(cls, entity):" in content

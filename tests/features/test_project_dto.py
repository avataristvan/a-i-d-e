import pytest
from aide.features.code_generation.application.project_dto import ProjectDtoUseCase

class MockFileSystem:
    def __init__(self, contents): self.contents = contents
    def read_file(self, path): return self.contents[path]
    def write_file(self, path, content): self.contents[path] = content

class MockParser: pass
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
    
    fs = MockFileSystem({"entity.kt": initial})
    use_case = ProjectDtoUseCase(fs, MockParser(), MockStrategyProvider())
    
    success = use_case.execute("entity.kt", "UserEntity", "dto.kt", "UserDTO", "kotlin")
    
    assert success is True
    content = fs.contents["dto.kt"]
    assert "data class UserDTO(" in content
    assert "val id: String," in content
    assert "val email: String?," in content
    assert "val isActive: Boolean" in content
    assert "fun UserEntity.toUserDTO() = UserDTO(" in content
    assert "id = this.id," in content

def test_project_dto_python():
    initial = (
        "@dataclass\n"
        "class UserEntity:\n"
        "    id: str\n"
        "    email: Optional[str]\n"
        "    is_active: bool\n"
    )
    
    fs = MockFileSystem({"entity.py": initial})
    use_case = ProjectDtoUseCase(fs, MockParser(), MockStrategyProvider())
    
    success = use_case.execute("entity.py", "UserEntity", "dto.py", "UserDTO", "python")
    
    assert success is True
    content = fs.contents["dto.py"]
    assert "class UserDTO:" in content
    assert "    id: str" in content
    assert "    email: Optional[str]" in content
    assert "    is_active: bool" in content
    assert "def from_entity(cls, entity):" in content
    assert "id=entity.id," in content

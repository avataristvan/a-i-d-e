import pytest
from aide.features.code_generation.application.scaffold_feature import ScaffoldFeatureUseCase

class MockFileSystem:
    def __init__(self, contents=None): self.contents = contents or {}
    def write_file(self, path, content): self.contents[path] = content
    def path_exists(self, path): return path in self.contents
    def read_file(self, path): return self.contents[path]

class MockLlmProvider:
    def __init__(self, response): self.response = response
    def generate(self, system, user): return self.response

class MockBriefingService:
    def get_persona_rules(self): return "Rules"
    def get_dependency_context(self, path=None): return "Deps"

def test_scaffold_feature_python():
    fs = MockFileSystem()
    llm = MockLlmProvider('{"domain/entity.py": "class Entity: pass"}')
    briefing = MockBriefingService()
    
    use_case = ScaffoldFeatureUseCase(fs, llm, briefing)
    success = use_case.execute("Auth", "python", "./src")
    
    assert success is True
    # The output path is constructed using os.path.join(output_dir, feature_slug, rel_path)
    assert "./src/auth/domain/entity.py" in fs.contents

def test_scaffold_feature_kotlin():
    fs = MockFileSystem()
    llm = MockLlmProvider('{"domain/Entity.kt": "class Entity"}')
    briefing = MockBriefingService()
    
    use_case = ScaffoldFeatureUseCase(fs, llm, briefing)
    success = use_case.execute("Auth", "kotlin", "./src")
    
    assert success is True
    assert "./src/auth/domain/Entity.kt" in fs.contents

import pytest
import os
from aide.features.code_generation.application.scaffold_feature import ScaffoldFeatureUseCase

class MockFileSystem:
    def __init__(self):
        self.files = {}
        
    def write_file(self, path, content):
        self.files[path] = content

def test_scaffold_feature_python():
    fs = MockFileSystem()
    use_case = ScaffoldFeatureUseCase(fs)
    
    success = use_case.execute("UserProfile", "python", "/fake/src")
    
    assert success is True
    assert "/fake/src/userprofile/domain/__init__.py" in fs.files
    assert "/fake/src/userprofile/application/__init__.py" in fs.files
    assert "/fake/src/userprofile/infrastructure/__init__.py" in fs.files
    
    assert "class UserprofileEntity:" in fs.files["/fake/src/userprofile/domain/entity.py"]
    assert "class GetUserprofileUseCase:" in fs.files["/fake/src/userprofile/application/use_cases.py"]
    assert "class UserprofileRepositoryImpl:" in fs.files["/fake/src/userprofile/infrastructure/repository.py"]

def test_scaffold_feature_kotlin():
    fs = MockFileSystem()
    use_case = ScaffoldFeatureUseCase(fs)
    
    success = use_case.execute("user-profile", "kotlin", "/fake/src")
    
    assert success is True
    
    domain_file = "/fake/src/user_profile/domain/UserProfileEntity.kt"
    assert domain_file in fs.files
    assert "data class UserProfileEntity" in fs.files[domain_file]
    
    app_file = "/fake/src/user_profile/application/GetUserProfileUseCase.kt"
    assert app_file in fs.files
    assert "class GetUserProfileUseCase" in fs.files[app_file]
    
    infra_file = "/fake/src/user_profile/infrastructure/UserProfileRepositoryImpl.kt"
    assert infra_file in fs.files
    assert "class UserProfileRepositoryImpl" in fs.files[infra_file]

def test_scaffold_feature_generic_fallback():
    fs = MockFileSystem()
    use_case = ScaffoldFeatureUseCase(fs)
    
    success = use_case.execute("UserProfile", "ruby", "/fake/src")
    
    assert success is True
    assert len(fs.files) > 0
    assert "/fake/src/userprofile/domain/UserprofileEntity.rb" in fs.files

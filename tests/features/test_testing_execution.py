import pytest
from aide.features.testing_execution.application.audit_fixtures import AuditFixturesUseCase
from aide.features.testing_execution.application.execute_tests import ExecuteTestsUseCase
from aide.features.testing_execution.application.test_audit import TestAuditUseCase
import json
import os

class MockFileSystem:
    def __init__(self, contents): self.contents = contents
    def read_file(self, path): return self.contents.get(path, "")

def test_audit_fixtures_unused():
    # A fake file system holding a pytest file
    content = (
        "import pytest\n"
        "@pytest.fixture\n"
        "def used_fixture(): return 1\n"
        "\n"
        "@pytest.fixture\n"
        "def unused_fixture(): return 2\n"
        "\n"
        "def test_app(used_fixture):\n"
        "    assert True\n"
    )
    
    fs = MockFileSystem({"/fake/test_mock.py": content})
    # We patch os.walk to return our mock file
    original_walk = os.walk
    def mock_walk(path):
        yield "/fake", [], ["test_mock.py"]
    os.walk = mock_walk
    
    try:
        use_case = AuditFixturesUseCase(fs)
        result = use_case.execute("/fake", format="text")
        
        assert result["total_fixtures"] == 2
        assert len(result["unused_fixtures"]) == 1
        assert result["unused_fixtures"][0]["name"] == "unused_fixture"
    finally:
        os.walk = original_walk

def test_execute_tests():
    use_case = ExecuteTestsUseCase()
    # It will run pytest on a fake nonexistent path
    result = use_case.execute("/run/this/is/fake/path", format="text")
    # Result should say success = False or returncode 4 (no tests collected) or 5 (no tests collected)
    # Pytest usually gives 4 if it's an error in args, or 5 if no tests collected
    assert result["success"] is False

def test_test_audit():
    use_case = TestAuditUseCase()
    # Path that doesn't exist
    result = use_case.execute("/fake/src", "/fake/tests", format="text")
    assert result["success"] is False

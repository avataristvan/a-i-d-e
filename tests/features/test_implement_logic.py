import os
import pytest
import json
from aide.core.domain.ports import LlmProvider
from aide.core.context import Context
from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.parsing.infrastructure.parsers import RegexLanguageParser, CompositeLanguageParser
from aide.parsing.infrastructure.ast_parsers import AstPythonParser
from aide.core.infrastructure.briefing_service import BriefingService
from aide.features.implementation.application.implement_logic import ImplementLogicUseCase

class MockLlmProvider(LlmProvider):
    def __init__(self, expected_response: str):
        self.expected_response = expected_response
        self.call_count = 0
        self.last_system_prompt = ""
        self.last_user_prompt = ""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return self.expected_response


@pytest.fixture
def test_env(tmp_path):
    # Setup Context
    file_system = OsFileSystem(jailed_root=str(tmp_path))
    
    fallback_parser = RegexLanguageParser()
    composite_parser = CompositeLanguageParser(fallback_parser)
    composite_parser.register(".py", AstPythonParser())
    
    # We'll use a Mock LLM
    mock_llm = MockLlmProvider("    def method(self):\n        return a + b")

    # Setup Briefing Service
    briefing_service = BriefingService(file_system, composite_parser)
    
    context = Context(file_system=file_system, language_parser=composite_parser, llm_provider=mock_llm, briefing_service=briefing_service)
    
    return context, mock_llm, str(tmp_path)


def test_implement_logic_python_basic(test_env):
    context, mock_llm, tmp_dir = test_env
    
    # Setup dummy file
    file_path = os.path.join(tmp_dir, "math_utils.py")
    original_code = '''
class MathUtils:
    def add(self, a: int, b: int) -> int:
        pass

    def sub(self, a: int, b: int) -> int:
        return a - b
'''
    context.file_system.write_file(file_path, original_code.strip())
    
    # Execute Use Case
    use_case = ImplementLogicUseCase(
        file_system=context.file_system,
        language_parser=context.language_parser,
        strategy_provider=context.strategy_provider,
        llm_provider=mock_llm,
        briefing_service=context.briefing_service
    )
    
    # Mock LLM returns the full block
    mock_llm.expected_response = "    def add(self, a: int, b: int) -> int:\n        return a + b"

    success, message = use_case.execute(file_path, "add", "Return the sum of a and b")
    
    assert success is True
    assert mock_llm.call_count == 1
    
    # Verify Content
    new_content = context.file_system.read_file(file_path)
    
    # The output should have replaced `pass` with `return a + b` at the correct indentation level.
    expected_code = '''
class MathUtils:
    def add(self, a: int, b: int) -> int:
        return a + b

    def sub(self, a: int, b: int) -> int:
        return a - b
'''
    assert new_content.strip() == expected_code.strip()


def test_implement_logic_forces_indentation(test_env):
    context, mock_llm, tmp_dir = test_env
    
    # Mock LLM returns poorly indented code (stripped of base indent)
    mock_llm.expected_response = "def calculate(a, b):\n    return a + b"
    
    file_path = os.path.join(tmp_dir, "math_utils2.py")
    original_code = '''
def calculate(a, b):
    # we need to do math
    pass
'''
    context.file_system.write_file(file_path, original_code.strip())
    
    use_case = ImplementLogicUseCase(
        file_system=context.file_system,
        language_parser=context.language_parser,
        strategy_provider=context.strategy_provider,
        llm_provider=mock_llm,
        briefing_service=context.briefing_service
    )
    
    success, _ = use_case.execute(file_path, "calculate", "do it")
    
    assert success is True
    
    new_content = context.file_system.read_file(file_path)
    expected_code = '''
def calculate(a, b):
    return a + b
'''
    assert new_content.strip() == expected_code.strip()


def test_implement_logic_dry_run(test_env):
    context, mock_llm, tmp_dir = test_env
    file_path = os.path.join(tmp_dir, "dry.py")
    original_code = "def foo():\n    pass\n"
    context.file_system.write_file(file_path, original_code)
    
    use_case = ImplementLogicUseCase(context.file_system, context.language_parser, context.strategy_provider, mock_llm, context.briefing_service)
    
    success, message = use_case.execute(file_path, "foo", "do it", dry_run=True)
    
    assert success is True
    # Verify file was NOT modified
    assert context.file_system.read_file(file_path) == original_code

from aide.core.infrastructure.llm_provider import HttpGeminiLlmProvider
import urllib.request
import io

def test_gemini_provider_payload(monkeypatch):
    """Verifies that the Gemini provider constructs the correct Google AI JSON payload."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    provider = HttpGeminiLlmProvider()
    
    mock_response = json.dumps({
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "return True"}]
                }
            }
        ]
    }).encode("utf-8")

    class MockResponse:
        def read(self): return mock_response
        def __enter__(self): return self
        def __exit__(self, *args): pass

    def mock_urlopen(req, timeout=None):
        # Verify URL has the key
        assert "key=test-key" in req.full_url
        # Verify JSON payload
        data = json.loads(req.data.decode("utf-8"))
        assert "contents" in data
        assert data["contents"][0]["parts"][0]["text"].startswith("System Instruction:")
        return MockResponse()

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
    
    response = provider.generate("system", "user")
    assert response == "return True"

from aide.core.infrastructure.llm_provider import ShellLlmProvider

def test_shell_provider_execution(monkeypatch):
    """Verifies that the Shell provider correctly executes a command and captures output."""
    # Use 'cat' as a mock LLM that just echoes the prompt
    monkeypatch.setenv("AIDE_LLM_COMMAND", "cat")
    provider = ShellLlmProvider()
    
    system = "Instructions"
    user = "Request"
    response = provider.generate(system, user)
    
    assert response == f"{system}\n\n{user}"

def test_shell_provider_failure(monkeypatch):
    """Verifies that the Shell provider handles command failures gracefully."""
    monkeypatch.setenv("AIDE_LLM_COMMAND", "false")
    provider = ShellLlmProvider()
    
    with pytest.raises(Exception) as excinfo:
        provider.generate("s", "u")
    assert "Command failed with exit code 1" in str(excinfo.value)


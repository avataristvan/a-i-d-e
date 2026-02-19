import pytest
from aide.features.code_inspection.application.outline import OutlineUseCase
from aide.parsing.infrastructure.parsers import RegexLanguageParser

class MockFileSystem:
    def __init__(self, files):
        self.files = files
    
    def walk_files(self, root):
        for path in self.files:
            yield path
            
    def read_file(self, path):
        return self.files[path]

def test_outline_use_case():
    files = {
        "src/app.py": "class App:\n    def run(self):\n        pass\n",
        "src/utils.ts": "export function helper() {}\n"
    }
    fs = MockFileSystem(files)
    parser = RegexLanguageParser()
    
    use_case = OutlineUseCase(fs, parser)
    
    output_py = use_case.execute("*.py")
    assert "## File: src/app.py" in output_py
    assert "- [C] App (L1)" in output_py
    assert "- [f] run (L2)" in output_py
    assert "utils.ts" not in output_py
    
    output_ts = use_case.execute("*.ts")
    assert "## File: src/utils.ts" in output_ts
    assert "- [f] helper (L1)" in output_ts

def test_outline_no_match():
    fs = MockFileSystem({"src/app.py": ""})
    parser = RegexLanguageParser()
    use_case = OutlineUseCase(fs, parser)
    
    output = use_case.execute("*.kt")
    assert "No files found" in output

import pytest
import os
from aide.features.code_cleanup.plugin import CleanupPlugin
from aide.core.context import Context

class MockFileSystem:
    def __init__(self, contents): self.contents = contents
    def read_file(self, path): return self.contents[path]
    def write_file(self, path, content): self.contents[path] = content
    def walk_files(self, root): return self.contents.keys()

def test_cleanup():
    fs = MockFileSystem({
        "test.kt": "import Foo\nimport Bar\nclass Main { val b = Bar() }\n",
        "dup.py": "import os\nimport os\n"
    })
    
    context = Context(file_system=fs, language_parser=None, strategy_provider=None)
    plugin = CleanupPlugin()
    
    # Test remove unused
    plugin.remove_unused_imports(".", context)
    assert "import Foo" not in fs.read_file("test.kt")
    assert "import Bar" in fs.read_file("test.kt")
    
    # Test remove duplicates
    plugin.remove_duplicate_imports(".", context)
    assert fs.read_file("dup.py").count("import os") == 1

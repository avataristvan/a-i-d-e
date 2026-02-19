import pytest
import os
from aide.features.code_inspection.application.find_usages import FindUsagesUseCase

class MockFileSystem:
    def __init__(self, contents):
        self.contents = contents
        
    def read_file(self, path):
        if path in self.contents:
            return self.contents[path]
        raise FileNotFoundError(path)

def test_find_usages(temp_dir):
    fs = MockFileSystem({
        os.path.join(temp_dir, "app.py"): "def helper(): pass\nhelper()\n# helper()\n",
        os.path.join(temp_dir, "utils.kt"): "import helper\nval x = helper()\n"
    })
    
    # We need real files to walk through
    os.makedirs(os.path.join(temp_dir, "src"))
    app_py = os.path.join(temp_dir, "app.py")
    utils_kt = os.path.join(temp_dir, "utils.kt")
    with open(app_py, "w") as f: f.write(fs.contents[app_py])
    with open(utils_kt, "w") as f: f.write(fs.contents[utils_kt])

    use_case = FindUsagesUseCase(fs, None)
    usages = use_case.execute(temp_dir, "helper")
    
    assert len(usages) == 3
    
    app_py_rel = os.path.relpath(app_py, temp_dir)
    utils_kt_rel = os.path.relpath(utils_kt, temp_dir)
    
    assert any(app_py_rel in u and ":1:5" in u for u in usages)
    assert any(app_py_rel in u and ":2:1" in u for u in usages)
    assert any(utils_kt_rel in u and ":2:9" in u for u in usages)
    # The comment (# helper()) and import (import helper) should be ignored

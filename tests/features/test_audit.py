import pytest
import os
from argparse import Namespace
from aide.features.architecture_audit.plugin import ArchitectureAuditPlugin
from aide.core.context import Context
from aide.parsing.domain.models import SymbolNode
from aide.core.infrastructure.os_file_system import OsFileSystem

class MockParser:
    def parse_imports(self, content, ext):
        if "Bad" in content:
            return ["com.infrastructure.Bad"]
        return []

def test_audit_kotlin(temp_dir):
    # Set up some test files
    os.makedirs(os.path.join(temp_dir, "app", "domain"))
    good_file = os.path.join(temp_dir, "app", "domain", "Good.kt")
    bad_file = os.path.join(temp_dir, "app", "domain", "Bad.kt")
    
    with open(good_file, "w", encoding="utf-8") as f:
        f.write("package domain\nclass Good {}\n")
        
    with open(bad_file, "w", encoding="utf-8") as f:
        f.write("package domain\nimport com.infrastructure.Bad\nclass Bad {}\n")
        
    fs = OsFileSystem(jailed_root=temp_dir)
    context = Context(file_system=fs, language_parser=MockParser(), strategy_provider=None)
    plugin = ArchitectureAuditPlugin()
    
    args = Namespace(stack="kotlin", src=temp_dir)
    
    # We capture stdout to see the violations
    import io
    import sys
    captured_output = io.StringIO()
    sys.stdout = captured_output
    
    plugin.run_audit(args, context)
    
    sys.stdout = sys.__stdout__
    output = captured_output.getvalue()
    
    assert "Found 1 Violations:" in output
    assert "Domain cannot import Infrastructure" in output
    assert "Good.kt" not in output

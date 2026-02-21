import os
import pytest
from argparse import Namespace
from aide.core.context import Context
from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.parsing.infrastructure.parsers import RegexLanguageParser
from aide.features.code_inspection.plugin import CodeInspectionPlugin
from aide.features.code_inspection.application.find_impact import FindImpactUseCase
from aide.core.infrastructure.strategy_provider import StrategyProvider

@pytest.fixture
def test_context(temp_dir):
    fs = OsFileSystem(jailed_root=temp_dir)
    parser = RegexLanguageParser()
    strategy_provider = StrategyProvider()
    return Context(file_system=fs, language_parser=parser, strategy_provider=strategy_provider)

def test_find_impact_python(temp_dir, test_context, capsys):
    # Setup files: class C in dir_c, class B in dir_b uses C, class A in dir_a uses B
    # Also test_c uses C
    
    os.makedirs(os.path.join(temp_dir, "dir_c"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "dir_b"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "dir_a"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "tests"), exist_ok=True)

    file_c = os.path.join(temp_dir, "dir_c", "c.py")
    test_context.file_system.write_file(file_c, "class ClassC:\n    def do_c(self):\n        pass\n")

    file_b = os.path.join(temp_dir, "dir_b", "b.py")
    test_context.file_system.write_file(file_b, "from dir_c.c import ClassC\nclass ClassB:\n    def do_b(self):\n        c = ClassC()\n")

    file_a = os.path.join(temp_dir, "dir_a", "a.py")
    test_context.file_system.write_file(file_a, "from dir_b.b import ClassB\nclass ClassA:\n    def do_a(self):\n        b = ClassB()\n")
    
    test_file_c = os.path.join(temp_dir, "tests", "test_c.py")
    test_context.file_system.write_file(test_file_c, "from dir_c.c import ClassC\ndef test_class_c():\n    assert ClassC() is not None\n")
    
    # False positive file (contains string but doesn't import)
    false_positive = os.path.join(temp_dir, "dir_a", "false.py")
    test_context.file_system.write_file(false_positive, "def foo():\n    # ClassC is great\n    pass\n")

    use_case = FindImpactUseCase(test_context.file_system, test_context.language_parser, test_context.strategy_provider)
    
    # We change directory to temp_dir so FindUsagesUseCase uses it as '.'
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        result = use_case.execute("ClassC", source_file=os.path.abspath(file_c))
        
        impacted_files = result['impacted_files']
        impacted_tests = result['impacted_tests']
        
        # dir_b/b.py uses ClassC. dir_a/a.py uses ClassB, not ClassC directly.
        assert len(impacted_files) == 1
        assert "dir_b/b.py" in impacted_files[0]
        
        assert len(impacted_tests) == 1
        assert "tests/test_c.py" in impacted_tests[0]
        
    finally:
        os.chdir(old_cwd)

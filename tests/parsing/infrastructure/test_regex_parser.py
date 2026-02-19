import pytest
from aide.parsing.infrastructure.parsers import RegexLanguageParser

def test_parse_python():
    parser = RegexLanguageParser()
    content = '''
class MyClass:
    def my_method(self):
        pass

def top_level_func():
    pass
'''
    nodes = parser.parse(content, ".py")
    assert len(nodes) == 3
    assert nodes[0].name == "MyClass"
    assert nodes[0].kind == "class"
    assert nodes[0].line_number == 2
    assert nodes[1].name == "my_method"
    assert nodes[1].kind == "function"
    assert nodes[1].line_number == 3
    assert nodes[2].name == "top_level_func"
    assert nodes[2].kind == "function"
    assert nodes[2].line_number == 6

def test_parse_ts():
    parser = RegexLanguageParser()
    content = '''
export class UserService {}
export interface User {}
export const MyComponent = () => {}
function helper() {}
'''
    nodes = parser.parse(content, ".ts")
    assert len(nodes) == 4
    assert nodes[0].name == "UserService"
    assert nodes[0].kind == "class"
    assert nodes[1].name == "User"
    assert nodes[1].kind == "interface"
    assert nodes[2].name == "MyComponent"
    assert nodes[2].kind == "component"
    assert nodes[3].name == "helper"
    assert nodes[3].kind == "function"

def test_parse_imports_python():
    parser = RegexLanguageParser()
    content = '''
import os
from sys import argv
'''
    imports = parser.parse_imports(content, ".py")
    assert "os" in imports
    assert "sys" in imports

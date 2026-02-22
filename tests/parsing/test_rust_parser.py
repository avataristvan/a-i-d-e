import pytest
from aide.parsing.domain.models import SymbolNode
from aide.parsing.infrastructure.rust_parser import RustLanguageParser

def test_rust_ast_parsing():
    parser = RustLanguageParser()
    content = """
    pub struct User {
        id: i32,
    }

    pub trait Repository {
        fn save(&self, user: &User);
    }

    impl Repository for Database {
        fn save(&self, user: &User) {
        }
    }

    pub enum Result {
        Ok,
        Err
    }
    
    pub fn main_process() {}
    """
    
    nodes = parser.parse(content, ".rs")
    
    # Verify Struct
    struct_node = next((n for n in nodes if n.name == "User"), None)
    assert struct_node is not None
    assert struct_node.kind == "struct"
    
    # Verify Trait
    trait_node = next((n for n in nodes if n.name == "Repository"), None)
    assert trait_node is not None
    assert trait_node.kind == "trait"
    
    # Verify Enum
    enum_node = next((n for n in nodes if n.name == "Result"), None)
    assert enum_node is not None
    assert enum_node.kind == "enum"
    
    # Verify Function
    fn_node = next((n for n in nodes if n.name == "main_process"), None)
    assert fn_node is not None
    assert fn_node.kind == "function"

    # Verify Impl blocks pull in functions
    save_node = next((n for n in nodes if n.name == "save"), None)
    assert save_node is not None
    assert save_node.kind == "function"
    
def test_rust_import_parsing():
    parser = RustLanguageParser()
    content = """
    use std::collections::HashMap;
    use crate::domain::User;
    
    pub struct Test {}
    """
    imports = parser.parse_imports(content, ".rs")
    assert len(imports) == 2
    assert "std::collections::HashMap" in imports
    assert "crate::domain::User" in imports

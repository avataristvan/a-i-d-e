import pytest
from aide.parsing.domain.models import SymbolNode
from aide.parsing.infrastructure.csharp_parser import CSharpLanguageParser

def test_csharp_ast_parsing():
    parser = CSharpLanguageParser()
    content = """
    using System;
    using System.Collections.Generic;

    namespace TestApp {
        public class MyService {
            public void DoSomething() {
            }
        }

        public interface IService {
            void DoSomething();
        }

        public enum Status {
            Active,
            Inactive
        }
    }
    """
    
    nodes = parser.parse(content, ".cs")
    
    # Check if nodes were extracted (should be 3 top-level items under namespace)
    # The parser currently flattens namespaces or returns them as children depending on the logic.
    # In our implementation, namespace bodies are flattened to the root list.
    assert len(nodes) == 3
    
    # Verify Class
    class_node = next((n for n in nodes if n.name == "MyService"), None)
    assert class_node is not None
    assert class_node.kind == "class"
    assert len(class_node.children) == 1
    assert class_node.children[0].name == "DoSomething"
    assert class_node.children[0].kind == "function"
    
    # Verify Interface
    interface_node = next((n for n in nodes if n.name == "IService"), None)
    assert interface_node is not None
    assert interface_node.kind == "interface"
    
    # Verify Enum
    enum_node = next((n for n in nodes if n.name == "Status"), None)
    assert enum_node is not None
    assert enum_node.kind == "enum"
    
def test_csharp_import_parsing():
    parser = CSharpLanguageParser()
    content = """
    using System;
    using System.Threading.Tasks;
    
    namespace Test { }
    """
    imports = parser.parse_imports(content, ".cs")
    assert len(imports) == 2
    assert "System" in imports
    assert "System.Threading.Tasks" in imports

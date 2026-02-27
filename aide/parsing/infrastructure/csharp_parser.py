import tree_sitter_c_sharp
from tree_sitter import Language, Parser
from typing import Any, Tuple, Callable, Generator
from aide.parsing.domain.ports import LanguageParserPort
from aide.parsing.domain.models import SymbolNode

class CSharpLanguageParser(LanguageParserPort):
    def __init__(self):
        self.language = Language(tree_sitter_c_sharp.language())
        self.parser = Parser(self.language)

    def parse(self, content: str, file_extension: str) -> list[SymbolNode]:
        tree = self.parser.parse(bytes(content, "utf8"))
        root_node = tree.root_node
        return self._extract_nodes(root_node)

    def _extract_nodes(self, node) -> list[SymbolNode]:
        symbols = []
        for child in node.children:
            match child.type:
                case "class_declaration" | "interface_declaration" | "struct_declaration" | "enum_declaration" | "record_declaration":
                    name_node = child.child_by_field_name("name")
                    if name_node:
                        name = name_node.text.decode("utf8")
                        kind = child.type.replace("_declaration", "")
                        # Extract children (methods, nested classes, etc.)
                        body = child.child_by_field_name("body")
                        children_symbols = []
                        if body:
                            children_symbols = self._extract_nodes(body)
                        
                        symbols.append(
                            SymbolNode(
                                name=name,
                                kind=kind,
                                line_number=child.start_point[0] + 1,
                                children=children_symbols
                            )
                        )
                case "method_declaration":
                    name_node = child.child_by_field_name("name")
                    if name_node:
                        name = name_node.text.decode("utf8")
                        symbols.append(
                            SymbolNode(
                                name=name,
                                kind="function",
                                line_number=child.start_point[0] + 1,
                                children=[]
                            )
                        )
                case "namespace_declaration" | "file_scoped_namespace_declaration":
                    # C# namespaces can contain classes directly
                    body = child.child_by_field_name("body")
                    if body:
                        symbols.extend(self._extract_nodes(body))
                    else: # file_scoped_namespace_declaration doesn't have a distinct body node, children are direct
                        symbols.extend(self._extract_nodes(child))

        return symbols

    def parse_imports(self, content: str, file_extension: str) -> list[str]:
        tree = self.parser.parse(bytes(content, "utf8"))
        root_node = tree.root_node
        imports = []
        
        # Simple tree walk to find using_directive
        cursor = root_node.walk()
        reached_root = False
        while not reached_root:
            node = cursor.node
            if node.type == "using_directive":
                # In C# tree-sitter, using_directive children are: using, identifier/qualified_name, ;
                for child in node.children:
                    if child.type in ["identifier", "qualified_name"]:
                        imports.append(child.text.decode("utf8"))
                        break
            
            if cursor.goto_first_child():
                continue
            if cursor.goto_next_sibling():
                continue
            
            retracing = True
            while retracing:
                if not cursor.goto_parent():
                    retracing = False
                    reached_root = True
                
                if cursor.goto_next_sibling():
                    retracing = False

        return imports

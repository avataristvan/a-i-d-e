import tree_sitter_rust
from tree_sitter import Language, Parser
from typing import List
from aide.parsing.domain.ports import LanguageParserPort
from aide.parsing.domain.models import SymbolNode

class RustLanguageParser(LanguageParserPort):
    def __init__(self):
        self.language = Language(tree_sitter_rust.language())
        self.parser = Parser(self.language)

    def parse(self, content: str, file_extension: str) -> List[SymbolNode]:
        tree = self.parser.parse(bytes(content, "utf8"))
        root_node = tree.root_node
        return self._extract_nodes(root_node)

    def _extract_nodes(self, node) -> List[SymbolNode]:
        symbols = []
        for child in node.children:
            if child.type in ["struct_item", "enum_item", "trait_item", "mod_item"]:
                name_node = child.child_by_field_name("name")
                if name_node:
                    name = name_node.text.decode("utf8")
                    kind = child.type.replace("_item", "")
                    
                    # Extract children
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
            elif child.type == "function_item":
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
            elif child.type == "impl_item": # `impl Trait for Struct { ... }` or `impl Struct { ... }`
                body = child.child_by_field_name("body")
                if body:
                    # We flatten the impl block's functions to the top level for outline simplicity,
                    # or they can be nested under the struct if we matched it.
                    symbols.extend(self._extract_nodes(body))

        return symbols

    def parse_imports(self, content: str, file_extension: str) -> List[str]:
        tree = self.parser.parse(bytes(content, "utf8"))
        root_node = tree.root_node
        imports = []
        
        cursor = root_node.walk()
        reached_root = False
        while not reached_root:
            node = cursor.node
            if node.type == "use_declaration":
                # To simplify we just take the raw string text inside the use statement, minus `use` and `;`
                text = node.text.decode("utf8")
                clean = text.replace("use ", "").replace(";", "").strip()
                if clean:
                    imports.append(clean)
            
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

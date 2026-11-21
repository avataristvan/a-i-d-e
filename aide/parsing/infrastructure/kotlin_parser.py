import tree_sitter_kotlin
from tree_sitter import Language, Parser
from aide.parsing.domain.ports import LanguageParserPort
from aide.parsing.domain.models import SymbolNode


class KotlinLanguageParser(LanguageParserPort):
    def __init__(self):
        self.language = Language(tree_sitter_kotlin.language())
        self.parser = Parser(self.language)

    def parse(self, content: str, file_extension: str) -> list[SymbolNode]:
        tree = self.parser.parse(bytes(content, "utf8"))
        return self._extract_nodes(tree.root_node)

    def _extract_nodes(self, node) -> list[SymbolNode]:
        symbols = []
        for child in node.children:
            match child.type:
                case "class_declaration":
                    name_node = child.child_by_field_name("name")
                    if name_node:
                        kind = self._class_kind(child)
                        body = self._find_child(child, "class_body") or self._find_child(child, "enum_class_body")
                        symbols.append(SymbolNode(
                            name=name_node.text.decode("utf8"),
                            kind=kind,
                            line_number=child.start_point[0] + 1,
                            children=self._extract_nodes(body) if body else [],
                        ))
                case "object_declaration":
                    name_node = child.child_by_field_name("name")
                    if name_node:
                        body = self._find_child(child, "class_body")
                        symbols.append(SymbolNode(
                            name=name_node.text.decode("utf8"),
                            kind="object",
                            line_number=child.start_point[0] + 1,
                            children=self._extract_nodes(body) if body else [],
                        ))
                case "companion_object":
                    body = self._find_child(child, "class_body")
                    symbols.append(SymbolNode(
                        name="Companion",
                        kind="object",
                        line_number=child.start_point[0] + 1,
                        children=self._extract_nodes(body) if body else [],
                    ))
                case "function_declaration":
                    name_node = child.child_by_field_name("name")
                    if name_node:
                        symbols.append(SymbolNode(
                            name=name_node.text.decode("utf8"),
                            kind="function",
                            line_number=child.start_point[0] + 1,
                            children=[],
                        ))
        return symbols

    def _class_kind(self, node) -> str:
        for child in node.children:
            if child.type == "interface":
                return "interface"
            if child.type == "modifiers":
                text = child.text.decode("utf8")
                if "enum" in text:
                    return "enum"
        return "class"

    def _find_child(self, node, child_type: str):
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    def parse_imports(self, content: str, file_extension: str) -> list[str]:
        tree = self.parser.parse(bytes(content, "utf8"))
        imports = []
        for child in tree.root_node.children:
            if child.type == "import":
                qi = self._find_child(child, "qualified_identifier")
                if qi:
                    imports.append(qi.text.decode("utf8"))
        return imports

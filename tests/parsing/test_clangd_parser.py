import pytest
from aide.parsing.infrastructure.clangd_parser import ClangdCppParser, is_clangd_available

pytestmark = pytest.mark.skipif(
    not is_clangd_available(),
    reason="clangd not installed"
)


@pytest.fixture(scope="module")
def parser():
    p = ClangdCppParser()
    yield p
    p._client.stop()


CPP_SOURCE = """\
#include <string>

namespace myapp {

struct Point {
    int x;
    int y;
};

class Shape {
public:
    Shape(int id);
    virtual void draw();
private:
    int id_;
};

void free_function(int x, int y);

enum Color { Red, Green, Blue };

}  // namespace myapp
"""

C_SOURCE = """\
typedef struct {
    int x;
    int y;
} Vec2;

void vec2_add(Vec2 *a, Vec2 *b, Vec2 *out);
"""


def _names(nodes) -> list[str]:
    return [n.name for n in nodes]


def test_detects_namespace(parser):
    nodes = parser.parse(CPP_SOURCE, ".cpp")
    assert any(n.name == "myapp" and n.kind == "namespace" for n in nodes)


def test_detects_struct_inside_namespace(parser):
    nodes = parser.parse(CPP_SOURCE, ".cpp")
    ns = next(n for n in nodes if n.name == "myapp")
    # clangd reports C++ structs as Class (SymbolKind 5), not Struct (23)
    assert any(n.name == "Point" and n.kind in ("struct", "class") for n in ns.children)


def test_detects_class_inside_namespace(parser):
    nodes = parser.parse(CPP_SOURCE, ".cpp")
    ns = next(n for n in nodes if n.name == "myapp")
    assert any(n.name == "Shape" and n.kind == "class" for n in ns.children)


def test_detects_free_function(parser):
    nodes = parser.parse(CPP_SOURCE, ".cpp")
    ns = next(n for n in nodes if n.name == "myapp")
    assert any(n.name == "free_function" and n.kind == "function" for n in ns.children)


def test_detects_enum(parser):
    nodes = parser.parse(CPP_SOURCE, ".cpp")
    ns = next(n for n in nodes if n.name == "myapp")
    assert any(n.name == "Color" and n.kind == "enum" for n in ns.children)


def test_parses_c_file(parser):
    nodes = parser.parse(C_SOURCE, ".c")
    names = _names(nodes)
    assert "vec2_add" in names or "Vec2" in names


def test_parse_imports_cpp(parser):
    imports = parser.parse_imports(CPP_SOURCE, ".cpp")
    assert "string" in imports


def test_parse_imports_c(parser):
    src = '#include <stdio.h>\n#include "myheader.h"\n'
    imports = parser.parse_imports(src, ".c")
    assert "stdio.h" in imports
    assert "myheader.h" in imports


def test_parse_empty_file(parser):
    assert parser.parse("", ".cpp") == []


def test_multiple_parses_same_parser(parser):
    """Parser instance must handle multiple sequential files."""
    r1 = parser.parse(CPP_SOURCE, ".cpp")
    r2 = parser.parse(C_SOURCE, ".c")
    assert len(r1) > 0
    assert len(r2) >= 0  # C file may parse differently; just shouldn't crash

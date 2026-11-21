import pytest

from aide.core.domain.declaration_extent import find_declaration_end


@pytest.mark.parametrize("lines, expected", [
    (["@Composable", "fun Foo() {", "  x()", "}", "fun Bar() {}"], 3),
    (["class Foo", "  : Bar() {", "}", "class Baz {}"], 2),
    (["class Foo :", "  Bar {", "}"], 2),
    (["fun f()", "{", "}", "class Q {}"], 2),
    (["data class P(val x: Int)", "class Q {", "}"], 0),
    (["val TemplateDefault = 5", "class Q {", "}"], 0),
    (["@JvmField val x = 5", "fun g() {}"], 0),
    (["val x =", "  5", "fun g() {}"], 1),
    (["fun f() {", "  if (x) {"], None),
])
def test_find_declaration_end(lines, expected):
    assert find_declaration_end(lines, 0) == expected

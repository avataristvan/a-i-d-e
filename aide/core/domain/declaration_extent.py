"""Where a C-family declaration (Kotlin, Java, TS, ...) ends, found by bracket balancing."""
import re

_PAIRS = {"{": "}", "(": ")", "[": "]"}
_CLOSERS = {v: k for k, v in _PAIRS.items()}
# A declaration continues past a balanced line that ends like this (`class Foo :`, `val x =`) ...
_CONTINUES_AT_END = (":", "=", ",", "(", "->", ".")
# ... or when the next code line starts like this (`class Foo` / `  : Bar() {`, `fun f()` / `{`).
_CONTINUES_AT_START = (":", "{", "=", ".", "->")
_ANNOTATIONS_ONLY = re.compile(r"(?:@[\w.:]+(?:\(.*\))?\s*)+")


def find_declaration_end(lines: list[str], start_index: int) -> int | None:
    """Returns the 0-based index of the last line of the declaration that starts at start_index
    (annotation and comment lines before the header are allowed), or None if it never closes.

    All bracket types are balanced together: a brace-only count would treat a brace-less
    declaration (`data class P(val x: Int)`, `val X = 5`) as still open and swallow the next
    unrelated `{...}` block."""
    stack: list[str] = []
    for i in range(start_index, len(lines)):
        for char in lines[i]:
            if char in _PAIRS:
                stack.append(char)
            elif char in _CLOSERS and stack:
                stack.pop()
        if stack:
            continue
        stripped = lines[i].strip()
        if not stripped or stripped.startswith("//") or _ANNOTATIONS_ONLY.fullmatch(stripped):
            continue
        if stripped.endswith(_CONTINUES_AT_END):
            continue
        following = next((l.strip() for l in lines[i + 1:] if l.strip()), "")
        if following.startswith(_CONTINUES_AT_START):
            continue
        return i
    return None

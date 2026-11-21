import os

import pytest

from aide.core.domain.workspace_edit import (
    WorkspaceEditApplier, WorkspaceEditError, apply_text_edits, path_to_uri,
)
from aide.core.infrastructure.lsp_registry import DEFAULT_SERVERS, LanguageServerProvider
from aide.core.infrastructure.os_file_system import OsFileSystem, SecurityError


def edit(sl, sc, el, ec, text):
    return {"range": {"start": {"line": sl, "character": sc}, "end": {"line": el, "character": ec}}, "newText": text}


# --- apply_text_edits ---

def test_multiple_edits_on_one_line_use_original_positions():
    assert apply_text_edits("foo(foo)\n", [edit(0, 0, 0, 3, "barbaz"), edit(0, 4, 0, 7, "x")]) == "barbaz(x)\n"


def test_utf16_positions_count_astral_characters_twice():
    # "😀" is one Python char but two UTF-16 code units
    assert apply_text_edits("a😀b = 1\n", [edit(0, 3, 0, 4, "c")]) == "a😀c = 1\n"


def test_inserts_at_same_position_keep_array_order():
    assert apply_text_edits("x\n", [edit(0, 0, 0, 0, "A"), edit(0, 0, 0, 0, "B")]) == "ABx\n"


def test_edit_spanning_lines_and_crlf():
    assert apply_text_edits("a\r\nb\r\nc\r\n", [edit(0, 1, 2, 0, "-")]) == "a-c\r\n"


def test_positions_past_line_end_and_file_end_are_clamped():
    assert apply_text_edits("ab\ncd", [edit(0, 99, 0, 99, "!"), edit(7, 0, 7, 0, "?")]) == "ab!\ncd?"


def test_overlapping_edits_are_rejected():
    with pytest.raises(WorkspaceEditError, match="Overlapping"):
        apply_text_edits("abcdef", [edit(0, 0, 0, 4, "x"), edit(0, 2, 0, 5, "y")])


# --- plan / apply ---

@pytest.fixture
def fs(temp_dir):
    return OsFileSystem(jailed_root=temp_dir)


def write(temp_dir, name, content):
    path = os.path.join(temp_dir, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return path


def read(path):
    with open(path) as f:
        return f.read()


def test_changes_map_is_planned_without_writing(fs, temp_dir):
    a = write(temp_dir, "a.py", "old = 1\n")
    plan = WorkspaceEditApplier(fs).plan({"changes": {path_to_uri(a): [edit(0, 0, 0, 3, "new")]}})

    assert read(a) == "old = 1\n"
    assert plan.changed_files == [a]
    assert "-old = 1\n+new = 1\n" in plan.diff(temp_dir)
    assert "a/a.py" in plan.diff(temp_dir)


def test_document_changes_rename_then_edit_new_uri(fs, temp_dir):
    old = write(temp_dir, "pkg/old.ts", "export const x = 1;\n")
    new = os.path.join(temp_dir, "pkg/new.ts")
    created = os.path.join(temp_dir, "pkg/extra.ts")
    applier = WorkspaceEditApplier(fs)
    plan = applier.plan({"documentChanges": [
        {"kind": "rename", "oldUri": path_to_uri(old), "newUri": path_to_uri(new)},
        {"textDocument": {"uri": path_to_uri(new), "version": None}, "edits": [edit(0, 13, 0, 14, "y")]},
        {"kind": "create", "uri": path_to_uri(created)},
    ]})
    applier.apply(plan)

    assert not os.path.exists(old)
    assert read(new) == "export const y = 1;\n"
    assert read(created) == ""
    assert plan.changed_files == sorted([old, new, created])


def test_documentchanges_win_over_changes(fs, temp_dir):
    a = write(temp_dir, "a.py", "abc\n")
    plan = WorkspaceEditApplier(fs).plan({
        "changes": {path_to_uri(a): [edit(0, 0, 0, 1, "X")]},
        "documentChanges": [{"textDocument": {"uri": path_to_uri(a)}, "edits": [edit(0, 0, 0, 1, "Y")]}],
    })
    assert plan.finals[a] == "Ybc\n"


def test_conflicting_resource_operations_are_rejected(fs, temp_dir):
    a = write(temp_dir, "a.py", "")
    b = write(temp_dir, "b.py", "")
    applier = WorkspaceEditApplier(fs)
    with pytest.raises(WorkspaceEditError, match="already exists"):
        applier.plan({"documentChanges": [{"kind": "create", "uri": path_to_uri(a)}]})
    with pytest.raises(WorkspaceEditError, match="already exists"):
        applier.plan({"documentChanges": [{"kind": "rename", "oldUri": path_to_uri(a), "newUri": path_to_uri(b)}]})
    with pytest.raises(WorkspaceEditError, match="missing"):
        applier.plan({"changes": {path_to_uri(os.path.join(temp_dir, "nope.py")): [edit(0, 0, 0, 0, "x")]}})
    assert applier.plan({"documentChanges": [
        {"kind": "create", "uri": path_to_uri(a), "options": {"ignoreIfExists": True}}]}).operations == []


def test_edit_outside_jail_is_refused(fs, temp_dir):
    outside = path_to_uri(os.path.join(os.path.dirname(temp_dir), "outside.py"))
    with pytest.raises(SecurityError):
        WorkspaceEditApplier(fs).apply(WorkspaceEditApplier(fs).plan({"documentChanges": [{"kind": "create", "uri": outside}]}))


def test_apply_inside_transaction_rolls_back(fs, temp_dir):
    a = write(temp_dir, "a.py", "keep\n")
    old = write(temp_dir, "old.py", "moved\n")
    applier = WorkspaceEditApplier(fs)
    plan = applier.plan({"documentChanges": [
        {"textDocument": {"uri": path_to_uri(a)}, "edits": [edit(0, 0, 0, 4, "lost")]},
        {"kind": "rename", "oldUri": path_to_uri(old), "newUri": path_to_uri(os.path.join(temp_dir, "new.py"))},
    ]})

    fs.start_transaction()
    applier.apply(plan)
    fs.rollback()

    assert read(a) == "keep\n"
    assert read(old) == "moved\n"
    assert not os.path.exists(os.path.join(temp_dir, "new.py"))


# --- end to end: real server rename -> plan -> apply ---

PYRIGHT = next(s for s in DEFAULT_SERVERS if s.name == "pyright")


@pytest.mark.skipif(not PYRIGHT.is_available(), reason="pyright-langserver not installed")
def test_pyright_rename_applied_end_to_end(fs, temp_dir):
    greeting = write(temp_dir, "greeting.py", "class Greeter:\n    pass\n")
    app = write(temp_dir, "app.py", "from greeting import Greeter\n\nx = Greeter()\nlabel = 'Greeter'\n")
    provider = LanguageServerProvider(temp_dir, (PYRIGHT,))
    try:
        server = provider.for_file(greeting)
        assert server is not None
        server.open_document(greeting)
        workspace_edit = server.rename(greeting, 0, 6, "Welcomer")
    finally:
        provider.stop_all()
    assert workspace_edit is not None

    applier = WorkspaceEditApplier(fs)
    applier.apply(applier.plan(workspace_edit))

    assert read(greeting) == "class Welcomer:\n    pass\n"
    assert read(app) == "from greeting import Welcomer\n\nx = Welcomer()\nlabel = 'Greeter'\n"

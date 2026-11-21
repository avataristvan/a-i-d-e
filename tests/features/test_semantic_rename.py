import os
import shutil

import pytest

from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.features.code_refactoring.application.semantic_rename import SemanticRenameUseCase
from aide.features.code_refactoring.application.smart_rename import SmartRenameUseCase
from aide.features.code_refactoring.infrastructure.project_files import filter_project_files
from aide.features.code_refactoring.infrastructure.ts_rename_runner import TsRenameError, find_rename_locations

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

TSCONFIG = """{
  "compilerOptions": {"strict": true, "noEmit": true, "module": "esnext", "moduleResolution": "bundler",
                      "jsx": "preserve", "baseUrl": ".", "paths": {"@/*": ["./src/*"]}},
  "include": ["**/*.ts", "**/*.tsx"]
}
"""

HOOK = """export function useSettings() {
  const resetAll = () => {};
  const other = 1;
  return { other, resetAll };
}
"""

CONTEXT = """import { useSettings } from '@/settings/use-settings';
type Store = ReturnType<typeof useSettings> & { extra: number };
declare const store: Store | null;
export function useStore(): Store {
  if (!store) throw new Error('no store');
  return store;
}
"""

PAGE = """import { useStore } from '@/store';
export function Page() {
  const { resetAll } = useStore();
  // resetAll is called on click
  const label = 'resetAll';
  resetAll();
  return label;
}
"""

UNRELATED = """export const settings = { resetAll: false };
export function resetAllLater() { return settings.resetAll; }
"""


def _write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def _read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def project(temp_dir):
    _write(temp_dir, "tsconfig.json", TSCONFIG)
    _write(temp_dir, "src/settings/use-settings.ts", HOOK)
    _write(temp_dir, "src/store.ts", CONTEXT)
    _write(temp_dir, "src/page.tsx", PAGE)
    _write(temp_dir, "src/unrelated.ts", UNRELATED)
    # AIDE_TEST_TYPESCRIPT: path to a typescript 5.x package dir, when none is installed globally.
    ts_pkg = os.environ.get("AIDE_TEST_TYPESCRIPT")
    if ts_pkg:
        os.makedirs(os.path.join(temp_dir, "node_modules"))
        os.symlink(ts_pkg, os.path.join(temp_dir, "node_modules", "typescript"))
    try:
        find_rename_locations(temp_dir, os.path.join(temp_dir, "src/store.ts"), "useStore")
    except TsRenameError as e:
        if "No 'typescript' package" in str(e):
            pytest.skip(f"{e} (set AIDE_TEST_TYPESCRIPT)")
        raise
    return temp_dir


def _rename(root, rel, old, new, **kw):
    return SemanticRenameUseCase(OsFileSystem(jailed_root=root), find_rename_locations).execute(root, os.path.join(root, rel), old, new, **kw)


def test_rename_from_declaration_reaches_destructuring_through_derived_type(project):
    res = _rename(project, "src/settings/use-settings.ts", "resetAll", "reset")

    assert res.success, res.message
    assert res.files_changed == 2
    assert "const reset = " in _read(project, "src/settings/use-settings.ts")
    assert "return { other, reset };" in _read(project, "src/settings/use-settings.ts")
    page = _read(project, "src/page.tsx")
    assert "const { reset } = useStore();" in page
    assert "  reset();" in page
    # comment and string stay by default
    assert "// resetAll is called" in page
    assert "'resetAll'" in page
    # same-named property of another object and a longer identifier stay
    assert _read(project, "src/unrelated.ts") == UNRELATED


def test_rename_from_consumer_gives_same_result(project):
    res = _rename(project, "src/page.tsx", "resetAll", "reset", line=3)

    assert res.success, res.message
    assert sorted({c["file"] for c in res.changes}) == ["src/page.tsx", "src/settings/use-settings.ts"]
    assert res.total_replacements == 4


def test_rename_follows_imports_and_alias_paths(project):
    res = _rename(project, "src/store.ts", "useStore", "useAppStore")

    assert res.success, res.message
    assert "import { useAppStore } from '@/store';" in _read(project, "src/page.tsx")
    assert "useAppStore();" in _read(project, "src/page.tsx")


def test_in_comments_and_strings_are_opt_in(project):
    res = _rename(project, "src/page.tsx", "resetAll", "reset", in_comments=True, in_strings=True)

    assert res.success, res.message
    page = _read(project, "src/page.tsx")
    assert "// reset is called" in page
    assert "'reset'" in page


def test_dry_run_writes_nothing(project):
    res = _rename(project, "src/settings/use-settings.ts", "resetAll", "reset", dry_run=True)

    assert res.success and res.files_changed == 2
    assert _read(project, "src/settings/use-settings.ts") == HOOK


def test_nested_worktree_copies_are_left_alone(project):
    # A worktree copy whose alias imports resolve into the root project's src.
    _write(project, ".claude/worktrees/agent-1/.git", "gitdir: /elsewhere\n")
    _write(project, ".claude/worktrees/agent-1/src/page.tsx", PAGE)

    res = _rename(project, "src/settings/use-settings.ts", "resetAll", "reset")

    assert res.success, res.message
    assert _read(project, ".claude/worktrees/agent-1/src/page.tsx") == PAGE
    assert all(not c["file"].startswith(".claude") for c in res.changes)


def test_unknown_symbol_fails_cleanly(project):
    res = _rename(project, "src/page.tsx", "doesNotExist", "x")

    assert not res.success
    assert "No renameable 'doesNotExist'" in res.message


def test_invalid_new_name_is_rejected(project):
    res = _rename(project, "src/page.tsx", "resetAll", "not-valid")

    assert not res.success


def test_textual_rename_skips_nested_worktrees(temp_dir):
    _write(temp_dir, "src/a.ts", "export const foo = 1;\n")
    _write(temp_dir, ".claude/worktrees/agent-1/.git", "gitdir: /elsewhere\n")
    _write(temp_dir, ".claude/worktrees/agent-1/src/a.ts", "export const foo = 1;\n")

    res = SmartRenameUseCase(OsFileSystem(jailed_root=temp_dir), file_filter=filter_project_files).execute(temp_dir, "foo", "bar", use_word_boundary=True)

    assert res.success and res.files_changed == 1
    assert _read(temp_dir, ".claude/worktrees/agent-1/src/a.ts") == "export const foo = 1;\n"

import os
import textwrap

import pytest

from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.features.code_refactoring.application.esm import ModuleResolver, scan, top_level_declarations
from aide.features.code_refactoring.application.move_esm_file import MoveEsmFileUseCase
from aide.features.code_refactoring.application.move_esm_symbol import MoveEsmSymbolUseCase, MoveSymbolError


def write(root, rel, content):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))
    return path


def read(root, rel):
    with open(os.path.join(root, rel)) as f:
        return f.read()


@pytest.fixture
def project(temp_dir):
    write(temp_dir, "tsconfig.json", """
        {
          // JSONC: comments and trailing commas
          "compilerOptions": {
            "paths": { "@/*": ["./src/*"], },
          },
        }
    """)
    return temp_dir


# ------------------------------------------------------------------ scanner / resolver

def test_scan_covers_all_import_shapes():
    text = textwrap.dedent("""
        import Foo, { a, type B as C } from "@/x/y";
        import type { D } from '../d';
        import * as ns from './ns';
        import './side';
        export { e } from './e';
        export * from './all';
        const m = await import('./lazy');
        vi.mock("@/x/y", () => ({}));
        // import { nope } from './commented';
    """)
    refs = scan(text)
    assert [r.spec for r in refs] == ["@/x/y", "../d", "./ns", "./side", "./e", "./all", "./lazy", "@/x/y"]
    first = refs[0]
    assert first.default == "Foo"
    assert [(b.imported, b.local, b.is_type) for b in first.named] == [("a", "a", False), ("B", "C", True)]
    assert refs[1].type_only and refs[1].named[0].is_type
    assert refs[2].namespace == "ns"
    assert refs[-1].callee == "vi.mock"


def test_resolver_alias_and_relative(project):
    target = write(project, "src/mod/a.ts", "export const a = 1;\n")
    importer = os.path.join(project, "src/other/b.ts")
    r = ModuleResolver(OsFileSystem(jailed_root=project), project)
    assert r.resolve("@/mod/a", importer) == target
    assert r.resolve("../mod/a", importer) == target
    moved = os.path.join(project, "src/infra/a.ts")
    assert r.specifier_for(moved, importer, "@/mod/a") == "@/infra/a"
    assert r.specifier_for(moved, importer, "../mod/a") == "../infra/a"


def test_declarations_include_let_and_jsdoc():
    text = "/** doc */\nexport function f() {\n  return `}`;\n}\nlet n = 0;\ntype T =\n  | 'a'\n  | 'b';\n"
    decls = top_level_declarations(text)
    assert [(d.name, d.kind) for d in decls] == [("f", "function"), ("n", "let"), ("T", "type")]
    assert text[decls[0].start:decls[0].end].startswith("/** doc */")


# ------------------------------------------------------------------ move-file

def test_move_file_rewrites_alias_relative_double_quotes_and_vi_mock(project):
    write(project, "src/domain/mods/generic.ts", """
        import { Types } from './types';
        import { util } from "@/shared/util";
        export class Generic {}
    """)
    write(project, "src/domain/mods/types.ts", "export type Types = string;\n")
    write(project, "src/shared/util.ts", "export const util = 1;\n")
    write(project, "src/domain/main/main.ts", "import { Generic } from '@/domain/mods/generic';\n")
    write(project, "src/domain/mods/index.ts", 'import { Generic } from "./generic";\nexport { Generic };\n')
    write(project, "src/domain/main/__tests__/m.test.ts", "vi.mock('../../mods/generic', () => ({}));\n")

    fs = OsFileSystem(jailed_root=project)
    uc = MoveEsmFileUseCase(fs)
    plan = uc.plan(["src/domain/mods/generic.ts"], "src/infra/mods/generic.ts", project)
    preview = plan.preview(project)
    assert set(preview["edits"]) == {
        "src/domain/mods/generic.ts", "src/domain/main/main.ts", "src/domain/mods/index.ts",
        "src/domain/main/__tests__/m.test.ts"}
    assert not os.path.exists(os.path.join(project, "src/infra/mods/generic.ts"))  # plan is read-only

    plan.apply(fs)
    moved = read(project, "src/infra/mods/generic.ts")
    assert "from '../../domain/mods/types'" in moved
    assert 'from "@/shared/util"' in moved  # alias import of an unmoved file stays
    assert read(project, "src/domain/main/main.ts") == "import { Generic } from '@/infra/mods/generic';\n"
    assert read(project, "src/domain/mods/index.ts").startswith('import { Generic } from "../../infra/mods/generic";')
    assert "vi.mock('../../../infra/mods/generic'" in read(project, "src/domain/main/__tests__/m.test.ts")
    assert not os.path.exists(os.path.join(project, "src/domain/mods/generic.ts"))


# ------------------------------------------------------------------ move-symbol

@pytest.fixture
def symbol_project(project):
    write(project, "src/engine/core.ts", """
        import { Tone, unused } from 'tone';
        import { type Config, helperValue } from '@/shared/config';

        let counter = 0;

        function bump(): number {
          return ++counter;
        }

        export interface Voice {
          id: number;
        }

        export function makeVoice(cfg: Config): Voice {
          return { id: bump() + helperValue + Tone.now() };
        }

        export function keep(v: Voice): number {
          return v.id + unused;
        }
    """)
    write(project, "src/shared/config.ts", "export type Config = {};\nexport const helperValue = 1;\n")
    write(project, "src/app/a.ts", 'import { makeVoice, keep, type Voice } from "@/engine/core";\n')
    write(project, "src/engine/b.ts", "import { makeVoice } from './core';\n")
    write(project, "src/engine/c.ts", "export { type Voice, keep } from './core';\n")
    return project


def test_move_symbol_full_flow(symbol_project):
    root = symbol_project
    fs = OsFileSystem(jailed_root=root)
    uc = MoveEsmSymbolUseCase(fs)
    plan = uc.plan(os.path.join(root, "src/engine/core.ts"), ["makeVoice", "Voice"],
                   os.path.join(root, "src/engine/voices/voice.ts"), root)
    assert plan.helpers == ["bump", "counter"]  # let + non-exported helper travel along
    plan.apply(fs)

    dest = read(root, "src/engine/voices/voice.ts")
    assert "let counter = 0;" in dest and "function bump()" in dest
    assert "import { Tone } from 'tone';" in dest            # only the used binding, not `unused`
    assert "import { type Config, helperValue } from '../../shared/config';" not in dest
    assert "import { type Config, helperValue } from '@/shared/config';" in dest  # alias style kept

    src = read(root, "src/engine/core.ts")
    assert "import { type Voice } from './voices/voice';" in src  # back-import, type-only
    assert "import { unused } from 'tone';" in src                  # Tone no longer needed here
    assert "@/shared/config" not in src
    assert "makeVoice" not in src and "let counter" not in src

    assert read(root, "src/app/a.ts") == (
        'import { keep } from "@/engine/core";\n'
        'import { makeVoice, type Voice } from "@/engine/voices/voice";\n')
    assert read(root, "src/engine/b.ts") == "import { makeVoice } from './voices/voice';\n"
    assert read(root, "src/engine/c.ts") == (
        "export { keep } from './core';\nexport { type Voice } from './voices/voice';\n")


def test_move_symbol_dry_run_lists_edits_and_writes_nothing(symbol_project):
    root = symbol_project
    before = read(root, "src/engine/core.ts")
    plan = MoveEsmSymbolUseCase(OsFileSystem(jailed_root=root)).plan(
        os.path.join(root, "src/engine/core.ts"), ["makeVoice"], os.path.join(root, "src/engine/voices/voice.ts"), root)
    preview = plan.preview(root)
    assert {"src/engine/core.ts", "src/engine/voices/voice.ts", "src/app/a.ts", "src/engine/b.ts"} <= set(preview["edits"])
    assert any("import of moved symbol" in e["reason"] for e in preview["edits"]["src/engine/b.ts"])
    assert read(root, "src/engine/core.ts") == before
    assert not os.path.exists(os.path.join(root, "src/engine/voices/voice.ts"))


def test_move_symbol_shared_helper_is_exported_and_warned(project):
    write(project, "src/x.ts", "function h() { return 1; }\nexport function a() { return h(); }\nexport function b() { return h(); }\n")
    fs = OsFileSystem(jailed_root=project)
    plan = MoveEsmSymbolUseCase(fs).plan("src/x.ts", ["a"], "src/y.ts", project)
    plan.apply(fs)
    assert read(project, "src/x.ts").startswith("export function h()")
    assert "import { h } from './x';" in read(project, "src/y.ts")
    assert any("circular" in w for w in plan.warnings)


def test_move_symbol_unknown_name_fails(project):
    write(project, "src/x.ts", "export const a = 1;\n")
    with pytest.raises(MoveSymbolError):
        MoveEsmSymbolUseCase(OsFileSystem(jailed_root=project)).plan(
            os.path.join(project, "src/x.ts"), ["nope"], os.path.join(project, "src/y.ts"), project)


def test_move_symbol_into_empty_existing_file_puts_imports_first(project):
    write(project, "src/x.ts", "import { dep } from './dep';\nexport function a() { return dep; }\n")
    write(project, "src/dep.ts", "export const dep = 1;\n")
    write(project, "src/y.ts", "")
    fs = OsFileSystem(jailed_root=project)
    MoveEsmSymbolUseCase(fs).plan("src/x.ts", ["a"], "src/y.ts", project).apply(fs)
    assert read(project, "src/y.ts").startswith("import { dep } from './dep';")


def test_move_symbol_drops_source_import_even_when_destination_already_has_it(project):
    write(project, "src/x.ts", "import { dep } from './dep';\nexport function a() { return dep; }\n")
    write(project, "src/dep.ts", "export const dep = 1;\n")
    write(project, "src/y.ts", "import { dep } from './dep';\nexport const b = dep;\n")
    fs = OsFileSystem(jailed_root=project)
    MoveEsmSymbolUseCase(fs).plan("src/x.ts", ["a"], "src/y.ts", project).apply(fs)
    assert "dep" not in read(project, "src/x.ts")
    assert read(project, "src/y.ts").count("import { dep }") == 1


def test_split_keeps_bindings_when_braces_contain_comments(project):
    write(project, "src/x.ts", "export const a = 1;\nexport const b = 2;\n")
    write(project, "src/use.ts", "import {\n  a, // the a\n  b,\n} from './x';\n")
    fs = OsFileSystem(jailed_root=project)
    MoveEsmSymbolUseCase(fs).plan("src/x.ts", ["b"], "src/y.ts", project).apply(fs)
    use = read(project, "src/use.ts")
    assert "import { b } from './y';" in use
    assert "  a," in use and "b," not in use.split("from './x'")[0]


def test_move_file_rejects_colliding_targets_and_moves_nothing(project):
    write(project, "src/a/util.ts", "export const u = 1;\n")
    write(project, "src/b/util.ts", "export const v = 1;\n")
    plan = MoveEsmFileUseCase(OsFileSystem(jailed_root=project)).plan(["src/a/util.ts", "src/b/util.ts"], "src/c", project)
    assert plan.errors and not plan.edits

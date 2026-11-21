import os
from aide.features.code_refactoring.application.clone_symbol import CloneSymbolUseCase
from aide.core.infrastructure.os_file_system import OsFileSystem
from aide.core.infrastructure.strategy_provider import StrategyProvider


def make_use_case(temp_dir):
    fs = OsFileSystem(jailed_root=temp_dir)
    provider = StrategyProvider()
    return CloneSymbolUseCase(fs, provider), fs


def test_clone_simple_class(temp_dir):
    use_case, fs = make_use_case(temp_dir)
    file_path = os.path.join(temp_dir, "Model.kt")
    fs.write_file(file_path, "package com.example\n\ndata class TargetTempo(val bpm: Int)\n")

    res = use_case.execute(file_path, "TargetTempo", "CountInBars")

    assert res.success
    content = fs.read_file(file_path)
    assert "data class TargetTempo(val bpm: Int)" in content
    assert "data class CountInBars(val bpm: Int)" in content


def test_clone_with_extension_functions_and_prefixed_declarations(temp_dir):
    use_case, fs = make_use_case(temp_dir)
    file_path = os.path.join(temp_dir, "TargetTempo.kt")
    source = (
        "package com.example\n\n"
        "data class TargetTempo(val bpm: Int) {\n"
        "    companion object\n"
        "}\n\n"
        "val TargetTempoPresets = listOf(TargetTempo(60), TargetTempo(120))\n\n"
        "fun TargetTempo.next(): TargetTempo {\n"
        "    return this\n"
        "}\n\n"
        "fun TargetTempo.label(): String = \"$bpm bpm\"\n\n"
        "fun unrelated() {}\n"
    )
    fs.write_file(file_path, source)

    res = use_case.execute(file_path, "TargetTempo", "CountInBars")

    assert res.success
    assert set(res.cloned_symbols) == {
        "TargetTempo",
        "TargetTempo.next",
        "TargetTempo.label",
        "TargetTempo.TargetTempoPresets",
    }

    content = fs.read_file(file_path)
    # Originals preserved
    assert "data class TargetTempo(val bpm: Int)" in content
    assert "val TargetTempoPresets = listOf(TargetTempo(60), TargetTempo(120))" in content
    assert "fun TargetTempo.next(): TargetTempo" in content
    # Clones present with renamed receiver/type and prefixed identifier
    assert "data class CountInBars(val bpm: Int)" in content
    assert "val CountInBarsPresets = listOf(CountInBars(60), CountInBars(120))" in content
    assert "fun CountInBars.next(): CountInBars" in content
    assert "fun CountInBars.label(): String" in content
    # Unrelated code untouched
    assert content.count("fun unrelated() {}") == 1


def test_clone_applies_extra_substitutions(temp_dir):
    use_case, fs = make_use_case(temp_dir)
    file_path = os.path.join(temp_dir, "Model.kt")
    fs.write_file(file_path, "package com.example\n\nenum class TargetTempo { SLOW, FAST }\n")

    res = use_case.execute(file_path, "TargetTempo", "CountInBars", substitutions={"SLOW": "SHORT", "FAST": "LONG"})

    assert res.success
    content = fs.read_file(file_path)
    assert "enum class CountInBars { SHORT, LONG }" in content
    assert "enum class TargetTempo { SLOW, FAST }" in content


def test_clone_fails_when_target_symbol_already_exists(temp_dir):
    use_case, fs = make_use_case(temp_dir)
    file_path = os.path.join(temp_dir, "Model.kt")
    fs.write_file(file_path, "package com.example\n\nclass TargetTempo\nclass CountInBars\n")

    res = use_case.execute(file_path, "TargetTempo", "CountInBars")

    assert not res.success
    assert "already exists" in res.message


def test_clone_fails_for_non_kotlin_file(temp_dir):
    use_case, fs = make_use_case(temp_dir)
    file_path = os.path.join(temp_dir, "model.py")
    fs.write_file(file_path, "class TargetTempo:\n    pass\n")

    res = use_case.execute(file_path, "TargetTempo", "CountInBars")

    assert not res.success
    assert "Kotlin" in res.message


def test_clone_fails_when_template_not_found(temp_dir):
    use_case, fs = make_use_case(temp_dir)
    file_path = os.path.join(temp_dir, "Model.kt")
    fs.write_file(file_path, "package com.example\n\nclass Other\n")

    res = use_case.execute(file_path, "TargetTempo", "CountInBars")

    assert not res.success
    assert "not found" in res.message

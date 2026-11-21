type: learning
topic: general
created: 1788689606.235747
---

Feature idea: `clone-symbol` command — IMPLEMENTED 2026-09-06 for Kotlin only (as scoped, the user explicitly asked for Kotlin-first).
**Where:** `aide/features/code_refactoring/application/clone_symbol.py` (`CloneSymbolUseCase`), CLI wired in `aide/features/code_refactoring/plugin.py` (`clone-symbol` subcommand), tests in `tests/features/test_clone_symbol.py`. Docs updated in both `setup-files/claude-global-aide/SKILL.md` and `setup-files/gemini-global-aide/SKILL.md`.
**What it does:** `aide clone-symbol <template> <new_name> --file <path> [--substitutions old=new,...] [-n] [--verify]`. Clones a template class/object/interface plus its structurally-coupled same-file companions — extension functions/properties (`fun/val/var Template.member`) and prefixed top-level declarations (`TemplatePresets`, `TemplateDefault`, ...) — renaming all occurrences (including as identifier prefixes) and inserting the clone after the original group. Guards against clobbering an existing symbol of the new name.
**Not yet done:** only Kotlin (.kt) is supported — other languages rejected with a clear error. Not yet installed into the deployed global skill (`scripts/install_global.py` was not run — that's an interactive, global-state-changing script, left for the user to run when ready).
**How to apply:** if asked to extend clone-symbol to other languages, follow the same pattern — dispatch via `strategy_provider.get_strategy()` and add per-language extension/prefixed-declaration regexes; the core rename/insert logic in `CloneSymbolUseCase` is already language-agnostic aside from the `.kt`-only gate and the Kotlin-specific regexes in `_find_related_declarations`.
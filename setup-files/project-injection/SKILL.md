---
name: aide
description: Deterministic multi-file refactoring CLI: move/rename/extract symbols, files and packages with reference updates and --verify auto-rollback; plus code inspection (outline, usages, impact, dead code, symbol history), structural search and test tooling. Prefer it over hand edits for structural refactoring.
binary: ./a-i-d-e/aide.py
---

# AIDE — Agent Interface for Deterministic Editing

The command is `python3 ./a-i-d-e/aide.py`; below it is written as `aide`.
Run it from the project root: all file access is jailed to that directory.
Every command prints JSON `{"success": ..., "message": ..., "data": {...}}`; check `success` first.

## Discover instead of guessing

```
aide commands               # categories (inspection, refactoring, generation, tests, ...)
aide commands <category>    # the commands in it, one line each
aide <command> --help       # exact arguments and usage notes; read it before first use
```

## Refactoring workflow

```
aide find-impact --symbol <name>   # blast radius first
aide <refactor-command> ... -n     # preview (dry run)
aide <refactor-command> ... --verify   # apply; runs the tests and reverts everything if they fail
```
Omit `--verify` when the project has no test suite (it fails hard).

## Most used

```
aide outline "**/*.kt"                          # symbol map
aide usages <symbol>
aide rename-symbol <old> <new> --file <path>    # semantic for TS/JS
aide move-symbol <symbol> --source <src> --dest <dest>
aide move-file <source> <dest>
```

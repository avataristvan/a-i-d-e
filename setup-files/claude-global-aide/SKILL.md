---
name: aide
description: Agent Interface for Deterministic Editing. Use when performing structural code refactoring (move, rename, extract symbols/files/packages), inspecting code structure (outline, usages, impact analysis), generating code (scaffold Clean Architecture features, implement interfaces, generate DTOs), or running tests with structured JSON output. All refactoring commands support --verify for atomic auto-rollback on test failure.
argument-hint: <command> [args]
---

# AIDE — Agent Interface for Deterministic Editing

Available via the `aide` global command. All file operations are jailed to the project root — path traversal is blocked at the OS level.

**Supported languages**: Kotlin, TypeScript, JavaScript, Python, C#, Rust, Go, C++, Scala, Ruby.

## Output format

Every command emits JSON to stdout:
```json
{"success": true, "message": "...", "data": { ... }}
```
Check `success` before consuming `data`. On failure, `message` contains the error.

## Flags (all refactoring commands)
- `-n` / `--dry-run` — Preview changes without writing to disk.
- `--verify` — Run tests after refactoring; auto-revert all changes if any test fails. Omit if the project has no test suite — it will hard-fail.

## Recommended workflow

```
# 1. Understand blast radius first
aide find-impact --symbol <name>

# 2. Preview the change
aide <refactor-command> ... --dry-run

# 3. Execute atomically (only if a test suite exists)
aide <refactor-command> ... --verify
```

## Inspection

```
aide outline "<glob>"                                # Symbol map — use ** for recursive, e.g. "**/*.py"
aide read <file> [--selection start:end]             # Line-numbered content (--selection is 1-based, inclusive)
aide usages <symbol> [--root <dir>]                 # Usages → data.usages: ["file:line:col", ...]
aide find-impact --symbol <name> [--file <file>]    # data.impacted_files / data.impacted_tests
```

`outline` legend: `[C]` = class/interface, `[f]` = function/method. Output is in `data.outline` as markdown.

Use `--file` on `find-impact` when the symbol name is ambiguous across multiple files.

## Which move command to use

| Goal | Command |
|---|---|
| Move a single symbol (class/function) to another file | `move-symbol` |
| Move one or more files to a different directory | `move-file` |
| Move a whole package/directory and update all references | `move-package` |
| Bulk-update import paths after a manual move | `update-references` |

## Refactoring

```
aide move-symbol <symbol> --source <src> --dest <dest> [-n] [--verify]
aide rename-symbol <old> <new> [--root <dir>] [-n] [--verify]
aide change-signature <symbol> --add-param <def> --default-value <val> [-n] [--verify]
aide extract --file <path> --selection <start:end> --name <name> [--scope <s>] [-n] [--verify]
aide extract-interface --file <path> --class-name <cls> [--interface-name <name>] [-n]
aide move-package <src> <dest_package> [--root <dir>] [-n] [--verify]
aide move-file <source> <dest_dir> [--src-root <dir>] [-n] [--verify]
aide update-references <old_fqdn> <new_fqdn> [-n] [--verify]
```

## Code Generation

```
aide scaffold-feature --name <Name> --stack <kotlin|python> [--output-dir <dir>]
aide implement-interface --file <path> --class-name <cls> --implements <iface>
aide register-dependency --file <path> --import-path <path> --binding <statement>
aide project-dto --source-file <path> --entity <E> --target-file <path> --dto <D> --stack <stack>
```

## Cleanup & Architecture Audit

```
aide cleanup [--path <dir>]                          # Remove unused/duplicate imports
aide audit --stack <kotlin|nextjs> [--src <dir>]    # Validate Clean Architecture layer rules
```

## Test Tools

```
aide test --path <dir> [--format json]
aide generate-tests --file <path> --symbol <name> [--format json]
aide scaffold-mocks --file <path> --class-name <name> [--format json]
aide audit-fixtures --path <dir> [--format json]
aide test-audit --src <src> --tests <tests> [--format json]
```

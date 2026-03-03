---
name: aide
description: Agent Interface for Deterministic Editing. Use when performing structural code refactoring (move, rename, extract symbols/files/packages), inspecting code structure (outline, usages, impact analysis), generating code (scaffold Clean Architecture features, implement interfaces, generate DTOs), or running tests with structured JSON output. All refactoring commands support --verify for atomic auto-rollback on test failure.
argument-hint: <command> [args]
---

# AIDE — Agent Interface for Deterministic Editing

Available via the `aide` global command. All file operations are jailed to the project root — path traversal is blocked at the OS level. Refactoring commands emit structured JSON.

**Supported languages**: Kotlin, TypeScript, JavaScript, Python, C#, Rust, Go, C++, Scala, Ruby.

## Flags (all refactoring commands)
- `-n` / `--dry-run` — Preview changes without writing to disk.
- `--verify` — Run tests after refactoring; auto-revert all changes if any test fails. **Always prefer this flag.**

## Inspection

```
aide outline <glob-pattern>                          # Symbol structure of matching files
aide read <file> [--selection start:end]             # Line-numbered file content
aide usages <symbol> [--root <dir>]                 # All usages of a symbol across the project
aide find-impact <symbol> [--root <dir>]            # Which source & test files are impacted by a symbol change
```

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

---
name: a-i-d-e-global
description: Agent Interface for Deterministic Editing (Global CLI Tool)
binary: aide
---

# a-i-d-e (Global)

CLI tool for deterministic file operations & refactoring.
Available everywhere on this system via the `aide` command.

Supported Languages: **Kotlin, TypeScript, JavaScript, Python, C#, Rust, Go, C++, Scala, Ruby**.

- **Security**: Operations are restricted to the project root (Path Boundary Jail).
- **Parsing Precision**: AST-based parsing (Tree-Sitter) for Python, C#, and Rust.

## Commands

### `outline`
Structural symbol discovery.
- **Args**: `pattern` (glob)
- **Invoke**: `aide outline <pattern>`

### `read`
Line-numbered file retrieval.
- **Args**: `file` (path), `--selection <range>` (optional)
- **Invoke**: `aide read <path> [--selection start:end]`

### `cleanup`
Automated code hygiene.
- **Args**: `--path <dir>` (default: .)
- **Invoke**: `aide cleanup [--path <path>]`

### `audit`
Architecture validation.
- **Args**: `--stack {kotlin,nextjs}`, `--src <dir>`
- **Invoke**: `aide audit --stack <stack> [--src <path>]`

### `move-package`
- **Invoke**: `aide move-package <src> <dest_package> [--root <p>] [-n] [--verify]`

### `extract`
Refactor: Extract code block to function.
- **Invoke**: `aide extract --file <path> --selection <range> --name <name> [-n]`

### `usages`
Inspection: Find semantic symbol usages.
- **Invoke**: `aide usages <symbol> [--root <dir>]`

### `find-impact`
Inspection: Identify files and tests impacted by a symbol change.
- **Invoke**: `aide find-impact <symbol> [--root <dir>]`

### `dead-code`
Inspection: Find unreferenced top-level symbols (classes, functions).
- **Invoke**: `aide dead-code [--root <dir>] [--ignore <glob-patterns>]`
- Use `--ignore '*Plugin,*Adapter'` to skip dynamically-registered symbols.

### `symbol-blame`
Git blame at symbol granularity — who last touched each line of a symbol and why.
- **Invoke**: `aide symbol-blame --file <path> --symbol <name>`

### `symbol-history`
Full commit history for a symbol's line range.
- **Invoke**: `aide symbol-history --file <path> --symbol <name> [--limit N]`

### `structural-search`
AST-aware pattern search via semgrep. Requires `pip install semgrep`.
- **Invoke**: `aide structural-search --pattern '<pattern>' --lang <lang> [--root <dir>]`

### `structural-replace`
AST-aware pattern replace via semgrep. Use `--dry-run` to preview.
- **Invoke**: `aide structural-replace --pattern '<pattern>' --rewrite '<expr>' --lang <lang> [--root <dir>] [--dry-run]`

### `change-signature`
Refactor: Update function definition and call sites.
- **Invoke**: `aide change-signature <symbol> --add-param <def> --default-value <val> [-n]`

### `move-symbol`
Refactor: Move top-level symbol to another file.
- **Invoke**: `aide move-symbol <symbol> --source <src> --dest <dest> [-n]`

### `rename-symbol`
Refactor: Rename symbol project-wide safely.
- **Invoke**: `aide rename-symbol <old> <new> [--root <p>] [-n]`

## Code Generation Tools

### `scaffold-feature`
- **Invoke**: `aide scaffold-feature --name <FeatureName> --stack <stack>`

### `implement-interface`
- **Invoke**: `aide implement-interface --file <path> --class-name <C> --implements <I>`

### `project-dto`
- **Invoke**: `aide project-dto --source-file <p> --entity <E> --target-file <p> --dto <D> --stack <s>`

## Test Tools

### `test`
- **Invoke**: `aide test --path <dir> [--format json]`

### `test-audit`
- **Invoke**: `aide test-audit --src <src> --tests <tests>`

## Global Rules
Always use the `--verify` flag when performing refactoring commands. This ensures that any change that breaks the build or tests is automatically rolled back.

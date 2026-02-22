---
name: a-i-d-e
description: Agent Interface for Deterministic Editing (CLI Tool)
binary: ./a-i-d-e/aide.py
---

# a-i-d-e

CLI tool for deterministic file operations & refactoring.
Supported Languages: **Kotlin, TypeScript, JavaScript, Python, C#, Rust, Go, C++, Scala, Ruby**.


- **Security**: Operations are restricted to the project root (Path Boundary Jail). Path traversal attempts (e.g. `../` or `/etc/`) will throw a `SecurityError`.

## Commands

### `outline`
Structural symbol discovery.
- **Args**: `pattern` (glob)
- **Invoke**: `./a-i-d-e/aide.py outline <pattern>`

### `read`
Line-numbered file retrieval.
- **Args**: `file` (path), `--selection <range>` (optional)
- **Invoke**: `./a-i-d-e/aide.py read <path> [--selection start:end]`

### `cleanup`
Automated code hygiene.
- **Tasks**: Remove unused imports (.kt), Remove duplicate imports (.kt, .ts, .js, .py)
- **Args**: `--path <dir>` (default: .)
- **Invoke**: `./a-i-d-e/aide.py cleanup [--path <path>]`

### `audit`
Architecture validation.
- **Args**: `--stack {kotlin,nextjs}`, `--src <dir>`
- **Invoke**: `./a-i-d-e/aide.py audit --stack <stack> [--src <path>]`

### `move-package`
Refactor: Move package + Update references.
- **Args**: 
  - `src`: Rel path from java-root (e.g. `domain/macro`)
  - `dest_package`: Target FQDN (e.g. `com.avataristvan.ExoDeck.features.macro.domain`)
  - `--root <dir>` (default: .)
  - `--java-root <dir>` (default: `app/src/main/java/com/avataristvan/ExoDeck`)
- **Invoke**: `./a-i-d-e/aide.py move-package <src> <dest_package> [--root <p>] [--java-root <p>] [-n]`

### `extract`
Refactor: Extract code block to function.
- **Args**:
  - `--file`: File path
  - `--selection`: Line range `start:end` (1-based)
  - `--name`: New function name
  - `--scope`: Visibility (private, internal, public)
- **Invoke**: `./a-i-d-e/aide.py extract --file <path> --selection <range> --name <name> [--scope <s_>] [-n]`
*(Supports Kotlin, TS/JS, Python, C#, Rust, Go, C++, Scala, Ruby)*

### `extract-interface`
Refactor: Create interface from class and implement it.
- **Args**:
  - `--file`: File path
  - `--class-name`: Class to extract from
  - `--interface-name`: Optional new interface name
- **Invoke**: `./a-i-d-e/aide.py extract-interface --file <path> --class-name <name> [--interface-name <name>] [-n]`
*(Supports Kotlin)*

### `usages`
Inspection: Find semantic symbol usages.
- **Args**:
  - `symbol`: Symbol name to search
  - `--root`: Search root (default: .)
- **Invoke**: `./a-i-d-e/aide.py usages <symbol> [--root <dir>]`

### `find-impact`
Inspection: Analyze imports and graph structure to output exactly which source files and test files are functionally impacted by a symbol change.
- **Args**:
  - `symbol`: Symbol name to check
  - `--root`: Project root
- **Invoke**: `./a-i-d-e/aide.py find-impact <symbol> [--root <dir>]`

### `change-signature`
Refactor: Update function definition and call sites.
- **Args**:
  - `symbol`: Function name
  - `--add-param`: New param definition (e.g. `x: Int`)
  - `--default-value`: Value for existing calls (e.g. `0`)
  - `--root`: Project root
- **Invoke**: `./a-i-d-e/aide.py change-signature <symbol> --add-param <def> --default-value <val> [-n]`
*(Supports Kotlin, TS/JS, Python, C#, Rust, Go, C++, Scala, Ruby)*

### `move-symbol`
Refactor: Move top-level symbol to another file.
- **Args**:
  - `symbol`: Symbol name (e.g. `MyFunc`) or comma-separated list for batch move (e.g. `FuncA,FuncB,ClassC`)
  - `--source`: Source file path
  - `--dest`: Destination file path
- **Smart Features**: 
  - Automatically merges required imports into destination.
  - Updates project-wide references if the symbol moves to a different package.
- **Invoke**: `./a-i-d-e/aide.py move-symbol <symbol> --source <src> --dest <dest> [-n]`
*(Supports Kotlin, TS/JS, Python, C#, Rust, Go, C++, Scala, Ruby)*

### `rename-symbol`
Refactor: Rename symbol project-wide with regex-safe whole-word matching.
- **Args**:
  - `old_symbol`: Current name
  - `new_symbol`: New name
  - `--root`: Project root
- **Invoke**: `./a-i-d-e/aide.py rename-symbol <old> <new> [--root <p>] [-n]`

## Deterministic Code Generation & Testing Tools

### `generate-tests`
Test Generation: Scaffold context payload for test generation.
- **Args**: `--file` (path), `--symbol` (name), `--format` (json|markdown)
- **Invoke**: `./a-i-d-e/aide.py generate-tests --file <path> --symbol <name> [--format json]`

### `scaffold-mocks`
Test Generation: Scaffold boilerplate mock dependencies for a class constructor.
- **Args**: `--file` (path), `--class-name` (name), `--format` (json|markdown)
- **Invoke**: `./a-i-d-e/aide.py scaffold-mocks --file <path> --class-name <name> [--format json]`

### `scaffold-feature`
Code Generation: Deterministically generate a Clean Architecture folder structure and boilerplate.
- **Args**: `--name` (FeatureName), `--stack` (kotlin|python), `--output-dir` (default: ./src)
- **Invoke**: `./a-i-d-e/aide.py scaffold-feature --name <FeatureName> --stack <stack> [--output-dir <dir>]`

### `implement-interface`
Code Generation: Mechanically inject missing method stubs from an interface into a concrete class.
- **Args**: `--file` (path), `--class-name` (ConcreteClass), `--implements` (InterfaceName)
- **Invoke**: `./a-i-d-e/aide.py implement-interface --file <path> --class-name <ConcreteClass> --implements <InterfaceName>`

### `register-dependency`
Code Generation: Safely inject an import and a DI binding statement into a DI registry file.
- **Args**: `--file` (path), `--import-path` (full import), `--binding` (exact statement)
- **Invoke**: `./a-i-d-e/aide.py register-dependency --file <path> --import-path <path> --binding <statement>`

### `project-dto`
Code Generation: Deterministically generate a DTO and mapping function from a Domain Entity.
- **Args**: `--source-file` (path), `--entity` (ClassName), `--target-file` (path), `--dto` (DTOName), `--stack` (kotlin|python)
- **Invoke**: `./a-i-d-e/aide.py project-dto --source-file <path> --entity <Entity> --target-file <path> --dto <DTO> --stack <stack>`



## Agentic Test Execution Tools

### `test`
Test Execution: Run tests and return a concise JSON/text payload omitting unreadable terminal traces.
- **Args**: `--path` (dir), `--format` (json|text)
- **Invoke**: `./a-i-d-e/aide.py test --path <dir> [--format json]`

### `audit-fixtures`
Test Execution: Scans pytest fixtures and correlates usages to report unused setup code.
- **Args**: `--path` (dir), `--format` (json|text)
- **Invoke**: `./a-i-d-e/aide.py audit-fixtures --path <dir> [--format json]`

### `test-audit`
Test Execution: Runs test suite with coverage and emits structured mapping of exactly which file lines lack tests.
- **Args**: `--src` (dir), `--tests` (dir), `--format` (json|text)
- **Invoke**: `./a-i-d-e/aide.py test-audit --src <src> --tests <tests> [--format json]`

## Flags
- `-n`, `--dry-run`: Preview all changes (file writes, renames, reference updates) without applying them.
- `--verify`: Automatically run tests after refactoring (`move-package`, `extract`, `extract-interface`, `change-signature`, `move-symbol`, `rename-symbol`). If tests fail, it instantly auto-reverts all file system changes back to exactly how they were.

## Extension
Plugin-based. Features in `a-i-d-e/aide/features/`. Each requires `plugin.py`.
## Usage Patterns

### "Show me the code"
When a human asks to see code (e.g., "show me the logic", "show me the implementation"), use `read` to provide a line-numbered output. This ensures the human can mention specific line numbers in follow-up instructions.
- **Pattern**: `aide.py read <file>`

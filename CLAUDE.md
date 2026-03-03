# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -e .[dev]               # Install with dev dependencies
pytest tests/ -v                    # Run full test suite
pytest tests/features/test_move_symbol.py -v  # Run a single test file
python3 check-aide.py               # Health check
python3 scripts/install_global.py  # Install globally (aide shim + Claude Code skill + Gemini extension)
```

## Architecture

AIDE is a plugin-based CLI tool. The entry point (`aide.py`) wires up the DI container, registers language parsers, then delegates to a plugin loader that auto-discovers all feature plugins.

### Startup flow

```
aide.py
  → OsFileSystem(jailed_root=cwd)   # Path-boundary security jail
  → CompositeLanguageParser          # Registers AST/tree-sitter parsers; regex fallback
  → Context                          # DI container
  → PluginLoader                     # Walks aide/features/, loads *plugin.py files
  → args.func(args)                  # Dispatches to handler
  → JSON printed to stdout
```

### Key modules

**`aide/core/`**
- `context.py` — DI container: `context.register(Interface, impl)` / `context.resolve(Interface)`
- `domain/ports.py` — `FileSystemPort` (with transaction rollback) and `LanguageStrategy` abstractions
- `infrastructure/os_file_system.py` — `_secure_path()` enforces path jail; `start_transaction()` / `rollback()` enables `--verify` auto-revert
- `infrastructure/strategy_provider.py` — Maps file extensions to language strategies (`.kt` → Kotlin, `.ts/.tsx/.js/.jsx` → TypeScript, etc.)

**`aide/parsing/`**
- `CompositeLanguageParser` — Routes by extension to a registered specialized parser, falls back to `RegexLanguageParser`
- `AstPythonParser` — Python-specific, uses built-in `ast` module for precise nested symbol parsing
- `CSharpLanguageParser` / `RustLanguageParser` — Use tree-sitter
- `RegexLanguageParser` — Handles all other languages; pattern per language for classes, functions, interfaces, etc.
- `SymbolNode` — Core dataclass: `name`, `kind`, `line_number`, `children`

**`aide/features/`** — Seven capability domains, each containing `plugin.py` + `application/` use cases:

| Domain | Commands |
|---|---|
| `code_inspection` | `outline`, `read`, `usages`, `find-impact` |
| `code_refactoring` | `move-symbol`, `extract`, `change-signature`, `rename-symbol`, `extract-interface`, `move-package`, `move-file`, `update-references` |
| `code_generation` | `scaffold-feature`, `implement-interface`, `register-dependency`, `project-dto` |
| `code_cleanup` | `cleanup` |
| `test_generation` | `generate-tests`, `scaffold-mocks` |
| `testing_execution` | `test`, `audit-fixtures`, `test-audit` |
| `architecture_audit` | `audit` (Kotlin, Next.js, default stacks) |

All refactoring commands support `--dry-run` and `--verify` (runs tests, auto-reverts on failure).

**`aide/plugin_system/`**
- `plugin_loader.py` walks `aide/features/`, finds files named `plugin.py` or `*_plugin.py`, discovers classes ending with `"Plugin"`, and calls `plugin.register(subparsers, context)`.

### Adding a command

1. Create a Use Case class with `execute(self, ...)` in `aide/features/<domain>/application/`
2. Resolve dependencies from `Context` in the constructor
3. Bind to argparse in `aide/features/<domain>/plugin.py`
4. Update `setup-files/gemini-global-aide/SKILL.md` so agents discover it

### Testing patterns

- `tests/conftest.py` provides the `temp_dir` fixture (auto-cleaned temporary directory)
- Each test file defines its own `test_context` fixture using `OsFileSystem(jailed_root=temp_dir)` + a parser
- Tests capture stdout JSON with `capsys` and assert on the parsed payload

```python
@pytest.fixture
def test_context(temp_dir):
    fs = OsFileSystem(jailed_root=temp_dir)
    parser = RegexLanguageParser()
    return Context(file_system=fs, language_parser=parser)
```

- Core tests: `tests/core/` | Parsing: `tests/parsing/` | Features: `tests/features/`

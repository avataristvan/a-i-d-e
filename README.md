# a-i-d-e — Agent Interface for Deterministic Editing

Deterministic, test-verified refactoring for AI agents — Clean Architecture and capability-centric DDD.

## The problem

Coding agents refactor with `grep` and text edits. That works for a single file. It breaks down as soon as a change crosses file boundaries:

- A class moves to another package, and half of the imports still point at the old location.
- A function gains a parameter, and some call sites are missed because the search pattern was slightly off.
- A rename hits `UserService` but also `UserServiceTest` and a string literal that happened to match.

The agent then spends its next turns chasing compile errors it introduced itself — or worse, the breakage only shows up in a file it never looked at.

## The solution

AIDE is a CLI whose only users are agents. Instead of editing text, the agent asks AIDE to perform a structural operation, and AIDE does it deterministically:

1. **Structural, not textual.** Python is parsed with the native `ast` module, C# and Rust with tree-sitter, other languages with dedicated per-language patterns. Moves, renames and signature changes update every reference, not just the ones a search pattern found.
2. **Test-verified and atomic.** Every refactoring command accepts `--verify`: AIDE applies the change, runs the project's test suite, and reverts every touched file if a single test fails. `--dry-run` shows the plan without writing.
3. **Built for agents.** Output is structured JSON, not terminal prose, so the agent can act on results directly.
4. **Jailed.** All file access goes through a path-boundary jail. Any attempt to read or write outside the working directory aborts with a `SecurityError`.

## Installation

Requires Python 3.12+.

```bash
git clone https://github.com/avataristvan/a-i-d-e.git
cd a-i-d-e
pip install -e .
python3 scripts/install_global.py          # interactive: claude | gemini | all
```

The installer copies AIDE to `~/.local/share/aide`, creates an `aide` shim in `~/.local/bin`, and registers the agent skill:

- **Claude Code:** installs the skill to `~/.claude/skills/aide` ([source](./setup-files/claude-global-aide/SKILL.md)).
- **Gemini CLI:** prepares the extension manifest; the installer prints the two commands to copy it to `~/.gemini/extensions/aide-extension` ([source](./setup-files/gemini-global-aide/)).

**Project-local alternative:** copy the repository into your project and add [setup-files/project-injection/SKILL.md](./setup-files/project-injection/SKILL.md) to the project's agent rules.

Verify:

```bash
aide --help                # global install
python3 check-aide.py      # health check
```

## Commands

**Inspection**
- `outline` — classes, functions and symbols of a file or glob
- `read` — line-numbered file content for precise context
- `usages` — semantic usages of a symbol across the project
- `find-impact` — files and tests affected by changing a symbol
- `dead-code` — symbols without usages
- `structural-search` / `structural-replace` — pattern search and rewrite on code structure
- `symbol-blame` / `symbol-history` — git history of a single symbol

**Refactoring** (all support `--verify` and `--dry-run`)
- `move-symbol` — move a top-level function or class to another file
- `move-package` / `move-file` — move code and update all references
- `rename-symbol` — project-wide rename on word boundaries
- `change-signature` — add a parameter and update all call sites
- `extract` — extract a code block into a new function, with variable analysis
- `extract-interface` — extract an interface from a class and implement it
- `update-references` — repair references after a manual move

**Generation**
- `scaffold-feature` — domain, application and infrastructure layers for a new capability
- `implement-interface` — inject missing method stubs into a class
- `project-dto` — DTO plus 1:1 mapping function from a domain entity
- `register-dependency` — add an import and a DI binding to a registry file
- `generate-tests` / `scaffold-mocks` — test and mock scaffolding

**Quality**
- `cleanup` — unused import removal
- `audit` — architecture rules for Kotlin and Next.js stacks
- `test` — run tests and return structured JSON instead of raw traces
- `test-audit` / `audit-fixtures` — coverage gaps and unused pytest fixtures

## Supported languages

| Language | Parser | Notes |
|---|---|---|
| Python | `ast` | Precise nested symbols; AIDE refactors itself |
| Kotlin | patterns | Including `move-package`, `change-signature` and `cleanup` |
| TypeScript / JavaScript | patterns | ESM imports |
| C#, Rust | tree-sitter | |
| Go, C++, Scala, Ruby | patterns | |

## Architecture

AIDE is a plugin-based CLI built on Clean Architecture. `aide.py` wires a small DI container, registers the language parsers and loads every feature plugin under `aide/features/` (one folder per capability: inspection, refactoring, generation, cleanup, testing, audit). Adding a command means adding a use case and binding it in the capability's `plugin.py` — see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Testing

```bash
pip install -e .[dev]
pytest tests/ -v
```

## License

MIT — see [LICENSE](./LICENSE).

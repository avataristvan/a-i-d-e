# a-i-d-e
**Agent Interface for Deterministic Editing**

AIDE is a specialized CLI tool designed to empower AI Agents with deterministic code analysis, refactoring, code generation, and test execution capabilities across multiple languages (**Kotlin, TypeScript, JavaScript, Python, C#, Rust, Go, C++, Scala, Ruby**). While it runs in a standard terminal, its primary "users" are automated sub-agents.

## Navigator's Guide (Setup for Humans)

AIDE provides workflow presets to help your AI collaborators find and use it. Follow these steps to set up a new project:

1.  **Drop the folder**: Copy the `a-i-d-e/` directory into your project root.

2.  **Enable Discovery**: Copy the appropriate workflow preset into your project's `.agent` directory:
    ```bash
    mkdir -p .agent/workflows
    cp a-i-d-e/rule-presets/use-aide-host.md .agent/workflows/
    ```
3.  **Check Permissions**: Ensure the runner is executable:
    ```bash
    chmod +x a-i-d-e/aide.py
    ```

Once these steps are complete, any AI agent interacting with your repository will automatically recognize the `a-i-d-e` capabilities via the `SKILL.md` file and follow the workflow.





## Core Capabilities

- **`outline`**: structural code discovery (classes, methods, symbols).
- **`read`**: line-numbered code retrieval for precise context.
- **`cleanup`**: automated hygiene (e.g., unused import removal).
- **`audit`**: architectural health checks against stack-specific rules (Kotlin/Next.js).
- **`move-package`**: automated package refactoring with full reference updates.
- **`extract`**: extract code block to new function with variable analysis.
- **`usages`**: find semantic usages of a symbol across the project.
- **`find-impact`**: analyze imports and structure to identify all files and tests functionally impacted by a symbol change.
- **`change-signature`**: update function signatures and all call sites safely (Multi-language).
- **`move-symbol`**: move top-level functions/classes to new files (Multi-language).
- **`rename-symbol`**: rename a symbol project-wide safely using accurate word boundaries.
- **`extract-interface`**: extract a new interface from a class and automatically implement it.

> **Note:** All AIDE refactoring commands (`move-package`, `extract`, `change-signature`, `move-symbol`, `rename-symbol`, `extract-interface`) support the **`--verify`** flag. When passed, AIDE performs the refactoring, automatically executes the project test suite, and instantly auto-reverts all file changes if any tests fail—providing zero-risk atomic refactoring.

### Code & Test Generation
- **`scaffold-feature`**: deterministically scaffold Clean Architecture domain, application, and infra layers.
- **`implement-interface`**: mechanically inject missing method stubs from interfaces into concrete classes.
- **`project-dto`**: automatically generate a DTO and a 1:1 schema mapping function from a Domain Entity.
- **`register-dependency`**: safely append an import and a DI binding statement cleanly into registry files.
- **`generate-tests` & `scaffold-mocks`**: build mock topologies and output JSON scaffolding to prepare test environments.


### Agentic Test Execution
- **`test`**: wrap test execution to return structured JSON payloads to agents, filtering out noisy terminal traces.
- **`audit-fixtures`**: scan pytest setups and mathematically report unused/redundant fixtures.
- **`test-audit`**: run internal coverage tools and emit specific line gaps for agent review.

## Supported Languages

- **Kotlin**: Full refactoring support including `move-package` and `cleanup`.
- **TypeScript / JavaScript**: Native ESM support for `move-symbol`, `extract`, and `change-signature`.
- **Python**: Self-hosting ready. Supports `move-symbol`, `extract`, and `change-signature`.
- **C#, Rust, Go, C++, Scala, Ruby**: Native support for `move-symbol`, `extract`, and `change-signature`.

## Philosophy

AIDE follows a **Safe and Deterministic** philosophy. It avoids common LLM pitfalls by employing a hybrid intelligence architecture: a **Composite Language Parser** routes structurally complex languages like Python to native Abstract Syntax Tree (AST) engines (`ast`), while falling back to highly robust Regex parsers for other stacks. This ensures refactoring results are mathematically stable and machine-parsable.

### Security by Default
AIDE is designed to run autonomously on behalf of an AI agent. To prevent malicious prompt-injection or repository traversal attacks, all file operations (`read`, `extract`, `move-symbol`, `test`, etc.) are intercepted by a mandatory **Path Boundary Jail** within the core `OsFileSystem`. If an agent attempts to access files outside the current working execution directory (e.g. `/etc/passwd`), AIDE halts execution immediately with a `SecurityError`.

## Testing

AIDE is fully tested using `pytest`. To run the suite:
```bash
pytest tests/ -v
```
See `CONTRIBUTING.md` for details on adding new tests.

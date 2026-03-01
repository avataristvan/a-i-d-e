# Contributing to AIDE

Thank you for your interest in contributing to **AIDE (Agent Interface for Deterministic Editing)**!

## Identifying Missing Features and Issues

AIDE is built by agents, for agents. Since an agent's primary goal is to solve the user's problem, it may not always be obvious when AIDE falls short or lacks a feature required for a deterministic result.

To discover areas for improvement, simply ask your agent for its feedback:
```
Could you use AIDE in your last task? Did you encounter any unexpected results, or was there any functionality you missed?
```

## Out-of-Scope Decisions

To keep AIDE focused and maintainable, the following are currently out of scope:

* **Support for Python < 3.12:** I prioritize modern Python features. While agents may naturally try to offer broader compatibility, supporting versions beyond their end-of-life simply makes development more complex than it needs to be.
* **AIDE as a cross-agent bridge:** I've experimented with using AIDE as a direct communication bridge between multiple agents. However, this often led to non-deterministic behavior and has been rolled back and excluded for now.

## Architecture Guidelines

AIDE is separated into a core execution environment and a modular plugin framework:
1. **`aide/core`**: Contains the state management `Context`, which acts as a robust **Dependency Injection (DI) Container**, and agnostic infrastructure like `OsFileSystem`. 
2. **`aide/parsing`**: Defines the extraction algorithms. A `CompositeLanguageParser` dynamically routes extraction to either precise AST parsers (`AstPythonParser`) or robust regex fallbacks (`RegexLanguageParser`) depending on the language.
3. **`aide/features`**: This is where all the functionality lives! Features are plugins added dynamically.

### Adding a New Command

To add a new refactoring, code generation, or testing utility command:
1. **Create the Use Case**: Inside an appropriately named domain under `aide/features/` (e.g., `aide/features/my_cool_feature/application/my_use_case.py`), implement a Use Case class that exposes an `execute(self, ...)` method.
2. **Interact with the Context**: During registration, extract dependencies from the Context using `context.resolve(Interface)` (e.g., `context.resolve(LanguageParserPort)`) and pass them into your Use Case constructor so it executes deterministically and can be unit tested without hitting a real disk.
3. **Draft the Plugin Registry**: In the domain's `plugin.py` file, bind your new Use Case to an `argparse` SubParser. 
4. **Update Docs**: Add your new command to `SKILL.md` so that AI agents inherently discover it.

## Testing

AIDE relies heavily on deterministic operations and static parsing. Because the agents modify source code autonomously, having a robust test suite is critical.

`pytest` is used for all unit and integration testing.

### Running Tests

1. Ensure you have `pytest` installed (`pip install pytest`).
2. Run the full test suite from the repository root:
   ```bash
   pytest tests/ -v
   ```

### Writing New Tests

*   **Core Infrastructure**: Place tests for fundamental components (like `OsFileSystem` and `RegexLanguageParser`) in `tests/core/` and `tests/parsing/`.
*   **Feature Plugins**: When adding or modifying a CLI feature (like `move-symbol` or `read`), include tests in `tests/features/`. 
*   **Fixtures**: Use the `temp_dir` and `test_context` fixtures from `tests/conftest.py` in your tests to avoid permanent side-effects on the file system.

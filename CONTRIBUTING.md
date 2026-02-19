# Contributing to AIDE

Thank you for your interest in contributing to **AIDE (Agent Interface for Deterministic Editing)**!

## Testing

AIDE relies heavily on deterministic operations and regex parsing. Because we modify source code, having a robust test suite is critical.

We use `pytest` for all unit and integration testing.

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

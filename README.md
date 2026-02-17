# a-i-d-e
**Agent Interface for Deterministic Editing**

AIDE is a specialized CLI tool designed to empower AI Agents with deterministic code analysis and refactoring capabilities across multiple languages (**Kotlin, TypeScript, JavaScript, Python, C#, Rust, Go, C++, Scala, Ruby**). While it runs in a standard terminal, its primary "users" are automated sub-agents.

## Navigator's Guide (Setup for Agents)

When you include this folder in a new project, follow these steps to ensure your AI collaborators can find and use it:

1.  **Drop the folder**: Copy the `a-i-d-e/` directory into your project root.
2.  **Enable Discovery**: Copy the `use-aide.md` workflow into your project's workflow directory:
    ```bash
    mkdir -p .agent/workflows
    cp a-i-d-e/workflows/use-aide.md .agent/workflows/
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
- **`change-signature`**: update function signatures and all call sites safely (Multi-language).
- **`move-symbol`**: move top-level functions/classes to new files (Multi-language).

## Supported Languages

- **Kotlin**: Full refactoring support including `move-package` and `cleanup`.
- **TypeScript / JavaScript**: Native ESM support for `move-symbol`, `extract`, and `change-signature`.
- **Python**: Self-hosting ready. Supports `move-symbol`, `extract`, and `change-signature`.
- **C#, Rust, Go, C++, Scala, Ruby**: Native support for `move-symbol`, `extract`, and `change-signature`.

## Philosophy

AIDE follows a **Safe and Deterministic** philosophy. It avoids common LLM pitfalls by using regex-based parsing and deterministic file operations, ensuring that refactoring results are predictable and parsable for machine consumption.

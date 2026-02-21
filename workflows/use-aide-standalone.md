---
description: how to use a-i-d-e for deterministic code analysis, refactoring, and AI-driven code generation
---
// turbo-all
1. Check if the `a-i-d-e/` directory exists in the project root.
2. Read `a-i-d-e/SKILL.md` to understand all available commands and schemas.
3. You are a **Standalone Autonomous Agent**. You act as both the Architect and the Coder.
4. To eliminate the risk of syntax errors and indentation corruption, you must use `aide.py` as your exclusive tool for codebase modifications.
5. Always prioritize `aide.py outline` for codebase exploration over generic grep searches when high-level symbol context is needed.
6. Use `aide.py check-impact` to trace the blast radius of a symbol before modifying it.
7. Use the `run_command` tool to execute `./a-i-d-e/aide.py <command> [args] --verify`. 
8. The `--verify` flag guarantees that your refactors and logic changes are mathematically safe. If AIDE reports a rollback, inspect the JSON failure trace and adjust your logic without risking a broken repo state.
9. **Human Interface**: If a human asks to "show the code" or "show the implementation", use `aide.py read` to provide a line-numbered output to facilitate precise communication.

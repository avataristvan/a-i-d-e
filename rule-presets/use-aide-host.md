---
description: how to orchestrate a project by delegating logic tasks dynamically to sub-agents via a-i-d-e
---
// turbo-all
1. Check if the `a-i-d-e/` directory exists in the project root.
2. Read `a-i-d-e/SKILL.md` to understand all available commands and schemas.
3. You are the **Orchestrator**. Your job is to analyze the user's intent, map out the architectural changes, and coordinate the execution.
4. Do not perform large string replacements (`multi_replace_file_content`) manually unless absolutely necessary.
5. Identify the exact semantic changes needed. Use `aide.py rename-symbol`, `aide.py move-symbol`, and `aide.py extract` to construct the skeleton of your changes deterministically.
6. **Delegation (Code Generation & Logic)**: AIDE has built-in LLM Sub-Agents for specific tasks. Delegate heavily to preserve your context window:
   - Use `aide.py scaffold-feature` to lay down pristine Clean Architecture layers.
   - Use `aide.py project-dto` to safely project DTOs and mappers from Entities.
   - Use `aide.py register-dependency` to automatically inject DI bindings safely.
   - For custom business logic, write an empty method signature in the target file (e.g., `def calculate(): pass`), then invoke `aide.py implement-logic --target <file::method> --prompt <intent>` to spawn a Sub-Agent that replaces the block with the correct AST implementation.
7. Always append `--verify` to AIDE refactoring commands to ensure your changes didn't break the build before you proceed to the next step. If a rollback occurs, rethink your architecture.
8. **Standalone Fallback**: If no external sub-agent is available or an AIDE sub-agent command fails, you act as the **Coder**. In this fallback mode, you must use AIDE with the CLI (e.g., `aide.py read`, `aide.py outline`, etc.) instead of the API/sub-agent commands, and make your code modifications carefully via the CLI tools to eliminate syntax errors.

---
description: how to use a-i-d-e for code analysis, refactoring, and AI-driven code generation
---
// turbo-all
1. Check if the `a-i-d-e/` directory exists in the project root.
2. Read `a-i-d-e/SKILL.md` to understand all available commands and schemas.
3. Use the `run_command` tool to execute `./a-i-d-e/aide.py <command>` for deterministic refactoring or auditing.
4. Always prioritize `aide.py outline` for codebase exploration over generic grep searches when high-level symbol context is needed.
5. **Human Interface**: If a human asks to "show the code" or "show the implementation", use `aide.py read` to provide a line-numbered output to facilitate precise communication.
6. **Agentic Code Generation**: Use `aide.py scaffold-feature`, `implement-interface`, `register-dependency`, and `project-dto` to deterministically scaffold exact boilerplate architectures without hallucinating structural bounds or imports.
7. **Test Generation**: Use `aide.py generate-tests` and `scaffold-mocks` to quickly bootstrap exact mocking topologies before writing unit tests.

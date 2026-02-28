---
description: how to orchestrate a project by delegating tasks dynamically to a-i-d-e
---
// turbo-all
1. Check if the `a-i-d-e/` directory exists in the project root.
2. Read `a-i-d-e/SKILL.md` to understand all available commands and schemas.
3. **Agent Roles**: When acting as the project **Orchestrator**, your job is to analyze the user's intent and use AIDE to safely map out the architectural changes. When acting as the **Coder**, you must manually implement the custom business logic yourself.
4. **Structure vs Logic Split**: Use AIDE's deterministic tools (`move-symbol`, `rename-symbol`, `extract`) to construct the file and class skeleton of your changes. AIDE acts as your structural scalpel.
5. **Boilerplate Generation**: AIDE has built-in deterministic generators for standard architectural layers. Delegate boilerplate to save time:
   - Use `aide.py scaffold-feature` to lay down pristine Clean Architecture layers.
   - Use `aide.py project-dto` to safely project DTOs and mappers from Entities.
   - Use `aide.py register-dependency` to automatically inject DI bindings safely.
6. Always append `--verify` to AIDE refactoring commands to ensure your changes didn't break the build before you proceed to the next step. If a rollback occurs, rethink your architecture.
7. **Implementation (Custom Logic)**: AIDE handles the scaffolding, but you must write the custom business logic yourself. Use `aide.py read` and `aide.py outline` to gather structural boundaries, and then make precise code modifications directly using your native file editing tools (e.g. `replace_file_content`).
8. **Local Intelligence Sidecar**: You have access to a local reasoning engine via the `lmstudio:ask_local_model` tool. **Always run `lmstudio:verify_local_model` first** to confirm availability and credentials. If available, use it for complex code drafting, "second opinions", or summarizing large files to support your deterministic work with AIDE.

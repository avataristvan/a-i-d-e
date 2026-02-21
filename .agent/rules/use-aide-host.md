---
description: how to orchestrate a project by delegating logic tasks dynamically to sub-agents via a-i-d-e
---
// turbo-all
1. Check if the `a-i-d-e/` directory exists in the project root.
2. Read `a-i-d-e/SKILL.md` to understand all available commands and schemas.
3. You are the **Orchestrator**. Your job is to analyze the user's intent, map out the architectural changes, and coordinate the execution.
4. Do not perform large string replacements (`multi_replace_file_content`) manually unless absolutely necessary.
5. Identify the exact semantic changes needed. Use `aide.py rename-symbol`, `aide.py move-symbol`, and `aide.py extract` to construct the skeleton of your changes deterministically.
6. **Delegation**: When logic needs to be written inside a function, construct the empty function signature deterministically using AIDE generators. Then, use `aide.py implement-logic --target <file::method> --prompt <intent>` to spawn a Sub-Agent to write the isolated business logic.
7. Always append `--verify` to AIDE refactoring commands to ensure your changes didn't break the build before you proceed to the next step. If a rollback occurs, rethink your architecture.
8. **Sub-Agent Configuration**: You can configure AIDE to use a specific fast sub-agent model via environment variables. For **Gemini 2.0 Flash** (highly recommended for performance), set `GEMINI_API_KEY`. For OpenAI, use `AIDE_LLM_API_KEY` and `AIDE_LLM_MODEL`.

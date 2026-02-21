# Context Provisioning

In a strict Hierarchical (or "Brain in a Vat") multi-agent system like AIDE, the sub-agents (LLMs) do not have direct access to the filesystem, network, or external tools. They operate entirely based on the text prompt provided to them at execution time.

Therefore, the quality, safety, and correctness of the generated code depend entirely on the **Context Provisioning** mechanism.

In AIDE, this mechanism is centralized within the `BriefingService`.

---

## The BriefingService

The `BriefingService` acts as the sensory input for the sub-agents. Before a sub-agent is spawned to write code, design a DTO, or scaffold a feature, the orchestration layer calls the `BriefingService` to gather three critical pieces of context:

1.  **Persona Rules**
2.  **Dependency Context**
3.  **Symbol Maps (Architectural Briefing)**

These inputs form the "System Prompt" that defines the rules of engagement and the environment for the LLM.

### 1. Persona Rules: Hierarchical Fallbacks

Rules dictate *how* the agent should write code (e.g., "Use functional patterns," "Always add docstrings," "Prefer tabs over spaces"). AIDE loads these rules hierarchically to ensure global standards don't overwrite project-specific needs.

The `BriefingService` looks for instructions in the following order of precedence:

1.  **Environment Variable Override:** If `AIDE_RULES_PATH` is set, it reads that file first. This allows developers to enforce personal or organizational coding standards globally across all projects.
2.  **Project-Specific Workflows:** If no environment variable is set, it looks for `./workflows/use-aide-tool.md` in the project root. This file is intended for project-specific instructions (e.g., "In this repo, we use React Query for data fetching").
3.  **Default Fallback:** A basic instruction to generate functional code if no specific rules are found.

### 2. Dependency Context Awareness

LLMs often hallucinate package versions or use deprecated APIs because they don't know what libraries are actually installed in the project they are modifying.

The `BriefingService` mitigates this by aggressively scanning the project root for common dependency management files. It extracts the raw text (or specific fragments) and injects them directly into the agent's prompt.

Currently, AIDE automatically scans and injects context from:
-   **NPM / Node.js:** Extracts the `dependencies` block from `package.json`.
-   **Python:** Injects the contents of `requirements.txt` and `pyproject.toml`.
-   **Kotlin / Android:** Injects snippets from `build.gradle`, `build.gradle.kts`, and `gradle/libs.versions.toml`.

By providing this data, the sub-agent knows exactly which version of a library to target, reducing the chance of generating incompatible syntax.

### 3. Symbol Maps (Architectural Briefing)

When modifying an existing file, an LLM acting as a "Brain in a Vat" needs to know what other methods and classes exist in that file to avoid redefining them, or to properly invoke them.

Instead of passing the entire, potentially massive file content to the LLM (which wastes tokens and context window), AIDE provides an **Architectural Briefing**.

Using the `LanguageParserPort` (which leverages native AST parsers like Python's `ast` module), the `BriefingService` constructs a high-level hierarchical outline of the file.

**Example Outline:**
```
- Class: UserService
  - Method: __init__
  - Method: get_user_by_id
  - Method: delete_user
- Function: helper_format_name
```

This outline is injected into the prompt. The agent can now see the "shape" of the file and reference existing architecture without needing the raw source code of every method.

---

## Conclusion

By centralizing and automating the injection of Rules, Dependencies, and Symbol Maps, AIDE guarantees that its isolated sub-agents possess the maximum exact context required to succeed, heavily minimizing hallucinations and syntax errors while preserving absolute security.

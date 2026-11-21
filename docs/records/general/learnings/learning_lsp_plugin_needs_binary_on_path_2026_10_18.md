type: learning
topic: general
perspective: agent
created: 1792346501.158707
cue: Setting up or enabling an LSP plugin for a project.
---

Observed: An enabled LSP plugin without its server binary on PATH fails only at the first call (ENOENT), not at enable time.
Cause: The plugin only spawns the server on first use, so a missing binary is not detected earlier.
Evidence: Experience while setting up pyright-lsp on 2026-10-18; check the binary (e.g. `pyright --version`) when setting up.

## Edges

- related: [learning_pyright_lsp_replaces_intellij_tools_2026_10_18](learning_pyright_lsp_replaces_intellij_tools_2026_10_18.md)

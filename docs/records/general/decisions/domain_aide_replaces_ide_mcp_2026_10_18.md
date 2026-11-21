type: domain
topic: general
perspective: user
created: 1792346500.761749
cue: Deciding whether a new capability belongs in AIDE or is already covered by LSP or an IDE integration.
---

Decision: AIDE's direction is to fully replace an IDE MCP server (IntelliJ) for agent work, together with Claude Code's LSP tool. LSP covers symbol search, hover, references and diagnostics; AIDE covers deterministic multi-file refactoring with --verify.
Why: No paid IDE subscription, no dependency on a running IDE, and the stack stays free for commercial use.
Scope: Feature scoping for AIDE. Do not build in AIDE what LSP already provides; build what LSP cannot do (verified, multi-file refactoring).

## Edges

- derived_from: [learning_pyright_lsp_replaces_intellij_tools_2026_10_18](../learnings/learning_pyright_lsp_replaces_intellij_tools_2026_10_18.md)
- related: [domain_aide_ts_esm_moves_own_scanner_not_lsp_2026_11_20](domain_aide_ts_esm_moves_own_scanner_not_lsp_2026_11_20.md)
- related: [domain_aide_ts_rename_via_project_typescript_languageservice_2026_11_21](domain_aide_ts_rename_via_project_typescript_languageservice_2026_11_21.md)

type: learning
topic: general
perspective: agent
created: 1792346500.974804
cue: Reaching for IntelliJ MCP tools in this repo, or getting an empty workspaceSymbol result from the LSP tool.
---

Observed: In this repo pyright-LSP replaces the IntelliJ tools: search_symbol -> workspaceSymbol, get_symbol_info -> hover, usages -> findReferences (more precise than grep), get_file_problems -> diagnostics after edits or `pyright aide/` (about 2.5s, no IDE). workspaceSymbol returns nothing until the server has indexed; touch one file first.
Cause: The LSP server indexes lazily, so the first workspace-wide query sees an empty index.
Evidence: Test on 2026-10-18 against StrategyProviderPort (33 references in 15 files); plugin pyright-lsp@claude-plugins-official enabled in .claude/settings.json.

## Edges

- related: [domain_aide_replaces_ide_mcp_2026_10_18](../decisions/domain_aide_replaces_ide_mcp_2026_10_18.md)

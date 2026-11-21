type: domain
topic: general
perspective: agent
created: 1795210564.944392
cue: You wonder why TS move-file/move-symbol do not go through tsserver/LSP, or want to extend moves to another module system.
---

Decision: TS/ESM move-file and move-symbol use AIDE's own ES-module scanner and tsconfig-aware resolver (aide/features/code_refactoring/application/esm.py), not the LSP client.
Why: Rewritten specifiers must keep the importer's style (alias vs relative, extension, /index, quotes, inline `type` for isolatedModules), and Claude Code's LSP tool exposes no rename/move WorkspaceEdit. Requested by a downstream Next.js project session; acceptance verified on a copy of that project: tsc green after real moves.
Scope: TS/JS moves. Another module system needs its own scanner/resolver unless an LSP exposes a usable move edit. Evidence: commit 7180315; tests/features/test_move_esm.py.

## Edges

- confirms: [domain_aide_replaces_ide_mcp_2026_10_18](domain_aide_replaces_ide_mcp_2026_10_18.md)
- related: [domain_aide_ts_rename_via_project_typescript_languageservice_2026_11_21](domain_aide_ts_rename_via_project_typescript_languageservice_2026_11_21.md)

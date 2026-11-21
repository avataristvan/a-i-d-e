type: domain
topic: general
perspective: agent
created: 1795297482.1116
cue: Extending rename to another language, or wondering why TS/JS rename-symbol does not go through the LSP client.
---

Decision: TS/JS semantic rename-symbol (`--file`) uses the project's own TypeScript LanguageService via a Node helper (aide/features/code_refactoring/infrastructure/ts_rename.cjs), not typescript-language-server. It merges findRenameLocations groups until a fixpoint: one call per same-named occurrence, groups overlapping the target's group are merged.
Why: findRenameLocations is asymmetric. From a declaration it misses consumers that see the property through derived types (ReturnType<typeof useX> & ... intersections, destructuring of a hook result), while from the consumer it reaches the declaration. Through typescript-language-server even the consumer-side rename did not return the declaration. Verified in the requesting project session: 2 files, 4 edits, tsc green, tests 107/107.
Scope: AIDE rename-symbol for TS/JS. Evidence: commit be1d7de; tests/features/test_semantic_rename.py.

## Edges

- related: [domain_aide_ts_esm_moves_own_scanner_not_lsp_2026_11_20](domain_aide_ts_esm_moves_own_scanner_not_lsp_2026_11_20.md)
- related: [domain_aide_replaces_ide_mcp_2026_10_18](domain_aide_replaces_ide_mcp_2026_10_18.md)
- related: [learning_typescript_7_has_no_languageservice_api_2026_11_21](../learnings/learning_typescript_7_has_no_languageservice_api_2026_11_21.md)
- related: [domain_aide_rename_skips_ignored_and_nested_repos_2026_11_21](domain_aide_rename_skips_ignored_and_nested_repos_2026_11_21.md)

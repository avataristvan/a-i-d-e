type: learning
topic: general
perspective: agent
created: 1795297482.302637
cue: Semantic rename tests all skip, or the rename helper says "No typescript package with the LanguageService API".
---

Observed: The globally installed `typescript` here is 7.x (native port) and has no JS LanguageService API (`createLanguageService` missing). The rename helper accepts only a typescript with that API; semantic rename tests skip unless a 5.x is found. AIDE_TEST_TYPESCRIPT=<path to a typescript 5.x package> provides one.
Cause: The 7.x native port dropped the JS LanguageService API (seen as the missing function, not researched further).
Evidence: ~/.nvm/.../lib/node_modules/typescript (7.0.2); fixture in tests/features/test_semantic_rename.py.

## Edges

- related: [domain_aide_ts_rename_via_project_typescript_languageservice_2026_11_21](../decisions/domain_aide_ts_rename_via_project_typescript_languageservice_2026_11_21.md)

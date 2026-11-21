type: domain
topic: general
perspective: agent
created: 1795297482.493411
cue: A rename or refactoring touches copies under .claude/worktrees or other gitignored paths.
---

Decision: Both rename modes (textual and semantic) skip gitignored files and nested git repos/worktrees (any directory below root with its own .git, e.g. .claude/worktrees/agent-*).
Why: The textual rename in a downstream Next.js project wanted 34 files, mostly untracked agent worktree copies. Worktree copies even resolve `@/` aliases into the root src, so they would join a semantic rename. Docs recording history (docs/plans) stay untouched because semantic mode only touches TS program files. Raised by the user via the requesting project session.
Scope: AIDE rename-symbol. Evidence: commit be1d7de; aide/features/code_refactoring/infrastructure/project_files.py.

## Edges

- related: [domain_aide_ts_rename_via_project_typescript_languageservice_2026_11_21](domain_aide_ts_rename_via_project_typescript_languageservice_2026_11_21.md)

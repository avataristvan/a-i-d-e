type: domain
topic: general
perspective: user
created: 1795297526.269362
cue: Wondering how AIDE reaches Claude Code or a terminal, or tempted to reinstall a global aide shim or skill.
---

Decision: AIDE is delivered to Claude Code as a per-project plugin (aide@aide), not as a global install. The global shim, skill and copy (~/.local/bin/aide, ~/.claude/skills/aide, ~/.local/share/aide) were removed. For the terminal, a ~/.bashrc alias guarded by `[ -z "$CLAUDECODE" ]` is used, because Claude Code reads .bashrc aliases into its Bash sessions and an unguarded alias would make aide visible in every project.
Why: Per-project activation, and the plugin's bin/ runs the live repo, so there is no installed-copy drift. Checked with headless sessions: a project with the plugin enabled resolves aide to the repo's bin/aide, a project without it has no aide.
Scope: AIDE delivery on this machine. Evidence: ~/.bashrc; the enabling project's .claude/settings.json.

## Edges

- supersedes: [learning_aide_global_shim_runs_installed_copy_2026_11_20](../learnings/learning_aide_global_shim_runs_installed_copy_2026_11_20.md)
- derived_from: [learning_plugin_bin_on_path_only_where_plugin_enabled_2026_11_21](../learnings/learning_plugin_bin_on_path_only_where_plugin_enabled_2026_11_21.md)

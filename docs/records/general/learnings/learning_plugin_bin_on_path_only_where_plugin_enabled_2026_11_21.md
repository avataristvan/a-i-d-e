type: learning
topic: general
perspective: agent
created: 1795297482.686247
cue: Shipping a CLI through a Claude Code plugin, or deciding whether the global install script is still needed.
---

Observed: Claude Code adds an enabled plugin's `bin/` to the Bash tool PATH only in projects where the plugin is enabled. For a directory-source marketplace it uses the source directory (live repo), not the plugin cache copy, appended after ~/.local/bin. A global shim of the same name (~/.local/bin/aide) therefore shadows the plugin's command.
Cause: PATH order (plugin bin appended last); seen directly, not read from docs.
Evidence: headless sessions 2026-11-21: a project with the plugin enabled (PATH has <repo>/bin) vs a project without it (not enabled, no entry).

## Edges

- related: [learning_aide_global_shim_runs_installed_copy_2026_11_20](learning_aide_global_shim_runs_installed_copy_2026_11_20.md)
- related: [domain_aide_delivered_as_per_project_plugin_not_global_install_2026_11_21](../decisions/domain_aide_delivered_as_per_project_plugin_not_global_install_2026_11_21.md)
- related: [learning_plugin_skill_loads_from_cache_copy_needs_version_bump_2026_11_22](learning_plugin_skill_loads_from_cache_copy_needs_version_bump_2026_11_22.md)

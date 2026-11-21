type: learning
topic: general
perspective: agent
created: 1795210565.148967
valid_until: 1795297526.467915
cue: A feature is done in the repo but another project session still sees the old aide behaviour.
---

Observed: The global `aide` shim (~/.local/bin/aide) runs a copy in ~/.local/share/aide, not the repo. Changes reach other projects only after `python3 scripts/install_global.py <claude|gemini|all>`. Without an argument the installer blocks on an interactive prompt (EOFError in non-interactive shells).
Cause: The installer copies the repo; prompt_target falls back to input() when argv[1] is missing.
Evidence: scripts/install_global.py (prompt_target, argv[1]).

## Edges

- related: [antipattern_source_vs_installed_drift](../../../../../../docs/records/general/decisions/antipattern_source_vs_installed_drift.md)
- related: [learning_plugin_bin_on_path_only_where_plugin_enabled_2026_11_21](learning_plugin_bin_on_path_only_where_plugin_enabled_2026_11_21.md)
- superseded_by: [domain_aide_delivered_as_per_project_plugin_not_global_install_2026_11_21](../decisions/domain_aide_delivered_as_per_project_plugin_not_global_install_2026_11_21.md)

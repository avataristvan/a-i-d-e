type: learning
topic: general
perspective: agent
created: 1795305102.637689
cue: Changed a Claude Code plugin skill text and sessions still show the old one.
---

Observed: A Claude Code plugin's skills are loaded from the plugin cache copy (~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/), while its bin/ runs from the source directory for a directory marketplace. Changes to the command itself are live; a skill text change is not.
Cause: Cache copy is keyed by version. To get a skill change into sessions: bump the version in .claude-plugin/plugin.json, run `claude plugin marketplace update <mp>`, then `claude plugin update <plugin>@<mp>`, then restart open sessions.
Evidence: cache aide/0.1.0 skill 8405 bytes vs aide/0.1.1 1457 bytes after the update (2026-11-22).

## Edges

- related: [learning_plugin_bin_on_path_only_where_plugin_enabled_2026_11_21](learning_plugin_bin_on_path_only_where_plugin_enabled_2026_11_21.md)
- related: [domain_aide_delivered_as_per_project_plugin_not_global_install_2026_11_21](../decisions/domain_aide_delivered_as_per_project_plugin_not_global_install_2026_11_21.md)

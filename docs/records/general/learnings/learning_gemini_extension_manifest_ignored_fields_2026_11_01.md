type: learning
topic: general
perspective: agent
created: 1793564328.348447
cue: Touching the Gemini install path or claiming Gemini support for AIDE.
---

Observed: setup-files/gemini-global-aide/gemini-extension.json is invalid in substance: Gemini CLI reads only name, version, description, mcpServers, contextFileName (and settings/excludeTools). entrypoint, capabilities and skill_source are ignored, so neither the command list nor SKILL.md ever reached Gemini. It also lacks about 10 newer commands.
Cause: Not noticed because Gemini CLI is not installed on this machine, so the install path was never exercised. Field list per https://geminicli.com/docs/extensions/reference/.
Evidence: setup-files/gemini-global-aide/gemini-extension.json, scripts/install_global.py.

## Edges

- related: [domain_aide_skill_texts_list_no_commands_cli_discovery_2026_11_22](../decisions/domain_aide_skill_texts_list_no_commands_cli_discovery_2026_11_22.md)

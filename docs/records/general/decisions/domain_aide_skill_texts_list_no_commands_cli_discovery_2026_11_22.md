type: domain
topic: general
perspective: user
created: 1795305102.425049
cue: Adding an AIDE command, or tempted to document commands in a SKILL.md or context file.
---

Decision: AIDE's skill/context texts (Claude skill, Gemini context file, project-injection SKILL.md) list no commands. They give only the entry points (JSON format, refactoring workflow, five common commands). Agents discover commands through the CLI: `aide commands` (categories = feature folders), `aide commands <category>` (commands with their argparse one-line help), `aide <command> --help` (arguments plus usage notes attached via add_notes()). Categories and one-liners are derived from what the plugins register, so nothing is hand-kept.
Why: The full command lists were permanent context load (Claude skill 8.4 KB, Gemini context 6.3 KB, loaded in every session; always-loaded description 623 chars) and the hand-kept lists drifted. Now about 1.5 KB each and 318 chars. Same pattern the user applied in mcp-kdenlive (category drill-down).
Scope: a-i-d-e skill and context texts; "Adding a command" step 4 in CLAUDE.md. Evidence: commit 32f20a2, tests/plugin_system/test_command_catalog.py.

## Edges

- related: [learning_gemini_extension_manifest_ignored_fields_2026_11_01](../learnings/learning_gemini_extension_manifest_ignored_fields_2026_11_01.md)
- related: [idea_clone_symbol_command](../learnings/idea_clone_symbol_command.md)

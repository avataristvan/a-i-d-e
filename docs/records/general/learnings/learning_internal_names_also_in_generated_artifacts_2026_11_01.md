type: learning
topic: general
perspective: agent
created: 1793564328.169089
cue: Polishing a repo or making it public, when checking for leaked personal or local information.
---

Observed: The internal-names rule also covers generated artifacts: .report.json (local absolute paths) and aide_cli.egg-info/PKG-INFO (a person's name) were tracked in the public repo, along with output.txt and pytest.pid. Fixed in a264339 by untracking and gitignoring.
Cause: Reviews looked at source and help strings only; generated files were tracked unnoticed.
Evidence: commit a264339; related records [antipattern_internal_names_in_oss](../decisions/antipattern_internal_names_in_oss.md), [learning_internal_names_also_in_code_strings_2026_10_18](learning_internal_names_also_in_code_strings_2026_10_18.md). Check `git ls-files` for generated files before going public.

## Edges

- confirms: [antipattern_internal_names_in_oss](../decisions/antipattern_internal_names_in_oss.md)
- related: [learning_internal_names_also_in_code_strings_2026_10_18](learning_internal_names_also_in_code_strings_2026_10_18.md)

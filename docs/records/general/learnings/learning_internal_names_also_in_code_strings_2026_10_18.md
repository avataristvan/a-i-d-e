type: learning
topic: general
perspective: user
created: 1792346502.204116
cue: Writing rule names, example package names or help texts in code of the public repo.
---

Observed: The rule in [antipattern_internal_names_in_oss](../decisions/antipattern_internal_names_in_oss.md) also covers code strings and help texts (rule names, example package names, references to local tools), not only docs and examples. On 2026-10-18 three spots were neutralised.
Cause: Internal names leaked in through string literals that are easy to overlook in a docs-only review.
Evidence: aide/features/architecture_audit/application/audit_nextjs.py, aide/features/code_refactoring/plugin.py, setup-files/project-injection/use-aide-host.md.

## Edges

- confirms: [antipattern_internal_names_in_oss](../decisions/antipattern_internal_names_in_oss.md)
- related: [learning_internal_names_also_in_generated_artifacts_2026_11_01](learning_internal_names_also_in_generated_artifacts_2026_11_01.md)

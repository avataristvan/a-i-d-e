type: anti-pattern
topic: general
perspective: user
created: 1783085194.030458
cue: Writing examples, test data or help text in the public repo and tempted to use a real project name.
---

Tried: Keeping internal project names (e.g. "MyApp" standing in for a real private project) as example values in an open-source repo.
Failed because: Internal cross-references polluted the codebase and design discussions; it is hard to see the general solution through the project-specific noise.
Instead: Use neutral placeholders (my-app, my-project) in all examples in the public repo. Internal setups stay local and are not committed.

## Edges

- related: [learning_internal_names_also_in_code_strings_2026_10_18](../learnings/learning_internal_names_also_in_code_strings_2026_10_18.md)
- related: [learning_internal_names_also_in_generated_artifacts_2026_11_01](../learnings/learning_internal_names_also_in_generated_artifacts_2026_11_01.md)

type: domain
topic: general
perspective: user
created: 1793564327.984782
cue: Updating README.md, e.g. after the LSP or clone-symbol work lands, and deciding what to list.
---

Decision: The public README is ordered problem first (agent grep/edit refactoring breaks imports and call sites), then the solution, then installation. It lists only commands present in the committed HEAD, not uncommitted work.
Why: The user wants the repo to read as a solution to a concrete problem, and the README must not promise what a clone does not contain.
Scope: README.md of a-i-d-e. Evidence: README.md at a264339.

## Edges

- related: [domain_aide_public_name_agent_interface_deterministic_editing_2026_11_01](domain_aide_public_name_agent_interface_deterministic_editing_2026_11_01.md)

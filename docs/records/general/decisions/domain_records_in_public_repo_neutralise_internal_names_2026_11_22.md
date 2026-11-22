type: domain
topic: general
perspective: user
created: 1795305103.063108
cue: Committing records or tests that came from a downstream project request, or about to push.
---

Decision: docs/records is tracked in the public a-i-d-e repo. Internal project names and home paths are neutralised in records (e.g. "a downstream Next.js project", "<repo>/bin"), and so is context about what the requesting project was doing, which carries nothing about AIDE. Test fixtures modelled on a downstream case use neutral identifiers too.
Why: The public repo must not carry internal cross-references; records and fixtures are as public as code.
Scope: records, test fixtures, commit messages. Before a push: grep the unpushed diff and commit messages for internal names. Evidence: commits 1293561 (records), 0affa0b (neutral fixture names).

## Edges

- confirms: [antipattern_internal_names_in_oss](antipattern_internal_names_in_oss.md)

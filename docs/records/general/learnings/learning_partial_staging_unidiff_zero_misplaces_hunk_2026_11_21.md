type: learning
topic: general
perspective: agent
created: 1795297482.879503
cue: Committing one feature out of a working tree full of other uncommitted work, or about to use git apply --cached --unidiff-zero.
---

Observed: Partial staging of mixed WIP files with `git apply --cached --unidiff-zero` placed a zero-context hunk inside the wrong function (plugin.py), breaking 3 tests in the commit snapshot while the working tree was green.
Cause: Zero context gives git no anchor, so the hunk landed at a matching line number in a different function (inferred from the result).
Evidence: commit be1d7de. Fix that worked: build the staged file from HEAD plus targeted replacements, then run the tests on `git checkout-index -a --prefix=<dir>`.

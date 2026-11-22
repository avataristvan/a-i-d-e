type: learning
topic: general
perspective: reviewer
created: 1795305102.851518
cue: Writing or changing code that finds where a source declaration ends (bracket balance, symbol range).
---

Observed: Applying the combined-bracket rule with "terminate as soon as the stack returns to empty" in KotlinLanguageStrategy.find_symbol_range regressed every annotated symbol (`@Composable` then `fun Foo() {...}` returned only the annotation line) and headers whose body starts on a later line (`class Foo` then `  : Bar() {`). move-symbol, extract and clone-symbol broke while the suite stayed green, because no test had annotated or continued headers. A /simplify quality reviewer subagent found it before the commit.
Cause: The early-termination rule is incomplete: an empty stack does not mean the declaration is over when only an annotation or an unfinished header has been seen.
Evidence: commit 64716dc; tests/core/test_declaration_extent.py. Fix: shared helper aide/core/domain/declaration_extent.py (find_declaration_end) skips annotation-only and comment lines, and continues when a balanced line ends with `:`/`=`/`,`/`(`/`->`/`.` or the next code line starts with `:`/`{`/`=`/`.`/`->`. The Kotlin strategy and clone-symbol both use it.

## Edges

- related: [the-coder_combined-bracket-balance-not-single-type](../decisions/the-coder_combined-bracket-balance-not-single-type.md)

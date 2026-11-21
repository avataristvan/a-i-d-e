type: pattern
topic: general
perspective: the-coder
created: 1788690742.648333
---

Rule: When writing a bracket-balance scanner to find the end of a source-code declaration, balance ALL bracket types together (`{}`, `()`, `[]`) in one stack/counter, not just the one the language's block bodies use (e.g. `{}`).
Why: A brace-only balance treats a brace-less single-line/statement declaration (e.g. Kotlin `data class Foo(val x: Int)` with no body) as never having "opened", so the scanner keeps walking forward through unrelated later code until it stumbles on the NEXT unrelated `{...}` pair anywhere in the file — and silently treats that as the declaration's own body, swallowing everything in between. Found in AIDE's `KotlinLanguageStrategy.find_symbol_range` (aide/parsing/infrastructure/kotlin_strategy.py) while implementing a `clone-symbol` feature: cloning a bodyless `data class TargetTempo(...)` followed later in the same file by an unrelated `fun TargetTempo.next() { ... }` caused the class's "range" to balloon to include everything up to `next()`'s closing brace.
How to apply: prefer a combined-bracket stack that terminates as soon as it returns to empty, rather than a single counter keyed to one bracket type. This also naturally handles the zero-brackets case (a bare `class Foo`) without a separate flag.
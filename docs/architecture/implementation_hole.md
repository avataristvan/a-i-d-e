# The "Implementation Agent" Hole

The current iteration of `implement-logic` in AIDE attempts to solve the "Brain in a Vat" problem by:
1. Using an AST strategy to find the bounds of a function.
2. Giving the LLM the function signature.
3. Asking the LLM for *only* the inner body.
4. Using string heuristics to splice that body back into the file.

### Why this is failing (The Hole)
The splicing heuristic (`new_block = [full_block[0]] ... new_block.append(full_block[-1])`) makes lethal assumptions:
- **Assumption 1**: The function signature is exactly one line. (Fails in React, modern Python type hinting, builder patterns).
- **Assumption 2**: The closing token is exactly `}` on its own line. (Fails for closures, inline functions, arrow functions).
- **Assumption 3**: The LLM understands the exact base indentation required just by looking at a number in the prompt.

When these assumptions fail, AIDE injects malformed syntax, the test runner fails, the transaction rolls back, and AIDE enters a doomed recursion loop because the LLM keeps outputting correct *logic* but AIDE keeps *splicing* it incorrectly.

### The Solution: Whole-Symbol Output
Instead of asking the LLM for only the "inner body" and trying to splice it manually:

1. Give the LLM the **entire symbol block** (signature + body + braces).
2. Ask the LLM to return the **entire replacement block**.
3. AIDE replaces lines `start_line` to `end_line` exactly with the LLM's output.

This pushes the syntax responsibility (brace matching, multi-line signature preservation) to the LLM (which is excellent at syntax) and removes the brittle regex/string heuristics from AIDE's Python core.

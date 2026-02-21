# Deterministic Execution & Verification

AIDE relies on the "Hierarchical" or "Supervisor/Worker" architectural pattern. The core AIDE orchestrator (`aide.py`) acts as the deterministic Supervisor. It holds all the power, dictates the context, and manages the execution environment.

The LLMs (Sub-Agents) are treated as pure "Workers." They receive context, process the request, and generate text (code). They do not run commands, they do not read files directly, and they do not have internet access.

This separation of concerns enables AIDE to provide **Deterministic Execution** and a **Self-Correcting Verification Loop**.

## Secure Code Injection

When an LLM sub-agent generates the required logic or implementation, it passes back a raw string of text. Because LLMs are inherently non-deterministic, they may hallucinate syntax, include unwanted markdown blocks, or format the text incorrectly.

AIDE handles this reliably using two key mechanisms:

1.  **Format Stripping:** The Supervisor automatically cleans the LLM's response, stripping away conversational filler, ````python` markdown markers, and ensuring only raw, parsable code remains.
2.  **Contextual Splicing:** Rather than replacing a whole file based on an LLM guess, AIDE only identifies the exact boundary of the symbol being modified (e.g., `def my_function():`). It calculates the exact indentation, splices the raw code into that specific boundary, and re-writes the whole file securely.

## The OsFileSystem Jail

Before AIDE even attempts to write the new code to disk, the `OsFileSystem` infrastructure component enforces a **Security Jail**.

-   **Path Traversal Protection:** The file system operations mathematically verify that any target file path strictly resolves within the bounds of the project root (the "jailed root").
-   If an LLM hallucinates and tries to output code to `../../etc/passwd`, AIDE's deterministic core instantly aborts the operation and prevents the traversal attack.

## The Verification Loop

The most powerful feature of AIDE's execution environment is the Verification Loop.

Because LLM logic is unpredictable, modifying a file directly is dangerous. AIDE mitigates this by applying a transactional approach to file modifications when the `--verify` flag is used.

### How `--verify` Works

1.  **Start Transaction:** Before any LLM code is spliced into the file, AIDE records the file's current state and begins a secure transaction in memory.
2.  **Code Injection:** The LLM's output is cleaned and written to disk.
3.  **Test Execution:** AIDE automatically executes the project's test suite (e.g., `pytest`, `npm test`, `./gradlew test`) to validate the new logic.
4.  **Mathematical Decision:**
    *   **Success (Exit Code 0):** If the tests pass, AIDE assumes the LLM's logic is mathematically sound. It **commits** the transaction, making the changes permanent.
    *   **Failure (Exit Code > 0):** If the new code causes syntax errors or test failures, AIDE instantly **rolls back** the transaction, restoring the file to its original state.

### Self-Correction

When a verification fails, AIDE captures the exact error trace outputted by the test runner (e.g., the specific `pytest` traceback). It formats this failure trace into a highly structured JSON report.

This report is fed back to the orchestrator, which constructs a new, specialized prompt containing:
1.  The failed code.
2.  The exact error trace.
3.  Instructions to fix the specific failure.

A brand new Sub-Agent is spawned with this context. It analyzes the error, hallucinates a new fix, and the transaction cycle begins again. This process repeats until the math holds true or the system limits are reached, resulting in a fully autonomous, self-correcting agent loop.

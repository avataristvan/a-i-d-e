# Autonomous Agent Architectures

When multiple autonomous agents work together on a single project, they are typically bound together using one of several architectural patterns. The choice of pattern relies heavily on the required degree of autonomy, the complexity of the task, and the necessary safeguards (sandboxing/security). 

The following are the four most common paradigms for integrating multi-agent systems.

---

## 1. Hierarchical (Supervisor / Worker)

This is the most predictable and structured pattern—**and it lies at the core of AIDE’s design**.

- **How it works:** A deterministic "Supervisor" agent (or orchestrator script) understands the macro-objective. It breaks the objective down into smaller, highly specialized tasks and spawns temporary "Worker" sub-agents to execute them.
- **The Binding:** The Supervisor controls the **Context** (what information the worker is allowed to see) and the **Output** (what action is taken based on the worker's result). The workers do not communicate with each other; they only report to the Supervisor.
- **Pros:** Extremely secure, predictable, and easy to rollback. "Hallucinations" are contained.
- **Cons:** Less autonomous and reliant on the Supervisor's ability to perfectly partition tasks.

## 2. Sequential (Pipelines)

Often used for content generation, data transformation, or strict factory-like workflows.

- **How it works:** Agents pass their outputs to the next agent down the line in a unidirectional flow. 
- **The Binding:** Data schemas and API contracts. Agent A is structurally bound to Agent B by a strict definition of what the intermittent data format should look like (e.g., structured JSON).
- **Example:** A "Researcher Agent" browses the web and outputs a JSON summary. A "Coder Agent" parses that JSON and writes an implementation. A "Reviewer Agent" analyzes the code for style and syntax.

## 3. Shared Workspace (Blackboard Pattern)

This pattern is deployed when agents need to be highly autonomous and collaborative, reacting to states rather than explicit commands.

- **How it works:** Multiple agents have concurrent access to a shared environment (like a GitHub repository, a shared database, or a simulated "blackboard"). They do not pass messages directly. Instead, they observe state changes in the environment and react accordingly.
- **The Binding:** The shared state environment itself. 
- **Example:** Agent A writes a pull request, modifying the shared environment. Agent B (a tester) observes the open PR, pulls the code, runs tests, and leaves a comment. Agent A reads the comment and pushes a fix.

## 4. Direct Communication (Swarm / Multi-Agent Chat)

The most experimental and conversational pattern (popularized by experimental frameworks like AutoGen or CrewAI).

- **How it works:** Agents are instantiated in a simulated chat room with distinct personas (e.g., "Senior Architect", "Junior Developer", "QA Engineer"). They converse dynamically to arrive at a solution.
- **The Binding:** Message passing protocols and turn-taking logic. A router or "speaker selection" algorithm determines which agent should speak next based on conversation history.
- **Pros:** Can handle highly ambiguous tasks requiring brainstorming.
- **Cons:** Very difficult to control, prone to endless loops, and highly non-deterministic.

---

## The AIDE Approach: "Brain in a Vat"

AIDE explicitly rejects the "Shared Workspace" and "Swarm" patterns in favor of a strictly **Hierarchical** approach. 

### Why? Security and Determinism.

In AIDE, sub-agents (the LLMs) have **no direct filesystem access**. This is a deliberate "Brain in a Vat" design. 

Instead of letting agents roam free in a shared workspace where they could accidentally delete files or corrupt the project state, AIDE binds the agent strictly through the `LlmProvider` and `BriefingService`. 

1. **Sensory Input:** AIDE feeds the agent hyper-specific context (the exact file content, the dependencies, the rules, and a symbol map of the architecture).
2. **Motor Output:** The agent returns a pure text string containing code. 
3. **Execution:** AIDE's deterministic core (the Supervisor) handles the "dangerous" part—splicing the code into the file, tracking the transaction, and running the verification tests. 

If the agent hallucinates, AIDE catches the verification failure, rolls back the transaction, and the codebase remains untouched.

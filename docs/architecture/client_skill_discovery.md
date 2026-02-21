# Client Skill Discovery: How Agents Learn AIDE

When a Client Agent (such as an IDE assistant, a chatbot, or an AI running in LM Studio) connects to a project, it needs to know what tools are at its disposal. 

If the agent doesn't know that `aide.py` exists, or what its arguments are, it cannot use it. There are two primary mechanisms for "teaching" your Client Agent about AIDE's capabilities.

---

## 1. The Semantic Anchor: `SKILL.md`

Every autonomous tool needs a human-and-AI-readable manual. In the root of the AIDE repository, you will find `SKILL.md`.

This file acts as the semantic anchor. It outlines the philosophy of AIDE and lists the primary commands in plain, descriptive language. 

### How the Client Uses It
When instantiating your Client Agent (the script talking to LM Studio), you should programmatically read `SKILL.md` and inject its contents directly into the agent's **System Prompt**.

**Example Initialization in Python:**
```python
with open("a-i-d-e/SKILL.md", "r") as f:
    aide_manual = f.read()

system_prompt = f"""
You are an autonomous coding assistant. 
You have access to a deterministic refactoring tool called AIDE. 

Here is the manual for your tool:
{aide_manual}

When you need to modify code, do NOT try to rewrite the file yourself. Use the AIDE tool.
"""
```

By reading the `SKILL.md`, the LLM gains a conceptual understanding of *why* it should use AIDE (e.g., to prevent syntax errors and ensure safe rollbacks).

---

## 2. The Syntactic Anchor: JSON Schema (Function Calling)

While `SKILL.md` tells the LLM *why* and *when* to use AIDE, the LLM still needs to know *how* to construct the exact API payload to trigger the tool. This is done via **JSON Schema Tool Definitions**.

As shown in the LM Studio Integration guide, you must pass an array of `tools` in the API payload.

### Static vs. Dynamic Discovery

**Option A: Static Hardcoding**
You can manually write out the JSON schema for the primary AIDE commands (like `outline`, `implement-logic`, `project-dto`) and hardcode them into your wrapper script. This is the simplest approach but requires maintenance if AIDE adds new commands.

**Option B: Dynamic Discovery (The "Self-Describing" Approach)**
Because AIDE is built using standard Python `argparse`, it is entirely possible to write a script that queries AIDE for its capabilities and dynamically translates them into OpenAI-compatible JSON schemas.

*Theoretical Example:*
If you run `python aide.py --help`, AIDE lists all available commands. If you run `python aide.py implement-logic --help`, it lists all the required arguments (`--target`, `--prompt`, etc.).

A sophisticated Client Wrapper will:
1. Run `python aide.py --help` on startup.
2. Parse the output.
3. Generate the required `tools` JSON array automatically.
4. Pass that array to the LM Studio `/chat/completions` endpoint.

### Example: The JSON Schema

Regardless of whether you use Static or Dynamic discovery, the end result must be a JSON object like this passed to the LLM:

```json
{
  "type": "function",
  "function": {
    "name": "aide_implement_logic",
    "description": "Uses AIDE to safely and deterministically edit logic within a specific symbol.",
    "parameters": {
      "type": "object",
      "properties": {
        "target": {
          "type": "string",
          "description": "Path and symbol separated by :: (e.g., src/main.py::login)"
        },
        "prompt": {
          "type": "string",
          "description": "Instructions for the sub-agent."
        }
      },
      "required": ["target", "prompt"]
    }
  }
}
```

## Summary

1. Inject `SKILL.md` into the **System Prompt** so the agent *understands* AIDE conceptually.
2. Provide the JSON Schema in the **Tools Payload** so the agent knows the exact syntax required to trigger the commands.

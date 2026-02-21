# Client Integration: LM Studio & External Agents

While AIDE contains its own internal "Sub-Agents" (the brains in the vat) for executing precise code refactors, you will often want a "Client Agent" (like an IDE assistant, a chatbot, or an AutoGen instance) to use AIDE as a tool.

If your Client Agent is running inside **LM Studio** and supporting the OpenAI API format (e.g., using `qwen2.5-coder` or similar models), here is how you bind them together.

---

## The Concept: Tool Calling (Function Calling)

AIDE is a CLI tool (`aide.py`). To allow an LM Studio client agent to use it, you must define AIDE as a **Tool Schema** in your API request to LM Studio. 

The client agent doesn't need to know *how* AIDE works; it just needs to know *what commands* are available and *when* to trigger them. 

When the user asks the Client Agent a question, the agent replies with a JSON "Tool Call" requesting to run `aide.py`. Your wrapper script intercepts this request, runs AIDE in the terminal, and feeds the terminal output back to the agent.

---

## 1. Defining AIDE in the LM Studio Payload

When you send a completion request to LM Studio (`http://localhost:1234/v1/chat/completions`), you inject `aide.py` into the `tools` array. 

Here is an example of exposing the `outline` and `read` commands to the client agent:

```json
{
  "model": "qwen2.5-coder-7b-instruct",
  "messages": [
    {"role": "system", "content": "You are a coding assistant. Use the AIDE tool to explore and modify the codebase."},
    {"role": "user", "content": "Can you show me what methods are in src/auth.py?"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "aide_outline",
        "description": "Explores the structure of the codebase. Use this to find classes and functions.",
        "parameters": {
          "type": "object",
          "properties": {
            "path": {
              "type": "string",
              "description": "The file or directory path to outline, e.g., src/auth.py"
            }
          },
          "required": ["path"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "aide_implement_logic",
        "description": "Refactors or implements logic within a specific function or class.",
        "parameters": {
          "type": "object",
          "properties": {
            "target": {
              "type": "string",
              "description": "The target symbol, format: file_path::symbol_name (e.g., src/auth.py::login)"
            },
            "prompt": {
              "type": "string",
              "description": "Instructions for the refactor."
            }
          },
          "required": ["target", "prompt"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

---

## 2. Handling the Agent's Response

Because LM Studio supports OpenAI-compatible function calling, when the agent decides it needs to see the outline, it won't return text. It will return a `tool_calls` object.

**LM Studio Response:**
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "aide_outline",
              "arguments": "{\"path\": \"src/auth.py\"}"
            }
          }
        ]
      }
    }
  ]
}
```

---

## 3. The Execution Wrapper ("The Middleman")

Your client script (the thing talking to LM Studio) must now act as the middleman.

1.  **Parse the Tool Call:** Catch the `tool_calls` request.
2.  **Execute AIDE:** Run the physical CLI command via `subprocess`.
    ```bash
    python aide.py outline --path src/auth.py
    ```
3.  **Capture Output:** AIDE is designed to output clean JSON or structured text. Capture this output.
4.  **Send Back to LM Studio:** Send a follow-up request to LM Studio containing the tool's result, so the agent can read it and formulate a final answer for the user.

**Follow-up Payload to LM Studio:**
```json
{
  "model": "qwen2.5-coder-7b-instruct",
  "messages": [
    ... previous messages ...
    {
      "role": "tool",
      "tool_call_id": "call_abc123",
      "name": "aide_outline",
      "content": "Line 5: class AuthManager\nLine 10: def login(self, user)\n..."
    }
  ]
}
```

---

## Summary of the Flow

1.  **User:** "Fix the login bug."
2.  **Client Agent (LM Studio):** Thinks -> *I need to see the file first.* -> Emits tool call `aide_outline`.
3.  **Wrapper:** Runs `python aide.py outline`. Feeds the AST outline back to the agent.
4.  **Client Agent:** Thinks -> *I see the `login` method. I will use AIDE to fix it.* -> Emits tool call `aide_implement_logic`.
5.  **Wrapper:** Runs `python aide.py implement-logic --target src/auth.py::login --prompt "Fix validation bug" --verify`.
6.  **AIDE Core:** (This triggers the internal Brain-in-a-Vat Sub-Agent, splices the code, runs tests, and confirms success or formats a rollback).
7.  **Wrapper:** Feeds the AIDE success JSON back to LM Studio.
8.  **Client Agent:** "I have successfully fixed the bug."

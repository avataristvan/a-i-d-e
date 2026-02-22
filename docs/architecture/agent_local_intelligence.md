# Agent Local Intelligence Pattern

Now that AIDE has been returned to its pure, deterministic core, you (the Host Agent) can leverage **LM Studio** directly to improve your own internal efficiency. This pattern keeps AIDE simple while giving you access to local inference.

## Why use LM Studio if you have Gemini?

1.  **Specialized Models**: You can call models like `qwen2.5-coder-7b` or `deepseek-v2` specifically for code generation tasks that might benefit from a different "perspective".
2.  **Context Pre-Processing**: Use a local model to summarize massive files or stack traces before you ingest them, saving your own context window and cloud tokens.
3.  **Local "Linter"**: Use a local model to double-check your proposed `multi_replace_file_content` logic for syntax errors before you even try to run it.
4.  **Privacy/Drafting**: Perform "reasoning" steps or initial drafts about sensitive logic locally.

## Official Integration: Model Context Protocol (MCP)

Antigravity is now configured to use LM Studio natively via MCP. A lightweight bridge script has been registered in your global `mcp_config.json`.

### Registered Tool: `lmstudio:ask_local_model`
You can now ask me to use LM Studio for specific tasks. I will use the `ask_local_model` tool to communicate with your local model.

### Configuration (`~/.gemini/antigravity/mcp_config.json`)
```json
{
  "mcpServers": {
    "lmstudio": {
      "command": "python3",
      "args": ["/home/istvan/workspace/a-i-d-e/scripts/lmstudio_mcp_server.py"]
    }
  }
}
```

## How to Orchestrate (The "Professional" Pattern)
Instead of raw `curl` commands, I can now use the `ask_local_model` tool:
1. **Host Agent (Me)**: "I'll double check this Rust syntax with your local model."
2. **Action**: I call `lmstudio:ask_local_model(prompt="Analyze this code...")`
3. **Internal Reasoning**: I combine the local model's feedback with AIDE's deterministic structural tools.

## The "Agent-Only" Bridge vs. "AIDE-Bridge"

*   **AIDE-Bridge (REMOVED)**: Attempted to hide the LLM inside a CLI tool. This led to non-determinism inside a tool that *needs* to be stable, and created a "blind spot" where the host agent couldn't see why a refactor was failing.
*   **Agent-Sidecar (RECOMMENDED)**: You (the agent) control the LLM call. You see the prompt, you see the response, and you use the response to drive the deterministic AIDE tool.

This maintains **Agent sovereignty**: You are the orchestrator, LM Studio is your local assistant, and AIDE is your structural scalpel.

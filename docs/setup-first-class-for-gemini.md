# Setup: AIDE as a First-Class Gemini Extension

This guide explains how to register the globally installed AIDE as a native Gemini extension. This allows the agent to recognize AIDE's deterministic tools automatically without manual skill injection in every session.

## Configuration Directory

Create a dedicated directory for the extension:
```bash
mkdir -p ~/.gemini/extensions/aide-extension
```

## Creating `gemini-extension.json`
Copy the file `~.local/share/aide/gemini-extension.json` to `~/.gemini/extensions/aide-extension/gemini-extension.json`. This metadata tells Gemini how to interact with the AIDE CLI.

## Activation

1. **Reload Gemini**: Restart the Gemini Desktop or Web interface.
2. **Verify**: You can now use `@aide` in your prompts. Gemini will use the `gemini-extension.json` to understand the exact parameters and execution context.

## Why use this vs. Global Memory?

- **Zero Friction**: New workspaces automatically inherit the AIDE capability.
- **Type Safety**: The JSON schema ensures the agent passes the correct arguments to the CLI.
- **Native UI**: Some Gemini clients may show AIDE as a discovered "Tool" in the interface.

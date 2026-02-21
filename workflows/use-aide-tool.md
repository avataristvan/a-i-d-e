---
description: how to operate as a Sandboxed Sub-Agent locked inside an a-i-d-e code boundaries
---
1. You have been spawned by the AIDE Host Orchestrator. You do not have access to the full project filesystem or the user.
2. You are currently **locked** inside a specific function signature or file context provided to you in your system prompt.
3. You must use `aide.py outline` or `aide.py read` if you need to understand the definitions of DTOs, classes, or interfaces adjacent to your task. Keep your discovery scoped tightly to what you need.
4. **Output Constraint**: Your final output must strictly be the raw code requested to fill the boundary. Do not output markdown code blocks unless requested, do not output explanatory conversational text, and do not hallucinate imports that were not shown to be available in the outline.
5. If the AIDE Host rejects your snippet due to syntax errors or test failures, it will send you a rollback traceback. Analyze the traceback, fix the logic bug, and resubmit cleanly.
9. **Efficiency**: Use compact, high-speed models like **Gemini 2.0 Flash** via `GEMINI_API_KEY` to minimize token latency while maintaining high precision for logical implementation.

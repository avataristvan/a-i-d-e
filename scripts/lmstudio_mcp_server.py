import sys
import json
import urllib.request
import os

# Ultra-lightweight MCP server for LM Studio
# Exposes a single tool: ask_local_model

LM_SERVER_URL = os.getenv("LM_SERVER_URL", "http://localhost:1234/v1/chat/completions")
LM_API_TOKEN = os.getenv("LM_API_TOKEN", "")

def get_mcp_metadata():
    return {
        "mcp_version": "1.0",
        "name": "lm-studio-mcp",
        "tools": [
            {
                "name": "ask_local_model",
                "description": "Sends a prompt to a local model running in LM Studio. Use this for specialized coding tasks or syntax validation.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "The prompt to send."},
                        "system_prompt": {"type": "string", "description": "Optional system context."},
                        "temperature": {"type": "number", "description": "Model temperature (default 0.0)."}
                    },
                    "required": ["prompt"]
                }
            },
            {
                "name": "verify_local_model",
                "description": "Checks if the local model server is reachable and if credentials are configured.",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }

def handle_tool_call(tool_name, arguments):
    if tool_name == "verify_local_model":
        return verify_connection()
    
    if tool_name != "ask_local_model":
        return {"error": f"Unknown tool: {tool_name}"}
    
    if not LM_API_TOKEN or LM_API_TOKEN == "YOUR_LM_STUDIO_API_TOKEN_HERE":
         return {"error": "LM_API_TOKEN is missing or not configured in mcp_config.json."}

    prompt = arguments.get("prompt")
    system_prompt = arguments.get("system_prompt", "You are a helpful coding assistant.")
    temperature = arguments.get("temperature", 0.0)
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "stream": False
    }
    
    headers = {"Content-Type": "application/json"}
    headers["Authorization"] = f"Bearer {LM_API_TOKEN}"
    
    try:
        req = urllib.request.Request(
            LM_SERVER_URL, 
            data=json.dumps(payload).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                result = json.loads(response.read().decode("utf-8"))
                return {"text": result["choices"][0]["message"]["content"]}
            else:
                return {"error": f"LM Studio API Error (Status {response.status}). Check if the model is loaded."}
    except Exception as e:
        return {"error": f"Connectivity Failure: Could not reach {LM_SERVER_URL}. Is LM Studio server running? Error: {str(e)}"}

def verify_connection():
    status = {
        "server_url": LM_SERVER_URL,
        "token_configured": bool(LM_API_TOKEN and LM_API_TOKEN != "YOUR_LM_STUDIO_API_TOKEN_HERE"),
        "reachable": False,
        "details": ""
    }
    
    if not status["token_configured"]:
        status["details"] = "LM_API_TOKEN is not set in mcp_config.json."
        return status

    try:
        # Check if server is up by asking for models (cheaper than a completion)
        models_url = LM_SERVER_URL.replace("/chat/completions", "/models")
        req = urllib.request.Request(models_url, headers={"Authorization": f"Bearer {LM_API_TOKEN}"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                status["reachable"] = True
                status["details"] = "Local server is active and responding."
            else:
                status["details"] = f"Server responded with status {response.status}."
    except Exception as e:
        status["details"] = f"Connection error: {str(e)}"
    
    return status

def main():
    # Simple stdio-based protocol handler
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line)
            method = request.get("method")
            
            if method == "initialize":
                 print(json.dumps({"result": get_mcp_metadata()}), flush=True)
            elif method == "call_tool":
                params = request.get("params", {})
                result = handle_tool_call(params.get("name"), params.get("arguments", {}))
                print(json.dumps({"id": request.get("id"), "result": result}), flush=True)
            elif method == "list_tools":
                 print(json.dumps({"result": {"tools": get_mcp_metadata()["tools"]}}), flush=True)
        except EOFError:
            break
        except Exception as e:
            sys.stderr.write(f"MCP Server Error: {str(e)}\n")

if __name__ == "__main__":
    main()

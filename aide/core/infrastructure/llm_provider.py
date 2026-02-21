import os
import json
import urllib.request
import urllib.error
from aide.core.domain.ports import LlmProvider

class HttpOpenAILlmProvider(LlmProvider):
    """
    Zero-dependency HTTP client for OpenAI-compatible completions endpoints.
    Requires AIDE_LLM_API_KEY environment variable.
    Can optionally configure AIDE_LLM_API_BASE (default: https://api.openai.com/v1)
    and AIDE_LLM_MODEL (default: gpt-4o).
    """
    
    def __init__(self):
        self.api_key = os.getenv("AIDE_LLM_API_KEY")
        self.api_base = os.getenv("AIDE_LLM_API_BASE", "https://api.openai.com/v1").rstrip("/")
        self.model = os.getenv("AIDE_LLM_MODEL", "gpt-4o")
        
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("AIDE_LLM_API_KEY environment variable is missing.")
            
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.0,
            "stream": False
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                return response_data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(f"HTTP Error {e.code}: {error_body}") from e
        except Exception as e:
            raise Exception(f"Failed to communicate with LLM provider: {e}") from e

class HttpGeminiLlmProvider(LlmProvider):
    """
    Zero-dependency HTTP client for Google Gemini (Google AI) API.
    Requires GEMINI_API_KEY environment variable.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("AIDE_LLM_MODEL", "gemini-2.0-flash")
        self.api_base = "https://generativelanguage.googleapis.com/v1beta/models"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing.")
            
        url = f"{self.api_base}/{self.model}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Google's payload structure is slightly different
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"System Instruction: {system_prompt}\n\nUser Request: {user_prompt}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 4096
            }
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                # Path: candidates[0].content.parts[0].text
                return response_data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(f"HTTP Error {e.code}: {error_body}") from e
        except Exception as e:
            raise Exception(f"Failed to communicate with Gemini provider: {e}") from e

class ShellLlmProvider(LlmProvider):
    """
    Provider that executes a shell command to generate text.
    The command receives the prompts via stdin or as arguments.
    Configured via AIDE_LLM_COMMAND environment variable.
    """
    def __init__(self):
        self.command = os.getenv("AIDE_LLM_COMMAND")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.command:
            raise ValueError("AIDE_LLM_COMMAND environment variable is missing.")
            
        import subprocess
        
        # Combine prompts for a standard CLI interface
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        try:
            # We run the command and pipe the prompt to stdin
            process = subprocess.Popen(
                self.command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=full_prompt, timeout=120)
            
            if process.returncode != 0:
                raise Exception(f"Command failed with exit code {process.returncode}: {stderr}")
                
            return stdout.strip()
        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception(f"LLM command timed out after 120 seconds.")
        except Exception as e:
            raise Exception(f"Failed to execute LLM command '{self.command}': {e}")



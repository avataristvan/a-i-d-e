import json
import subprocess
from typing import Dict, Any

class ExecuteTestsUseCase:
    """Wraps test execution and returns a machine-readable JSON payload of the results."""
    
    def execute(self, path: str, format: str = "json") -> Dict[str, Any]:
        print(f"🔄 Running tests in {path}...")
        
        try:
            # We use junitxml because it's built into pytest and doesn't require extra plugins
            # However, parsing it is annoying in pure python without xml.etree.
            # A simpler approach for AIDE: run pytest normally, grep for FAILURES.
            # But wait, pytest-json-report is better. Let's just run pytest to standard output for now
            # and format a simplistic dictionary if we don't have the plugin.
            
            result = subprocess.run(
                ["pytest", path, "-q", "--tb=short"], 
                capture_output=True, 
                text=True
            )
            
            # Very naive parsing of pytest output for agent consumption
            lines = result.stdout.splitlines()
            failures = []
            current_failure = None
            
            for line in lines:
                if line.startswith("FAILED "):
                    if current_failure:
                        failures.append(current_failure)
                    current_failure = {"test": line.replace("FAILED ", "").split(" - ")[0].strip(), "error": " ".join(line.split(" - ")[1:]) if " - " in line else ""}
                elif current_failure and line.strip() and not line.startswith("="):
                    # Append tb lines
                    current_failure["error"] += "\n" + line

            if current_failure:
                failures.append(current_failure)

            summary = lines[-1] if lines else "No output"
            
            payload = {
                "success": result.returncode == 0,
                "summary": summary,
                "failures": failures
            }
            
            if format == "json":
                out = json.dumps(payload, indent=2)
                print(out)
            else:
                if payload["success"]:
                    print(f"✅ All tests passed: {summary}")
                else:
                    print(f"❌ Tests failed: {summary}")
                    for f in failures:
                        print(f"  - {f['test']}")
            
            return payload

        except Exception as e:
            err = {"success": False, "error": str(e)}
            if format == "json":
                print(json.dumps(err))
            return err

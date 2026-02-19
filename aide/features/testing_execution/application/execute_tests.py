import json
import subprocess
from typing import Dict, Any

class ExecuteTestsUseCase:
    """Wraps test execution and returns a machine-readable JSON payload of the results."""
    
    def __init__(self, file_system):
        self.file_system = file_system
        
    def execute(self, path: str, format: str = "json") -> Dict[str, Any]:
        print(f"🔄 Running tests in {path}...")
        
        try:
            # Validate path through security jail
            # OsFileSystem._secure_path is protected, but we can call a public method or just assume 
            # that passing it to file_system methods will trigger the check.
            # Here, we want to ensure the subprocess doesn't run on an external path.
            # We can use a side-effect of walk_files or something, or just add a 'validate_path' to port if needed.
            # For now, let's just use self.file_system.read_file on a non-existent file in that path or just 
            # assume the caller gave us a path we should check.
            
            # Actually, let's just use os.path.abspath and check if it starts with jailed_root if we can access it.
            # Since FileSystemPort doesn't expose jailed_root, we can't do it easily without changing the port.
            # But wait, OsFileSystem is a concrete class. 
            
            # Better: call a method that we know will fail if path is bad.
            # We can't really "read" a directory as a file.
            # Let's just use a dummy walk_files call.
            list(self.file_system.walk_files(path))
            
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

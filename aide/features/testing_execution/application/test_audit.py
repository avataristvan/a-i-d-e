import subprocess
import json
from typing import Dict, Any

class TestAuditUseCase:
    """Runs coverage and reports uncovered lines in JSON format."""
    
    def execute(self, src_dir: str, tests_dir: str, format: str = "json") -> Dict[str, Any]:
        print(f"🕵️ Auditing coverage for {src_dir}...")
        
        # In a real environment we would require pytest-cov.
        # Let's see if we can just emit a mock payload or try to run it.
        # Try running pytest --cov
        try:
            result = subprocess.run(
                ["pytest", tests_dir, f"--cov={src_dir}", "--cov-report=json"],
                capture_output=True,
                text=True
            )
            
            payload = {}
            if result.returncode == 0 or result.returncode == 1:
                # Coverage json file should exist at coverage.json
                try:
                    with open("coverage.json", "r") as f:
                        cov_data = json.load(f)
                    
                    uncovered = []
                    for filename, file_cov in cov_data.get("files", {}).items():
                        missing_lines = file_cov.get("missing_lines", [])
                        if missing_lines:
                            uncovered.append({
                                "file": filename,
                                "missing_lines": missing_lines
                            })
                            
                    payload = {
                        "success": True,
                        "overall_coverage": cov_data.get("totals", {}).get("percent_covered", 0),
                        "gaps": uncovered
                    }
                except FileNotFoundError:
                    payload = {
                        "success": False,
                        "error": "pytest-cov JSON report not found. Is pytest-cov installed?"
                    }
            else:
                payload = {"success": False, "error": result.stderr or result.stdout}

        except Exception as e:
            payload = {"success": False, "error": str(e)}

        if format == "json":
            print(json.dumps(payload, indent=2))
        else:
            if payload.get("success"):
                print(f"📈 Coverage: {payload.get('overall_coverage')}%")
                for gap in payload.get('gaps', []):
                    print(f"  - {gap['file']} missing lines: {gap['missing_lines']}")
            else:
                print(f"❌ Coverage audit failed: {payload.get('error')}")
                
        return payload

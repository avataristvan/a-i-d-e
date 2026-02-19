import subprocess
import json
from typing import Dict, Any

class AuditCoverageUseCase:
    """Runs coverage and reports uncovered lines in JSON format."""
    __test__ = False
    
    
    def __init__(self, file_system):
        self.file_system = file_system
        
    def execute(self, src_dir: str, tests_dir: str, format: str = "json") -> Dict[str, Any]:
        print(f"🕵️ Auditing coverage for {src_dir}...")
        
        try:
            # Validate paths
            list(self.file_system.walk_files(src_dir))
            list(self.file_system.walk_files(tests_dir))
            
            result = subprocess.run(
                ["pytest", tests_dir, f"--cov={src_dir}", "--cov-report=json"],
                capture_output=True,
                text=True
            )
            
            payload = {}
            if result.returncode == 0 or result.returncode == 1:
                # Coverage json file should exist at coverage.json
                try:
                    content = self.file_system.read_file("coverage.json")
                    cov_data = json.loads(content)
                    
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

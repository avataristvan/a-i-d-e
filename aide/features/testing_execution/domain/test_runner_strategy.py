import subprocess
from typing import Dict, Any, Tuple

class TestRunnerStrategy:
    """Strategy interface for test execution and coverage reporting."""
    def run_tests(self, path: str) -> Tuple[bool, str, list]:
        """Runs tests and returns (success, summary_string, list_of_failures_dicts)"""
        raise NotImplementedError
        
    def run_coverage(self, src_dir: str, tests_dir: str) -> Tuple[bool, float, list, str]:
        """Runs coverage and returns (success, overall_coverage_float, list_of_gaps, error_string)"""
        raise NotImplementedError

class PythonTestRunner(TestRunnerStrategy):
    def run_tests(self, path: str) -> Tuple[bool, str, list]:
        result = subprocess.run(
            ["pytest", path, "-q", "--tb=short"], 
            capture_output=True, 
            text=True
        )
        
        lines = result.stdout.splitlines()
        failures = []
        current_failure = None
        
        for line in lines:
            if line.startswith("FAILED "):
                if current_failure:
                    failures.append(current_failure)
                current_failure = {"test": line.replace("FAILED ", "").split(" - ")[0].strip(), "error": " ".join(line.split(" - ")[1:]) if " - " in line else ""}
            elif current_failure and line.strip() and not line.startswith("="):
                current_failure["error"] += "\n" + line

        if current_failure:
            failures.append(current_failure)

        summary = lines[-1] if lines else "No output"
        return result.returncode == 0, summary, failures

    def run_coverage(self, src_dir: str, tests_dir: str) -> Tuple[bool, float, list, str]:
        import json
        result = subprocess.run(
            ["pytest", tests_dir, f"--cov={src_dir}", "--cov-report=json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 or result.returncode == 1:
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
                        
                overall = cov_data.get("totals", {}).get("percent_covered", 0)
                return True, overall, uncovered, ""
            except FileNotFoundError:
                return False, 0.0, [], "pytest-cov JSON report not found."
        else:
            return False, 0.0, [], result.stderr or result.stdout

class GenericTestRunner(TestRunnerStrategy):
    """Fallback runner for unsupported languages, simulates a run or returns a not implemented error."""
    def run_tests(self, path: str) -> Tuple[bool, str, list]:
        return False, f"Test runner not yet implemented for the language in '{path}'.", []
        
    def run_coverage(self, src_dir: str, tests_dir: str) -> Tuple[bool, float, list, str]:
        return False, 0.0, [], f"Coverage runner not yet implemented for the language in '{src_dir}'."

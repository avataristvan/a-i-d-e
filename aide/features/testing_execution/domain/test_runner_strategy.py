import subprocess
from typing import Dict, Any, Tuple

class TestRunnerStrategy:
    """Strategy interface for test execution and coverage reporting."""
    def run_tests(self, path: str) -> tuple[bool, str, list]:
        """Runs tests and returns (success, summary_string, list_of_failures_dicts)"""
        raise NotImplementedError
        
    def run_coverage(self, src_dir: str, tests_dir: str) -> tuple[bool, float, list, str]:
        """Runs coverage and returns (success, overall_coverage_float, list_of_gaps, error_string)"""
        raise NotImplementedError

    @property
    def is_implemented(self) -> bool:
        return True

class PythonTestRunner(TestRunnerStrategy):
    def run_tests(self, path: str) -> tuple[bool, str, list]:
        import json
        import os
        
        report_file = os.path.join(path if os.path.isdir(path) else os.path.dirname(path), ".report.json")
        if os.path.exists(report_file):
            try:
                os.remove(report_file)
            except OSError:
                pass

        result = subprocess.run(
            ["pytest", path, "-q", "--json-report", f"--json-report-file={report_file}"], 
            capture_output=True, 
            text=True
        )
        
        if not os.path.exists(report_file):
            return False, "Test suite failed (collection error, no JSON report generated).", [{"test": "Test Suite", "error": result.stdout or result.stderr}]
            
        try:
            with open(report_file, "r") as f:
                report = json.load(f)
        except Exception as e:
            return False, f"Failed to parse test report: {e}", [{"test": "Test Suite", "error": result.stdout}]

        summary_data = report.get("summary", {})
        total = summary_data.get("total", 0)
        passed = summary_data.get("passed", 0)
        failed = summary_data.get("failed", 0) + summary_data.get("error", 0)
        
        summary = f"{passed} passed, {failed} failed out of {total} tests"
        
        failures = []
        for test in report.get("tests", []):
            if test.get("outcome") in ["failed", "error"]:
                test_name = test.get("nodeid", "Unknown Test")
                # Error details can be in setup if the fixture failed, or call if the test failed
                phase = test.get("call", {}) if "call" in test else test.get("setup", {})
                
                error_msg = ""
                if "crash" in phase and phase.get("crash"):
                    error_msg = phase["crash"].get("message", "")
                
                if not error_msg and "longrepr" in phase:
                    # longrepr can be a string or a dict/list depending on the error type
                    error_msg = str(phase.get("longrepr", ""))
                    
                failures.append({
                    "test": test_name,
                    "error": error_msg or "Unknown error"
                })
        
        return result.returncode == 0 and failed == 0, summary, failures

    def run_coverage(self, src_dir: str, tests_dir: str) -> tuple[bool, float, list, str]:
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
    def run_tests(self, path: str) -> tuple[bool, str, list]:
        return False, f"Test runner not yet implemented for the language in '{path}'.", []
        
    def run_coverage(self, src_dir: str, tests_dir: str) -> tuple[bool, float, list, str]:
        return False, 0.0, [], f"Coverage runner not yet implemented for the language in '{src_dir}'."

    @property
    def is_implemented(self) -> bool:
        return False

class KotlinTestRunner(TestRunnerStrategy):
    """Kotlin/Gradle test runner using the Gradle wrapper."""
    def run_tests(self, path: str) -> tuple[bool, str, list]:
        import os
        
        # Determine root project by searching for gradlew
        root_dir = path
        while root_dir and root_dir != os.path.sep:
            if os.path.exists(os.path.join(root_dir, "gradlew")) or os.path.exists(os.path.join(root_dir, "build.gradle.kts")):
                break
            parent = os.path.dirname(root_dir)
            if parent == root_dir: break
            root_dir = parent
            
        executable = "./gradlew" if os.path.exists(os.path.join(root_dir, "gradlew")) else "gradle"
        
        # We try to run the tests. Note: we don't have a structured report like pytest-json-report yet for Gradle,
        # but we can parse the output or just return success/failure.
        # For now, let's keep it simple.
        result = subprocess.run(
            [executable, "test"],
            cwd=root_dir,
            capture_output=True,
            text=True
        )
        
        success = result.returncode == 0
        summary = "Gradle tests passed." if success else "Gradle tests failed."
        failures = []
        if not success:
            failures.append({"test": "Gradle Test Suite", "error": result.stdout[-500:]}) # Tail of the output
            
        return success, summary, failures

    def run_coverage(self, src_dir: str, tests_dir: str) -> tuple[bool, float, list, str]:
        # Placeholder for Jacoco or similar
        return False, 0.0, [], "Coverage runner not yet implemented for Kotlin."

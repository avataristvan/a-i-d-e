import json
import subprocess
from typing import Dict, Any
from aide.features.testing_execution.domain.test_runner_provider import TestRunnerProvider
from aide.core.domain.ports import FileSystemPort

class ExecuteTestsUseCase:
    """Wraps test execution and returns a machine-readable JSON payload of the results."""
    
    def __init__(self, file_system: FileSystemPort) -> None:
        self.file_system = file_system
        
    def execute(self, path: str, format: str = "json") -> dict[str, Any]:
        try:
            list(self.file_system.walk_files(path))
            
            runner = TestRunnerProvider.get_runner(path)
            success, summary, failures = runner.run_tests(path)
            
            payload = {
                "success": success,
                "summary": summary,
                "failures": failures,
                "is_implemented": runner.is_implemented
            }
            
            return payload

        except Exception as e:
            err = {"success": False, "error": str(e)}
            return err

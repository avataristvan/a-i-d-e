import subprocess
import json
from typing import Dict, Any
from aide.features.testing_execution.domain.test_runner_provider import TestRunnerProvider

class AuditCoverageUseCase:
    """Runs coverage and reports uncovered lines in JSON format."""
    __test__ = False
    
    
    def __init__(self, file_system):
        self.file_system = file_system
        
    def execute(self, src_dir: str, tests_dir: str, format: str = "json") -> Dict[str, Any]:
        try:
            # Validate paths
            list(self.file_system.walk_files(src_dir))
            list(self.file_system.walk_files(tests_dir))
            
            runner = TestRunnerProvider.get_runner(src_dir)
            success, overall, uncovered, error = runner.run_coverage(src_dir, tests_dir)
            
            if not error:
                 payload = {
                     "success": success,
                     "overall_coverage": overall,
                     "gaps": uncovered
                 }
            else:
                 payload = {"success": False, "error": error}

        except Exception as e:
            payload = {"success": False, "error": str(e)}

        return payload

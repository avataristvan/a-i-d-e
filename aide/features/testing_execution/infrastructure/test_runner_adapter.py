from aide.core.domain.ports import TestRunnerPort
from aide.features.testing_execution.application.execute_tests import ExecuteTestsUseCase


class TestRunnerAdapter(TestRunnerPort):
    def __init__(self, file_system):
        self._use_case = ExecuteTestsUseCase(file_system)

    def run(self, root_path: str) -> dict:
        return self._use_case.execute(root_path)

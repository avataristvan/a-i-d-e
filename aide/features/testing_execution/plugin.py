import json
from argparse import _SubParsersAction
from aide.core.context import Context
from aide.core.domain.ports import TestRunnerPort
from aide.features.testing_execution.application.execute_tests import ExecuteTestsUseCase
from aide.features.testing_execution.application.audit_fixtures import AuditFixturesUseCase
from aide.features.testing_execution.application.test_audit import AuditCoverageUseCase
from aide.features.testing_execution.infrastructure.test_runner_adapter import TestRunnerAdapter

class TestExecutionPlugin:
    """Plugin to handle deterministic AI-readable test execution and coverage reports."""

    def register(self, subparsers: _SubParsersAction, context: Context) -> None:
        context.register(TestRunnerPort, TestRunnerAdapter(context.file_system))
        # aide test
        test_parser = subparsers.add_parser("test", help="Run tests and return machine-readable report")
        test_parser.add_argument("--path", required=True, help="Path to tests directory")
        test_parser.add_argument("--format", default="json", choices=["json", "text"], help="Output format")
        test_parser.set_defaults(func=lambda args: self.run_test(args, context))
        
        # aide audit-fixtures
        fixt_parser = subparsers.add_parser("audit-fixtures", help="Finds unused or redundant pytest fixtures")
        fixt_parser.add_argument("--path", required=True, help="Path to tests directory")
        fixt_parser.add_argument("--format", default="json", choices=["json", "text"], help="Output format")
        fixt_parser.set_defaults(func=lambda args: self.run_audit_fixtures(args, context))
        
        # aide test-audit
        cov_parser = subparsers.add_parser("test-audit", help="Run coverage and report gap bounds")
        cov_parser.add_argument("--src", required=True, help="Source directory to analyze")
        cov_parser.add_argument("--tests", required=True, help="Test directory")
        cov_parser.add_argument("--format", default="json", choices=["json", "text"], help="Output format")
        cov_parser.set_defaults(func=lambda args: self.run_test_audit(args, context))

    def run_test(self, args, context: Context):
        use_case = ExecuteTestsUseCase(context.file_system)
        result = use_case.execute(args.path, args.format)
        print(json.dumps(result, indent=2))
        
    def run_audit_fixtures(self, args, context: Context):
        use_case = AuditFixturesUseCase(context.file_system)
        result = use_case.execute(args.path, args.format)
        print(json.dumps(result, indent=2))
        
    def run_test_audit(self, args, context: Context):
        use_case = AuditCoverageUseCase(context.file_system)
        result = use_case.execute(args.src, args.tests, args.format)
        print(json.dumps(result, indent=2))

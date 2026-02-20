import json
from argparse import _SubParsersAction
from aide.core.context import Context
from aide.features.test_generation.application.generate_tests import GenerateTestsUseCase
from aide.features.test_generation.application.scaffold_mocks import ScaffoldMocksUseCase

class TestGenerationPlugin:
    def register(self, subparsers: _SubParsersAction, context: Context) -> None:
        parser = subparsers.add_parser("generate-tests", help="Scaffold test context JSON for a symbol")
        parser.add_argument("--file", required=True, help="Path to the file containing the symbol")
        parser.add_argument("--symbol", required=True, help="Name of the class or function to test")
        parser.add_argument("--format", default="json", choices=["json", "markdown"], help="Output format (json, markdown)")
        parser.set_defaults(func=lambda args: self.run_generate(args, context))

        mock_parser = subparsers.add_parser("scaffold-mocks", help="Generate boilerplate mock classes for a symbol's dependencies")
        mock_parser.add_argument("--file", required=True, help="Path to the file containing the class")
        mock_parser.add_argument("--class-name", required=True, help="Name of the class to scaffold mocks for")
        mock_parser.add_argument("--format", default="json", choices=["json", "markdown"], help="Output format (json, markdown)")
        mock_parser.set_defaults(func=lambda args: self.run_scaffold(args, context))

    def run_generate(self, args, context: Context):
        use_case = GenerateTestsUseCase(
            context.file_system,
            context.language_parser,
            context.strategy_provider
        )
        
        output = use_case.execute(args.file, args.symbol, args.format)
        
        result = {
            "success": bool(output),
            "message": "Evaluation context acquired successfully." if output else f"Symbol '{args.symbol}' was not found in '{args.file}'.",
            "data": {
                "file": args.file,
                "symbol": args.symbol,
                "format": args.format,
                "output": output
            }
        }
        print(json.dumps(result, indent=2))

    def run_scaffold(self, args, context: Context):
        use_case = ScaffoldMocksUseCase(
            context.file_system,
            context.language_parser,
            context.strategy_provider
        )
        
        output = use_case.execute(args.file, args.class_name, args.format)
        
        result = {
            "success": bool(output),
            "message": "Mock scaffolding successful." if output else f"Class '{args.class_name}' was not found in '{args.file}'.",
            "data": {
                "file": args.file,
                "class_name": args.class_name,
                "format": args.format,
                "output": output
            }
        }
        print(json.dumps(result, indent=2))

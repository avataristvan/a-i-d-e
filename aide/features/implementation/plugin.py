import json
import argparse
from aide.core.context import Context

class ImplementationPlugin:
    def register(self, subparsers: argparse._SubParsersAction, context: Context) -> None:
        impl_parser = subparsers.add_parser("implement-logic", help="Spawn a Sub-Agent to write deterministic logic inside a function boundary.")
        impl_parser.add_argument("--target", required=True, help="Target in format 'file_path::symbol_name'")
        impl_parser.add_argument("--prompt", required=True, help="The business logic intent for the Sub-Agent to implement.")
        impl_parser.add_argument("-n", "--dry-run", action="store_true", help="Preview the LLM logic without saving.")
        impl_parser.add_argument("--verify", action="store_true", help="Automatically run tests and revert changes if the Sub-Agent breaks the build.")
        impl_parser.add_argument("--root", default=".", help="Project root for testing.")
        impl_parser.set_defaults(func=lambda args: self.handle_implement_logic(args, context))

    def handle_implement_logic(self, args, context: Context):
        from aide.features.implementation.application.implement_logic import ImplementLogicUseCase
        
        # Parse target Target
        if "::" not in args.target:
             print(json.dumps({"success": False, "error": "Target must be in format 'file_path::symbol_name'"}))
             return
             
        file_path, symbol_name = args.target.split("::", 1)
        
        try:
            llm_provider = context.llm_provider
        except Exception as e:
            # Fallback for discovery
            print(json.dumps({
                "success": False, 
                "error": "LlmProvider is not registered or API keys are missing. Cannot spawn Sub-Agent.",
                "hint": "Ensure AIDE_LLM_API_KEY environment variable is set."
            }))
            return

        use_case = ImplementLogicUseCase(
            file_system=context.file_system,
            language_parser=context.language_parser,
            strategy_provider=context.strategy_provider,
            llm_provider=llm_provider
        )

        reverted = False
        if getattr(args, "verify", False): context.file_system.start_transaction()
        
        success, message = use_case.execute(file_path, symbol_name, args.prompt, dry_run=args.dry_run)
        
        if success and getattr(args, "verify", False) and not args.dry_run:
            from aide.features.testing_execution.application.execute_tests import ExecuteTestsUseCase
            test_use_case = ExecuteTestsUseCase(context.file_system)
            test_res = test_use_case.execute(args.root)
            if not test_res.get("success", False):
                context.file_system.rollback()
                success = False
                message = "Sub-Agent logic failed project verification tests. Rollback executed."
                reverted = True
            else:
                context.file_system.commit()

        result = {
            "success": success,
            "message": message,
            "data": {
                "file": file_path,
                "symbol": symbol_name,
                "dry_run": args.dry_run,
                "reverted": reverted
            }
        }
        print(json.dumps(result, indent=2))

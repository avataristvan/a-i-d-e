import json
from argparse import _SubParsersAction
import os
from aide.core.context import Context
from aide.features.code_inspection.application.outline import OutlineUseCase

class CodeInspectionPlugin:
    def register(self, subparsers: _SubParsersAction, context: Context) -> None:
        # Outline Command
        parser_outline = subparsers.add_parser("outline", help="Show symbol outline of files")
        parser_outline.add_argument("pattern", help="File pattern (e.g. *.py)")
        parser_outline.set_defaults(func=lambda args: self.handle_outline(args, context))
        
        parser_read = subparsers.add_parser("read", help="Read files with line numbers")
        parser_read.add_argument("file", help="File path")
        parser_read.add_argument("--selection", help="Line range (start:end, 1-based)")
        parser_read.set_defaults(func=lambda args: self.handle_read(args, context))

        # Usages Command
        parser_usages = subparsers.add_parser("usages", help="Find symbol usages")
        parser_usages.add_argument("symbol", help="Symbol name to search for")
        parser_usages.add_argument("--root", default=".", help="Root directory to search in")
        parser_usages.set_defaults(func=lambda args: self.handle_usages(args, context))

        # Find Impact Command
        parser_impact = subparsers.add_parser("find-impact", help="Find all files and tests impacted by a symbol")
        parser_impact.add_argument("--symbol", required=True, help="Symbol name to analyze")
        parser_impact.add_argument("--file", help="File where the symbol is defined (optional)")
        parser_impact.add_argument("--format", default="json", choices=["json", "text"], help="Output format")
        parser_impact.set_defaults(func=lambda args: self.handle_find_impact(args, context))

    def handle_outline(self, args, context: Context):
        use_case = OutlineUseCase(context.file_system, context.language_parser)
        outline_data = use_case.execute(args.pattern)
        
        result = {
            "success": True,
            "message": "Outline generation complete.",
            "data": {"outline": outline_data}
        }
        print(json.dumps(result, indent=2))

    def handle_read(self, args, context: Context):
        if os.path.exists(args.file):
            content = context.file_system.read_file(args.file)
            lines = content.splitlines()
            
            start_line = 1
            end_line = len(lines)
            
            if args.selection:
                try:
                    parts = args.selection.split(':')
                    start_line = int(parts[0])
                    if len(parts) > 1:
                        end_line = int(parts[1])
                except ValueError:
                    print(json.dumps({"success": False, "error": f"Invalid selection format: {args.selection}. Use start:end (e.g. 10:20)"}))
                    return
            
            read_lines = []
            for i in range(start_line - 1, end_line):
                if i < len(lines):
                    read_lines.append(f"{i+1}: {lines[i]}")

            result = {
                "success": True,
                "message": "File read complete.",
                "data": {
                    "file_path": os.path.abspath(args.file),
                    "total_lines": len(lines),
                    "total_bytes": len(content),
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": "\n".join(read_lines)
                }
            }
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps({"success": False, "error": f"File not found: {args.file}"}))

    def handle_usages(self, args, context: Context):
        from aide.features.code_inspection.application.find_usages import FindUsagesUseCase
        use_case = FindUsagesUseCase(context.file_system, context.language_parser)
        
        results = use_case.execute(args.root, args.symbol)
        
        payload = {
            "success": True,
            "message": f"Found {len(results)} usages." if results else "No usages found.",
            "data": {
                "symbol": args.symbol,
                "root": args.root,
                "usages": results
            }
        }
        print(json.dumps(payload, indent=2))

    def handle_find_impact(self, args, context: Context):
        from aide.features.code_inspection.application.find_impact import FindImpactUseCase
        use_case = FindImpactUseCase(context.file_system, context.language_parser, context.strategy_provider)
        
        results = use_case.execute(args.symbol, args.file)
        
        payload = {
            "success": True,
            "message": f"Found {len(results.get('impacted_files', []))} impacted files and {len(results.get('impacted_tests', []))} impacted tests.",
            "data": {
                "symbol": args.symbol,
                "source_file": args.file,
                "impacted_files": results.get("impacted_files", []),
                "impacted_tests": results.get("impacted_tests", [])
            }
        }
        
        if args.format == "json":
            print(json.dumps(payload, indent=2))
        else:
            print(f"💥 Impact Analysis for '{args.symbol}'")
            print(f"Impacted Source Files ({len(results.get('impacted_files', []))}):")
            for f in results.get("impacted_files", []):
                print(f"  - {f}")
            print(f"Impacted Test Files ({len(results.get('impacted_tests', []))}):")
            for f in results.get("impacted_tests", []):
                print(f"  - {f}")

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

    def handle_outline(self, args, context: Context):
        use_case = OutlineUseCase(context.file_system, context.language_parser)
        print(use_case.execute(args.pattern))

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
                    print(f"❌ Invalid selection format: {args.selection}. Use start:end (e.g. 10:20)")
                    return

            print(f"File Path: `file://{os.path.abspath(args.file)}`")
            print(f"Total Lines: {len(lines)}")
            print(f"Total Bytes: {len(content)}")
            print(f"Showing lines {start_line} to {end_line}")
            
            for i in range(start_line - 1, end_line):
                if i < len(lines):
                    print(f"{i+1}: {lines[i]}")
        else:
            print(f"❌ File not found: {args.file}")

    def handle_usages(self, args, context: Context):
        from aide.features.code_inspection.application.find_usages import FindUsagesUseCase
        use_case = FindUsagesUseCase(context.file_system, context.language_parser)
        
        print(f"🔎 Searching for usages of '{args.symbol}' in {args.root}...")
        results = use_case.execute(args.root, args.symbol)
        
        if results:
            print(f"✅ Found {len(results)} usages:")
            for usage in results:
                print(f"   {usage}")
        else:
            print(f"ℹ️  No usages found for '{args.symbol}'")

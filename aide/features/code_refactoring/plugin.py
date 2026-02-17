from argparse import _SubParsersAction
import os
from aide.core.context import Context
from aide.features.code_refactoring.application.smart_rename import SmartRenameUseCase

class RefactorPlugin:
    def register(self, subparsers: _SubParsersAction, context: Context) -> None:
        parser = subparsers.add_parser("move-package", help="Move a package and update references")
        parser.add_argument("src", help="Source package path relative to java-root (e.g. domain/macro)")
        parser.add_argument("dest_package", help="Destination package (e.g. com.istvan.ExoDeck.features.macro.domain)")
        parser.add_argument("--root", default=".", help="Project root")
        parser.add_argument("--java-root", default="app/src/main/java/com/istvan/ExoDeck", help="Java source root")
        parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        parser.set_defaults(func=lambda args: self.handle_move_package(args, context))

        # aide refactor extract
        extract_parser = subparsers.add_parser("extract", help="Extract code block to function")
        extract_parser.add_argument("--file", required=True, help="File path")
        extract_parser.add_argument("--selection", required=True, help="Line range (start:end, 1-based)")
        extract_parser.add_argument("--name", required=True, help="New function name")
        extract_parser.add_argument("--scope", default="private", help="Visibility (private, internal, public)")
        extract_parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        extract_parser.set_defaults(func=lambda args: self.handle_extract(args, context))

        # aide refactor change-signature
        sig_parser = subparsers.add_parser("change-signature", help="Change function signature")
        sig_parser.add_argument("symbol", help="Function name")
        sig_parser.add_argument("--add-param", required=True, help="New parameter definition (e.g. 'x: Int')")
        sig_parser.add_argument("--default-value", required=True, help="Default value for call sites (e.g. '0')")
        sig_parser.add_argument("--root", default=".", help="Root directory")
        sig_parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        sig_parser.set_defaults(func=lambda args: self.handle_change_signature(args, context))

        # aide refactor move-symbol
        move_parser = subparsers.add_parser("move-symbol", help="Move top-level symbol to another file")
        move_parser.add_argument("symbol", help="Symbol name (Function, Class, Object)")
        move_parser.add_argument("--source", required=True, help="Source file path")
        move_parser.add_argument("--dest", required=True, help="Destination file path")
        move_parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        move_parser.set_defaults(func=lambda args: self.handle_move_symbol(args, context))

        # aide refactor rename-symbol
        rename_parser = subparsers.add_parser("rename-symbol", help="Rename symbol project-wide")
        rename_parser.add_argument("old_symbol", help="Current symbol name")
        rename_parser.add_argument("new_symbol", help="New symbol name")
        rename_parser.add_argument("--root", default=".", help="Project root")
        rename_parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        rename_parser.set_defaults(func=lambda args: self.handle_rename_symbol(args, context))

        # aide refactor extract-interface
        ext_int_parser = subparsers.add_parser("extract-interface", help="Extract interface from class")
        ext_int_parser.add_argument("--file", required=True, help="File path")
        ext_int_parser.add_argument("--class-name", required=True, help="Class name to extract from")
        ext_int_parser.add_argument("--interface-name", help="New interface name (default: same as class)")
        ext_int_parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        ext_int_parser.set_defaults(func=lambda args: self.handle_extract_interface(args, context))

    def handle_extract_interface(self, args, context: Context):
        from aide.features.code_refactoring.application.extract_interface import ExtractInterfaceUseCase
        
        print(f"🧬 Extracting interface from '{args.class_name}' in {args.file}...")
        use_case = ExtractInterfaceUseCase(context.file_system, context.language_parser, context.strategy_provider)
        success = use_case.execute(args.file, args.class_name, args.interface_name, dry_run=args.dry_run)
        
        if success:
            print(f"✅ Interface extraction complete.")
        else:
            print(f"❌ Interface extraction failed.")

    def handle_rename_symbol(self, args, context: Context):
        from aide.features.code_refactoring.application.smart_rename import SmartRenameUseCase
        
        use_case = SmartRenameUseCase(context.file_system)
        result = use_case.execute(args.root, args.old_symbol, args.new_symbol, use_word_boundary=True, dry_run=args.dry_run)
        
        if result.success:
            status = "Preview (No changes made)" if args.dry_run else "Success"
            print(f"✅ Rename complete [{status}]. Files changed: {result.files_changed}, Total replacements: {result.total_replacements}")
        else:
            print(f"❌ Rename failed: {result.message}")

    def handle_move_package(self, args, context: Context):
        src_path = os.path.abspath(os.path.join(args.root, args.src))
        java_root = os.path.abspath(os.path.join(args.root, args.java_root))
        
        if not os.path.exists(src_path):
            print(f"❌ Source path does not exist: {src_path}")
            return

        # Infer old package name
        rel_path = os.path.relpath(src_path, java_root)
        if rel_path.startswith(".."):
            print(f"❌ Source path must be inside java-root: {java_root}")
            return
            
        old_package = rel_path.replace(os.sep, ".")
        new_package = args.dest_package
        
        print(f"📦 Moving package: {old_package} -> {new_package}")
        
        # Calculate destination path
        dest_rel_path = new_package.replace(".", os.sep)
        dest_path = os.path.join(java_root, dest_rel_path)
        
        # Move files
        try:
            if args.dry_run:
                print(f"   [Dry Run] Would move files from {src_path} to {dest_path}")
            else:
                print(f"   Moving files from {src_path} to {dest_path}...")
                context.file_system.move_path(src_path, dest_path)
        except Exception as e:
             print(f"❌ Failed to move files: {e}")
             return

        # Smart Rename package refs
        print(f"🔄 Updating references ({old_package} -> {new_package}){' [Dry Run]' if args.dry_run else ''}...")
        use_case = SmartRenameUseCase(context.file_system)
        result = use_case.execute(args.root, old_package, new_package, dry_run=args.dry_run)
        
        if result.success:
            print(f"✅ Move complete.")
            print(f"   Files updated: {result.files_changed}")
            print(f"   Replacements: {result.total_replacements}")
        else:
            print(f"⚠️ Move succeeded but reference update failed: {result.message}")

    def handle_extract(self, args, context: Context):
        from aide.features.code_refactoring.application.extract_function import ExtractFunctionUseCase
        
        file_path = os.path.abspath(args.file)
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return

        print(f"✂️  Extracting to '{args.name}' from {args.file} ({args.selection})...")
        
        use_case = ExtractFunctionUseCase(context.file_system, context.strategy_provider)
        success = use_case.execute(file_path, args.selection, args.name, args.scope, dry_run=args.dry_run)
        
        if success:
            print(f"✅ Extraction complete.")
        else:
            print(f"❌ Extraction failed.")

    def handle_change_signature(self, args, context: Context):
        from aide.features.code_refactoring.application.change_signature import ChangeSignatureUseCase
        
        print(f"🔄 Changing signature for '{args.symbol}'...")
        use_case = ChangeSignatureUseCase(context.file_system, context.language_parser, context.strategy_provider)
        success = use_case.execute(args.root, args.symbol, args.add_param, args.default_value, dry_run=args.dry_run)
        
        if success:
            print(f"✅ Signature update complete.")
        else:
            print(f"❌ Signature update failed.")

    def handle_move_symbol(self, args, context: Context):
        from aide.features.code_refactoring.application.move_symbol import MoveSymbolUseCase
        
        print(f"🚚 Moving symbol '{args.symbol}' to {args.dest}...")
        use_case = MoveSymbolUseCase(context.file_system, context.language_parser, context.strategy_provider)
        success = use_case.execute(args.source, args.symbol, args.dest, dry_run=args.dry_run)
        
        if success:
            status = "Preview (No changes made)" if args.dry_run else ""
            print(f"✅ Move complete. {status}")
        else:
            print(f"❌ Move failed.")

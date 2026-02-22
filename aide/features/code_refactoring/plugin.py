import json
from argparse import _SubParsersAction
import os
from aide.core.context import Context
from aide.features.code_refactoring.application.smart_rename import SmartRenameUseCase

class RefactorPlugin:
    def register(self, subparsers: _SubParsersAction, context: Context) -> None:
        parser = subparsers.add_parser("move-package", help="Move a package/module and update references")
        parser.add_argument("src", help="Source package path relative to src-root (e.g. domain/macro)")
        parser.add_argument("dest_package", help="Destination package/module logic path (e.g. com.istvan.ExoDeck.features.macro.domain or my_app.features.macro)")
        parser.add_argument("--root", default=".", help="Project root")
        parser.add_argument("--src-root", default="app/src/main/java", help="Source root directory containing the packages")
        parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        parser.add_argument("--verify", action="store_true", help="Automatically run tests and revert changes if they fail")
        parser.set_defaults(func=lambda args: self.handle_move_package(args, context))

        # aide refactor extract
        extract_parser = subparsers.add_parser("extract", help="Extract code block to function")
        extract_parser.add_argument("--file", required=True, help="File path")
        extract_parser.add_argument("--selection", required=True, help="Line range (start:end, 1-based)")
        extract_parser.add_argument("--name", required=True, help="New function name")
        extract_parser.add_argument("--scope", default="private", help="Visibility (private, internal, public)")
        extract_parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        extract_parser.add_argument("--verify", action="store_true", help="Automatically run tests and revert changes if they fail")
        extract_parser.set_defaults(func=lambda args: self.handle_extract(args, context))

        # aide refactor change-signature
        sig_parser = subparsers.add_parser("change-signature", help="Change function signature")
        sig_parser.add_argument("symbol", help="Function name")
        sig_parser.add_argument("--add-param", required=True, help="New parameter definition (e.g. 'x: Int')")
        sig_parser.add_argument("--default-value", required=True, help="Default value for call sites (e.g. '0')")
        sig_parser.add_argument("--root", default=".", help="Root directory")
        sig_parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        sig_parser.add_argument("--verify", action="store_true", help="Automatically run tests and revert changes if they fail")
        sig_parser.set_defaults(func=lambda args: self.handle_change_signature(args, context))

        # aide refactor move-symbol
        move_parser = subparsers.add_parser("move-symbol", help="Move top-level symbol to another file")
        move_parser.add_argument("symbol", help="Symbol name (Function, Class, Object)")
        move_parser.add_argument("--source", required=True, help="Source file path")
        move_parser.add_argument("--dest", required=True, help="Destination file path")
        move_parser.add_argument("--root", default=".", help="Project root")
        move_parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        move_parser.add_argument("--verify", action="store_true", help="Automatically run tests and revert changes if they fail")
        move_parser.set_defaults(func=lambda args: self.handle_move_symbol(args, context))

        # aide refactor rename-symbol
        rename_parser = subparsers.add_parser("rename-symbol", help="Rename symbol project-wide")
        rename_parser.add_argument("old_symbol", help="Current symbol name")
        rename_parser.add_argument("new_symbol", help="New symbol name")
        rename_parser.add_argument("--root", default=".", help="Project root")
        rename_parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        rename_parser.add_argument("--verify", action="store_true", help="Automatically run tests and revert changes if they fail")
        rename_parser.set_defaults(func=lambda args: self.handle_rename_symbol(args, context))

        # aide refactor extract-interface
        ext_int_parser = subparsers.add_parser("extract-interface", help="Extract interface from class")
        ext_int_parser.add_argument("--file", required=True, help="File path")
        ext_int_parser.add_argument("--class-name", required=True, help="Class name to extract from")
        ext_int_parser.add_argument("--interface-name", help="New interface name (default: same as class)")
        ext_int_parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        ext_int_parser.add_argument("--verify", action="store_true", help="Automatically run tests and revert changes if they fail")
        ext_int_parser.set_defaults(func=lambda args: self.handle_extract_interface(args, context))

        # aide refactor update-references
        upd_ref_parser = subparsers.add_parser("update-references", help="Update all project references (imports/XML) from an old FQDN to a new FQDN")
        upd_ref_parser.add_argument("old_fqdn", help="Old fully qualified name (e.g. com.example.old.MyClass)")
        upd_ref_parser.add_argument("new_fqdn", help="New fully qualified name (e.g. com.example.new.MyClass)")
        upd_ref_parser.add_argument("--root", default=".", help="Project root")
        upd_ref_parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        upd_ref_parser.add_argument("--verify", action="store_true", help="Automatically run tests and revert changes if they fail")
        upd_ref_parser.set_defaults(func=lambda args: self.handle_update_references(args, context))

        # aide refactor move-file
        mv_file_parser = subparsers.add_parser("move-file", help="Move one or more files and update their internal packages and project-wide references")
        mv_file_parser.add_argument("source", help="Comma-separated list of source file paths")
        mv_file_parser.add_argument("dest_dir", help="Destination directory path")
        mv_file_parser.add_argument("--src-root", default="app/src/main/java", help="Source root directory for JVM package inference")
        mv_file_parser.add_argument("--root", default=".", help="Project root")
        mv_file_parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without writing to files")
        mv_file_parser.add_argument("--verify", action="store_true", help="Automatically run tests and revert changes if they fail")
        mv_file_parser.set_defaults(func=lambda args: self.handle_move_file(args, context))

    def handle_move_file(self, args, context: Context):
        from aide.features.code_refactoring.application.move_file import MoveFileUseCase
        
        reverted = False
        if getattr(args, "verify", False): context.file_system.start_transaction()
        
        sources = [s.strip() for s in args.source.split(',')]
        use_case = MoveFileUseCase(context.file_system, context.strategy_provider)
        res = use_case.execute(sources, args.dest_dir, args.root, args.src_root, dry_run=args.dry_run)
        
        if res.success and getattr(args, "verify", False) and not args.dry_run:
            from aide.features.testing_execution.application.execute_tests import ExecuteTestsUseCase
            test_use_case = ExecuteTestsUseCase(context.file_system)
            test_res = test_use_case.execute(args.root)
            if not test_res.get("success", False):
                context.file_system.rollback()
                res.success = False
                res.message = "Tests failed. Changes reverted."
                reverted = True
            else:
                context.file_system.commit()
        
        result = {
            "success": res.success,
            "message": "Preview (No changes made)" if args.dry_run and res.success else "Success" if res.success else res.message,
            "data": {
                "files_moved": res.files_changed,
                "total_replacements": res.total_replacements,
                "sources": sources,
                "dest_dir": args.dest_dir,
                "reverted": reverted
            }
        }
        print(json.dumps(result, indent=2))

    def handle_update_references(self, args, context: Context):
        from aide.features.code_refactoring.application.update_refs import UpdateReferencesUseCase
        
        reverted = False
        if getattr(args, "verify", False): context.file_system.start_transaction()
        
        use_case = UpdateReferencesUseCase(context.file_system)
        res = use_case.execute(args.root, args.old_fqdn, args.new_fqdn, dry_run=args.dry_run)
        
        if res.success and getattr(args, "verify", False) and not args.dry_run:
            from aide.features.testing_execution.application.execute_tests import ExecuteTestsUseCase
            test_use_case = ExecuteTestsUseCase(context.file_system)
            test_res = test_use_case.execute(args.root)
            if not test_res.get("success", False):
                context.file_system.rollback()
                res.success = False
                res.message = "Tests failed. Changes reverted."
                reverted = True
            else:
                context.file_system.commit()
        
        result = {
            "success": res.success,
            "message": "Preview (No changes made)" if args.dry_run and res.success else "Success" if res.success else res.message,
            "data": {
                "files_changed": res.files_changed,
                "total_replacements": res.total_replacements,
                "old_fqdn": args.old_fqdn,
                "new_fqdn": args.new_fqdn,
                "reverted": reverted
            }
        }
        print(json.dumps(result, indent=2))

    def handle_extract_interface(self, args, context: Context):
        from aide.features.code_refactoring.application.extract_interface import ExtractInterfaceUseCase
        
        reverted = False
        if getattr(args, "verify", False): context.file_system.start_transaction()
        
        use_case = ExtractInterfaceUseCase(context.file_system, context.language_parser, context.strategy_provider)
        success = use_case.execute(args.file, args.class_name, args.interface_name, dry_run=args.dry_run)
        
        if success and getattr(args, "verify", False) and not args.dry_run:
            from aide.features.testing_execution.application.execute_tests import ExecuteTestsUseCase
            test_use_case = ExecuteTestsUseCase(context.file_system)
            test_res = test_use_case.execute(args.root_path if hasattr(args, "root_path") else ".")
            if not test_res.get("success", False):
                context.file_system.rollback()
                success = False
                reverted = True
            else:
                context.file_system.commit()
        
        result = {
            "success": success,
            "message": "Interface extraction complete." if success else "Interface extraction failed.",
            "data": {
                "file": args.file,
                "class_name": args.class_name,
                "interface_name": args.interface_name,
                "dry_run": args.dry_run,
                "reverted": reverted
            }
        }
        print(json.dumps(result, indent=2))

    def handle_rename_symbol(self, args, context: Context):
        from aide.features.code_refactoring.application.smart_rename import SmartRenameUseCase
        
        reverted = False
        if getattr(args, "verify", False): context.file_system.start_transaction()
        
        use_case = SmartRenameUseCase(context.file_system)
        res = use_case.execute(args.root, args.old_symbol, args.new_symbol, use_word_boundary=True, dry_run=args.dry_run)
        
        if res.success and getattr(args, "verify", False) and not args.dry_run:
            from aide.features.testing_execution.application.execute_tests import ExecuteTestsUseCase
            test_use_case = ExecuteTestsUseCase(context.file_system)
            test_res = test_use_case.execute(args.root)
            if not test_res.get("success", False):
                context.file_system.rollback()
                res.success = False
                res.message = "Tests failed. Changes reverted."
                reverted = True
            else:
                context.file_system.commit()
        
        result = {
            "success": res.success,
            "message": "Preview (No changes made)" if args.dry_run and res.success else "Success" if res.success else res.message,
            "data": {
                "files_changed": res.files_changed,
                "total_replacements": res.total_replacements,
                "old_symbol": args.old_symbol,
                "new_symbol": args.new_symbol,
                "reverted": reverted
            }
        }
        print(json.dumps(result, indent=2))

    def handle_move_package(self, args, context: Context):
        src_path = os.path.abspath(os.path.join(args.root, args.src))
        src_root = os.path.abspath(os.path.join(args.root, args.src_root))
        
        if not os.path.exists(src_path):
            print(json.dumps({"success": False, "error": f"Source path does not exist: {src_path}"}))
            return

        # Infer old package/module name
        rel_path = os.path.relpath(src_path, src_root)
        if rel_path.startswith(".."):
            print(json.dumps({"success": False, "error": f"Source path must be inside src-root: {src_root}"}))
            return
            
        old_package = rel_path.replace(os.sep, ".")
        new_package = args.dest_package
        
        reverted = False
        if getattr(args, "verify", False): context.file_system.start_transaction()
        
        # Calculate destination path (assume standard dot-to-slash mapping)
        dest_rel_path = new_package.replace(".", os.sep)
        dest_path = os.path.join(src_root, dest_rel_path)
        
        # Move files
        moved_success = True
        try:
            if not args.dry_run:
                context.file_system.move_path(src_path, dest_path)
                # Cleanup old empty parent folders up to src-root
                context.file_system.delete_empty_parents(src_path, src_root)
        except Exception as e:
             if getattr(args, "verify", False): context.file_system.rollback()
             print(json.dumps({"success": False, "error": f"Failed to move files: {e}"}))
             return

        # Smart Rename package refs
        use_case = SmartRenameUseCase(context.file_system)
        res = use_case.execute(args.root, old_package, new_package, dry_run=args.dry_run)
        
        if res.success and getattr(args, "verify", False) and not args.dry_run:
            from aide.features.testing_execution.application.execute_tests import ExecuteTestsUseCase
            test_use_case = ExecuteTestsUseCase(context.file_system)
            test_res = test_use_case.execute(args.root)
            if not test_res.get("success", False):
                context.file_system.rollback()
                res.success = False
                reverted = True
            else:
                context.file_system.commit()
        
        result = {
            "success": res.success,
            "message": "Move complete." if res.success else f"Move succeeded but reference update failed: {res.message}",
            "data": {
                "old_package": old_package,
                "new_package": new_package,
                "files_updated": res.files_changed,
                "replacements": res.total_replacements,
                "dry_run": args.dry_run,
                "reverted": reverted
            }
        }
        print(json.dumps(result, indent=2))

    def handle_extract(self, args, context: Context):
        from aide.features.code_refactoring.application.extract_function import ExtractFunctionUseCase
        
        file_path = os.path.abspath(args.file)
        if not os.path.exists(file_path):
            print(json.dumps({"success": False, "error": f"File not found: {file_path}"}))
            return
        
        use_case = ExtractFunctionUseCase(context.file_system, context.strategy_provider)
        
        reverted = False
        if getattr(args, "verify", False): context.file_system.start_transaction()
        
        success = use_case.execute(file_path, args.selection, args.name, args.scope, dry_run=args.dry_run)
        
        if success and getattr(args, "verify", False) and not args.dry_run:
            from aide.features.testing_execution.application.execute_tests import ExecuteTestsUseCase
            test_use_case = ExecuteTestsUseCase(context.file_system)
            test_res = test_use_case.execute(".")
            if not test_res.get("success", False):
                context.file_system.rollback()
                success = False
                reverted = True
            else:
                context.file_system.commit()
        
        result = {
            "success": success,
            "message": "Extraction complete." if success else "Extraction failed.",
            "data": {
                "file": args.file,
                "selection": args.selection,
                "name": args.name,
                "dry_run": args.dry_run,
                "reverted": reverted
            }
        }
        print(json.dumps(result, indent=2))

    def handle_change_signature(self, args, context: Context):
        from aide.features.code_refactoring.application.change_signature import ChangeSignatureUseCase
        
        reverted = False
        if getattr(args, "verify", False): context.file_system.start_transaction()
        
        use_case = ChangeSignatureUseCase(context.file_system, context.language_parser, context.strategy_provider)
        success = use_case.execute(args.root, args.symbol, args.add_param, args.default_value, dry_run=args.dry_run)
        
        if success and getattr(args, "verify", False) and not args.dry_run:
            from aide.features.testing_execution.application.execute_tests import ExecuteTestsUseCase
            test_use_case = ExecuteTestsUseCase(context.file_system)
            test_res = test_use_case.execute(args.root)
            if not test_res.get("success", False):
                context.file_system.rollback()
                success = False
                reverted = True
            else:
                context.file_system.commit()
        
        result = {
            "success": success,
            "message": "Signature update complete." if success else "Signature update failed.",
            "data": {
                "symbol": args.symbol,
                "add_param": args.add_param,
                "default_value": args.default_value,
                "dry_run": args.dry_run,
                "reverted": reverted
            }
        }
        print(json.dumps(result, indent=2))

    def handle_move_symbol(self, args, context: Context):
        from aide.features.code_refactoring.application.move_symbol import MoveSymbolUseCase
        
        reverted = False
        if getattr(args, "verify", False): context.file_system.start_transaction()
        
        use_case = MoveSymbolUseCase(context.file_system, context.language_parser, context.strategy_provider)
        success = use_case.execute(args.source, args.symbol, args.dest, dry_run=args.dry_run, root_path=args.root)
        
        if success and getattr(args, "verify", False) and not args.dry_run:
            from aide.features.testing_execution.application.execute_tests import ExecuteTestsUseCase
            test_use_case = ExecuteTestsUseCase(context.file_system)
            test_res = test_use_case.execute(args.root)
            if not test_res.get("success", False):
                context.file_system.rollback()
                success = False
                reverted = True
            else:
                context.file_system.commit()
        
        result = {
            "success": success,
            "message": "Move complete." if success else "Move failed.",
            "data": {
                "symbol": args.symbol,
                "source": args.source,
                "dest": args.dest,
                "dry_run": args.dry_run,
                "reverted": reverted
            }
        }
        print(json.dumps(result, indent=2))

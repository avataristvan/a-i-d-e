import json
from argparse import _SubParsersAction

from aide.core.context import Context
from aide.plugin_system.infrastructure.command_catalog import add_notes

_SEMGREP_NOTES = """
Requires semgrep (pip install semgrep). Patterns use semgrep metavariables ($X, $Y, ...);
always single-quote them in the shell. --lang: python, kotlin, typescript, javascript, java, go, rust, ruby, ...
  aide structural-search --pattern 'if $X: return $X' --lang python --root src/
  aide structural-replace --pattern 'old_api($X)' --rewrite 'new_api($X)' --lang python --dry-run
"""

_SEMGREP_REPLACE_NOTES = """
See `aide structural-search --help` for pattern syntax and examples.
"""
from aide.features.structural_search.domain.ports import SemgrepRunnerPort


class StructuralSearchPlugin:
    def register(self, subparsers: _SubParsersAction, context: Context) -> None:
        from aide.features.structural_search.infrastructure.semgrep_runner import SemgrepRunner
        context.register(SemgrepRunnerPort, SemgrepRunner())

        p = subparsers.add_parser("structural-search", help="AST-aware pattern search via semgrep")
        p.add_argument("--pattern", required=True, help="Semgrep pattern, e.g. 'if $X: return $X'")
        p.add_argument("--lang", required=True, help="Language: python, kotlin, typescript, java, go, ...")
        p.add_argument("--root", default=".", help="Root directory to search (default: .)")
        add_notes(p, _SEMGREP_NOTES)
        p.set_defaults(func=lambda args: self._handle_search(args, context))

        p = subparsers.add_parser("structural-replace", help="AST-aware pattern replace via semgrep")
        p.add_argument("--pattern", required=True, help="Semgrep pattern to match")
        p.add_argument("--rewrite", required=True, help="Replacement expression")
        p.add_argument("--lang", required=True, help="Language")
        p.add_argument("--root", default=".", help="Root directory (default: .)")
        p.add_argument("--dry-run", action="store_true", help="Preview changes without writing to disk")
        add_notes(p, _SEMGREP_REPLACE_NOTES)
        p.set_defaults(func=lambda args: self._handle_replace(args, context))

    def _handle_search(self, args, context: Context) -> None:
        from aide.features.structural_search.application.structural_search import StructuralSearchUseCase
        runner = self._resolve(context)
        if runner is None:
            return
        matches = StructuralSearchUseCase(runner).execute(args.pattern, args.lang, args.root)
        print(json.dumps({
            "success": True,
            "message": f"Found {len(matches)} match(es).",
            "data": {
                "pattern": args.pattern,
                "lang": args.lang,
                "root": args.root,
                "matches": [
                    {
                        "file": m.file,
                        "line": m.line,
                        "column": m.column,
                        "end_line": m.end_line,
                        "end_column": m.end_column,
                        "match_text": m.match_text,
                    }
                    for m in matches
                ],
            },
        }, indent=2))

    def _handle_replace(self, args, context: Context) -> None:
        from aide.features.structural_search.application.structural_replace import StructuralReplaceUseCase
        runner = self._resolve(context)
        if runner is None:
            return
        result = StructuralReplaceUseCase(runner).execute(
            args.pattern, args.rewrite, args.lang, args.root, args.dry_run
        )
        action = "Would modify" if result.dry_run else "Modified"
        print(json.dumps({
            "success": True,
            "message": f"{action} {len(result.files_modified)} file(s), {result.total_fixes} fix(es).",
            "data": {
                "pattern": args.pattern,
                "rewrite": args.rewrite,
                "lang": args.lang,
                "dry_run": result.dry_run,
                "files_modified": result.files_modified,
                "total_fixes": result.total_fixes,
            },
        }, indent=2))

    def _resolve(self, context: Context) -> SemgrepRunnerPort | None:
        try:
            return context.resolve(SemgrepRunnerPort)
        except KeyError:
            print(json.dumps({"success": False, "error": "semgrep is not installed. Run: pip install semgrep"}))
            return None

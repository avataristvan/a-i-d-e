import json
from argparse import _SubParsersAction
from datetime import datetime, timezone

from aide.core.context import Context
from aide.features.symbol_history.domain.ports import GitPort


class SymbolHistoryPlugin:
    def register(self, subparsers: _SubParsersAction, context: Context) -> None:
        from aide.features.symbol_history.infrastructure.git_runner import GitRunner
        context.register(GitPort, GitRunner())

        p = subparsers.add_parser("symbol-blame", help="Git blame at symbol granularity")
        p.add_argument("--file", required=True, help="Source file path")
        p.add_argument("--symbol", required=True, help="Symbol name (class or function)")
        p.set_defaults(func=lambda args: self._handle_blame(args, context))

        p = subparsers.add_parser("symbol-history", help="Commit history for a symbol's line range")
        p.add_argument("--file", required=True, help="Source file path")
        p.add_argument("--symbol", required=True, help="Symbol name (class or function)")
        p.add_argument("--limit", type=int, default=10, help="Max commits to return (default: 10)")
        p.set_defaults(func=lambda args: self._handle_history(args, context))

    def _handle_blame(self, args, context: Context) -> None:
        from aide.features.symbol_history.application.symbol_blame import SymbolBlameUseCase
        from aide.features.symbol_history.application.symbol_locator import SymbolNotFoundError
        try:
            lines = SymbolBlameUseCase(
                context.file_system, context.language_parser, context.resolve(GitPort)
            ).execute(args.file, args.symbol)
        except SymbolNotFoundError as e:
            print(json.dumps({"success": False, "error": str(e)}))
            return

        print(json.dumps({
            "success": True,
            "message": f"Blame for '{args.symbol}' ({len(lines)} lines).",
            "data": {
                "file": args.file,
                "symbol": args.symbol,
                "lines": [
                    {
                        "line": l.line_number,
                        "content": l.content,
                        "commit": l.commit_hash[:8],
                        "author": l.author,
                        "date": _iso(l.timestamp),
                        "summary": l.summary,
                    }
                    for l in lines
                ],
            },
        }, indent=2))

    def _handle_history(self, args, context: Context) -> None:
        from aide.features.symbol_history.application.symbol_history import SymbolHistoryUseCase
        from aide.features.symbol_history.application.symbol_locator import SymbolNotFoundError
        try:
            commits = SymbolHistoryUseCase(
                context.file_system, context.language_parser, context.resolve(GitPort)
            ).execute(args.file, args.symbol, args.limit)
        except SymbolNotFoundError as e:
            print(json.dumps({"success": False, "error": str(e)}))
            return

        print(json.dumps({
            "success": True,
            "message": f"Found {len(commits)} commit(s) touching '{args.symbol}'.",
            "data": {
                "file": args.file,
                "symbol": args.symbol,
                "commits": [
                    {
                        "hash": c.hash[:8],
                        "full_hash": c.hash,
                        "author": c.author,
                        "date": _iso(c.timestamp),
                        "message": c.message,
                    }
                    for c in commits
                ],
            },
        }, indent=2))


def _iso(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")

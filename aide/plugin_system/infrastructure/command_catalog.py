"""Progressive command discovery, derived from what the plugins registered (never a hand-kept list):
`aide commands` -> categories, `aide commands <category>` -> commands with one-liners,
`aide <command> --help` -> exact arguments and usage notes."""
import argparse
import json
import textwrap
from argparse import _SubParsersAction


def add_notes(parser: argparse.ArgumentParser, notes: str) -> None:
    """Attaches usage notes shown by `aide <command> --help`, kept verbatim (line breaks preserved)."""
    parser.epilog = textwrap.dedent(notes).strip()
    parser.formatter_class = argparse.RawDescriptionHelpFormatter


def register_commands_command(subparsers: _SubParsersAction, categories: dict[str, str]) -> None:
    one_liners = {action.dest: action.help or "" for action in subparsers._choices_actions}

    def handle(args) -> None:
        by_category: dict[str, list[str]] = {}
        for command, category in sorted(categories.items()):
            by_category.setdefault(category, []).append(command)

        if not args.category:
            data = {
                "categories": [f"{c} ({len(cmds)})" for c, cmds in sorted(by_category.items())],
                "next": "aide commands <category>",
            }
        elif args.category in by_category:
            data = {
                "category": args.category,
                "commands": {c: one_liners.get(c, "") for c in by_category[args.category]},
                "next": "aide <command> --help",
            }
        else:
            print(json.dumps({"success": False, "message": f"Unknown category '{args.category}'",
                              "data": {"categories": sorted(by_category)}}, indent=2))
            return
        print(json.dumps({"success": True, "message": "Success", "data": data}, indent=2))

    parser = subparsers.add_parser("commands", help="Discover commands: categories, then the commands in one")
    parser.add_argument("category", nargs="?", help="Category name from `aide commands`")
    parser.set_defaults(func=handle)

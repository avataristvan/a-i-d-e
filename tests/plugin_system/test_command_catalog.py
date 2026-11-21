import json
import subprocess
import sys
from pathlib import Path

AIDE = str(Path(__file__).resolve().parents[2] / "aide.py")


def _run(*args):
    out = subprocess.run([sys.executable, AIDE, *args], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def test_every_command_is_reachable_through_exactly_one_category():
    categories = [c.rsplit(" (", 1)[0] for c in _run("commands")["data"]["categories"]]
    seen = {}
    for category in categories:
        for command, summary in _run("commands", category)["data"]["commands"].items():
            assert command not in seen, f"{command} in {seen.get(command)} and {category}"
            assert summary, f"{command} has no one-line help"
            seen[command] = category
    assert {"rename-symbol", "move-symbol", "outline", "test"} <= set(seen)


def test_unknown_category_lists_valid_ones():
    payload = _run("commands", "nope")
    assert not payload["success"] and "code_refactoring" in payload["data"]["categories"]


def test_usage_notes_appear_in_command_help():
    out = subprocess.run([sys.executable, AIDE, "rename-symbol", "--help"], capture_output=True, text=True).stdout
    assert "nested git worktrees" in out

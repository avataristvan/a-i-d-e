import json
import os
import shutil
import subprocess

HELPER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ts_rename.cjs")


class TsRenameError(RuntimeError):
    pass


def find_rename_locations(root: str, file: str, symbol: str, line: int | None = None,
                          in_strings: bool = False, in_comments: bool = False,
                          timeout: float = 300.0) -> dict:
    """Runs the Node helper against the project's own TypeScript. Returns its JSON payload
    (locations with 0-based line and UTF-16 character, as LSP positions)."""
    node = shutil.which("node")
    if node is None:
        raise TsRenameError("Semantic TS/JS rename needs 'node' on PATH")
    request = {"root": os.path.abspath(root), "file": os.path.abspath(file), "symbol": symbol,
               "line": line, "findInStrings": in_strings, "findInComments": in_comments}
    proc = subprocess.run([node, HELPER], input=json.dumps(request), capture_output=True,
                          text=True, timeout=timeout)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise TsRenameError(f"TS rename helper failed: {(proc.stderr or proc.stdout).strip()[:2000]}")
    if not payload.get("ok"):
        raise TsRenameError(payload.get("message", "TS rename helper failed"))
    return payload

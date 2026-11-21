import os
import subprocess


def filter_project_files(root: str, files: list[str]) -> tuple[list[str], list[str]]:
    """Splits files into (kept, excluded). Excluded: inside a nested git repo or worktree below root
    (a directory with its own .git, e.g. .claude/worktrees/agent-*) or gitignored. Outside a git
    repo nothing is gitignored. Mirrors the exclusion in ts_rename.cjs."""
    root = os.path.abspath(root)
    nested: dict[str, bool] = {}

    def in_nested_repo(path: str) -> bool:
        d = os.path.dirname(path)
        chain = []
        hit = False
        while len(d) > len(root) and d.startswith(root):
            if d in nested:
                hit = nested[d]
                break
            chain.append(d)
            if os.path.exists(os.path.join(d, ".git")):
                hit = True
                break
            d = os.path.dirname(d)
        for c in chain:
            nested[c] = hit
        return hit

    candidates = [f for f in files if not in_nested_repo(os.path.abspath(f))]
    ignored: set[str] = set()
    if candidates:
        try:
            proc = subprocess.run(["git", "-C", root, "check-ignore", "--stdin"], input="\n".join(candidates),
                                  capture_output=True, text=True, timeout=60)
            if proc.returncode in (0, 1):
                ignored = {os.path.abspath(os.path.join(root, p)) for p in proc.stdout.splitlines() if p}
        except (OSError, subprocess.TimeoutExpired):
            pass
    kept = [f for f in candidates if os.path.abspath(f) not in ignored]
    kept_set = set(kept)
    return kept, [f for f in files if f not in kept_set]

import subprocess
from datetime import datetime, timezone

from aide.features.symbol_history.domain.ports import GitPort, BlameLine, CommitInfo

_COMMIT_SEP = "\x1f"


class GitRunner(GitPort):
    def blame(self, file_path: str, start_line: int, end_line: int) -> list[BlameLine]:
        result = self._run(
            ["git", "blame", "--porcelain", f"-L{start_line},{end_line}", file_path]
        )
        return self._parse_blame(result.stdout)

    def log(self, file_path: str, start_line: int, end_line: int, limit: int) -> list[CommitInfo]:
        fmt = f"COMMIT %H{_COMMIT_SEP}%an{_COMMIT_SEP}%ae{_COMMIT_SEP}%at{_COMMIT_SEP}%s"
        result = self._run(
            ["git", "log", f"-L{start_line},{end_line}:{file_path}",
             f"--max-count={limit}", f"--pretty=format:{fmt}", "-s"]
        )
        return self._parse_log(result.stdout)

    # --- parsing ---

    def _parse_blame(self, output: str) -> list[BlameLine]:
        # Porcelain format: metadata is only emitted on the first occurrence of each commit.
        # Subsequent lines with the same commit only carry hash + line numbers.
        # We cache per-commit metadata and merge it on reuse.
        lines: list[BlameLine] = []
        commit_cache: dict[str, dict] = {}
        current: dict = {}

        for raw in output.splitlines():
            if raw.startswith("\t"):
                meta = commit_cache.get(current["hash"], {})
                lines.append(BlameLine(
                    line_number=current["final_line"],
                    content=raw[1:],
                    commit_hash=current["hash"],
                    author=meta.get("author", ""),
                    author_email=meta.get("author-mail", ""),
                    timestamp=int(meta.get("author-time", 0)),
                    summary=meta.get("summary", ""),
                ))
            elif " " in raw and len(raw.split()[0]) == 40:
                parts = raw.split()
                h = parts[0]
                current = {"hash": h, "final_line": int(parts[2])}
                if h not in commit_cache:
                    commit_cache[h] = {}
            else:
                key, _, value = raw.partition(" ")
                current[key] = value
                commit_cache.setdefault(current["hash"], {})[key] = value

        return lines

    def _parse_log(self, output: str) -> list[CommitInfo]:
        commits = []
        for line in output.splitlines():
            if not line.startswith("COMMIT "):
                continue
            parts = line[len("COMMIT "):].split(_COMMIT_SEP, 4)
            if len(parts) < 5:
                continue
            commits.append(CommitInfo(
                hash=parts[0],
                author=parts[1],
                author_email=parts[2],
                timestamp=int(parts[3]),
                message=parts[4],
            ))
        return commits

    def _run(self, cmd: list[str]) -> subprocess.CompletedProcess:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"git error: {result.stderr.strip()}")
        return result

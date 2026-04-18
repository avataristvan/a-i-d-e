import json
import subprocess

from aide.features.structural_search.domain.ports import SemgrepRunnerPort, SemgrepMatch, SemgrepReplaceResult


class SemgrepRunner(SemgrepRunnerPort):
    def search(self, pattern: str, lang: str, root: str) -> list[SemgrepMatch]:
        result = self._run(["semgrep", "scan", "--pattern", pattern, "--lang", lang, "--json", root])
        data = json.loads(result.stdout)
        return [self._to_match(r) for r in data.get("results", [])]

    def replace(self, pattern: str, rewrite: str, lang: str, root: str, dry_run: bool) -> SemgrepReplaceResult:
        cmd = ["semgrep", "scan", "--pattern", pattern, "--replacement", rewrite, "--lang", lang, "--json"]
        if dry_run:
            cmd.append("--dryrun")
        else:
            cmd.append("--autofix")
        cmd.append(root)
        data = json.loads(self._run(cmd).stdout)
        results = data.get("results", [])
        return SemgrepReplaceResult(
            files_modified=sorted({r["path"] for r in results}),
            total_fixes=len(results),
            dry_run=dry_run,
        )

    def _run(self, cmd: list[str]) -> subprocess.CompletedProcess:
        result = subprocess.run(cmd, capture_output=True, text=True)
        # semgrep exits 1 on findings (older versions); > 1 means an actual error
        if result.returncode > 1:
            raise RuntimeError(f"semgrep error (exit {result.returncode}): {result.stderr.strip()}")
        return result

    def _to_match(self, r: dict) -> SemgrepMatch:
        # extra.lines requires semgrep login; extra.message contains the matched source text
        match_text = r["extra"].get("message") or r["extra"].get("lines", "")
        return SemgrepMatch(
            file=r["path"],
            line=r["start"]["line"],
            column=r["start"]["col"],
            end_line=r["end"]["line"],
            end_column=r["end"]["col"],
            match_text=match_text.strip(),
        )

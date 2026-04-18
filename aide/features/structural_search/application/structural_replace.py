from aide.features.structural_search.domain.ports import SemgrepRunnerPort, SemgrepReplaceResult


class StructuralReplaceUseCase:
    def __init__(self, semgrep_runner: SemgrepRunnerPort) -> None:
        self.semgrep_runner = semgrep_runner

    def execute(self, pattern: str, rewrite: str, lang: str, root: str, dry_run: bool) -> SemgrepReplaceResult:
        return self.semgrep_runner.replace(pattern, rewrite, lang, root, dry_run)

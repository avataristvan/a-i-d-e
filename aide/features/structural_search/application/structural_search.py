from aide.features.structural_search.domain.ports import SemgrepRunnerPort, SemgrepMatch


class StructuralSearchUseCase:
    def __init__(self, semgrep_runner: SemgrepRunnerPort) -> None:
        self.semgrep_runner = semgrep_runner

    def execute(self, pattern: str, lang: str, root: str) -> list[SemgrepMatch]:
        return self.semgrep_runner.search(pattern, lang, root)

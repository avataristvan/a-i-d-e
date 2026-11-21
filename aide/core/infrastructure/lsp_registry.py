import os
import shutil
from dataclasses import dataclass, field

from aide.core.domain.ports import LanguageServerPort, LanguageServerProviderPort
from aide.core.infrastructure.lsp_client import LspError, StdioLspClient


@dataclass(frozen=True)
class ServerSpec:
    """How to start one language server. Server-specific knowledge lives here, not in the client."""
    name: str
    command: tuple[str, ...]
    language_ids: dict[str, str] = field(hash=False)
    init_timeout: float = 30.0
    request_timeout: float = 30.0
    # Log line that marks the end of the initial workspace scan, for servers that do not
    # report it via $/progress. Without it, early queries return partial results.
    ready_log_pattern: str | None = None
    env: dict[str, str] | None = field(default=None, hash=False)

    def is_available(self) -> bool:
        return shutil.which(self.command[0]) is not None


CLANGD = ServerSpec("clangd", ("clangd", "--log=error"), {
    ".c": "c", ".h": "cpp", ".cc": "cpp", ".cpp": "cpp", ".cxx": "cpp", ".hpp": "cpp", ".hh": "cpp",
})

DEFAULT_SERVERS: tuple[ServerSpec, ...] = (
    ServerSpec("pyright", ("pyright-langserver", "--stdio"), {".py": "python", ".pyi": "python"},
               ready_log_pattern=r"Found \d+ source files?"),
    ServerSpec("typescript", ("typescript-language-server", "--stdio"), {
        ".ts": "typescript", ".tsx": "typescriptreact", ".mts": "typescript", ".cts": "typescript",
        ".js": "javascript", ".jsx": "javascriptreact", ".mjs": "javascript", ".cjs": "javascript",
    }),
    CLANGD,
    # JetBrains kotlin-lsp ships its own JBR; expects `kotlin-lsp` on PATH pointing at bin/intellij-server.
    # Start behaviour not yet verified against a real project (Kotlin spike pending).
    ServerSpec("kotlin", ("kotlin-lsp", "--stdio"), {".kt": "kotlin", ".kts": "kotlin"},
               init_timeout=300.0, request_timeout=120.0),
)


class LanguageServerProvider(LanguageServerProviderPort):
    """Starts at most one server per spec, rooted at the workspace root, on first use."""

    def __init__(self, root_path: str, specs: tuple[ServerSpec, ...] = DEFAULT_SERVERS):
        self._root = os.path.abspath(root_path)
        self._specs = specs
        self._running: dict[str, StdioLspClient] = {}

    def spec_for(self, file_path: str) -> ServerSpec | None:
        ext = os.path.splitext(file_path)[1]
        return next((s for s in self._specs if ext in s.language_ids), None)

    def for_file(self, file_path: str) -> LanguageServerPort | None:
        spec = self.spec_for(file_path)
        if spec is None:
            return None
        client = self._running.get(spec.name)
        if client is None:
            if not spec.is_available():
                return None
            client = StdioLspClient(list(spec.command), root_path=self._root, language_ids=spec.language_ids,
                                    init_timeout=spec.init_timeout, request_timeout=spec.request_timeout,
                                    ready_log_pattern=spec.ready_log_pattern, env=spec.env)
            try:
                client.start()
            except Exception:
                client.stop()
                raise
            if not client.wait_until_ready(spec.init_timeout):
                client.stop()
                raise LspError(f"{spec.name} did not finish indexing within {spec.init_timeout:.0f}s; "
                               "refusing to run queries against a partial index")
            self._running[spec.name] = client
        return client

    def stop_all(self) -> None:
        for client in self._running.values():
            client.stop()
        self._running.clear()

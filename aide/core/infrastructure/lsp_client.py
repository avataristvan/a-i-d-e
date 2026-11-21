import atexit
import json
import os
import queue
import re
import subprocess
import threading
import time
from typing import Any, Optional

from aide.core.domain.ports import LanguageServerPort
from aide.core.domain.workspace_edit import path_to_uri


class LspError(RuntimeError):
    pass


class StdioLspClient(LanguageServerPort):
    """Generic LSP client speaking JSON-RPC over a server process's stdio.

    A reader thread parses framed messages: responses go to a queue for the waiting
    request, server->client requests are answered immediately (servers like pyright
    block until workspace/configuration is answered), and diagnostics are collected.
    """

    def __init__(self, command: list[str], root_path: str | None = None,
                 language_ids: dict[str, str] | None = None,
                 init_timeout: float = 30.0, request_timeout: float = 30.0,
                 ready_log_pattern: str | None = None, env: dict[str, str] | None = None):
        self._command = command
        self._root = os.path.abspath(root_path) if root_path else None
        self._language_ids = language_ids or {}
        self._init_timeout = init_timeout
        self._request_timeout = request_timeout
        self._ready_pattern = re.compile(ready_log_pattern) if ready_log_pattern else None
        self._env = env
        self._ready_logged = threading.Event()
        self._active_progress: set[Any] = set()
        self._proc: Optional[subprocess.Popen[bytes]] = None
        self._seq = 0
        self._write_lock = threading.Lock()
        self._responses: "queue.Queue[dict]" = queue.Queue()
        self._open_uris: set[str] = set()
        self.diagnostics: dict[str, list[dict]] = {}

    # --- lifecycle ---

    def start(self) -> None:
        self._proc = subprocess.Popen(
            self._command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=self._root,
            env={**os.environ, **self._env} if self._env else None,
        )
        threading.Thread(target=self._read_loop, daemon=True).start()
        atexit.register(self.stop)
        self._initialize()

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            try:
                self._send({"jsonrpc": "2.0", "id": self._next_id(), "method": "shutdown", "params": None})
                self.notify("exit", None)
            except Exception:
                pass
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None

    def wait_until_ready(self, timeout: float) -> bool:
        """Waits until the server has finished its initial workspace scan: the server-specific
        ready log line was seen (if one is configured) and no work-done progress is open.
        Queries sent earlier can silently return partial results (e.g. a rename touching one file)."""
        deadline = time.monotonic() + timeout
        if self._ready_pattern and not self._ready_logged.wait(timeout):
            return False
        while self._active_progress:
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.05)
        return True

    # --- LanguageServerPort ---

    def open_document(self, file_path: str, text: str | None = None) -> None:
        uri = path_to_uri(file_path)
        if text is None:
            with open(file_path, encoding="utf-8") as f:
                text = f.read()
        if uri in self._open_uris:
            self.close_document(file_path)
        self._open_uris.add(uri)
        self.notify("textDocument/didOpen", {
            "textDocument": {"uri": uri, "languageId": self._language_id(file_path), "version": 1, "text": text}
        })

    def close_document(self, file_path: str) -> None:
        uri = path_to_uri(file_path)
        if uri in self._open_uris:
            self._open_uris.discard(uri)
            self.notify("textDocument/didClose", {"textDocument": {"uri": uri}})

    def document_symbols(self, file_path: str) -> list[dict]:
        result = self.request("textDocument/documentSymbol", {"textDocument": {"uri": path_to_uri(file_path)}})
        return result if isinstance(result, list) else []

    def workspace_symbols(self, query: str) -> list[dict]:
        result = self.request("workspace/symbol", {"query": query})
        return result if isinstance(result, list) else []

    def references(self, file_path: str, line: int, character: int) -> list[dict]:
        result = self.request("textDocument/references", {
            **self._position(file_path, line, character),
            "context": {"includeDeclaration": True},
        })
        return result if isinstance(result, list) else []

    def rename(self, file_path: str, line: int, character: int, new_name: str) -> dict | None:
        result = self.request("textDocument/rename", {
            **self._position(file_path, line, character),
            "newName": new_name,
        })
        return result if isinstance(result, dict) else None

    # --- JSON-RPC ---

    def request(self, method: str, params: Any, timeout: float | None = None) -> Any:
        if self._proc is None:
            raise LspError(f"Language server {self._command[0]} is not running")
        req_id = self._next_id()
        self._send({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
        wait = timeout if timeout is not None else self._request_timeout
        while True:
            try:
                msg = self._responses.get(timeout=wait)
            except queue.Empty:
                raise LspError(f"{method} timed out after {wait:.0f}s ({self._command[0]})")
            if msg.get("id") != req_id:
                continue  # late response to an earlier, timed-out request
            if "error" in msg:
                raise LspError(f"{method}: {msg['error'].get('message', msg['error'])}")
            return msg.get("result")

    def notify(self, method: str, params: Any) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    # --- private ---

    def _initialize(self) -> None:
        root_uri = path_to_uri(self._root) if self._root else None
        self.request("initialize", {
            "processId": os.getpid(),
            "rootUri": root_uri,
            "rootPath": self._root,
            "workspaceFolders": [{"uri": root_uri, "name": os.path.basename(self._root)}] if root_uri and self._root else None,
            "capabilities": {
                "workspace": {
                    "workspaceEdit": {"documentChanges": True, "resourceOperations": ["create", "rename", "delete"]},
                    "configuration": True,
                    "workspaceFolders": True,
                    "symbol": {},
                },
                "textDocument": {
                    "documentSymbol": {"hierarchicalDocumentSymbolSupport": True},
                    "rename": {"prepareSupport": False},
                    "references": {},
                    "publishDiagnostics": {},
                    "synchronization": {},
                },
                "window": {"workDoneProgress": True},
            },
        }, timeout=self._init_timeout)
        self.notify("initialized", {})

    def _position(self, file_path: str, line: int, character: int) -> dict:
        return {"textDocument": {"uri": path_to_uri(file_path)}, "position": {"line": line, "character": character}}

    def _language_id(self, file_path: str) -> str:
        return self._language_ids.get(os.path.splitext(file_path)[1], "plaintext")

    def _next_id(self) -> int:
        self._seq += 1
        return self._seq

    def _send(self, message: dict) -> None:
        proc = self._proc
        if proc is None or proc.stdin is None:
            raise LspError(f"Language server {self._command[0]} is not running")
        body = json.dumps(message).encode()
        with self._write_lock:
            proc.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
            proc.stdin.flush()

    def _read_loop(self) -> None:
        proc = self._proc
        if proc is None or proc.stdout is None:
            return
        stdout = proc.stdout
        try:
            while True:
                headers: dict[str, str] = {}
                while True:
                    line = stdout.readline()
                    if not line:
                        return  # server exited
                    stripped = line.decode("ascii", errors="replace").strip()
                    if not stripped:
                        break
                    key, _, value = stripped.partition(":")
                    headers[key.strip().lower()] = value.strip()
                length = int(headers.get("content-length", 0))
                if not length:
                    continue
                self._dispatch(json.loads(stdout.read(length).decode("utf-8", errors="replace")))
        except (OSError, ValueError):
            return

    def _dispatch(self, msg: dict) -> None:
        method = msg.get("method")
        if method is None:
            self._responses.put(msg)
        elif "id" in msg:
            self._answer_server_request(msg)
        elif method == "textDocument/publishDiagnostics":
            params = msg.get("params") or {}
            self.diagnostics[params.get("uri", "")] = params.get("diagnostics", [])
        elif method == "$/progress":
            params = msg.get("params") or {}
            kind = (params.get("value") or {}).get("kind")
            if kind == "begin":
                self._active_progress.add(params.get("token"))
            elif kind == "end":
                self._active_progress.discard(params.get("token"))
        elif method in ("window/logMessage", "window/showMessage") and self._ready_pattern:
            if self._ready_pattern.search(str((msg.get("params") or {}).get("message", ""))):
                self._ready_logged.set()

    def _answer_server_request(self, msg: dict) -> None:
        method = msg["method"]
        result: Any = None
        if method == "workspace/configuration":
            result = [None for _ in (msg.get("params") or {}).get("items", [])]
        elif method == "workspace/workspaceFolders" and self._root:
            result = [{"uri": path_to_uri(self._root), "name": os.path.basename(self._root)}]
        try:
            self._send({"jsonrpc": "2.0", "id": msg["id"], "result": result})
        except LspError:
            pass

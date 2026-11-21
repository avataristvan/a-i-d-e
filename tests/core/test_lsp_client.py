import os
import sys
import time

import pytest

from aide.core.domain.workspace_edit import path_to_uri, uri_to_path
from aide.core.infrastructure.lsp_client import LspError, StdioLspClient
from aide.core.infrastructure.lsp_registry import DEFAULT_SERVERS, LanguageServerProvider, ServerSpec

# Minimal fake server: answers initialize, then for every request first sends a burst of
# notifications plus a server->client request in a single write (the case a select()-based
# reader misses), waits for the client's answer, and echoes it back in the response.
FAKE_SERVER = r'''
import json, sys

def read():
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            sys.exit(0)
        line = line.decode().strip()
        if not line:
            break
        k, _, v = line.partition(":")
        headers[k.lower()] = v.strip()
    return json.loads(sys.stdin.buffer.read(int(headers["content-length"])))

def frame(msg):
    body = json.dumps(msg).encode()
    return f"Content-Length: {len(body)}\r\n\r\n".encode() + body

def send(*msgs):
    sys.stdout.buffer.write(b"".join(frame(m) for m in msgs))
    sys.stdout.buffer.flush()

while True:
    msg = read()
    if "id" not in msg or "method" not in msg:
        continue
    if msg["method"] == "initialize":
        send({"jsonrpc": "2.0", "id": msg["id"], "result": {"capabilities": {}}})
    elif msg["method"] == "fail":
        send({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32600, "message": "nope"}})
    elif msg["method"] == "shutdown":
        send({"jsonrpc": "2.0", "id": msg["id"], "result": None})
    else:
        send(
            {"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics",
             "params": {"uri": "file:///x.py", "diagnostics": [{"message": "boom"}]}},
            {"jsonrpc": "2.0", "method": "window/logMessage", "params": {"type": 3, "message": "hi"}},
            {"jsonrpc": "2.0", "id": "srv-1", "method": "workspace/configuration",
             "params": {"items": [{"section": "a"}, {"section": "b"}]}},
        )
        answer = read()
        send({"jsonrpc": "2.0", "id": msg["id"], "result": {"echo": msg["params"], "answer": answer}})
'''


@pytest.fixture
def fake_client(temp_dir):
    script = os.path.join(temp_dir, "fake_server.py")
    with open(script, "w") as f:
        f.write(FAKE_SERVER)
    client = StdioLspClient([sys.executable, script], temp_dir, request_timeout=5.0)
    client.start()
    yield client
    client.stop()


def test_burst_of_messages_and_server_request(fake_client):
    result = fake_client.request("custom/echo", {"n": 1})

    assert result["echo"] == {"n": 1}
    assert result["answer"]["id"] == "srv-1"
    assert result["answer"]["result"] == [None, None]
    assert fake_client.diagnostics["file:///x.py"] == [{"message": "boom"}]


def test_ready_log_pattern_gates_readiness(temp_dir, fake_client):
    script = os.path.join(temp_dir, "fake_server.py")
    gated = StdioLspClient([sys.executable, script], temp_dir, request_timeout=5.0, ready_log_pattern=r"^hi$")
    gated.start()
    try:
        assert not gated.wait_until_ready(0.2)
        gated.request("custom/echo", {})  # the fake server logs "hi" in its burst
        assert gated.wait_until_ready(1.0)
    finally:
        gated.stop()
    assert fake_client.wait_until_ready(0.1)  # no pattern, no open progress


def test_error_response_raises(fake_client):
    with pytest.raises(LspError, match="nope"):
        fake_client.request("fail", {})


def test_request_after_stop_raises(fake_client):
    fake_client.stop()
    with pytest.raises(LspError):
        fake_client.request("custom/echo", {})


def test_uri_roundtrip(temp_dir):
    path = os.path.join(temp_dir, "dir with space", "ä.py")
    assert uri_to_path(path_to_uri(path)) == path


def test_provider_picks_spec_by_extension(temp_dir):
    provider = LanguageServerProvider(temp_dir)
    names = {f: getattr(provider.spec_for(f), "name", None) for f in ("a.py", "a.tsx", "a.hpp", "a.kt", "a.unknown")}
    assert names == {"a.py": "pyright", "a.tsx": "typescript", "a.hpp": "clangd", "a.kt": "kotlin", "a.unknown": None}


def test_provider_returns_none_when_binary_missing(temp_dir):
    missing = ServerSpec("missing", ("aide-no-such-server-binary",), {".py": "python"})
    assert LanguageServerProvider(temp_dir, (missing,)).for_file("a.py") is None


# --- integration against a real server ---

PYRIGHT = next(s for s in DEFAULT_SERVERS if s.name == "pyright")


@pytest.fixture
def pyright_project(temp_dir):
    files = {
        "greeting.py": "class Greeter:\n    def greet(self) -> str:\n        return 'hi'\n",
        "app.py": "from greeting import Greeter\n\n\ndef main() -> str:\n    return Greeter().greet()\n",
        "other.py": "Greeter = 'unrelated string, not the class'\n",
    }
    for name, content in files.items():
        with open(os.path.join(temp_dir, name), "w") as f:
            f.write(content)
    provider = LanguageServerProvider(temp_dir, (PYRIGHT,))
    yield temp_dir, provider
    provider.stop_all()


def _edited_paths(edit: dict) -> set[str]:
    if edit.get("documentChanges"):
        return {os.path.basename(uri_to_path(c["textDocument"]["uri"])) for c in edit["documentChanges"] if "textDocument" in c}
    return {os.path.basename(uri_to_path(uri)) for uri in edit.get("changes", {})}


@pytest.mark.skipif(not PYRIGHT.is_available(), reason="pyright-langserver not installed")
def test_pyright_symbols_references_and_rename(pyright_project):
    root, provider = pyright_project
    greeting = os.path.join(root, "greeting.py")
    server = provider.for_file(greeting)
    assert server is not None
    assert provider.for_file(os.path.join(root, "app.py")) is server

    server.open_document(greeting)
    assert [s["name"] for s in server.document_symbols(greeting)] == ["Greeter"]

    refs = server.references(greeting, 0, 6)
    assert {os.path.basename(uri_to_path(r["uri"])) for r in refs} == {"greeting.py", "app.py"}

    edit = server.rename(greeting, 0, 6, "Welcomer")
    assert edit is not None
    assert _edited_paths(edit) == {"greeting.py", "app.py"}  # other.py's same-named string is untouched


@pytest.mark.skipif(not PYRIGHT.is_available(), reason="pyright-langserver not installed")
def test_pyright_workspace_symbols(pyright_project):
    root, provider = pyright_project
    greeting = os.path.join(root, "greeting.py")
    server = provider.for_file(greeting)
    assert server is not None
    server.open_document(greeting)

    found: list[dict] = []
    deadline = time.monotonic() + 15
    while not found and time.monotonic() < deadline:  # pyright indexes lazily
        found = [s for s in server.workspace_symbols("Greeter") if s["name"] == "Greeter"]
        time.sleep(0.2)
    assert found

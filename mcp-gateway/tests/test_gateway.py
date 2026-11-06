import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.testclient import TestClient

from src.gateway import GatewaySettings, create_app


class Upstream(BaseHTTPRequestHandler):
    calls = 0
    delay = 0

    def do_POST(self):
        type(self).calls += 1
        if self.delay:
            time.sleep(self.delay)
        size = int(self.headers.get("content-length", "0"))
        self.rfile.read(size)
        body = json.dumps({"ok": True}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except OSError:
            # The gateway may close the socket after its bounded timeout.
            pass

    def log_message(self, *_):
        pass


@pytest.fixture
def upstream():
    Upstream.calls = 0
    Upstream.delay = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=2)


def gateway(upstream, permissions=frozenset({"mcp.call"}), timeout=0.2):
    audits = []
    app = create_app(GatewaySettings("test-token", {"local": upstream}, permissions, timeout,
                                     allow_private_hosts=True, audit=audits.append))
    return TestClient(app), audits


def call(client, **values):
    payload = {"server": "local", "tool": "read", "arguments": {}}
    payload.update(values)
    return client.post("/mcp", headers={"Authorization": "Bearer test-token"}, json=payload)


def test_deny_before_forward(upstream):
    client, audits = gateway(upstream, permissions=frozenset())
    response = call(client, operation="delete")
    assert response.status_code == 200
    assert response.json()["decision"] == "DENY"
    assert response.json()["forwarded"] is False
    assert Upstream.calls == 0
    assert audits[-1]["forwarded"] is False


def test_allow_forwards(upstream):
    client, _ = gateway(upstream)
    response = call(client)
    assert response.status_code == 200
    assert response.json()["forwarded"] is True
    assert Upstream.calls == 1


def test_require_approval_does_not_forward(upstream):
    client, _ = gateway(upstream)
    response = call(client, action_type="finance.payment", operation="execute",
                    amount=5001, currency="USD", supplier_verified=True)
    assert response.status_code == 200
    assert response.json()["decision"] == "REQUIRE_APPROVAL"
    assert response.json()["forwarded"] is False
    assert Upstream.calls == 0


def test_ssrf_and_unknown_server_rejected(upstream):
    client, _ = gateway(upstream)
    response = call(client, server="http://127.0.0.1:1", tool="read")
    assert response.status_code == 422
    assert Upstream.calls == 0
    response = call(client, server="unknown")
    assert response.status_code == 403
    assert Upstream.calls == 0
    with pytest.raises(ValueError):
        create_app(GatewaySettings("x", {"bad": "http://127.0.0.1:1"}))


def test_malformed_input(upstream):
    client, _ = gateway(upstream)
    response = client.post("/mcp", headers={"Authorization": "Bearer test-token"}, content=b"not-json")
    assert response.status_code == 422
    assert Upstream.calls == 0


def test_timeout(upstream):
    Upstream.delay = 0.5
    client, _ = gateway(upstream, timeout=0.05)
    response = call(client)
    assert response.status_code == 504
    assert Upstream.calls == 1

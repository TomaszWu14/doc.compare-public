"""Regresja SSRF: webhook nie może podążać za przekierowaniem 3xx na adres wewnętrzny."""
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

pytest.importorskip("flask")

_TMP = tempfile.mkdtemp(prefix="doccompare_whredir_")
os.environ.setdefault("SECRET_KEY", "test-webhook-redirect")
os.environ["SQLITE_PATH"] = os.path.join(_TMP, "wh.db")
os.environ.pop("DATABASE_URL", None)

import app as _app_mod  # noqa: E402


def _serve(handler_cls):
    srv = HTTPServer(("127.0.0.1", 0), handler_cls)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_webhook_does_not_follow_redirect_to_internal_address(monkeypatch):
    hits = {"internal": 0}

    class Internal(BaseHTTPRequestHandler):
        def do_POST(self):
            hits["internal"] += 1
            self.send_response(200)
            self.end_headers()

        do_GET = do_POST

        def log_message(self, *a):
            pass

    internal = _serve(Internal)
    internal_url = f"http://127.0.0.1:{internal.server_port}/secret"

    class Redirector(BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(302)
            self.send_header("Location", internal_url)
            self.end_headers()

        def log_message(self, *a):
            pass

    redirector = _serve(Redirector)
    public_url = f"http://127.0.0.1:{redirector.server_port}/hook"

    class _Rows:
        def fetchall(self):
            return [{"url": public_url, "secret": "", "events": "*"}]

    class _Db:
        def execute(self, *a, **k):
            return _Rows()

        def close(self):
            pass

    # Symulacja: pierwszy URL przechodzi sprawdzenie SSRF (jak publiczny host),
    # każdy inny (cel przekierowania) byłby zablokowany.
    monkeypatch.setattr(_app_mod, "_is_ssrf_blocked_url", lambda u: u != public_url)
    monkeypatch.setattr(_app_mod, "get_db", lambda: _Db())

    try:
        _app_mod._fire_webhooks("test.event", {"a": 1})
    finally:
        internal.shutdown()
        redirector.shutdown()

    assert hits["internal"] == 0, "webhook podążył za przekierowaniem na adres wewnętrzny"

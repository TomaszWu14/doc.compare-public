"""Nagłówki bezpieczeństwa na każdej odpowiedzi (after_request `_set_security_headers` w app.py)."""
import pytest

pytest.importorskip("flask")


def test_baseline_headers_on_html(client):
    resp = client.get("/login")
    h = resp.headers
    assert h.get("X-Content-Type-Options") == "nosniff"
    assert h.get("X-Frame-Options") in ("DENY", "SAMEORIGIN")
    assert h.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in h.get("Permissions-Policy", "")
    assert h.get("Cross-Origin-Opener-Policy") == "same-origin"
    assert "frame-ancestors" in h.get("Content-Security-Policy", "")


def test_no_hsts_over_plain_http(client):
    # Test działa po http i bez DATABASE_URL/FORCE_HTTPS — HSTS tylko za HTTPS.
    assert "Strict-Transport-Security" not in client.get("/login").headers


def test_json_api_responses_are_not_cached(client):
    resp = client.get("/api/nie-ma-takiego-endpointu")
    assert resp.is_json
    assert resp.headers.get("Cache-Control") == "no-store"
    assert resp.headers.get("Cross-Origin-Opener-Policy") == "same-origin"


def test_explicit_cache_control_is_kept():
    import app as app_mod

    with app_mod.app.test_request_context("/api/x"):
        resp = app_mod.jsonify({"ok": True})
        resp.headers["Cache-Control"] = "public, max-age=60"
        resp = app_mod._set_security_headers(resp)
    assert resp.headers.get("Cache-Control") == "public, max-age=60"

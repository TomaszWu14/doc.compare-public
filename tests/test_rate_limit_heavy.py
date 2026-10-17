"""US-006: limit wywołań kosztownych tras i rejestracja kosztu każdego wywołania Claude.

Testy nie wołają prawdziwego API — sieć jest podmieniana atrapami.
"""
import io
import json
import types

import pytest

pytest.importorskip("flask")

import app as _app_mod  # noqa: E402
import core.rate_limit as rl  # noqa: E402
from tests.conftest import CSRF_TOKEN, set_session_csrf  # noqa: E402

# Kosztowne trasy (AI, OCR, render PDF), które muszą mieć @heavy_rate_limit.
HEAVY_ENDPOINTS = [
    "api_scan_extract",
    "api_artwork_preview_crops",
    "api_artwork_split_compare",
    "api_artwork_3d",
    "api_artwork_pdf_pages",
    "api_artwork_compare_multi",
    "api_artwork_batch_start",
    "api_artwork_batch_run",
    "api_artwork_field_queue_init",
    "api_artwork_profile_ai_detect",
    "api_artwork_profile_ai_detect_image",
    "api_artwork_profile_render",
    "api_artwork_profile_render_blank",
    "api_extract_po_preview",
    "api_validate_shipment_file",
    "palviz.api_palviz_generate",
    "palviz.api_palviz_batch",
    "palviz.api_templates_analyze",
    "suppliers.api_suppliers_preview_table",
]


def _view(endpoint):
    funcs = _app_mod.app.view_functions
    if endpoint in funcs:
        return funcs[endpoint]
    # blueprint może być zarejestrowany pod inną nazwą — szukamy po nazwie funkcji
    short = endpoint.split(".")[-1]
    matches = [f for name, f in funcs.items() if name.split(".")[-1] == short]
    assert matches, f"brak endpointu {endpoint}"
    return matches[0]


@pytest.mark.parametrize("endpoint", HEAVY_ENDPOINTS)
def test_heavy_endpoint_has_rate_limit(endpoint):
    assert getattr(_view(endpoint), "_heavy_rate_limited", False), \
        f"{endpoint} nie ma @heavy_rate_limit"


def test_limited_request_gets_429_with_retry_after(admin_client, monkeypatch):
    monkeypatch.setattr(rl, "check_and_record", lambda uid: True)
    set_session_csrf(admin_client, CSRF_TOKEN)
    resp = admin_client.post("/api/artwork/pdf-pages", data={"_csrf_token": CSRF_TOKEN})
    assert resp.status_code == 429
    assert resp.headers.get("Retry-After") == str(rl.API_RATE_WINDOW)
    assert "Zbyt wiele" in resp.get_json()["error"]


def test_request_under_limit_reaches_view(admin_client, monkeypatch):
    monkeypatch.setattr(rl, "check_and_record", lambda uid: False)
    set_session_csrf(admin_client, CSRF_TOKEN)
    resp = admin_client.post("/api/artwork/pdf-pages", data={"_csrf_token": CSRF_TOKEN})
    assert resp.status_code != 429  # brak pliku → błąd walidacji widoku, nie limit


def test_anonymous_and_bad_csrf_do_not_consume_limit(client, admin_client, monkeypatch):
    calls = []
    monkeypatch.setattr(rl, "check_and_record", lambda uid: calls.append(uid) or False)
    anon = _app_mod.app.test_client()
    anon.post("/api/artwork/pdf-pages")
    set_session_csrf(admin_client, CSRF_TOKEN)
    resp = admin_client.post("/api/artwork/pdf-pages", data={"_csrf_token": "zly"})
    assert resp.status_code == 403
    assert calls == []


def test_check_and_record_counts_per_user(monkeypatch):
    monkeypatch.setattr(rl, "API_RATE_MAX", 2)
    uid = 987654  # użytkownik spoza danych testowych
    assert rl.check_and_record(uid) is False
    assert rl.check_and_record(uid) is False
    assert rl.check_and_record(uid) is True
    assert rl.check_and_record(uid + 1) is False  # inny użytkownik ma osobny licznik


# ── Rejestracja kosztu ────────────────────────────────────────────────────────

def test_record_usage_accepts_sdk_usage_object(monkeypatch):
    import api_usage_tracker as t
    rows = []

    class _DB:
        def execute(self, sql, params=()):
            rows.append(params)
        def commit(self):
            pass
        def close(self):
            pass

    import db as _db
    monkeypatch.setattr(_db, "get_db", lambda: _DB())
    t.record_usage("claude-sonnet-4-6",
                   types.SimpleNamespace(input_tokens=1000, output_tokens=100),
                   call_type="artwork_ai_detect", user_id=7)
    assert rows, "brak zapisu do api_usage"
    model, inp, out, cost, call_type, uid = rows[0]
    assert (model, inp, out, call_type, uid) == ("claude-sonnet-4-6", 1000, 100, "artwork_ai_detect", 7)
    assert cost == pytest.approx((1000 * 3 + 100 * 15) / 1_000_000)


def test_record_usage_takes_user_from_request_session(monkeypatch):
    import api_usage_tracker as t
    with _app_mod.app.test_request_context("/"):
        from flask import session
        session["user_id"] = 42
        assert t._current_user_id() == 42
    assert t._current_user_id() is None  # poza żądaniem


def test_table_vision_records_usage(monkeypatch):
    pytest.importorskip("PIL")
    import sys
    from PIL import Image
    import api_usage_tracker as t
    import table_extractor as te

    calls = []
    monkeypatch.setattr(t, "record_usage", lambda *a, **k: calls.append((a, k)))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    class _Resp:
        status_code = 200
        def json(self):
            return {"content": [{"type": "text", "text": "[]"}],
                    "usage": {"input_tokens": 10, "output_tokens": 2}}

    # atrapa modułu httpx (import w funkcji) — działa także bez zainstalowanego httpx
    monkeypatch.setitem(sys.modules, "httpx", types.SimpleNamespace(post=lambda *a, **k: _Resp()))
    te._claude_extract_table(Image.new("RGB", (10, 10)))
    assert calls and calls[0][1]["call_type"] == "table_vision"


def test_scan_extract_records_usage(monkeypatch):
    import api_usage_tracker as t
    import scan_extractor as se

    calls = []
    monkeypatch.setattr(t, "record_usage", lambda *a, **k: calls.append((a, k)))
    body = json.dumps({"model": "claude-sonnet-4-6",
                       "content": [{"type": "text", "text": "{}"}],
                       "usage": {"input_tokens": 5, "output_tokens": 1}}).encode()

    class _CM(io.BytesIO):
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    monkeypatch.setattr(se.urllib.request, "urlopen", lambda *a, **k: _CM(body))
    se._call_claude_vision("aGVsbG8=", "test-key")
    assert calls and calls[0][1]["call_type"] == "scan_extract"


def _report():
    return types.SimpleNamespace(matched_items=[], diff_items=[], manufacturer=[],
                                 product_code="A", product_name="B",
                                 critical_count=0, warning_count=0)


def test_report_comment_skipped_when_budget_exceeded(monkeypatch):
    import api_usage_tracker as t
    import artwork_report_engine as are
    import urllib.request

    monkeypatch.setattr(are, "_get_api_key", lambda: "test-key")
    monkeypatch.setattr(t, "budget_allows_optional_ai", lambda: False)

    def _boom(*a, **k):
        raise AssertionError("nie wolno wołać API po przekroczeniu budżetu")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    assert are._generate_ai_comment(_report()) == ""


def test_report_comment_records_usage(monkeypatch):
    import api_usage_tracker as t
    import artwork_report_engine as are
    import urllib.request

    calls = []
    monkeypatch.setattr(are, "_get_api_key", lambda: "test-key")
    monkeypatch.setattr(t, "budget_allows_optional_ai", lambda: True)
    monkeypatch.setattr(t, "record_usage", lambda *a, **k: calls.append((a, k)))
    body = json.dumps({"content": [{"type": "text", "text": "OK"}],
                       "usage": {"input_tokens": 50, "output_tokens": 20}}).encode()

    class _CM(io.BytesIO):
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: _CM(body))
    assert are._generate_ai_comment(_report()) == "OK"
    assert calls and calls[0][1]["call_type"] == "artwork_report_comment"

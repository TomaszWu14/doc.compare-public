"""US-027 / SEC-010 / R-10 — drobne wycieki informacji.

Kryteria akceptacji (docs/analiza/HISTORYJKI.md, US-027):
  1. odpowiedzi 500 PalViz nie zawierają tracebacku ani treści wyjątku (jest identyfikator błędu do logu),
  2. `/api/ai/status` i `check_api_key()` nie zwracają fragmentu klucza API,
  3. eksport CSV materiałów neutralizuje formuły (`= + - @ \\t \\r` → prefiks apostrofu),
  4. podgląd szablonu PalViz serwuje tylko pliki użytkownika (prefiks uid) lub superuserowi/adminowi.
Wylogowanie przez POST wydzielone do US-028 (zmiana UI w 4 szablonach).
"""
import csv
import io
import os

import pytest

pytest.importorskip("flask")

import app as app_mod  # noqa: E402
from tests.conftest import CSRF_TOKEN, set_session_csrf  # noqa: E402

# Wartość klucza składana w runtime, żeby skaner sekretów nie traktował testu jak wycieku.
_FAKE_KEY = "sk-" + "ant-" + "TEST" + "0" * 24


def _uid(username):
    db = app_mod.get_db()
    try:
        return db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()[0]
    finally:
        db.close()


# ── 1. PalViz: bez tracebacku w odpowiedzi 500 ────────────────────────────────
def test_SEC010_palviz_analyze_error_has_no_traceback(manager_client):
    set_session_csrf(manager_client, CSRF_TOKEN)
    resp = manager_client.post(
        "/api/artwork/templates/analyze",
        data={"file": (io.BytesIO(b"to nie jest PDF"), "zly.pdf")},
        headers={"X-CSRF-Token": CSRF_TOKEN},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 500
    body = resp.get_json()
    assert "detail" not in body
    text = resp.get_data(as_text=True)
    assert "Traceback" not in text and "File \"" not in text
    assert body.get("error_id"), "odpowiedź powinna mieć identyfikator błędu do korelacji z logiem"


def test_SEC010_palviz_generate_error_has_no_traceback(manager_client, monkeypatch):
    import artwork_palviz

    def boom(*a, **k):
        raise RuntimeError("SEKRETNA_SCIEZKA /srv/internal/db.sqlite")

    monkeypatch.setattr(artwork_palviz, "build_bundle", boom)
    monkeypatch.setattr("blueprints.palviz._template_apply", lambda p: (None, None))
    set_session_csrf(manager_client, CSRF_TOKEN)
    resp = manager_client.post(
        "/api/artwork/palviz",
        data={"file": (io.BytesIO(b"%PDF-1.4"), "a.pdf"), "level": "opz", "sku": "X1"},
        headers={"X-CSRF-Token": CSRF_TOKEN},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 500
    text = resp.get_data(as_text=True)
    assert "SEKRETNA_SCIEZKA" not in text and "Traceback" not in text


# ── 2. Klucz API nie wycieka ──────────────────────────────────────────────────
def test_SEC010_ai_status_has_no_key_fragment(user_client, monkeypatch):
    import ai_validator
    monkeypatch.setattr(ai_validator, "_get_api_key", lambda: _FAKE_KEY)
    resp = user_client.get("/api/ai/status")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["api_key_set"] is True
    assert "key_prefix" not in body
    assert _FAKE_KEY[:10] not in resp.get_data(as_text=True)


def test_SEC010_check_api_key_has_no_key_fragment(monkeypatch):
    import ai_validator
    monkeypatch.setattr(ai_validator, "_get_api_key", lambda: _FAKE_KEY)
    monkeypatch.setattr(ai_validator, "_call_claude", lambda *a, **k: {"ok": True})
    result = ai_validator.check_api_key()
    assert result["ok"] is True
    assert "key_prefix" not in result


# ── 3. CSV materiałów: neutralizacja formuł ───────────────────────────────────
def test_SEC010_materials_csv_neutralizes_formulas(manager_client):
    db = app_mod.get_db()
    try:
        app_mod._ensure_artwork_profile_tables(db)
        db.execute("DELETE FROM artwork_material WHERE ref_code LIKE 'SEC010-%'")
        db.execute("INSERT INTO artwork_material(ref_code, name, product_family, ean, notes) "
                   "VALUES (?,?,?,?,?)",
                   ("SEC010-A", "=HYPERLINK(\"http://x\",\"klik\")", "+rodzina", "@ean", "-2+3"))
        db.commit()
    finally:
        db.close()
    resp = manager_client.get("/api/artwork/materials/export-csv")
    assert resp.status_code == 200
    rows = list(csv.DictReader(io.StringIO(resp.get_data(as_text=True).lstrip("﻿"))))
    row = next(r for r in rows if r["ref_code"] == "SEC010-A")
    for col in ("name", "product_family", "ean", "notes"):
        assert row[col].startswith("'"), (col, row[col])


def test_SEC010_formula_safe_helper():
    from export_engine import formula_safe
    assert formula_safe("=1+1") == "'=1+1"
    assert formula_safe("\tx") == "'\tx"
    assert formula_safe("ACM-1002") == "ACM-1002"
    assert formula_safe("") == ""
    assert formula_safe(None) == ""


# ── 4. Podgląd szablonu: tylko własne pliki ───────────────────────────────────
def _preview_file(name):
    d = os.path.join(app_mod.app.config["UPLOAD_FOLDER"], "tpl_preview")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n")
    return name


def test_SEC010_template_preview_foreign_file_denied(user_client):
    name = _preview_file(f"{_uid('it_user') + 1000}_sec010.png")
    assert user_client.get(f"/artwork/templates/preview/{name}").status_code == 403


def test_SEC010_template_preview_own_file_allowed(user_client):
    name = _preview_file(f"{_uid('it_user')}_sec010.png")
    assert user_client.get(f"/artwork/templates/preview/{name}").status_code == 200

"""US-001 / SEC-005 / R-01 — endpointy szablonów wykrojników PalViz wymagają roli manager.

Błąd: `if not require_role("manager"):` traktował fabrykę dekoratorów jak wartość
logiczną (zawsze prawdziwą), więc kontrola nigdy się nie wykonywała i każdy
zalogowany użytkownik mógł analizować i zapisywać szablony.

Kryteria akceptacji (docs/analiza/HISTORYJKI.md, US-001):
  1. user z poprawnym CSRF → 403 "Brak uprawnień", szablon nie zostaje zapisany,
  2. manager → działa jak dotychczas,
  3. w kodzie nie ma żadnego użycia `require_role(...)` poza dekoratorem (strażnik).
"""
import ast
import pathlib

import pytest

pytest.importorskip("flask")

from tests.conftest import CSRF_TOKEN, set_session_csrf  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]

ANALYZE = "/api/artwork/templates/analyze"
SAVE = "/api/artwork/templates/save"

_SAVE_PAYLOAD = {
    "name": "test-SEC005",
    "sig_key": "sec-sec-sec",  # syntetyczna sygnatura szablonu, nie sekret
    "page_w_mm": 300,
    "page_h_mm": 200,
    "regions": {"front": [0.1, 0.1, 0.4, 0.4]},
}


def _template_count(sig_key):
    import app as _app_mod
    from blueprints.palviz import ensure_dieline_templates_table
    db = _app_mod.get_db()
    try:
        ensure_dieline_templates_table(db)
        return db.execute(
            "SELECT COUNT(*) FROM dieline_templates WHERE sig_key=?", (sig_key,)
        ).fetchone()[0]
    finally:
        db.close()


def _post_save(c, sig_key):
    set_session_csrf(c, CSRF_TOKEN)
    return c.post(SAVE, json=dict(_SAVE_PAYLOAD, sig_key=sig_key),
                  headers={"X-CSRF-Token": CSRF_TOKEN})


# ── Kryterium 1: user → 403, bez zapisu ───────────────────────────────────────
def test_SEC005_user_cannot_save_template(user_client):
    sig = "sec005-user-save"
    resp = _post_save(user_client, sig)
    assert resp.status_code == 403
    assert resp.get_json() == {"error": "Brak uprawnień"}
    assert _template_count(sig) == 0


def test_SEC005_user_cannot_analyze_template(user_client):
    set_session_csrf(user_client, CSRF_TOKEN)
    resp = user_client.post(ANALYZE, data={}, headers={"X-CSRF-Token": CSRF_TOKEN})
    assert resp.status_code == 403
    assert resp.get_json() == {"error": "Brak uprawnień"}


def test_SEC005_external_role_cannot_reach_templates(forwarder_client):
    set_session_csrf(forwarder_client, CSRF_TOKEN)
    resp = forwarder_client.post(SAVE, json=_SAVE_PAYLOAD, headers={"X-CSRF-Token": CSRF_TOKEN})
    assert resp.status_code == 403


def test_SEC005_anonymous_is_redirected_to_login(client):
    resp = client.post(SAVE, json=_SAVE_PAYLOAD)
    assert resp.status_code in (302, 303)
    assert "/login" in resp.headers["Location"]


# ── Kryterium 2: manager działa jak dotychczas ────────────────────────────────
def test_SEC005_manager_can_save_template(manager_client):
    sig = "sec005-manager-save"
    resp = _post_save(manager_client, sig)
    assert resp.status_code == 200, resp.get_data(as_text=True)
    assert resp.get_json()["ok"] is True
    assert _template_count(sig) == 1


def test_SEC005_manager_reaches_analyze_validation(manager_client):
    # Brak pliku → 400 z walidacji, czyli żądanie przeszło kontrolę roli.
    set_session_csrf(manager_client, CSRF_TOKEN)
    resp = manager_client.post(ANALYZE, data={}, headers={"X-CSRF-Token": CSRF_TOKEN})
    assert resp.status_code == 400


def test_SEC005_manager_without_csrf_is_rejected(manager_client):
    resp = manager_client.post(SAVE, json=_SAVE_PAYLOAD)
    assert resp.status_code == 403


# ── Kryterium 3: strażnik statyczny ───────────────────────────────────────────
def _require_role_non_decorator_uses():
    """Zwraca wywołania require_role(...), które nie są dekoratorem funkcji."""
    offenders = []
    skip = {".git", ".venv", "venv", "node_modules", "static", "tests"}
    for path in ROOT.rglob("*.py"):
        if skip.intersection(path.relative_to(ROOT).parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        decorator_calls = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    decorator_calls.add(id(dec))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and getattr(node.func, "id", getattr(node.func, "attr", None)) == "require_role"
                    and id(node) not in decorator_calls):
                offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    return offenders


def test_SEC005_require_role_only_used_as_decorator():
    assert _require_role_non_decorator_uses() == [], (
        "require_role() to fabryka dekoratorów — użycie jako wartości logicznej "
        "nigdy nie sprawdza roli. Użyj @require_role(...) albo role_level()."
    )

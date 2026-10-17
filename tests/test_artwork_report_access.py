"""US-004 / SEC-016 / R-04 — dostęp do raportów i wyników porównań artworków po cache_id jest fail-closed.

Przed poprawką kontrola miała postać `owner is not None and owner != uid ...`, więc wpis bez
właściciela był widoczny dla każdego zalogowanego; writer batcha (NDJSON) nie ustawiał
`_owner_id`, a eksport ZIP batcha, zone-select i zone-compare w ogóle nie sprawdzały właściciela.

Kryteria akceptacji (docs/analiza/HISTORYJKI.md, US-004):
  1. wpis bez właściciela → odmowa dla użytkownika niebędącego superuserem/adminem,
  2. wpis cudzy → odmowa; własny lub publiczny → dostęp; superuser/admin → dostęp,
  3. raport z batcha ma `_owner_id` zlecającego.
"""
import uuid

import pytest

pytest.importorskip("flask")

import app as app_mod  # noqa: E402
from tests.conftest import CSRF_TOKEN, set_session_csrf  # noqa: E402


def _uid(username):
    db = app_mod.get_db()
    try:
        return db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()[0]
    finally:
        db.close()


def _put_report(report):
    cid = uuid.uuid4().hex[:16]
    with app_mod._rpt_cache_lock:
        cache = getattr(app_mod.app, "_artwork_report_cache", {})
        cache[cid] = report
        app_mod.app._artwork_report_cache = cache
    return cid


class _FakeResult:
    page_diffs = []

    def page_images(self, idx):
        return {"page": idx, "ok": True}


# ── Reguła dostępu (jedno miejsce decyzji) ────────────────────────────────────
@pytest.mark.parametrize("owner, public, uid, role, expected", [
    (None, False, 5, "user", False),        # brak właściciela → odmowa (fail-closed)
    (None, False, 5, "manager", False),
    (7, False, 5, "user", False),           # cudzy
    (5, False, 5, "user", True),            # własny
    (7, True, 5, "user", True),             # publiczny
    (None, False, 5, "superuser", True),    # can_see_all
    (7, False, 5, "admin", True),
    (5, False, None, "user", False),        # brak użytkownika w kontekście
])
def test_SEC016_access_rule(owner, public, uid, role, expected):
    assert app_mod._artwork_access_allowed(owner, public, uid=uid, role=role) is expected


# ── Cache raportów: builder i strona raportu ──────────────────────────────────
def test_SEC016_builder_denies_ownerless_report_to_user():
    cid = _put_report({"product_code": "SEC016-OWNERLESS"})
    assert app_mod._build_report_from_cache_or_db(cid, user_id=_uid("it_user"), role="user") is None


def test_SEC016_builder_allows_owner_and_admin():
    uid = _uid("it_user")
    cid = _put_report({"product_code": "SEC016-OWN", "_owner_id": uid})
    assert app_mod._build_report_from_cache_or_db(cid, user_id=uid, role="user") is not None
    other = _put_report({"product_code": "SEC016-OTHER", "_owner_id": uid + 1000})
    assert app_mod._build_report_from_cache_or_db(other, user_id=uid, role="user") is None
    assert app_mod._build_report_from_cache_or_db(other, user_id=uid, role="admin") is not None


def test_SEC016_report_page_hides_ownerless_report(user_client):
    cid = _put_report({"product_code": "SEC016-PAGE-MARKER"})
    resp = user_client.get(f"/artwork/report?cache_id={cid}")
    assert resp.status_code == 200
    assert b"SEC016-PAGE-MARKER" not in resp.data


# ── Eksport ZIP batcha ────────────────────────────────────────────────────────
def test_SEC016_batch_zip_skips_reports_of_other_users(user_client, monkeypatch):
    import artwork_batch_processor
    import artwork_report_engine
    exported, zipped = [], []
    monkeypatch.setattr(artwork_report_engine, "export_to_docx",
                        lambda rpt: exported.append(rpt) or b"docx")
    monkeypatch.setattr(artwork_batch_processor, "build_artwork_batch_zip",
                        lambda results: zipped.extend(results) or b"PK")
    uid = _uid("it_user")
    mine = _put_report({"product_code": "SEC016-MINE", "_owner_id": uid})
    foreign = _put_report({"product_code": "SEC016-FOREIGN", "_owner_id": uid + 1000})
    ownerless = _put_report({"product_code": "SEC016-NOOWNER"})
    import json
    set_session_csrf(user_client, CSRF_TOKEN)
    resp = user_client.post("/api/artwork/batch/zip", data={
        "results": json.dumps([{"cache_id": c} for c in (mine, foreign, ownerless)]),
        "_csrf_token": CSRF_TOKEN,
    })
    assert resp.status_code == 200
    codes = [r["product_code"] for r in exported]
    assert codes == ["SEC016-MINE"]
    assert [bool(r["report_obj"]) for r in zipped] == [True, False, False]


# ── Cache wyników porównania: podgląd stron, zone-select, zone-compare ────────
def test_SEC016_page_images_ownerless_denied(user_client):
    cid = uuid.uuid4().hex[:16]
    app_mod._cache_put(cid, _FakeResult(), owner_id=None)
    assert user_client.get(f"/api/artwork/page/{cid}/0").status_code == 403


def test_SEC016_page_images_owner_allowed(user_client):
    cid = uuid.uuid4().hex[:16]
    app_mod._cache_put(cid, _FakeResult(), owner_id=_uid("it_user"))
    resp = user_client.get(f"/api/artwork/page/{cid}/0")
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


def test_SEC016_zone_compare_foreign_denied(user_client):
    cid = uuid.uuid4().hex[:16]
    app_mod._cache_put(cid, _FakeResult(), owner_id=_uid("it_user") + 1000)
    set_session_csrf(user_client, CSRF_TOKEN)
    resp = user_client.post("/api/artwork/zone-compare", json={"cache_id": cid, "zones": []},
                            headers={"X-CSRF-Token": CSRF_TOKEN})
    assert resp.status_code == 403


def test_SEC016_zone_compare_owner_passes_access_check(user_client):
    cid = uuid.uuid4().hex[:16]
    app_mod._cache_put(cid, _FakeResult(), owner_id=_uid("it_user"))
    set_session_csrf(user_client, CSRF_TOKEN)
    resp = user_client.post("/api/artwork/zone-compare", json={"cache_id": cid, "zones": []},
                            headers={"X-CSRF-Token": CSRF_TOKEN})
    assert resp.status_code == 400   # brak stref — kontrola dostępu przeszła


def test_SEC016_zone_select_foreign_denied(user_client):
    cid = uuid.uuid4().hex[:16]
    app_mod._cache_put(cid, _FakeResult(), owner_id=_uid("it_user") + 1000)
    assert user_client.get(f"/artwork/zone-select?cache_id={cid}").status_code == 403


# ── Writer batcha ustawia właściciela ─────────────────────────────────────────
def test_SEC016_batch_writer_sets_owner(user_client, monkeypatch):
    import artwork_batch_processor

    def fake_batch(pairs, upload_dir, uid, use_ai=True, heavy_sem=None):
        yield {"pair": 1, "report_obj": {"product_code": "SEC016-BATCH"}}

    monkeypatch.setattr(artwork_batch_processor, "run_artwork_batch", fake_batch)
    set_session_csrf(user_client, CSRF_TOKEN)
    resp = user_client.post("/api/artwork/batch/run",
                            data={"pairs": "[]", "use_ai": "0", "_csrf_token": CSRF_TOKEN})
    assert resp.status_code == 200
    import json
    line = json.loads(resp.get_data(as_text=True).splitlines()[0])
    with app_mod._rpt_cache_lock:
        rpt = app_mod.app._artwork_report_cache[line["cache_id"]]
    assert rpt["_owner_id"] == _uid("it_user")


# ── Strażnik: stary warunek fail-open nie wraca ───────────────────────────────
def test_SEC016_no_fail_open_owner_checks():
    import pathlib
    import re
    root = pathlib.Path(__file__).resolve().parents[1]
    pattern = re.compile(r"(\w*owner\w*) is not None and \1 != ")
    hits = []
    for path in root.rglob("*.py"):
        if {".git", "tests", "static", ".venv", "venv"}.intersection(path.relative_to(root).parts):
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if pattern.search(line):
                hits.append(f"{path.relative_to(root)}:{n}")
    assert hits == [], "Kontrola właściciela fail-open — użyj _artwork_access_allowed(): " + ", ".join(hits)

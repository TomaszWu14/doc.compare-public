"""Aktywność gościa bramki demo (blueprints/visitor_activity.py + hook w demo_gate)."""

import json
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("flask")

from itsdangerous import URLSafeTimedSerializer  # noqa: E402

from blueprints import demo_gate as dg  # noqa: E402
from blueprints import visitor_activity as va  # noqa: E402
from blueprints import visitor_notify as vn  # noqa: E402
from db import get_db  # noqa: E402
from tests.conftest import CSRF_TOKEN, _app_mod  # noqa: E402

GOOD = {"first": "Jan", "last": "Kowalski", "company": "ACME", "gdpr": "1", "website": ""}


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setenv("DEMO_VISITOR_GATE", "1")
    monkeypatch.setenv("NTFY_URL", "https://ntfy.example/tajny-temat")
    monkeypatch.delenv("NTFY_WATCH_COMPANIES", raising=False)
    monkeypatch.delenv("NTFY_ENGAGED_VIEWS", raising=False)
    monkeypatch.setattr(vn, "_start", vn._send)
    db = get_db()
    try:
        dg.ensure_table(db)
        db.execute("DELETE FROM demo_visitors")
        db.commit()
    finally:
        db.close()


@pytest.fixture
def sent(monkeypatch):
    calls = []

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, n=-1):
            return b""

    monkeypatch.setattr(
        vn.urllib.request, "urlopen", lambda req, timeout=None: calls.append(req) or _Resp()
    )
    return calls


def _enter(client, **over):
    with client.session_transaction() as s:
        s["_csrf_token"] = CSRF_TOKEN
    resp = client.post("/demo-gate", data={**GOOD, "_csrf_token": CSRF_TOKEN, **over})
    assert resp.status_code == 302
    return resp


def _row():
    db = get_db()
    try:
        row = db.execute(
            "SELECT id, created_at, page_views, last_seen_at, sections FROM demo_visitors"
        ).fetchone()
        return dict(row) if row else None
    finally:
        db.close()


def _sign(payload, secret=None):
    key = secret or _app_mod.app.secret_key
    return URLSafeTimedSerializer(key, salt="demo-visitor-gate").dumps(payload)


def test_wejscie_i_trzy_ekrany(client):
    _enter(client)
    for _ in range(3):
        assert client.get("/login").status_code == 200
    row = _row()
    assert row["page_views"] == 3
    assert json.loads(row["sections"]) == {"login": 3}
    assert row["last_seen_at"]


@pytest.mark.parametrize(
    "path", ["/static/x.css", "/health", "/api/nieistnieje", "/nie-ma-takiej-strony", "/"]
)
def test_nie_liczone_static_health_api_404_redirect(client, path):
    _enter(client)
    client.get(path)
    assert _row()["page_views"] == 0


def test_gosc_bez_flagi_nie_liczony(client):
    _enter(client)
    client.delete_cookie("visitor_ok")
    client.get("/login")  # przekierowanie na bramkę
    assert _row()["page_views"] == 0


def test_podrobiona_flaga_nie_liczona(client):
    _enter(client)
    vid = _row()["id"]
    client.set_cookie("visitor_ok", _sign({"id": vid}, secret="cudzy-klucz"))
    assert client.get("/login").status_code == 302
    assert _row()["page_views"] == 0


def test_stara_flaga_bez_id_wpuszcza_ale_nie_liczy(client):
    _enter(client)
    with _app_mod.app.app_context():
        client.set_cookie("visitor_ok", _sign("ok"))
    assert client.get("/login").status_code == 200
    assert _row()["page_views"] == 0


def test_prog_zaangazowania_dokladnie_jeden_push(client, sent, monkeypatch):
    monkeypatch.setenv("NTFY_ENGAGED_VIEWS", "2")
    _enter(client)
    for _ in range(4):
        client.get("/login")
    engaged = [r for r in sent if r.get_header("Tags") == "eyes"]
    assert len(engaged) == 1
    req = engaged[0]
    assert req.get_header("Title") == "Gosc oglada demo: DocCompare"
    assert req.get_header("Priority") == "default"
    assert req.data.decode("utf-8") == "Jan Kowalski (ACME) obejrzał już 2 ekranów w DocCompare"


def test_prog_zaangazowania_firma_z_listy_urgent(client, sent, monkeypatch):
    monkeypatch.setenv("NTFY_ENGAGED_VIEWS", "1")
    monkeypatch.setenv("NTFY_WATCH_COMPANIES", "acme")
    _enter(client)
    client.get("/login")
    engaged = [r for r in sent if r.get_header("Tags") == "eyes"]
    assert len(engaged) == 1 and engaged[0].get_header("Priority") == "urgent"


def test_prog_zero_wylacza(client, sent, monkeypatch):
    monkeypatch.setenv("NTFY_ENGAGED_VIEWS", "0")
    _enter(client)
    client.get("/login")
    assert [r for r in sent if r.get_header("Tags") == "eyes"] == []


def test_wyjatek_przy_liczeniu_nie_psuje_odpowiedzi(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("baza leży")

    monkeypatch.setattr(va, "get_db", boom)
    _enter(client)
    assert client.get("/login").status_code == 200


def test_sekcje_z_sciezki():
    assert va.section_for("/") == "start"
    assert va.section_for("/palety/123") == "palety"
    assert va.section_for("/Artwork/x") == "artwork"
    assert va.section_for("/zał$ą") == "za"
    assert va.section_for("/ąę") is None
    assert va.section_for("/" + "a" * 60) == "a" * 40


def test_limit_20_sekcji():
    sections = {f"s{i}": 1 for i in range(20)}
    va.bump_section(sections, "nowa")
    assert "nowa" not in sections and len(sections) == 20
    va.bump_section(sections, "s3")
    assert sections["s3"] == 2


def test_record_view_limit_sekcji_w_bazie():
    db = get_db()
    try:
        vid = dg.save_visitor(db, "Anna", "Nowak", "Firma")
    finally:
        db.close()
    for i in range(25):
        va.record_view(vid, f"/sekcja{i}/x")
    row = _row()
    assert row["page_views"] == 25 and len(json.loads(row["sections"])) == 20


@pytest.fixture
def gate_off(monkeypatch):
    monkeypatch.setenv("DEMO_VISITOR_GATE", "0")


def test_lista_pokazuje_aktywnosc(gate_off, admin_client):
    now = datetime.now(timezone.utc)
    db = get_db()
    try:
        vid = dg.save_visitor(db, "Anna", "Nowak", "Firma", now - timedelta(minutes=5))
        dg.save_visitor(db, "Bez", "Ruchu", "Firma")
    finally:
        db.close()
    for path in ("/palety/1", "/palety/2", "/login", "/raporty", "/raporty", "/raporty", "/x"):
        va.record_view(vid, path, now)
    html = admin_client.get("/admin/demo-visitors").get_data(as_text=True)
    for col in ("Ekrany", "Czas", "Najczęściej"):
        assert col in html
    assert "ok. 5 min" in html
    assert "raporty (3), palety (2), login (1)" in html
    assert "—" in html  # gość bez aktywności


def test_format_czasu():
    assert va.format_duration("2026-01-01 10:00:00", None) == "—"
    assert va.format_duration("2026-01-01 10:00:00", "2026-01-01 10:12:20") == "ok. 12 min"


def test_leniwa_migracja_starej_tabeli(monkeypatch):
    monkeypatch.setattr(va, "_columns_ready", False)
    db = sqlite3.connect(":memory:")
    db.execute(
        "CREATE TABLE demo_visitors (id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT, "
        "last_name TEXT, company TEXT, created_at TEXT)"
    )
    db.execute("INSERT INTO demo_visitors(first_name) VALUES ('Stary')")
    db.commit()
    va.ensure_columns(db)
    cols = {r[1] for r in db.execute("PRAGMA table_info(demo_visitors)")}
    assert {"page_views", "last_seen_at", "sections"} <= cols
    assert db.execute("SELECT page_views FROM demo_visitors").fetchone()[0] == 0

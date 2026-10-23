"""Bramka odwiedzin demo (blueprints/demo_gate.py)."""

from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("flask")

from blueprints import demo_gate as dg  # noqa: E402
from db import get_db  # noqa: E402
from tests.conftest import CSRF_TOKEN  # noqa: E402

GOOD = {"first": "Jan", "last": "Kowalski", "company": "ACME", "gdpr": "1", "website": ""}


@pytest.fixture(autouse=True)
def gate_on(monkeypatch):
    monkeypatch.setenv("DEMO_VISITOR_GATE", "1")
    db = get_db()
    try:
        dg.ensure_table(db)
        db.execute("DELETE FROM demo_visitors")
        db.commit()
    finally:
        db.close()


@pytest.fixture
def gate_off(monkeypatch):
    monkeypatch.setenv("DEMO_VISITOR_GATE", "0")


def _post(client, **over):
    with client.session_transaction() as s:
        s["_csrf_token"] = CSRF_TOKEN
    data = {**GOOD, "_csrf_token": CSRF_TOKEN, **over}
    return client.post("/demo-gate", data=data)


def _count():
    db = get_db()
    try:
        return db.execute("SELECT COUNT(*) FROM demo_visitors").fetchone()[0]
    finally:
        db.close()


def test_domyslnie_wylaczona(client, monkeypatch):
    monkeypatch.delenv("DEMO_VISITOR_GATE", raising=False)
    monkeypatch.delenv("APP_BASE_URL", raising=False)
    assert client.get("/login").status_code == 200


def test_wlaczona_na_domenie_demo(monkeypatch):
    monkeypatch.delenv("DEMO_VISITOR_GATE", raising=False)
    monkeypatch.setenv("APP_BASE_URL", "https://doc.compare.twapp.pl")
    assert dg.gate_enabled()
    monkeypatch.setenv("DEMO_VISITOR_GATE", "0")
    assert not dg.gate_enabled()


def test_login_przekierowuje_na_bramke(client):
    resp = client.get("/login")
    assert resp.status_code == 302 and "/demo-gate" in resp.headers["Location"]
    assert "Zanim wejdziesz do wersji demonstracyjnej" in client.get("/demo-gate").get_data(
        as_text=True
    )


def test_brak_danych_odmowa(client):
    for over in (
        {"first": ""},
        {"last": " "},
        {"company": "x"},
        {"first": "a\x07b"},
        {"company": "x" * 101},
    ):
        assert _post(client, **over).status_code == 400
    assert _count() == 0


def test_brak_zgody_odmowa(client):
    assert _post(client, gdpr="").status_code == 400
    assert _count() == 0


def test_honeypot_odmowa(client):
    assert _post(client, website="http://spam").status_code == 400
    assert _count() == 0


def test_poprawne_dane_zapis_i_flaga(client):
    resp = _post(client, first="  Jan  ")
    assert resp.status_code == 302
    assert "visitor_ok=" in resp.headers.get("Set-Cookie", "")
    assert _count() == 1
    assert client.get("/login").status_code == 200  # przepustka działa


def test_podrobiona_przepustka_nie_dziala(client):
    client.set_cookie("visitor_ok", "podrobione")
    assert client.get("/login").status_code == 302


@pytest.mark.parametrize(
    "path",
    [
        "/health",
        "/robots.txt",
        "/static/x.css",
        "/api/nieistnieje",
        "/transport/confirm/abc",
        "/forgot-password",
        "/reset-password",
    ],
)
def test_wyjatki_nie_sa_blokowane(client, path):
    loc = client.get(path).headers.get("Location", "")
    assert "/demo-gate" not in loc


def test_retencja_90_dni():
    db = get_db()
    try:
        now = datetime.now(timezone.utc)
        dg.save_visitor(db, "Stary", "Wpis", "Firma", now - timedelta(days=91))
        dg.save_visitor(db, "Swiezy", "Wpis", "Firma", now - timedelta(days=89))
        dg.save_visitor(db, "Nowy", "Wpis", "Firma", now)
        names = [r[0] for r in db.execute("SELECT first_name FROM demo_visitors").fetchall()]
    finally:
        db.close()
    assert "Stary" not in names and {"Swiezy", "Nowy"} <= set(names)


def test_lista_bez_logowania_odmowa(client):
    assert client.get("/admin/demo-visitors").status_code in (302, 403)


def test_lista_manager_odmowa(gate_off, manager_client):
    assert manager_client.get("/admin/demo-visitors").status_code == 403


def test_lista_admin_widzi_wpisy(gate_off, admin_client):
    db = get_db()
    try:
        dg.save_visitor(db, "Anna", "Nowak", "Firma Sp. z o.o.")
    finally:
        db.close()
    html = admin_client.get("/admin/demo-visitors").get_data(as_text=True)
    assert "Anna" in html and "Nowak" in html

"""Przepustka z portfolio (blueprints/portfolio_pass.py + bramka demo). Bez prawdziwej sieci."""

import urllib.request

import pytest

pytest.importorskip("flask")

from blueprints import demo_gate as dg  # noqa: E402
from blueprints import portfolio_pass as pp  # noqa: E402
from db import get_db  # noqa: E402


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setenv("DEMO_VISITOR_GATE", "1")
    monkeypatch.delenv("PORTFOLIO_PASS", raising=False)
    monkeypatch.delenv("PORTFOLIO_URL", raising=False)
    pp._cache.clear()
    calls = []
    monkeypatch.setattr(
        urllib.request, "urlopen", lambda *a, **k: pytest.fail("prawdziwa sieć w teście")
    )
    monkeypatch.setattr(pp, "_fetch_status", lambda url, tok: calls.append((url, tok)) or 200)
    monkeypatch.setattr(dg, "notify_visitor", lambda *a: pytest.fail("własny push"))
    db = get_db()
    try:
        dg.ensure_table(db)
        db.execute("DELETE FROM demo_visitors")
        db.commit()
    finally:
        db.close()
    return calls


def _client_with(client, token="tok123"):
    client.set_cookie("gosc", token)
    return client


def test_wazna_przepustka_wpuszcza_bez_formularza(client, setup):
    r = _client_with(client).get("/login")
    assert r.status_code == 200
    assert setup == [("https://portfolio.twapp.pl", "tok123")]
    assert "visitor_ok=" in r.headers.get("Set-Cookie", "")
    # kolejne żądanie: ciasteczko dema, bez ponownego pytania portfolio
    assert client.get("/login").status_code == 200
    assert len(setup) == 1
    db = get_db()
    try:
        assert db.execute("SELECT COUNT(*) FROM demo_visitors").fetchone()[0] == 0
    finally:
        db.close()


def test_strona_bramki_przekierowuje_gdy_przepustka(client):
    r = _client_with(client).get("/demo-gate?next=/login")
    assert r.status_code == 302 and r.headers["Location"] == "/login"


def test_401_formularz(client, monkeypatch):
    monkeypatch.setattr(pp, "_fetch_status", lambda u, t: 401)
    r = _client_with(client).get("/login")
    assert r.status_code == 302 and "/demo-gate" in r.headers["Location"]
    page = client.get("/demo-gate")
    assert page.status_code == 200
    assert b"/px/doccompare" not in page.data


def test_blad_sieci_formularz(client, monkeypatch):
    def boom(u, t):
        raise TimeoutError

    monkeypatch.setattr(pp, "_fetch_status", boom)
    r = _client_with(client).get("/login")
    assert r.status_code == 302 and "/demo-gate" in r.headers["Location"]


def test_brak_ciasteczka_bez_wywolania(client, setup):
    r = client.get("/login")
    assert r.status_code == 302
    assert setup == []


def test_wylaczona_i_http(client, setup, monkeypatch):
    monkeypatch.setenv("PORTFOLIO_PASS", "0")
    assert _client_with(client).get("/login").status_code == 302
    monkeypatch.setenv("PORTFOLIO_PASS", "1")
    monkeypatch.setenv("PORTFOLIO_URL", "http://portfolio.local")
    assert client.get("/login").status_code == 302
    assert setup == []


def test_zbyt_dlugi_token():
    assert pp.valid_pass("x" * 201) is False

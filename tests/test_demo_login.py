"""„Wejdź jako demo” (core/demo.py): domyślnie wyłączone, a włączone daje sesję tylko do odczytu."""
import pytest

pytest.importorskip("flask")

from tests.conftest import CSRF_TOKEN  # noqa: E402


def _demo_login(client):
    with client.session_transaction() as sess:
        sess["_csrf_token"] = CSRF_TOKEN
    return client.post("/login/demo", data={"_csrf_token": CSRF_TOKEN})


def test_domyslnie_wylaczone(client, monkeypatch):
    monkeypatch.delenv("DEMO_LOGIN", raising=False)
    assert 'data-testid="demo-login"' not in client.get("/login").get_data(as_text=True)
    assert _demo_login(client).status_code == 404


def test_przycisk_i_wejscie_do_demo(client, monkeypatch):
    monkeypatch.setenv("DEMO_LOGIN", "it_demo")
    assert 'data-testid="demo-login"' in client.get("/login").get_data(as_text=True)
    resp = _demo_login(client)
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess["demo_readonly"] is True
        assert sess["role"] == "superuser"
        assert sess["username"] == "it_demo"


def test_wejscie_wymaga_csrf(client, monkeypatch):
    monkeypatch.setenv("DEMO_LOGIN", "it_demo")
    assert client.post("/login/demo").status_code in (400, 403)


def test_sesja_demo_tylko_do_odczytu(client, monkeypatch):
    monkeypatch.setenv("DEMO_LOGIN", "it_demo")
    _demo_login(client)
    assert client.get("/home").status_code in (200, 302)
    for method in ("post", "put", "patch", "delete"):
        resp = getattr(client, method)("/api/suppliers", json={"name": "x"})
        assert resp.status_code == 403, method
        assert "tylko podgląd" in resp.get_json()["error"]
    assert client.post("/zapisz-cokolwiek", data={"x": "1"}).status_code == 403


def test_pasek_demo_na_stronach(client, monkeypatch):
    monkeypatch.setenv("DEMO_LOGIN", "it_demo")
    _demo_login(client)
    html = client.get("/home", follow_redirects=True).get_data(as_text=True)
    assert "tylko podgląd" in html


def test_wylogowanie_dziala_w_demo(client, monkeypatch):
    monkeypatch.setenv("DEMO_LOGIN", "it_demo")
    _demo_login(client)
    with client.session_transaction() as sess:   # logowanie czyści sesję; strona da nowy token
        sess["_csrf_token"] = CSRF_TOKEN
    resp = client.post("/logout", data={"_csrf_token": CSRF_TOKEN})
    assert resp.status_code in (200, 302)
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_zwykla_sesja_bez_blokady(admin_client, monkeypatch):
    monkeypatch.setenv("DEMO_LOGIN", "it_demo")
    resp = admin_client.post("/zapisz-cokolwiek", data={"x": "1"})
    assert resp.status_code != 403 or "tylko podgląd" not in resp.get_data(as_text=True)

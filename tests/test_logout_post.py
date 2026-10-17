"""US-028: wylogowanie tylko metodą POST z tokenem CSRF.

GET /logout nie może zmieniać stanu sesji — inaczej obca strona może
wylogować użytkownika obrazkiem <img src="/logout"> (CSRF logout).
"""
import pathlib
import re

import pytest

pytest.importorskip("flask")

from tests.conftest import CSRF_TOKEN, set_session_csrf  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_get_logout_does_not_end_session(admin_client):
    resp = admin_client.get("/logout")
    assert resp.status_code == 200
    assert b'method="post"' in resp.data
    assert b'name="_csrf_token"' in resp.data
    assert admin_client.get("/home").status_code == 200


def test_post_logout_without_csrf_is_rejected(admin_client):
    resp = admin_client.post("/logout")
    assert resp.status_code == 403
    assert admin_client.get("/home").status_code == 200


def test_post_logout_with_wrong_csrf_is_rejected(admin_client):
    set_session_csrf(admin_client, CSRF_TOKEN)
    resp = admin_client.post("/logout", data={"_csrf_token": "zły-token-ąęó"})
    assert resp.status_code == 403
    assert admin_client.get("/home").status_code == 200


def test_post_logout_with_csrf_ends_session(admin_client):
    set_session_csrf(admin_client, CSRF_TOKEN)
    resp = admin_client.post("/logout", data={"_csrf_token": CSRF_TOKEN})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    assert admin_client.get("/home").status_code == 302


def test_logout_when_not_logged_in_redirects_to_login(client):
    for method in (client.get, client.post):
        resp = method("/logout")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


def test_forwarder_can_log_out(forwarder_client):
    set_session_csrf(forwarder_client, CSRF_TOKEN)
    resp = forwarder_client.post("/logout", data={"_csrf_token": CSRF_TOKEN})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_no_template_links_to_logout_via_get():
    """Strażnik: żaden szablon nie może wylogowywać linkiem (GET)."""
    offenders = []
    for path in (ROOT / "templates").rglob("*.html"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"""href\s*=\s*["']/logout""", text) or "location.href='/logout'" in text \
                or 'location.href="/logout"' in text:
            offenders.append(path.name)
    assert not offenders, f"GET /logout w szablonach: {offenders}"

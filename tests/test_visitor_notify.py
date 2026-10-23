"""Powiadomienie push (ntfy) o nowym gościu bramki demo (blueprints/visitor_notify.py)."""

import pytest

pytest.importorskip("flask")

from blueprints import demo_gate as dg  # noqa: E402
from blueprints import visitor_notify as vn  # noqa: E402
from db import get_db  # noqa: E402
from tests.conftest import CSRF_TOKEN  # noqa: E402

GOOD = {"first": "Jan", "last": "Kowalski", "company": "ACME", "gdpr": "1", "website": ""}


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setenv("DEMO_VISITOR_GATE", "1")
    monkeypatch.setenv("NTFY_URL", "https://ntfy.example/tajny-temat")
    monkeypatch.delenv("NTFY_TOKEN", raising=False)
    # Wątek uruchamiamy synchronicznie, żeby test widział wynik od razu.
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

    def fake_urlopen(req, timeout=None):
        calls.append((req, timeout))
        return _Resp()

    monkeypatch.setattr(vn.urllib.request, "urlopen", fake_urlopen)
    return calls


def _post(client, **over):
    with client.session_transaction() as s:
        s["_csrf_token"] = CSRF_TOKEN
    return client.post("/demo-gate", data={**GOOD, "_csrf_token": CSRF_TOKEN, **over})


def test_poprawny_formularz_wysyla_jedno_powiadomienie(client, sent):
    assert _post(client).status_code == 302
    assert len(sent) == 1
    req, timeout = sent[0]
    assert req.full_url == "https://ntfy.example/tajny-temat"
    assert req.get_method() == "POST" and timeout == 5
    assert req.data.decode("utf-8") == "Jan Kowalski (ACME) wszedł do DocCompare"
    h = {k.lower(): v for k, v in req.header_items()}
    assert h["title"] == "Nowy gosc: DocCompare"
    assert h["tags"] == "bell" and h["priority"] == "high"
    assert "authorization" not in h
    assert all(v.isascii() for v in h.values())


@pytest.mark.parametrize(
    "over", [{"website": "http://spam"}, {"first": ""}, {"gdpr": ""}, {"company": "x"}]
)
def test_honeypot_i_bledne_dane_bez_wysylki(client, sent, over):
    assert _post(client, **over).status_code == 400
    assert sent == []


def test_bez_ntfy_url_bez_wysylki(client, sent, monkeypatch):
    monkeypatch.delenv("NTFY_URL")
    assert _post(client).status_code == 302
    assert sent == []


def test_wyjatek_przy_wysylce_nie_psuje_odpowiedzi(client, monkeypatch):
    def boom(*a, **k):
        raise OSError("sieć leży")

    monkeypatch.setattr(vn.urllib.request, "urlopen", boom)
    resp = _post(client)
    assert resp.status_code == 302
    assert "visitor_ok=" in resp.headers.get("Set-Cookie", "")


def test_token_daje_naglowek_authorization(client, sent, monkeypatch):
    monkeypatch.setenv("NTFY_TOKEN", "tk_abc")
    assert _post(client).status_code == 302
    assert sent[0][0].get_header("Authorization") == "Bearer tk_abc"


def test_body_przyciete_do_300_znakow():
    req = vn.build_request("A" * 100, "B" * 100, "C" * 100)
    assert len(req.data.decode("utf-8")) == 300


def test_klauzula_wspomina_ntfy():
    assert "ntfy" in dg.GDPR_PL and "poza tym nikomu danych nie przekazuję" in dg.GDPR_PL
    assert "ntfy" in dg.GDPR_EN and "apart from that I do not share" in dg.GDPR_EN

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


def test_klauzula_wspomina_ntfy_i_aktywnosc():
    assert (
        "O każdej wizycie (imię, nazwisko, firma) dostaję powiadomienie na telefon przez usługę "
        "powiadomień push ntfy. Zapisuję też, ile i jakie ekrany wersji demonstracyjnej "
        "obejrzałeś (bez adresu IP), żeby wiedzieć, co zainteresowało gości. Poza tym nikomu "
        "danych nie przekazuję." in dg.GDPR_PL
    )
    assert (
        "I receive a phone notification of each visit (first name, last name, company) via the "
        "ntfy push notification service. I also record how many and which screens of the demo "
        "you viewed (without your IP address) to see what visitors find interesting. Apart from "
        "that I do not share the data with anyone." in dg.GDPR_EN
    )


# ── A. Alarm „uwaga, ta firma” (NTFY_WATCH_COMPANIES) ───────────────────────────


def _headers(req):
    return {k.lower(): v for k, v in req.header_items()}


def test_firma_z_listy_daje_alarm(client, sent, monkeypatch):
    monkeypatch.setenv("NTFY_WATCH_COMPANIES", "globex, acme")
    assert _post(client, company="ÄCME sp. z o.o.").status_code == 302
    req = sent[0][0]
    h = _headers(req)
    assert h["priority"] == "urgent" and h["tags"] == "rotating_light"
    assert h["title"] == "UWAGA firma z listy: DocCompare"
    assert all(v.isascii() for v in h.values())
    assert req.data.decode("utf-8") == "⚠️ Jan Kowalski (ÄCME sp. z o.o.) wszedł do DocCompare"


@pytest.mark.parametrize(
    "company,phrases,hit",
    [
        ("Łódzka  Firma  Testowa", "lodzka firma", True),
        ("ZAŻÓŁĆ Sp. z o.o.", "zazolc", True),
        ("Inna firma", "acme", False),
        ("ACME", "", False),
        ("ACME", " , a ,", False),  # frazy krótsze niż 2 znaki są ignorowane
    ],
)
def test_dopasowanie_firmy(monkeypatch, company, phrases, hit):
    monkeypatch.setenv("NTFY_WATCH_COMPANIES", phrases)
    assert vn.is_watched(company) is hit


def test_brak_trafienia_zwykly_push(client, sent, monkeypatch):
    monkeypatch.setenv("NTFY_WATCH_COMPANIES", "globex")
    assert _post(client).status_code == 302
    h = _headers(sent[0][0])
    assert h["priority"] == "high" and h["tags"] == "bell"


def test_pusta_lista_zwykly_push(client, sent, monkeypatch):
    monkeypatch.setenv("NTFY_WATCH_COMPANIES", "")
    assert _post(client).status_code == 302
    assert _headers(sent[0][0])["title"] == "Nowy gosc: DocCompare"


def test_alarm_bez_ntfy_url_nic_nie_wysyla(client, sent, monkeypatch):
    monkeypatch.delenv("NTFY_URL")
    monkeypatch.setenv("NTFY_WATCH_COMPANIES", "acme")
    assert _post(client).status_code == 302
    assert sent == []

"""
blueprints/visitor_notify.py — powiadomienia push (ntfy) o gościach bramki demo.

Dwa rodzaje powiadomień (oba no-op bez env `NTFY_URL`):
  • `notify_visitor` — nowy gość (wywołanie z `demo_gate.gate` po UDANYM zapisie),
  • `notify_engaged` — gość obejrzał już `NTFY_ENGAGED_VIEWS` ekranów (z `visitor_activity`).
Firma gościa pasująca do listy `NTFY_WATCH_COMPANIES` → priorytet `urgent` (alarm).
Wysyłka w wątku daemon, żeby nie opóźniać odpowiedzi; każdy błąd → ostrzeżenie w logu,
nigdy błąd dla gościa. Zero ruchu sieciowego lokalnie, w CI i w testach.

Env:
  NTFY_URL              — pełny URL tematu, np. https://ntfy.sh/<tajny-temat> (lub własny serwer),
  NTFY_TOKEN            — opcjonalny token → nagłówek `Authorization: Bearer <token>`,
  NTFY_WATCH_COMPANIES  — frazy rozdzielone przecinkami; fraza zawarta w nazwie firmy gościa
                          (bez wielkości liter i polskich znaków) → alarm „UWAGA firma z listy”,
  NTFY_ENGAGED_VIEWS    — próg ekranów dla pushu „zaangażowany gość” (domyślnie 10; 0 = wyłączone).

Stdlib (`urllib.request`) celowo: httpx jest tylko w requirements-prod, a CI go nie instaluje.
"""

from __future__ import annotations

import logging
import os
import threading
import unicodedata
import urllib.request

log = logging.getLogger(__name__)

APP_NAME = "DocCompare"
TIMEOUT_S = 5
MAX_BODY = 300
DEFAULT_ENGAGED_VIEWS = 10
MIN_PHRASE = 2
# „ł” nie rozkłada się w NFKD (to osobna litera, nie l + znak łączący).
_EXTRA = str.maketrans({"ł": "l", "Ł": "l", "ø": "o", "Ø": "o", "đ": "d", "Đ": "d"})


def normalize(text: str) -> str:
    """casefold + usunięcie znaków diakrytycznych (NFKD) + redukcja spacji."""
    decomposed = unicodedata.normalize("NFKD", (text or "").translate(_EXTRA))
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(stripped.casefold().split())


def watch_phrases() -> list[str]:
    raw = os.environ.get("NTFY_WATCH_COMPANIES", "")
    phrases = (normalize(p) for p in raw.split(","))
    return [p for p in phrases if len(p) >= MIN_PHRASE]


def is_watched(company: str) -> bool:
    """True, gdy któraś fraza z `NTFY_WATCH_COMPANIES` jest zawarta w nazwie firmy."""
    name = normalize(company)
    return bool(name) and any(p in name for p in watch_phrases())


def engaged_threshold() -> int:
    raw = os.environ.get("NTFY_ENGAGED_VIEWS", "").strip()
    if not raw:
        return DEFAULT_ENGAGED_VIEWS
    try:
        return max(0, int(raw))
    except ValueError:
        log.warning("NTFY_ENGAGED_VIEWS nie jest liczbą — używam %s", DEFAULT_ENGAGED_VIEWS)
        return DEFAULT_ENGAGED_VIEWS


def _make_request(body: str, title: str, tags: str, priority: str) -> urllib.request.Request | None:
    """Żądanie POST do ntfy albo None, gdy `NTFY_URL` nie jest ustawiony / niepoprawny."""
    url = os.environ.get("NTFY_URL", "").strip()
    if not url:
        return None
    if not url.lower().startswith(("https://", "http://")):
        log.warning("NTFY_URL musi zaczynać się od http(s):// — powiadomienie pominięte")
        return None
    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Title": title,  # nagłówki tylko ASCII
        "Tags": tags,
        "Priority": priority,
    }
    token = os.environ.get("NTFY_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = body[:MAX_BODY].encode("utf-8")
    return urllib.request.Request(url, data=data, headers=headers, method="POST")


def build_request(first: str, last: str, company: str) -> urllib.request.Request | None:
    """Push o nowym gościu; firma z listy obserwowanych → alarm (urgent)."""
    body = f"{first} {last} ({company}) wszedł do {APP_NAME}"
    if is_watched(company):
        return _make_request(
            "⚠️ " + body, f"UWAGA firma z listy: {APP_NAME}", "rotating_light", "urgent"
        )
    return _make_request(body, f"Nowy gosc: {APP_NAME}", "bell", "high")


def build_engaged_request(
    first: str, last: str, company: str, views: int
) -> urllib.request.Request | None:
    """Push „gość ogląda demo” (normalny priorytet; firma z listy → urgent)."""
    body = f"{first} {last} ({company}) obejrzał już {views} ekranów w {APP_NAME}"
    priority = "urgent" if is_watched(company) else "default"
    return _make_request(body, f"Gosc oglada demo: {APP_NAME}", "eyes", priority)


def _send(req: urllib.request.Request) -> None:
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # nosec B310 — URL z env operatora
            resp.read(0)
    except Exception as exc:  # noqa: BLE001 — powiadomienie nie może psuć bramki
        log.warning("Powiadomienie ntfy o gościu nie wysłane: %s", type(exc).__name__)


def _start(req: urllib.request.Request) -> None:
    threading.Thread(target=_send, args=(req,), daemon=True, name="ntfy-visitor").start()


def _dispatch(builder, *args) -> None:
    try:
        req = builder(*args)
        if req is not None:
            _start(req)
    except Exception as exc:  # noqa: BLE001
        log.warning("Powiadomienie ntfy o gościu pominięte: %s", type(exc).__name__)


def notify_visitor(first: str, last: str, company: str) -> None:
    """Wysyła powiadomienie o nowym gościu w tle; no-op bez `NTFY_URL`. Nigdy nie rzuca."""
    _dispatch(build_request, first, last, company)


def notify_engaged(first: str, last: str, company: str, views: int) -> None:
    """Wysyła push „zaangażowany gość” w tle; no-op bez `NTFY_URL`. Nigdy nie rzuca."""
    _dispatch(build_engaged_request, first, last, company, views)

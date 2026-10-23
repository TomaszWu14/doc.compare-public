"""
blueprints/visitor_notify.py — powiadomienie push (ntfy) o nowym gościu bramki demo.

Wywoływane z `demo_gate.gate` tylko po UDANYM zapisie gościa. Bez env `NTFY_URL` → no-op
(zero ruchu sieciowego; tak jest lokalnie, w CI i w testach). Wysyłka w wątku daemon,
żeby nie opóźniać odpowiedzi; każdy błąd → ostrzeżenie w logu, nigdy błąd dla gościa.

Env:
  NTFY_URL   — pełny URL tematu, np. https://ntfy.sh/<tajny-temat> (lub własny serwer ntfy),
  NTFY_TOKEN — opcjonalny token → nagłówek `Authorization: Bearer <token>`.

Stdlib (`urllib.request`) celowo: httpx jest tylko w requirements-prod, a CI go nie instaluje.
"""

from __future__ import annotations

import logging
import os
import threading
import urllib.request

log = logging.getLogger(__name__)

APP_NAME = "DocCompare"
TIMEOUT_S = 5
MAX_BODY = 300


def build_request(first: str, last: str, company: str) -> urllib.request.Request | None:
    """Buduje żądanie POST do ntfy albo None, gdy `NTFY_URL` nie jest ustawiony."""
    url = os.environ.get("NTFY_URL", "").strip()
    if not url:
        return None
    if not url.lower().startswith(("https://", "http://")):
        log.warning("NTFY_URL musi zaczynać się od http(s):// — powiadomienie pominięte")
        return None
    body = f"{first} {last} ({company}) wszedł do {APP_NAME}"[:MAX_BODY]
    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Title": f"Nowy gosc: {APP_NAME}",  # nagłówki tylko ASCII
        "Tags": "bell",
        "Priority": "high",
    }
    token = os.environ.get("NTFY_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, data=body.encode("utf-8"), headers=headers, method="POST")


def _send(req: urllib.request.Request) -> None:
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # nosec B310 — URL z env operatora
            resp.read(0)
    except Exception as exc:  # noqa: BLE001 — powiadomienie nie może psuć bramki
        log.warning("Powiadomienie ntfy o gościu nie wysłane: %s", type(exc).__name__)


def _start(req: urllib.request.Request) -> None:
    threading.Thread(target=_send, args=(req,), daemon=True, name="ntfy-visitor").start()


def notify_visitor(first: str, last: str, company: str) -> None:
    """Wysyła powiadomienie w tle; no-op bez `NTFY_URL`. Nigdy nie rzuca wyjątku."""
    try:
        req = build_request(first, last, company)
        if req is not None:
            _start(req)
    except Exception as exc:  # noqa: BLE001
        log.warning("Powiadomienie ntfy o gościu pominięte: %s", type(exc).__name__)

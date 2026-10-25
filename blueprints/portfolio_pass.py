"""
blueprints/portfolio_pass.py — przepustka z portfolio (https://portfolio.twapp.pl).

Rekruter przedstawia się raz w portfolio; portfolio ustawia ciasteczko `gosc` (domena `.twapp.pl`).
Gdy bramka demo (blueprints/demo_gate.py) nie zna gościa, a w żądaniu jest `gosc`, pytamy portfolio
server-to-server: `GET {PORTFOLIO_URL}/api/gosc` z nagłówkiem `Cookie: gosc=<token>` (timeout 2 s,
bez przekierowań). Interpretujemy wyłącznie kod statusu: 200 = wpuść; wszystko inne (401, błąd
sieci, timeout) = zachowanie jak dziś (formularz). Nigdy nie rzuca wyjątku.

Env: `PORTFOLIO_URL` (domyślnie https://portfolio.twapp.pl; musi zaczynać się od https://),
`PORTFOLIO_PASS` (`0` wyłącza sprawdzanie). Wartość ciasteczka nie trafia do logów.
Wynik pozytywny jest cache'owany w pamięci procesu po skrócie SHA-256 tokenu (10 min); dodatkowo
demo wystawia własne ciasteczko `visitor_ok`, więc kolejne żądania w ogóle tu nie trafiają.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
import urllib.error
import urllib.request

log = logging.getLogger(__name__)

COOKIE_NAME = "gosc"
MAX_TOKEN_LEN = 200
TIMEOUT_S = 2
CACHE_TTL_S = 600
CACHE_MAX = 1000
DEFAULT_URL = "https://portfolio.twapp.pl"
_FALSE = {"0", "false", "no", "off", "nie"}

_cache: dict[str, float] = {}  # sha256(token) -> czas wygaśnięcia (monotonic)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401 — wyłącza podążanie za 3xx
        return None


def pass_enabled() -> bool:
    return os.environ.get("PORTFOLIO_PASS", "").strip().lower() not in _FALSE


def _base_url() -> str | None:
    url = (os.environ.get("PORTFOLIO_URL", "").strip() or DEFAULT_URL).rstrip("/")
    if not url.lower().startswith("https://"):
        log.warning(
            "PORTFOLIO_URL musi zaczynać się od https:// — sprawdzanie przepustki wyłączone"
        )
        return None
    return url


def _fetch_status(url: str, token: str) -> int:
    """Kod statusu odpowiedzi portfolio (osobna funkcja = jedno miejsce do zamockowania w testach)."""
    req = urllib.request.Request(
        url + "/api/gosc", headers={"Cookie": f"{COOKIE_NAME}={token}"}, method="GET"
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=TIMEOUT_S) as resp:  # nosec B310 — https wymuszone w _base_url
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


def valid_pass(token: str | None) -> bool:
    """True, gdy portfolio potwierdziło przepustkę `token` (z cache lub zapytaniem)."""
    try:
        if not token or len(token) > MAX_TOKEN_LEN or not pass_enabled():
            return False
        key = hashlib.sha256(token.encode("utf-8", "replace")).hexdigest()
        now = time.monotonic()
        if _cache.get(key, 0.0) > now:
            return True
        base = _base_url()
        if base is None:
            return False
        if _fetch_status(base, token) != 200:
            return False
        if len(_cache) >= CACHE_MAX:
            for k in [k for k, exp in _cache.items() if exp <= now] or [next(iter(_cache))]:
                _cache.pop(k, None)
        _cache[key] = now + CACHE_TTL_S
        return True
    except Exception as exc:  # noqa: BLE001 — błąd portfolio = formularz, nie 500
        log.warning("Sprawdzenie przepustki z portfolio nieudane: %s", type(exc).__name__)
        return False

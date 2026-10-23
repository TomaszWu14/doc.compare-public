"""
blueprints/demo_gate.py — „bramka odwiedzin” przed wersją demonstracyjną.

Uprzejmy, obowiązkowy formularz: imię, nazwisko, firma + zgoda RODO (+ honeypot).
Dopóki odwiedzający się nie przedstawi, każda strona (poza wyjątkami) przekierowuje
na /demo-gate. Zalogowani (autor) przechodzą bez formularza.

Włączanie (patrz `gate_enabled`):
  • DEMO_VISITOR_GATE=1/true/on  → włączona,  =0/false/off → wyłączona,
  • zmienna nieustawiona → włączona tylko na instancji demo, tj. gdy APP_BASE_URL wskazuje
    doc.compare.twapp.pl; lokalnie i w CI → wyłączona.

Znacznik „przedstawił się” to PODPISANE ciasteczko `visitor_ok` (30 dni). Celowo nie sesja
Flask: ta żyje 8 h, a logowanie robi `session.clear()`.

Przechowujemy wyłącznie imię, nazwisko, firmę i datę (bez IP i user-agenta); wpisy starsze
niż 90 dni kasujemy przy każdym zapisie. Import: core/db (blueprint → core, nigdy → app).
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from itsdangerous import BadSignature, URLSafeTimedSerializer

from core.audit import log_audit as _log_audit
from core.security import require_role, verify_csrf
from db import get_db

bp = Blueprint("demo_gate", __name__)

COOKIE_NAME = "visitor_ok"
COOKIE_MAX_AGE = 30 * 24 * 3600  # 30 dni
RETENTION_DAYS = 90
GATE_PATH = "/demo-gate"
DEMO_HOST = "doc.compare.twapp.pl"

# Wyjątki: nigdy nie blokujemy (health-check, boty, zasoby, API z tokenem, linki z tokenem, reset hasła).
EXEMPT_EXACT = frozenset(
    {"/health", "/robots.txt", GATE_PATH, "/favicon.ico", "/manifest.json", "/sw.js"}
)
EXEMPT_PREFIXES = (
    "/static/",
    "/api/",
    "/transport/confirm/",
    "/forgot-password",
    "/reset-password",
)

_CTRL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_TRUE = {"1", "true", "yes", "on", "tak"}
_FALSE = {"0", "false", "no", "off", "nie"}

GDPR_PL = (
    "Administratorem danych jest Tomasz Wierzbowski (kontakt: tomasz.wierzbowski@op.pl). "
    "Imię, nazwisko i nazwę firmy przetwarzam wyłącznie w celu kontroli dostępu do wersji "
    "demonstracyjnej i statystyki odwiedzin portfolio, na podstawie prawnie uzasadnionego interesu "
    "(art. 6 ust. 1 lit. f RODO). Dane przechowuję 90 dni, potem są automatycznie usuwane, i nikomu "
    "ich nie przekazuję. Masz prawo dostępu do danych, ich sprostowania, usunięcia, ograniczenia "
    "przetwarzania i sprzeciwu – napisz na adres powyżej. Przysługuje Ci skarga do Prezesa UODO."
)
GDPR_EN = (
    "The data controller is Tomasz Wierzbowski (contact: tomasz.wierzbowski@op.pl). I process your "
    "first name, last name and company name solely to control access to the demo version and to "
    "compile portfolio visit statistics, based on legitimate interest (Art. 6(1)(f) GDPR). Data is "
    "kept for 90 days and then deleted automatically; it is not shared with anyone. You have the "
    "right of access, rectification, erasure, restriction of processing and objection - write to the "
    "address above. You may lodge a complaint with the Polish data protection authority (UODO)."
)
TEXTS = {
    "pl": {
        "title": "Przedstaw się",
        "lead": "Zanim wejdziesz do wersji demonstracyjnej, przedstaw się, proszę.",
        "first": "Imię",
        "last": "Nazwisko",
        "company": "Firma",
        "submit": "Wchodzę →",
        "consent": "Zapoznałem(-am) się z klauzulą informacyjną i chcę wejść do wersji demonstracyjnej.",
        "gdpr": GDPR_PL,
        "err_len": "Wpisz imię, nazwisko i firmę (2–100 znaków, bez znaków specjalnych).",
        "err_consent": "Zaznacz zgodę na przetwarzanie danych, aby wejść.",
        "err_generic": "Nie udało się zapisać formularza. Odśwież stronę i spróbuj ponownie.",
    },
    "en": {
        "title": "Introduce yourself",
        "lead": "Before you enter the demo, please introduce yourself.",
        "first": "First name",
        "last": "Last name",
        "company": "Company",
        "submit": "Enter →",
        "consent": "I have read the information clause and want to enter the demo.",
        "gdpr": GDPR_EN,
        "err_len": "Enter first name, last name and company (2-100 characters, no control characters).",
        "err_consent": "Please tick the consent box to continue.",
        "err_generic": "The form could not be saved. Reload the page and try again.",
    },
}


def gate_enabled() -> bool:
    raw = os.environ.get("DEMO_VISITOR_GATE", "").strip().lower()
    if raw in _TRUE:
        return True
    if raw in _FALSE:
        return False
    return DEMO_HOST in os.environ.get("APP_BASE_URL", "").lower()


def is_exempt(path: str) -> bool:
    path = path or "/"
    return path in EXEMPT_EXACT or path.startswith(EXEMPT_PREFIXES)


def clean_field(value) -> str | None:
    """Trim + 2–100 znaków, bez znaków sterujących; None gdy niepoprawne."""
    v = (value or "").strip() if isinstance(value, str) else ""
    if not 2 <= len(v) <= 100 or _CTRL.search(v):
        return None
    return v


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.secret_key, salt="demo-visitor-gate")


def has_pass() -> bool:
    tok = request.cookies.get(COOKIE_NAME)
    if not tok:
        return False
    try:
        return _serializer().loads(tok, max_age=COOKIE_MAX_AGE) == "ok"
    except BadSignature:
        return False


def ensure_table(db) -> None:
    db.execute(
        "CREATE TABLE IF NOT EXISTS demo_visitors ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT NOT NULL, "
        "last_name TEXT NOT NULL, company TEXT NOT NULL, created_at TEXT NOT NULL)"
    )


def _ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def save_visitor(db, first: str, last: str, company: str, now: datetime | None = None) -> None:
    """Zapisuje wpis i kasuje wpisy starsze niż 90 dni (zapytania parametryzowane)."""
    now = now or datetime.now(timezone.utc)
    ensure_table(db)
    db.execute(
        "DELETE FROM demo_visitors WHERE created_at < ?",
        (_ts(now - timedelta(days=RETENTION_DAYS)),),
    )
    db.execute(
        "INSERT INTO demo_visitors(first_name, last_name, company, created_at) VALUES (?,?,?,?)",
        (first, last, company, _ts(now)),
    )
    db.commit()


def _safe_next(value: str | None) -> str:
    """Tylko ścieżka wewnętrzna (bez open-redirect)."""
    if (
        value
        and value.startswith("/")
        and not value.startswith(("//", "/\\"))
        and GATE_PATH not in value
    ):
        return value
    return "/"


def _lang() -> str:
    return "en" if session.get("lang") == "en" else "pl"


@bp.before_app_request
def _gate():
    if not gate_enabled() or is_exempt(request.path):
        return None
    if session.get("user_id") or has_pass():
        return None
    if request.method == "GET":
        nxt = request.full_path.rstrip("?")
        return redirect(url_for("demo_gate.gate", next=nxt))
    return redirect(url_for("demo_gate.gate"))


@bp.route(GATE_PATH, methods=["GET", "POST"])
def gate():
    if not gate_enabled():
        return ("Nie znaleziono", 404)
    nxt = _safe_next(request.values.get("next"))
    tx = TEXTS[_lang()]
    status, error = 200, None
    form = {"first": "", "last": "", "company": ""}
    if request.method == "POST":
        form = {k: (request.form.get(k) or "") for k in form}
        if not verify_csrf():
            status, error = 403, tx["err_generic"]
        elif request.form.get("website"):  # honeypot — człowiek tego nie widzi
            status, error = 400, tx["err_generic"]
        elif not request.form.get("gdpr"):
            status, error = 400, tx["err_consent"]
        else:
            vals = [clean_field(form[k]) for k in ("first", "last", "company")]
            if None in vals:
                status, error = 400, tx["err_len"]
            else:
                db = get_db()
                try:
                    save_visitor(db, *vals)
                finally:
                    db.close()
                resp = redirect(nxt)
                resp.set_cookie(
                    COOKIE_NAME,
                    _serializer().dumps("ok"),
                    max_age=COOKIE_MAX_AGE,
                    httponly=True,
                    samesite="Lax",
                    secure=bool(current_app.config.get("SESSION_COOKIE_SECURE")),
                )
                return resp
    return render_template(
        "demo_gate.html", tx=tx, lang=_lang(), error=error, form=form, next=nxt
    ), status


@bp.route("/admin/demo-visitors")
@require_role("admin")
def visitors():
    db = get_db()
    try:
        ensure_table(db)
        rows = db.execute(
            "SELECT id, first_name, last_name, company, created_at FROM demo_visitors "
            "ORDER BY created_at DESC, id DESC"
        ).fetchall()
    finally:
        db.close()
    _log_audit("demo_visitors_view", session.get("username"), f"{len(rows)} wpisów")
    return render_template(
        "demo_visitors.html", rows=[dict(r) for r in rows], retention=RETENTION_DAYS
    )

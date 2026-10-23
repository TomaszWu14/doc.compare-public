"""
blueprints/visitor_activity.py — aktywność gościa bramki demo po wejściu.

Przy wpisie w `demo_visitors` liczymy: `page_views` (obejrzane ekrany), `last_seen_at`
(ostatni ekran, UTC) i `sections` (JSON: sekcja → liczba, max 20 kluczy). Bez IP i user-agenta.

Liczy hook `after_app_request` w `demo_gate` (tylko udane GET-y stron HTML od gościa
z podpisanym ciasteczkiem `visitor_ok` niosącym id wpisu); tu jest logika zapisu i prezentacji.
Każdy błąd → ostrzeżenie w logu, odpowiedź bez zmian. Po osiągnięciu dokładnie
`NTFY_ENGAGED_VIEWS` ekranów → jeden push (blueprints/visitor_notify.py).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from db import get_db

from blueprints.visitor_notify import engaged_threshold, notify_engaged

log = logging.getLogger(__name__)

MAX_SECTIONS = 20
SECTION_LEN = 40
TS_FMT = "%Y-%m-%d %H:%M:%S"
COLUMNS = (
    ("page_views", "INTEGER NOT NULL DEFAULT 0"),
    ("last_seen_at", "TEXT"),
    ("sections", "TEXT"),
)
_NOT_SECTION = re.compile(r"[^a-z0-9_-]")
_columns_ready = False


def ensure_columns(db) -> None:
    """Leniwie dodaje kolumny aktywności do starej tabeli (raz na proces)."""
    global _columns_ready
    if _columns_ready:
        return
    for col, definition in COLUMNS:
        try:
            db.execute(f"SELECT {col} FROM demo_visitors WHERE 1=0").fetchall()  # nosec B608 — kolumna ze stałej COLUMNS
        except Exception:  # noqa: BLE001 — brak kolumny
            db.rollback()
            db.execute(f"ALTER TABLE demo_visitors ADD COLUMN {col} {definition}")
            db.commit()
    _columns_ready = True


def section_for(path: str) -> str | None:
    """Pierwszy segment ścieżki (`/` → `start`), tylko [a-z0-9_-], max 40 znaków."""
    first = (path or "/").strip("/").split("/", 1)[0]
    if not first:
        return "start"
    clean = _NOT_SECTION.sub("", first.lower())[:SECTION_LEN]
    return clean or None


def load_sections(raw) -> dict[str, int]:
    try:
        data = json.loads(raw) if raw else {}
    except (TypeError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): int(v) for k, v in data.items() if isinstance(v, int)}


def bump_section(sections: dict[str, int], section: str | None) -> dict[str, int]:
    if section and (section in sections or len(sections) < MAX_SECTIONS):
        sections[section] = sections.get(section, 0) + 1
    return sections


def record_view(visitor_id: int, path: str, now: datetime | None = None) -> None:
    """Zapisuje jeden obejrzany ekran gościa. Nigdy nie rzuca wyjątku."""
    try:
        _record(visitor_id, path, now or datetime.now(timezone.utc))
    except Exception as exc:  # noqa: BLE001 — liczenie nie może psuć odpowiedzi
        log.warning("Aktywność gościa demo nie zapisana: %s", type(exc).__name__)


def _record(visitor_id: int, path: str, now: datetime) -> None:
    db = get_db()
    try:
        ensure_columns(db)
        row = db.execute(
            "SELECT first_name, last_name, company, page_views, sections "
            "FROM demo_visitors WHERE id=?",
            (visitor_id,),
        ).fetchone()
        if row is None:  # wpis skasowany (retencja) — nic nie liczymy
            return
        row = dict(row)
        sections = bump_section(load_sections(row["sections"]), section_for(path))
        db.execute(
            "UPDATE demo_visitors SET page_views=COALESCE(page_views, 0)+1, last_seen_at=?, "
            "sections=? WHERE id=?",
            (now.strftime(TS_FMT), json.dumps(sections, ensure_ascii=False), visitor_id),
        )
        db.commit()
    finally:
        db.close()
    views = int(row["page_views"] or 0) + 1
    threshold = engaged_threshold()
    if threshold and views == threshold:
        notify_engaged(row["first_name"], row["last_name"], row["company"], views)


def format_duration(created_at, last_seen_at) -> str:
    """Czas wizyty = last_seen_at − created_at jako „ok. N min” albo „—”."""
    try:
        start = datetime.strptime(str(created_at), TS_FMT)
        end = datetime.strptime(str(last_seen_at), TS_FMT)
    except (TypeError, ValueError):
        return "—"
    minutes = max(0, round((end - start).total_seconds() / 60))
    return f"ok. {minutes} min"


def top_sections(raw, n: int = 3) -> str:
    items = sorted(load_sections(raw).items(), key=lambda kv: (-kv[1], kv[0]))[:n]
    return ", ".join(f"{k} ({v})" for k, v in items) or "—"


def enrich(row: dict) -> dict:
    """Dokłada do wiersza listy gości kolumny „Ekrany”, „Czas”, „Najczęściej”."""
    row["page_views"] = int(row.get("page_views") or 0)
    row["duration"] = format_duration(row.get("created_at"), row.get("last_seen_at"))
    row["top_sections"] = top_sections(row.get("sections"))
    return row

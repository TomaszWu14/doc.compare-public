"""core/rate_limit.py — limit wywołań kosztownych endpointów per użytkownik.

Wydzielone z app.py (US-006), żeby blueprinty (PalViz, dostawcy) mogły używać
tego samego limitu bez importu z `app`.

Licznik jest w bazie (tabela `api_rate_events`), więc jest wspólny dla wszystkich
workerów gunicorna. Przy błędzie bazy działa awaryjnie licznik w pamięci procesu.
Wszystkie ciężkie trasy dzielą jeden licznik: API_RATE_MAX wywołań na
API_RATE_WINDOW sekund na użytkownika.
"""
from __future__ import annotations

import threading
import time
from functools import wraps

from flask import jsonify, session

from constants import API_RATE_MAX, API_RATE_WINDOW
from db import get_db

RATE_LIMIT_MESSAGE = "Zbyt wiele żądań. Odczekaj minutę i spróbuj ponownie."

_table_ready = False
_mem_attempts: dict = {}
_mem_lock = threading.Lock()


def _ensure_table(db) -> None:
    global _table_ready
    if _table_ready:
        return
    db.execute("""CREATE TABLE IF NOT EXISTS api_rate_events (
        user_id INTEGER NOT NULL,
        created_at DOUBLE PRECISION NOT NULL
    )""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_api_rate_user_ts ON api_rate_events(user_id, created_at)")
    db.commit()
    _table_ready = True


def check_and_record(user_id: int) -> bool:
    """Sprawdza limit i rejestruje wywołanie. Zwraca True, gdy limit przekroczony."""
    now = time.time()
    cutoff = now - API_RATE_WINDOW
    try:
        db = get_db()
        try:
            _ensure_table(db)
            db.execute("DELETE FROM api_rate_events WHERE user_id=? AND created_at < ?",
                       (user_id, cutoff))
            count = db.execute(
                "SELECT COUNT(*) FROM api_rate_events WHERE user_id=? AND created_at >= ?",
                (user_id, cutoff)).fetchone()[0]
            if count >= API_RATE_MAX:
                db.commit()
                return True
            db.execute("INSERT INTO api_rate_events(user_id, created_at) VALUES(?,?)",
                       (user_id, now))
            db.commit()
            return False
        finally:
            db.close()
    except Exception:
        with _mem_lock:
            ts = [t for t in _mem_attempts.get(user_id, []) if now - t < API_RATE_WINDOW]
            if len(ts) >= API_RATE_MAX:
                _mem_attempts[user_id] = ts
                return True
            ts.append(now)
            _mem_attempts[user_id] = ts[-(API_RATE_MAX + 5):]
            return False


def rate_limit_response():
    resp = jsonify({"error": RATE_LIMIT_MESSAGE})
    resp.status_code = 429
    resp.headers["Retry-After"] = str(API_RATE_WINDOW)
    return resp


def heavy_rate_limit(f):
    """Dekorator: limit wywołań dla kosztownych tras (AI, OCR, render PDF).

    Umieszczać POD `@login_required` i `@csrf_protect`, żeby żądania
    niezalogowane lub z błędnym tokenem nie zużywały limitu.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        uid = session.get("user_id")
        # check_and_record szukane w czasie wywołania — testy mogą je podmienić.
        if uid is not None and check_and_record(uid):
            return rate_limit_response()
        return f(*args, **kwargs)
    wrapper._heavy_rate_limited = True
    return wrapper

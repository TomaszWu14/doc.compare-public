"""
core/demo.py — konto gościa „Wejdź jako demo” (tylko podgląd).

Domyślnie WYŁĄCZONE. Włącza je zmienna DEMO_LOGIN (nazwa konta demo, np. `demo`) — ustaw ją
wyłącznie na instancji pokazowej z danymi syntetycznymi. Wtedy:
  • strona logowania pokazuje przycisk „Wejdź jako demo”, który wysyła POST /login/demo (z CSRF),
  • konto demo zakłada się samo (rola superuser — widzi wszystkie dostawy; losowe, nieznane hasło),
  • sesja demo jest TYLKO DO ODCZYTU: każdy POST/PUT/PATCH/DELETE (poza wylogowaniem) dostaje 403.
Blokada działa w jednym miejscu (before_request), więc nowa trasa zapisu nie może jej ominąć.
"""
from __future__ import annotations

import os
import secrets

from flask import jsonify, request, session
from werkzeug.security import generate_password_hash

DEMO_ROLE = "superuser"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
# Zapisy dozwolone w sesji demo: wyłącznie wylogowanie.
ALLOWED_WRITE_ENDPOINTS = frozenset({"auth.logout"})
READONLY_MSG = "Wersja demo: tylko podgląd — zapis jest wyłączony."


def demo_login() -> str:
    """Nazwa konta demo albo pusty tekst (funkcja wyłączona)."""
    return os.environ.get("DEMO_LOGIN", "").strip()


def demo_enabled() -> bool:
    return bool(demo_login())


def ensure_demo_user(db):
    """Zwraca wiersz konta demo; zakłada je przy pierwszym wejściu. Hasło losowe i nigdzie
    niezapisane — na konto demo da się wejść tylko przyciskiem, nie formularzem logowania."""
    name = demo_login()
    row = db.execute("SELECT * FROM users WHERE username=?", (name,)).fetchone()
    if row is None:
        db.execute(
            "INSERT INTO users(username, password_hash, role) VALUES (?,?,?)",
            (name, generate_password_hash(secrets.token_urlsafe(32)), DEMO_ROLE),
        )
        db.commit()
        row = db.execute("SELECT * FROM users WHERE username=?", (name,)).fetchone()
    return row


def readonly_guard():
    """before_request: w sesji demo odrzuca każdą metodę zapisu (poza wylogowaniem)."""
    if not session.get("demo_readonly"):
        return None
    if request.method in SAFE_METHODS or request.endpoint in ALLOWED_WRITE_ENDPOINTS:
        return None
    wants_json = (request.path or "").startswith("/api/") or request.is_json \
        or "application/json" in (request.headers.get("Accept") or "")
    if wants_json:
        return jsonify({"error": READONLY_MSG}), 403
    return READONLY_MSG, 403

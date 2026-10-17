# Runbook operacyjny

> [DEV] Wersja 0.1 (2026-10-16). Źródła szczegółowe: `docs/DOKUMENTACJA_IT.md` (hosting, stos), `docs/BACKUP_RESTORE.md`
> (backup, offsite, próba odtworzenia), `docs/OBRAZ_BAZOWY_ML.md` (obraz ML), `.env.example` (konfiguracja).
> Pozycje **(do potwierdzenia)** wymagają decyzji PO.

## 1. Środowiska

| Środowisko | Gdzie | Dane | Dostęp |
|---|---|---|---|
| Lokalne dev | `python app.py`, SQLite `instance/doccompare.db` | syntetyczne, konta seedowane przy pierwszym starcie | deweloper |
| Demo | `https://doc.compare.twapp.pl` — Coolify na Hetzner, PostgreSQL, wolumen `/data` | syntetyczne, bez kluczy AI | właściciel (brak konta gościa) |
| Produkcja ACME (oryginał) | Coolify/Hetzner wg `DOKUMENTACJA_IT.md` | realne | poza tą kopią portfolio |

## 2. Wdrożenie

1. PR scalony do `main` po akceptacji PO.
2. `ci.yml` (lint + testy) zielone na `main` → `deploy.yml` wywołuje API Coolify (`workflow_run`). Zmiany tylko
   w `*.md`/`docs/**` nie uruchamiają CI, więc nie wdrażają się.
3. Kontener startuje: `python migrate_db.py` (idempotentne migracje) → `gunicorn app:app` (2 workery × 3 wątki,
   timeout 300 s). Health check: `GET /login` (Docker `HEALTHCHECK`), liveness `GET /health`.
4. Ręczne wdrożenie: Actions → „Deploy — demo (Coolify)” → *Run workflow*.

**Wycofanie:** w Coolify wybrać poprzedni udany deploy (lub `git revert` na `main` → automatyczny deploy).
Migracje są addytywne (`CREATE IF NOT EXISTS`, `add_column`), więc cofnięcie kodu nie wymaga cofania schematu.
Procedura w Coolify **(do potwierdzenia i przećwiczenia)**.

**Obraz:** `Dockerfile` (monolit, 7–8 min) lub `Dockerfile.slim` na obrazie bazowym `ghcr.io/<owner>/doccompare-ml-base`
budowanym przez `ml-base-image.yml` przy zmianie `requirements.txt`/`Dockerfile.base`.

## 3. Konfiguracja

Wymagane: `SECRET_KEY`, `DATABASE_URL` (lub `SQLITE_PATH`), `APP_BASE_URL` (po US-003 obowiązkowe w produkcji).
Opcjonalne: `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`, `RESEND_API_KEY`/`EMAIL_FROM`, klucze trackingu, `SENTRY_DSN`,
`REDIS_URL`, `ARTWORK_ENGINE_URL`, `INTAKE_TOKEN`, `INTEGRATION_API_KEY`, `DISABLE_QWEN=1` (hosty < 16 GB RAM),
`WEB_CONCURRENCY`, `THREADS_PER_WORKER`, `DB_POOL_SIZE`, `LOG_DIR`, `LOG_LEVEL`, `PROXY_COUNT`, `FORCE_HTTPS`.
Pełna lista z opisami: `.env.example`. Walidator startowy przerywa start produkcji przy niepewnym `SECRET_KEY`.

## 4. Backup i odtwarzanie

| Element | Jak | RPO / RTO |
|---|---|---|
| PostgreSQL | nocny `pg_dump -Fc` (`scripts/backup_db.sh`), rotacja 14 dziennych + 3 miesięczne (`scripts/rotate_backups.sh`), kopia offsite przez SSH | RPO ≤ 24 h; RTO ≤ 4 h **(do potwierdzenia)** |
| `/data` (wzorce artworków, `instance/.secret_key`) | tar w tym samym skrypcie | jw. |
| `uploads/` | nie jest kopiowany (pliki tymczasowe 24 h) | — |
| SQLite (dev/demo bez PG) | kopia dzienna z aplikacji, 7 sztuk (`app.py:540-586`) | — |

Próba odtworzenia: `docs/BACKUP_RESTORE.md` §4 — tylko lokalnie/dev; częstotliwość **(do potwierdzenia, propozycja: co kwartał)**.

## 5. Monitoring i logi

- Sentry (jeśli `SENTRY_DSN`): błędy z kontekstem użytkownika (nazwa, IP — patrz `RODO.md`).
- Logi: gunicorn na stdout/stderr (Coolify), plik rotowany w `LOG_DIR` (`app.py:76-94`), poziom `LOG_LEVEL`.
- Strony statusu: `/health` (publiczny, minimalny), `/api/admin/system-status` (admin: baza, narzędzia, klucze).
- Koszty AI: `/api-costs`, tabela `api_usage`, budżet `settings.budget_monthly_usd`.
- Alerty **(do zbudowania — NFR-022)**: wzrost 5xx, błąd backupu, przekroczenie budżetu AI.

## 6. Incydenty

| Sygnał | Pierwsze kroki |
|---|---|
| 5xx / brak odpowiedzi | sprawdzić logi kontenera w Coolify; `docker restart`; jeśli OOM → `DISABLE_QWEN=1`, `WEB_CONCURRENCY=2`; sprawdzić pulę DB (`DB_POOL_SIZE`) |
| Baza niedostępna | aplikacja celowo nie wylogowuje użytkowników (fail-open w `check_session_active`); sprawdzić PG w Coolify; odtworzyć z backupu wg `BACKUP_RESTORE.md` |
| Podejrzenie wycieku sekretu | **rotacja**: `SECRET_KEY` (wylogowuje wszystkich), `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`, `RESEND_API_KEY`, klucze trackingu i SMS (także w tabeli `settings` — do czasu US-002 jawnym tekstem), `INTAKE_TOKEN`, `INTEGRATION_API_KEY`, token biblioteki, `COOLIFY_TOKEN` w sekretach GitHub; przegląd `audit_log` i `/activity`; wpis w `RYZYKA.md` |
| Podejrzenie nieuprawnionego dostępu | dezaktywować konto (`is_active=0` — odcina sesję przy następnym żądaniu), przejrzeć `audit_log` po IP/nazwie, zabezpieczyć kopię logów |
| Naruszenie ochrony danych osobowych | zakres wg `KLASYFIKACJA_DANYCH.md`; ocena ryzyka dla osób; zgłoszenie do UODO w 72 h, jeśli wymagane — decyzja administratora danych (`RODO.md` §5) |
| Czerwony skan bezpieczeństwa na `main` | patrz `security.yml`: ustalenie → poprawka w `security/…` branch; wyjątek tylko z uzasadnieniem i datą w `RYZYKA.md` |

Kontakty dyżurne i eskalacja: **(do potwierdzenia przez PO)**.

## 7. Rutyny

| Co | Kiedy | Kto |
|---|---|---|
| Przegląd PR Dependabota | co tydzień | DEV/SEC |
| Przegląd rejestru ryzyk i wyjątków (`RYZYKA.md`) | co sprint; daty przeglądu wyjątków | SEC + PO |
| Skan obrazu (job `image` w `security.yml`) | 1. dnia miesiąca | SEC |
| Próba odtworzenia backupu | co kwartał **(do potwierdzenia)** | DEV |
| Przegląd kont i ról (`/admin`) | co kwartał | admin |
| Aktualizacja `CHANGELOG.md` i `APP_VERSION` | każde wydanie | DEV |

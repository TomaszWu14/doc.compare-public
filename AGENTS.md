# AGENTS.md

See `CLAUDE.md` for full project overview, architecture, conventions, and common commands.

## Cursor Cloud specific instructions

### Service overview

DocCompare v6 is a single monolithic Flask app (`app.py`). There is no separate frontend build step and no external services required for local dev (Dockerfiles exist for production/demo builds, but are not needed locally). SQLite is the default dev database (auto-created at `instance/doccompare.db`).

### Running the dev server

```bash
python3 app.py
```

The server starts on `http://localhost:5000` with debug mode enabled. The login form field for username is `identifier` (accepts username or email).

### Default test accounts

| Username | Password | Role |
|---|---|---|
| admin | random — printed to the console and written to `INITIAL_ADMIN_PASSWORD.txt` (gitignored) | admin |
| superuser | random, not shown — reset it as admin | superuser |
| jan.kowalski | random, not shown — reset it as admin | user |
| anna.nowak | random, not shown — reset it as admin | manager |

These are seeded automatically on first startup when no `admin` user exists.

### Database migrations

Run `python3 migrate_db.py` after code changes that alter the schema. This is idempotent and safe to re-run.

### System dependencies

The VM update script installs Python packages only. These system packages must be pre-installed (they are baked into the VM snapshot):

- `tesseract-ocr` + `tesseract-ocr-pol` (OCR fallback for scanned PDFs)
- `poppler-utils` (required by `pdf2image` for PDF-to-image conversion)
- `ghostscript` (improves Camelot PDF table parsing quality)

### Gotchas

- Tests: `python3 -m pytest tests/ -q` (pure-logic suite, heavy ML deps are skipped); lint: `ruff check .`. CI (`.github/workflows/ci.yml`) runs both plus `compileall`.
- The `python` command is not available; always use `python3`.
- The `.env` file must exist with at least `SECRET_KEY` and `SQLITE_PATH=instance/doccompare.db` set. Copy from `.env.example` if missing.
- `ANTHROPIC_API_KEY` is required for AI validation features but the app starts fine without it; AI-dependent routes will error at runtime.
- `RESEND_API_KEY` is optional (password-reset emails). `SENTRY_DSN` is optional (error tracking).
- Uploaded PDFs go to `uploads/` (auto-created, gitignored).

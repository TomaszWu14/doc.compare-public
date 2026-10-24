# DocCompare

[![ci](https://github.com/TomaszWu14/doc.compare-public/actions/workflows/ci.yml/badge.svg)](https://github.com/TomaszWu14/doc.compare-public/actions/workflows/ci.yml)
[![security](https://github.com/TomaszWu14/doc.compare-public/actions/workflows/security.yml/badge.svg)](https://github.com/TomaszWu14/doc.compare-public/actions/workflows/security.yml)

🇵🇱 [Polska wersja](README.md) · 🇬🇧 English

**Compares import documents (purchase order, proforma invoice, commercial invoice, packing list, customs
declaration) line by line and stops a delivery before a quantity or price mismatch reaches customs
clearance — built for purchasing and logistics teams.**

![PO vs proforma comparison result — the quantity difference is highlighted in red](docs/screenshots/porownanie-dokumentow.png)

**▶ See the demo: [https://doc.compare.twapp.pl](https://doc.compare.twapp.pl)** (on entry the demo asks for your first name, last name and company) — a running instance (synthetic data, no AI keys).
Login is restricted to the author (a read-only guest account exists in code but is disabled by default).
You can run it locally in a few minutes ([see below](#how-to-run)).

> **Portfolio project.** Company names are replaced with fictional ones (ACME); demo and test data are synthetic.
> The UI and most of the documentation are in Polish — the app was built for a Polish team.

## Problem → solution

A single import delivery means several documents from different parties, each with its own layout. The team
checked them by hand, and delivery status lived in Excel and e-mail, so a wrong quantity or price surfaced only
at customs clearance or settlement. DocCompare reads tables from PDFs, matches line items despite different
product-code spellings and compares them using tolerances from the supplier profile. The result lands on the
delivery card: a mismatch blocks the next step, and before clearance the app requires an approved document set.

## What it does

- **Document comparison** — PO ↔ PI, CI ↔ PL, customs declaration (SAD) checks, arithmetic validation
  (qty × price = net), payment-term equivalents, typo detection (`I/1`, `O/0`).
- **Delivery workflow** — a delivery card with a state machine and gates (a mismatch blocks "Next"),
  customs document checklist, demurrage & detention tracking.
- **External portals** — separate role-scoped portals for freight forwarders and customs agencies.
- **Artwork** — visual comparison of packaging PDFs with EAN/GS1 barcode validation.
- **Invoices → Excel**, supplier profiles, material master data, optional AI risk scoring.

## Documentation (Polish)

| Document | Contents |
|---|---|
| [01 — Problem & scope](docs/01-problem-i-zakres.md) | The process before the app, stakeholders and roles, what is in and out of scope. |
| [02 — Process](docs/02-proces.md) | AS-IS / TO-BE process with diagrams, decision points taken from the code, delivery state machine. |
| [03 — User flow](docs/03-user-flow.md) | Map of 75 screens and transitions, alternative paths and dead ends. |
| [04 — Data model](docs/04-model-danych.md) | ERD, entities, integrity rules and where the model does not enforce them. |
| [05 — Requirements](docs/05-wymagania.md) | Requirements with acceptance criteria, mapped to code and tests. |
| [06 — Decisions](docs/06-decyzje.md) | Log of 12 decisions: context, options considered, rationale, consequences. |
| [07 — Limitations](docs/07-ograniczenia.md) | What the app does not do, known issues, next steps. |

The repository is run like a three-person team (business analyst, developer, security) with a Product Owner:
story → threat model → ADR → PR with security review and BA acceptance → changelog. See
[`CONTRIBUTING.md`](CONTRIBUTING.md), [`docs/AUDYT.md`](docs/AUDYT.md) (opening audit),
[`docs/architektura/`](docs/architektura/) (C4, API, ADRs) and [`docs/bezpieczenstwo/`](docs/bezpieczenstwo/)
(threat model, risk register, GDPR, ASVS checklist).

## Security

Vulnerability reporting: [`SECURITY.md`](SECURITY.md). CI ([`security.yml`](.github/workflows/security.yml))
runs on every PR and push to `main`: gitleaks (secrets), Bandit and Semgrep OWASP Top 10 (SAST), pip-audit and
Trivy (dependencies), plus Dependabot. Actions are pinned to commit SHAs with least-privilege permissions.
The app sets security headers on every response (CSP, `nosniff`, `X-Frame-Options`, `Referrer-Policy`,
`Permissions-Policy`, COOP, HSTS behind HTTPS) — covered by `tests/test_security_headers.py`.

## How to run

The full `requirements.txt` installs the ML/OCR stack (PyTorch, DocTR…) — several GB. The tests and the core
comparison logic need only a light set, the same as CI (Python 3.11+):

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r dev-requirements.txt
pip install flask werkzeug pypdf reportlab pdfplumber rapidfuzz numpy "pandas>=2.0"

python -m pytest tests/ -q           # ~600 tests; those needing heavy deps are skipped
python migrate_db.py                 # database schema (SQLite in instance/)
python app.py                        # http://localhost:5000
```

Without a `.env` file the app starts on SQLite. On first start it creates the `admin`, `superuser`,
`jan.kowalski` and `anna.nowak` accounts with **random passwords**. The admin password is printed to the console
and written to `INITIAL_ADMIN_PASSWORD.txt` (gitignored); the admin sets the others. OCR, ML and AI validation
need the full `requirements.txt` and the keys listed in `.env.example`.

## Stack and why

| Component | Why |
|---|---|
| **Python + Flask** | An internal, document-centric tool: server-rendered pages, no separate front-end build. Modules are gradually extracted into blueprints. |
| **pdfplumber / PyMuPDF / Camelot + OCR (Mistral, RapidOCR, Tesseract)** | No single library handles every supplier layout, so extraction is a cascade: cheap methods first, OCR only for scans. |
| **rapidfuzz + TF-IDF** | Suppliers spell the same codes differently (`NL753-S-40` ≈ `NL753S40`); fuzzy matching instead of string equality. |
| **Deterministic rules + optional Claude API** | Rules and supplier tolerances decide compliance; AI only scores risk on the finished result and its suggestions wait for manager approval. The app works without an API key. |
| **SQLite (dev) / PostgreSQL (prod) via `db.py`** | One layer translates SQL dialects, so no database server is needed locally. |
| **Threads + RQ/Redis with fallback** | Heavy jobs (artwork batches, extraction) do not block the HTTP request; without Redis they run in threads. |
| **Docker + gunicorn** | The demo runs as a container on Coolify (Hetzner); after green CI on `main`, [`deploy.yml`](.github/workflows/deploy.yml) triggers a rebuild. |
| **Alpine.js, Tailwind, Chart.js** | Interactivity in Jinja templates without an SPA framework. |
| **pytest + GitHub Actions** | ~600 pure-logic tests run in CI in under a minute; heavy ML imports are lazy. |

## Scope and limitations

- **In scope:** PO/PI/CI/PL/SAD comparison, delivery card with gates, customs checklist, forwarder and customs
  agency portals, artwork comparison with EAN/GS1 validation, invoices → Excel, AI risk scoring.
- **Out of scope:** SAP integration (the PO PDF is the reference), automatic e-mail alerts, an ETD confirmation
  portal for suppliers.
- **Known issues and technical limits** (e.g. `app.py` is ~20k lines, heavy ML dependencies):
  [07 — Limitations](docs/07-ograniczenia.md).

## Where to start in the code

- [`enhanced_comparator.py`](enhanced_comparator.py) — splits tables into line items and compares them with tolerances.
- [`delivery_workflow.py`](delivery_workflow.py) — delivery card steps, statuses, SLA.
- [`pdf_extractor.py`](pdf_extractor.py) — the text and table extraction cascade.
- [`invoice_pipeline.py`](invoice_pipeline.py) — one invoice from supplier profile to saved line items.

Commit history was squashed when preparing the portfolio version (anonymisation).

## My contribution

I am the sole author: process analysis with the purchasing and logistics teams, data model, extraction cascade,
comparison engine, UI, tests and deployment. Scale: ~600 tests, ~410 Flask routes covering
purchasing → transport → customs → settlement.

---

License: all rights reserved, source available for review only — [`LICENSE`](LICENSE).
Notes for developers and AI agents: [`CLAUDE.md`](CLAUDE.md), [`AGENTS.md`](AGENTS.md).

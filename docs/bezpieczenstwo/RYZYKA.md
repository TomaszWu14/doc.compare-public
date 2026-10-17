# Rejestr ryzyk i wyjątków

> [SEC] Wersja 0.1 (2026-10-16). Ocena = wpływ (1–3) × prawdopodobieństwo (1–3). Decyzje o akceptacji ryzyka
> podejmuje PO i są tu zapisywane z datą. Przegląd rejestru: co sprint i przy każdym nowym ustaleniu HIGH.

## 1. Ryzyka

| ID | Ryzyko | Wpływ | Prawd. | Ocena | Dowód | Decyzja / plan | Właściciel | Przegląd |
|---|---|---|---|---|---|---|---|---|
| R-01 | Endpointy szablonów PalViz dostępne dla każdego zalogowanego (`require_role` jako bool) | 2 | 3 | **6 🟠** | `blueprints/palviz.py:236, 287` | **zamknięte** — PR #11 scalony 2026-10-17 (dekorator + 8 testów + strażnik statyczny) | DEV | 2026-10-17 |
| R-02 | Klucze API/SMS/Anthropic jawnym tekstem w `settings`, zapis przez managera, token SMSAPI w URL | 3 | 2 | **6 🟡** | `app.py:16005, 17167, 8526, 17234` | naprawa US-002 | DEV/SEC | 2026-11-30 |
| R-03 | Link resetu hasła z nagłówka Host przy braku `APP_BASE_URL` | 3 | 1 | 3 🟡 | `blueprints/auth.py:303`, `app.py:110` | naprawa US-003; do tego czasu `APP_BASE_URL` ustawione na demo (do sprawdzenia) | DEV | 2026-11-30 |
| R-04 | Raport artworku bez właściciela dostępny po identyfikatorze (fail-open) | 2 | 1 | 2 🟡 | `app.py:7590, 7671, 8097` | **zamknięte** — PR #11 scalony 2026-10-17 (reguła fail-closed w 6 miejscach + 19 testów) | DEV | 2026-10-17 |
| R-05 | CSP nie chroni przed XSS (`unsafe-inline`/`unsafe-eval`, 244 `innerHTML`, brak SRI) | 2 | 2 | 4 🟡 | `app.py:242-249`, `base.html` | US-025; wyjątek E-05 do tego czasu | DEV | 2026-12-31 |
| R-06 | 22 ciężkie endpointy bez limitu; budżet AI omijany przez część wywołań | 2 | 2 | 4 🟡 | `app.py:476-510`, `api_usage_tracker.py:111` | **naprawione w PR US-006** (limit na 19 trasach, koszt rejestrowany wszędzie); ryzyko szczątkowe: budżet nie blokuje odczytu dokumentów (Z-16) | DEV | po merge |
| R-07 | Łańcuch dostaw: brak pinów/locka, kontener root, obraz bez digestu | 2 | 2 | 4 🟡 | `requirements*.txt`, `Dockerfile*` | US-022; Dependabot od PR #11; wyjątki E-01, E-04 | DEV/SEC | 2026-11-30 |
| R-08 | Prompt injection przez treść PDF w uczeniu profili | 2 | 2 | 4 🟡 | `ai_learning.py:205-211` | **zmitygowane w PR #11** (sanityzacja + blok danych niezaufanych + reguła systemowa; nadal akceptacja managera); ryzyko szczątkowe: model może zignorować regułę — dlatego sugestie nigdy nie stosują się same | DEV | 2026-12-31 |
| R-09 | RODO: brak retencji, anonimizacji, eksportu; PII w `audit_log` po usunięciu konta; brak umów powierzenia w docs | 2 | 2 | 4 🟡 | `app.py:3885`, brak `DELETE` dla `audit_log` | US-007; decyzje Z-06, Z-07 | PO/SEC | 2026-11-30 |
| R-10 | Drobne wycieki: traceback PalViz, prefiks klucza, CSV bez escape, logout GET | 1 | 2 | 2 ⚪ | `palviz.py:126, 270`; `ai_validator.py:141`; `app.py:13489` | **naprawione**: PR #11 (US-027) + PR #22 (US-028, wylogowanie tylko POST z CSRF) | DEV | 2026-12-31 |
| R-11 | Obejścia bramek procesu (advance bez porównania, confirm-departure z `artwork_bledne`, set-status bez checklisty) — ryzyko biznesowe: dostawa z błędem przechodzi | 3 | 2 | **6 🟡** | `docs/07-ograniczenia.md` §3 | US-008/US-009; wymaga decyzji PO (Z-03) | PO/BA | po odpowiedzi PO |
| R-12 | Stan per proces przy 2 workerach (cache, limity, semafor, wątki przy imporcie) → niespójne limity, zdublowane pętle | 2 | 3 | 6 🟡 | `app.py:339, 443, 535, 585, 6282` | US-020 | DEV | 2026-12-31 |
| R-13 | Schemat w 3 źródłach → dryf SQLite/PG, ciche braki kolumn/CHECK | 2 | 2 | 4 🟡 | `docs/AUDYT.md` §3.6 | US-018 | DEV | 2026-12-31 |
| R-14 | Repo publiczne: przypadkowe ujawnienie danych produkcyjnych lub sekretów w PR | 3 | 1 | 3 🟡 | — | gitleaks pre-commit + CI, checklista PR, dane syntetyczne | wszyscy | ciągle |

## 2. Wyjątki (świadomie akceptowane do daty przeglądu)

| ID | Wyjątek | Gdzie zapisany | Uzasadnienie | Ryzyko | Przegląd | Akceptacja PO |
|---|---|---|---|---|---|---|
| E-01 | Kontener działa jako root (`DS002`/`AVD-DS-0002` ignorowane w Trivy) | `.trivyignore` | zmiana użytkownika wymaga testu uprawnień wolumenu `/data` (uploads, `instance/.secret_key`, migracje przy starcie) | R-07 | 2026-11-30 | do potwierdzenia (Z-13) |
| E-02 | `# nosec B310` w `tools/generate_voiceover.py:85` | kod | `urlopen` ze stałym adresem https API, bez wejścia użytkownika; narzędzie deweloperskie poza aplikacją | — | przy zmianie pliku | n/d |
| E-03 | Zapadka ruff: `F401,F841,F541,F601,F811` poza bramką blokującą | `ci.yml`, `pyproject.toml` | 90 ustaleń długu + celowe leniwe importy; pełna konfiguracja raportowana doradczo | — | 2026-11-30 | do potwierdzenia (Z-14) |
| E-04 | Skan obrazu Trivy doradczy (`--exit-code 0`), tylko miesięcznie | `security.yml` job `image` | obraz bazowy ML wymaga triage'u bazowych CVE przed blokadą; za ciężki na każdy PR | R-07 | 2026-11-30 | do potwierdzenia |
| E-05 | CSP z `unsafe-inline`/`unsafe-eval` | `app.py:242-249` | 15 tys. linii inline JS; przejście na nonce to osobna historyjka | R-05 | 2026-12-31 | do potwierdzenia |
| E-06 | `check_session_active` fail-open przy awarii bazy | `core/security.py:66-69` | świadoma decyzja: awaria bazy nie wylogowuje wszystkich; inne błędy fail-closed | — | przy zmianie | zapisane w kodzie |
| E-07 | Hasła pbkdf2:sha256 zamiast argon2/bcrypt | `blueprints/auth.py` | werkzeug domyślnie; migracja wymaga rehash przy logowaniu | — | 2026-12-31 | do decyzji PO |
| E-08 | Fałszywy alarm gitleaks `generic-api-key` w `tests/test_palviz_roles.py` (pole `sig_key` z syntetyczną sygnaturą szablonu) | `.gitleaksignore` (fingerprint commita `a96ec35`) | wartość nie jest sekretem; w kolejnym commicie zmieniona na mniej podobną do klucza | — | przy zmianie pliku | n/d |

## 3. Zamknięte

| ID | Ryzyko | Zamknięte | Dowód |
|---|---|---|---|
| — | Hardcoded `SECRET_KEY` w prod (czerwiec #4) | przed 2026-10 | `app.py:152-164, 309-330` |
| — | KPI bez filtra użytkownika (czerwiec #6) | przed 2026-10 | `app.py:3693-3756` |
| — | Bandit HIGH/MEDIUM w `tools/generate_voiceover.py` | PR #11 | adnotacje `usedforsecurity=False`, `# nosec B310` |

# Changelog

Format wg [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/), wersjonowanie wg [SemVer](https://semver.org/lang/pl/).
Wersja aplikacji: `constants.APP_VERSION`.

## [Unreleased]

### Added
- `docs/AUDYT.md` — audyt otwierający w trzech rolach (BA/DEV/SEC) ze stanu `ef950bb` (PR #11).
- Szkielet procesu zespołowego: `CONTRIBUTING.md` (role, proces, DoR/DoD, konwencje, bramki), `SECURITY.md`,
  szablony issue (`user_story`, `bug`, `security_issue`), szablon PR z checklistami BA/DEV/SEC, `CODEOWNERS`,
  `dependabot.yml`.
- Dokumentacja analityczna `docs/analiza/` (wizja, interesariusze, procesy, wymagania 0.1, historyjki, słownik,
  założenia, śledzenie), architektoniczna `docs/architektura/` (C4, ERD, API, ADR-0001), bezpieczeństwa
  `docs/bezpieczenstwo/` (klasyfikacja danych, threat model 0.1, rejestr ryzyk, RODO, checklista ASVS),
  `docs/testy/STRATEGIA_TESTOW.md`, `docs/operacje/RUNBOOK.md`.
- CI: lint ruff jako bramka „zapadkowa” + raport doradczy, raport pokrycia i lista pominiętych testów;
  skany bezpieczeństwa (bandit, pip-audit, gitleaks, trivy) na każdym PR i pushu do `main`, miesięczny skan obrazu.
- Pre-commit: gitleaks, kontrola końców linii, dużych plików, YAML i kluczy prywatnych.

### Changed
- `tests/conftest.py`: konto testowe `it_user` i fixture `user_client` (testy „brak dostępu” dla najniższej roli).
- `security.yml` uruchamia się także na PR i pushu do `main` (dotąd tylko co miesiąc); Python 3.11 jak w produkcji.

### Fixed

- CI: deploy demo do Coolify — przy odpowiedzi 405 na GET ponawia wywołanie metodą POST i loguje kod HTTP (deploy po merge #11 nie ruszył).

### Security
- **R-15:** obraz produkcyjny (Dockerfile → `requirements.txt`) miał pypdf 4.3.1 z 85 znanymi podatnościami
  i pillow 10.4.0; podniesione do pypdf ≥6.20.1 i pillow ≥12.3 (wersje, na których CI już testował).
  Pozostaje transformers 4.57.6 → US-029.
- **US-006 / R-06:** limit 30 wywołań / 60 s na użytkownika dla 19 kosztownych tras (Claude Vision, OCR skanów,
  render PDF i 3D, batch i porównania artworków, PalViz, podgląd tabeli dostawcy); odpowiedź 429 z `Retry-After`.
  Limiter przeniesiony do `core/rate_limit.py` (dekorator `heavy_rate_limit`, dostępny też dla blueprintów).
  Koszt zapisuje teraz każde wywołanie Claude (`table_extractor`, `scan_extractor`, komentarz raportu artworku,
  wykrywanie pól profilu), z użytkownikiem z sesji; komentarz AI w raporcie pomijany po przekroczeniu budżetu.
- **US-028 / R-10:** wylogowanie tylko metodą POST z tokenem CSRF (formularz zamiast linku w `base.html`,
  `home.html`, `spedycja.html`, `agencja.html`). `GET /logout` niczego nie zmienia: zalogowanemu pokazuje
  stronę z przyciskiem, niezalogowanego odsyła na login. Obca strona nie wyloguje już użytkownika.
- **US-026 / R-08:** treść dokumentów w promptach AI jest danymi — nowy `core/prompt_safety.py`
  (`sanitize`, `wrap_untrusted`, reguła w prompcie systemowym); `ai_learning` sanityzuje i opakowuje nagłówek PDF,
  komórki tabel, znaleziska i ocenę AI; `ai_validator` używa tej samej funkcji sanityzującej.
- **US-027 / R-10:** odpowiedzi 500 PalViz bez tracebacku i treści wyjątku (identyfikator błędu do logu);
  `/api/ai/status` i `check_api_key()` bez fragmentu klucza API; eksport CSV materiałów neutralizuje formuły
  (wspólny `export_engine.formula_safe`); podgląd szablonów PalViz tylko dla właściciela pliku lub superusera/admina.
- **US-004 / R-04:** dostęp do raportów i wyników porównań artworków po `cache_id` jest fail-closed —
  jedna reguła `_artwork_access_allowed()` (właściciel, raport publiczny, superuser/admin) w sześciu miejscach.
  Domknięte też luki bez żadnej kontroli: eksport ZIP batcha, zone-select, zone-compare; writer batcha ustawia właściciela.
- **US-001 / R-01:** endpointy kreatora szablonów wykrojników PalViz (`/api/artwork/templates/analyze`, `/save`)
  wymagają roli `manager`. Wcześniej `if not require_role(...)` nigdy nie sprawdzał roli, więc każdy zalogowany
  użytkownik mógł analizować i zapisywać szablony. Dodany strażnik w testach: `require_role()` tylko jako dekorator.
- `tools/generate_voiceover.py`: SHA1 oznaczony jako nie-kryptograficzny (`usedforsecurity=False`), stały adres
  https w `urlopen` opisany adnotacją Bandit — bramka SAST bez ustaleń ≥ MEDIUM.

## [6.0.0] — stan bazowy (2026-10-12, commit `ef950bb`)

Stan aplikacji przed wprowadzeniem CHANGELOG. Historia zmian: `git log`, dokumentacja analityczna `docs/01…07-*.md`.

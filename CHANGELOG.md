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

### Security
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

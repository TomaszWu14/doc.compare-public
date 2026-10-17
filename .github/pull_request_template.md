## Co i dlaczego

<1–3 zdania: co zmienia ten PR i jaki problem rozwiązuje>

- Historyjka: `US-xxx` (`docs/analiza/HISTORYJKI.md`) / wymaganie: `FR-/NFR-/SEC-xxx`
- Typ: feat / fix / security / docs / refactor / chore / ci
- ADR (jeśli decyzja istotna): `docs/architektura/adr/00xx-*.md`

## Jak przetestować

1.
2.

Zrzuty ekranu (jeśli UI):

## Checklista [DEV]

- [ ] małe commity w konwencji Conventional Commits z ID historyjki
- [ ] testy pokrywają każde kryterium akceptacji (w tym negatywne)
- [ ] `ruff check .`, `python -m pytest tests/ -q` lokalnie zielone
- [ ] model danych / API / ADR zaktualizowane przed kodem, jeśli dotyczy
- [ ] wpis w `CHANGELOG.md` (sekcja Unreleased)
- [ ] brak nowych `except: pass` bez logowania; brak nowego stanu per proces bez uzasadnienia

## Checklista [SEC]

- [ ] uwierzytelnianie i autoryzacja: każdy nowy endpoint ma `login_required`/`require_role`/`require_api_key`; test „rola bez dostępu → 403”
- [ ] CSRF: każdy sesyjny POST/PUT/DELETE/PATCH ma `csrf_protect`
- [ ] walidacja wejścia; SQL tylko parametryzowany przez `db.get_db()`
- [ ] wyjście escapowane (brak `|safe`, `innerHTML` tylko z `escHtml`)
- [ ] upload: `validate_pdf_upload`, limit rozmiaru, `secure_filename`, sprzątanie
- [ ] sekrety tylko w env; brak sekretów, PII i danych produkcyjnych w kodzie, testach, logach
- [ ] logi i `audit_log` dla operacji wrażliwych, bez haseł/tokenów
- [ ] nagłówki bezpieczeństwa nienaruszone (CSP, HSTS, nosniff)
- [ ] zależności: nowe pakiety uzasadnione, bez ustaleń pip-audit/trivy HIGH+
- [ ] AI/LLM: treść użytkownika jako dane (delimitowana, sanityzowana), koszt bramkowany budżetem
- [ ] RODO: nowe dane osobowe wpisane do `KLASYFIKACJA_DANYCH.md` i `RODO.md` z retencją
- [ ] threat model zaktualizowany, jeśli PR dodaje nowy przepływ danych

**Wynik przeglądu SEC:** ✅ bez uwag / ⚠️ uwagi (poniżej) / ❌ blokada — uzasadnienie:

## Checklista [BA]

- [ ] kryteria akceptacji sprawdzone punkt po punkcie
- [ ] komunikaty i UI zrozumiałe (PL, EN jeśli dotyczy portali)
- [ ] `docs/analiza/SLEDZENIE.md` zaktualizowane (wymaganie → historyjka → test → PR)

**Wynik odbioru BA:** ✅ / ⚠️ / ❌ — uwagi:

## Ryzyka i decyzje PO

- Ryzyka otwarte: `R-xx` / brak
- Potrzebna akceptacja PO: tak / nie — czego dotyczy:

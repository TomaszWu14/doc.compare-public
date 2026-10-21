# DocCompare

[![ci](https://github.com/TomaszWu14/doc.compare-public/actions/workflows/ci.yml/badge.svg)](https://github.com/TomaszWu14/doc.compare-public/actions/workflows/ci.yml)

🇵🇱 Polski · 🇬🇧 [English version](README.en.md)

**Porównuje dokumenty importowe (zamówienie, proformę, fakturę, listę pakową, zgłoszenie celne) linia po linii i zatrzymuje dostawę, zanim rozbieżność ilości lub ceny dotrze do odprawy — dla działów zakupów i logistyki.**

![Wynik porównania zamówienia z proformą — różnica ilości zaznaczona na czerwono](docs/screenshots/porownanie-dokumentow.png)

🎞️ GIF z działania: `<DO UZUPEŁNIENIA: docs/screenshots/demo.gif — nagram>`

📹 Prezentacja działania — 2 min: `<DO UZUPEŁNIENIA: link YouTube>`

🌐 Demo: **[doc.compare.twapp.pl](https://doc.compare.twapp.pl)** — działająca instancja (dane syntetyczne, bez kluczy AI). Logowanie tylko dla autora, bez konta gościa; przebieg pokazuje wideo. Lokalnie uruchomisz ją w kilka minut ([niżej](#jak-uruchomić)).

> **Projekt portfolio.** Nazwy firm są zastąpione fikcyjnymi (ACME), dane demo i testowe są syntetyczne.

## Problem → rozwiązanie

Jedna dostawa importowa to kilka dokumentów od różnych stron, każdy w innym układzie. Zespół
sprawdzał je ręcznie, a stan dostaw żył w Excelu i w mailach, więc błąd w ilości lub cenie wychodził
dopiero przy odprawie albo rozliczeniu. DocCompare czyta tabele z PDF, dopasowuje pozycje mimo różnych
zapisów kodów i porównuje je z tolerancjami z profilu dostawcy. Wynik trafia na kartę dostawy:
niezgodność blokuje kolejny krok, a przed odprawą aplikacja wymaga zatwierdzonego kompletu dokumentów.

## Dokumentacja analityczna

| Dokument | Co zawiera |
|---|---|
| [01 — Problem i zakres](docs/01-problem-i-zakres.md) | Jak proces wyglądał przed aplikacją, interesariusze i role, co jest w zakresie, a co poza nim. |
| [02 — Proces](docs/02-proces.md) | Proces PRZED i PO z diagramami, aktorzy, punkty decyzyjne z warunkami z kodu, maszyna stanów dostawy. |
| [03 — User flow](docs/03-user-flow.md) | Mapa 75 ekranów i przejść: diagramy per obszar, tabela ekranów, ścieżki alternatywne i ślepe zaułki. |
| [04 — Model danych](docs/04-model-danych.md) | ERD, opis encji, reguły integralności i miejsca, gdzie model nie trzyma ograniczeń. |
| [05 — Wymagania](docs/05-wymagania.md) | Wymagania z kryteriami akceptacji i wskazaniem, gdzie są zrealizowane i przetestowane. |
| [06 — Decyzje](docs/06-decyzje.md) | Dziennik 12 decyzji: kontekst, rozważane opcje, uzasadnienie, skutki. |
| [07 — Ograniczenia](docs/07-ograniczenia.md) | Czego aplikacja nie robi, funkcje opisane, ale niezaimplementowane, znane problemy, co dalej. |

Starsze dokumenty w `docs/` (runbook IT, backup, kolejkowanie, plan refaktoru) opisują stronę techniczną.
`PROCES_ZAKUPY_FLOW.md` i `PROCES_POTWIERDZENIE_ETD.md` to proces docelowy — stan obecny opisują 02 i 07.

## Jak prowadzony jest projekt (proces zespołowy)

Od 2026-10 repozytorium jest prowadzone jak przez trzyosobowy zespół: **[BA]** analityk biznesowy, **[DEV]** developer,
**[SEC]** bezpieczeństwo, z Product Ownerem decydującym o zakresie i ryzykach. Każda zmiana zostawia ślad:
historyjka → threat model → ADR → PR z przeglądem SEC i odbiorem BA → CHANGELOG. Proces, Definition of Ready/Done
i bramki CI: [`CONTRIBUTING.md`](CONTRIBUTING.md). Zgłaszanie podatności: [`SECURITY.md`](SECURITY.md).

| Obszar | Dokumenty |
|---|---|
| Audyt otwierający (BA/DEV/SEC) | [`docs/AUDYT.md`](docs/AUDYT.md) |
| Analiza [BA] | [`docs/analiza/`](docs/analiza/) — wizja, interesariusze, procesy, wymagania, historyjki (backlog), słownik, założenia, śledzenie |
| Architektura [DEV] | [`docs/architektura/`](docs/architektura/) — C4, model danych, API, ADR |
| Bezpieczeństwo [SEC] | [`docs/bezpieczenstwo/`](docs/bezpieczenstwo/) — klasyfikacja danych, threat model, rejestr ryzyk, RODO, checklista ASVS |
| Testy i operacje | [`docs/testy/STRATEGIA_TESTOW.md`](docs/testy/STRATEGIA_TESTOW.md), [`docs/operacje/RUNBOOK.md`](docs/operacje/RUNBOOK.md) |
| Historia zmian | [`CHANGELOG.md`](CHANGELOG.md) |

**Status (2026-10-16):** audyt zakończony; szkielet procesu i bramki CI (lint, testy z pokryciem, bandit, pip-audit,
gitleaks, trivy, Dependabot) wdrożone; backlog startowy z poprawkami bezpieczeństwa na czele czeka na decyzje PO
(`docs/analiza/ZALOZENIA.md`).

## Bezpieczeństwo

Zgłaszanie podatności: [`SECURITY.md`](SECURITY.md) (prywatnie, przez GitHub „Report a vulnerability”).
CI (`.github/workflows/security.yml`) na każdym PR i pushu do `main` pilnuje:

- **sekretów** — gitleaks (przypięta wersja + sha256; wyjątki w `.gitleaksignore` z uzasadnieniem),
- **SAST** — Bandit (ustalenia ≥ MEDIUM blokują) i Semgrep `p/owasp-top-ten` (na PR blokuje każde nowe ustalenie),
- **zależności** — pip-audit (`requirements-prod.txt`, `requirements.txt`, `dev-requirements.txt`) i Trivy `fs`
  (HIGH/CRITICAL z dostępną poprawką blokują; wyjątki w `.trivyignore`), Dependabot (pip, akcje GitHub, Docker),
- **higieny workflow** — `permissions: contents: read`, akcje przypięte do SHA.

Aplikacja ustawia nagłówki bezpieczeństwa na każdej odpowiedzi (CSP, `nosniff`, `X-Frame-Options`, `Referrer-Policy`,
`Permissions-Policy`, `Cross-Origin-Opener-Policy`, HSTS za HTTPS, `Cache-Control: no-store` dla JSON) —
test: `tests/test_security_headers.py`.

## Jak uruchomić

Pełne `requirements.txt` instaluje stos ML/OCR (PyTorch, DocTR…) — kilka GB. Do testów i głównej
logiki porównania wystarczy lekki zestaw, ten sam co w CI (Python 3.11+):

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install pytest python-dateutil dateparser babel flask werkzeug pydantic pypdf \
            reportlab pdfplumber rapidfuzz numpy "pandas>=2.0"

python -m pytest tests/ -q           # ~600 testów; te, które wymagają ciężkich zależności, są pomijane
python migrate_db.py                 # schemat bazy (SQLite w instance/) — bez tego część ekranów zwraca 500
python app.py                        # http://localhost:5000
```

Bez pliku `.env` aplikacja startuje na SQLite. Przy pierwszym starcie tworzy konta `admin`, `superuser`,
`jan.kowalski` i `anna.nowak` z **losowymi hasłami**. Hasło admina jest wypisywane w konsoli i zapisywane
w `INITIAL_ADMIN_PASSWORD.txt` (plik w `.gitignore`); hasła pozostałych kont ustawia admin.
Funkcje OCR, ML i walidacja AI wymagają pełnego `requirements.txt` oraz kluczy z `.env.example`.

## Stack i dlaczego taki

| Element | Dlaczego |
|---|---|
| **Python + Flask** | Narzędzie wewnętrzne oparte na dokumentach: strony renderowane po stronie serwera, bez osobnego builda front-endu. Moduły wydzielane stopniowo do blueprintów ([D-05](docs/06-decyzje.md)). |
| **pdfplumber / PyMuPDF / Camelot + OCR (Mistral, RapidOCR, Tesseract)** | Żadna pojedyncza biblioteka nie radzi sobie z układem każdego dostawcy, więc ekstrakcja to kaskada: tańsze metody najpierw, OCR tylko dla skanów ([D-03](docs/06-decyzje.md)). |
| **rapidfuzz + TF-IDF** | Dostawcy zapisują te same kody inaczej (`NL753-S-40` ≈ `NL753S40`); dopasowanie rozmyte zamiast porównania tekstów. |
| **Reguły deterministyczne + opcjonalnie API Claude** | O zgodności decydują reguły i tolerancje z profilu dostawcy; AI ocenia ryzyko na gotowym wyniku, a jej sugestie czekają na akceptację managera. Aplikacja działa bez klucza API ([D-01](docs/06-decyzje.md)). |
| **SQLite (dev) / PostgreSQL (prod) przez `db.py`** | Jedna warstwa tłumaczy dialekty SQL, więc lokalnie nie trzeba stawiać serwera bazy ([D-04](docs/06-decyzje.md)). |
| **Wątki + RQ/Redis z fallbackiem** | Ciężkie zadania (paczki artworków, ekstrakcja) nie blokują żądania HTTP; bez Redisa działają w wątkach ([D-06](docs/06-decyzje.md)). |
| **Docker + gunicorn** | Oryginał był wdrażany jako kontener na Coolify / Hetzner; ta kopia portfolio nie ma workflow wdrożenia. |
| **Alpine.js, Tailwind, Chart.js** | Interaktywność w szablonach Jinja bez frameworka SPA. |
| **pytest + GitHub Actions** | ~600 testów czystej logiki uruchamianych w CI w kilkadziesiąt sekund; ciężkie importy ML są leniwe ([D-11](docs/06-decyzje.md)). |

## Zakres i ograniczenia

- **W zakresie:** porównanie PO/PI/CI/PL/SAD, karta dostawy z bramkami, checklista celna, portale
  spedytora i agencji celnej, porównanie artworków z walidacją EAN/GS1, Faktury → Excel, ocena ryzyka AI.
- **Poza zakresem:** integracja z SAP (wzorcem jest PDF zamówienia), automatyczne alerty e-mail,
  portal potwierdzeń ETD dla dostawcy. Pełna lista z powodami: [01](docs/01-problem-i-zakres.md#5-poza-zakresem-nie-zaimplementowane).
- **Znane problemy** (np. przyjęcie magazynowe nie tworzy się automatycznie, ceny porównywane bez
  waluty) i ograniczenia techniczne (`app.py` ~20 tys. linii, ciężkie zależności ML):
  [07 — Ograniczenia](docs/07-ograniczenia.md).

## Kod — od czego zacząć

- [`enhanced_comparator.py`](enhanced_comparator.py) — rozbiór tabel na pozycje i porównanie z tolerancjami.
- [`delivery_workflow.py`](delivery_workflow.py) — kroki karty dostawy, statusy, SLA.
- [`pdf_extractor.py`](pdf_extractor.py) — kaskada ekstrakcji tekstu i tabel.
- [`invoice_pipeline.py`](invoice_pipeline.py) — jedna faktura od profilu dostawcy do zapisanych pozycji.

Historia commitów została spłaszczona przy przygotowaniu wersji portfolio (anonimizacja).

## Kontekst projektu

`<DO UZUPEŁNIENIA: w jakiej roli i dla kogo powstał projekt, okres, ilu użytkowników>`

**Mój wkład.** Jestem jedynym autorem: analiza procesu z działami zakupów i logistyki, model danych,
kaskada ekstrakcji, silnik porównania, interfejs, testy i wdrożenie. Skala: ~600 testów, ~410 tras
Flask obejmujących zakupy → transport → cło → rozliczenie.

---

Licencja: wszelkie prawa zastrzeżone, kod udostępniony do wglądu — [`LICENSE`](LICENSE).
Notatki dla deweloperów i agentów AI: [`CLAUDE.md`](CLAUDE.md), [`AGENTS.md`](AGENTS.md).

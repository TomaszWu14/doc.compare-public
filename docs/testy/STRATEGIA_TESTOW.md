# Strategia testów

> [DEV] Wersja 0.1 (2026-10-16). Stan bazowy: `docs/AUDYT.md` §3.5. Progi oznaczone **(do potwierdzenia)** — Z-08.

## 1. Stan bazowy (2026-10-15, Python 3.13, lekki zestaw zależności)

| Miara | Wartość |
|---|---|
| Pliki / funkcje testowe | 83 / 597 (607 przebiegów z parametryzacją) |
| Wynik | 607 passed, 12 skipped, ~11–18 s |
| Pominięcia | 12: brak `fitz` (PyMuPDF) 9, brak `trimesh` 3; `pytest.importorskip` występuje 136 razy |
| Pokrycie łączne | 35% (34 056 instrukcji) |
| Pokrycie wybranych modułów | `delivery_workflow.py` 96%, `blueprints/kolejka.py` 90%, `core/security.py` 84%, `blueprints/auth.py` 70%, `normalizer.py` 74%, `enhanced_comparator.py` 34%, `db.py` 31%, `app.py` 16%, `export_engine.py` 13% |
| Moduły bez testów | `export_engine`, `supplier_profiles`, `ai_learning`, `translation_en`, `alert_engine`, `scan_extractor`, `batch_processor`, `pdf_annotator`, `artwork_zone_comparator`, `yolo_detector`, `library_sync` |
| Wymagania bez testu | 25 z 52 (`docs/05-wymagania.md`, kolumna Test) |

## 2. Piramida

| Poziom | Co | Narzędzie | Kiedy |
|---|---|---|---|
| Jednostkowe | czysta logika: normalizacja, dopasowanie, komparator, kody kreskowe, workflow, demurrage, CN, UOM | pytest, bez ciężkich zależności ML | każdy PR (CI) |
| Integracyjne | trasy Flask przez `test_client` z prawdziwym logowaniem i CSRF (`tests/conftest.py`: `client`, `admin_client`, `manager_client`, `forwarder_client`), SQLite tymczasowy | pytest | każdy PR (CI) |
| Bezpieczeństwa | per endpoint: „rola bez dostępu → 403”, „bez CSRF → 403”, „rola zewnętrzna poza portalem → 403/redirect”, „cudzy obiekt → 403/404”; strażniki statyczne (np. zakaz `if not require_role`) | pytest | każdy PR; obowiązkowe dla nowych tras |
| Kontraktowe / dokumentacyjne | strażniki plików i runbooków (`test_hosting_docs.py`, `test_backup_*`) | pytest | każdy PR |
| E2E | 3 ścieżki krytyczne: (1) logowanie → porównanie PO↔PI → raport PDF, (2) dostawa: upload PI → weryfikacja → twarda bramka → nadpisanie z notatką, (3) spedytor widzi tylko swoje zlecenia | Playwright (Chromium jest w środowisku) — **do zbudowania** | przed wydaniem; nocnie |
| Ręczne / eksploracyjne | UX komunikatów, PDF/Excel wizualnie, demo | lista kontrolna w PR | odbiór BA |

Poza zakresem automatyzacji w CI: jakość OCR/ML (ciężkie zależności, niedeterminizm) — testy regresji na próbkach
syntetycznych uruchamiane ręcznie z pełnym `requirements.txt`.

## 3. Zasady

1. **Każde kryterium akceptacji ma test** (funkcjonalne i bezpieczeństwa). Nazwa lub docstring zawiera ID wymagania
   (`test_SEC005_templates_require_manager`), żeby `SLEDZENIE.md` dało się zbudować z kodu.
2. **Nowa trasa = trzy testy minimum:** happy path, rola bez dostępu (403), brak CSRF (403, jeśli sesyjna).
3. **Pokrycie: zapadka per moduł.** Raport w każdym PR (`--cov`), próg globalny na razie brak **(do potwierdzenia)**.
   Pokrycie modułów ≥ 80% (`delivery_workflow`, `core/security`, `blueprints/kolejka`) nie może spaść poniżej 80%;
   cel dla logiki domenowej 80% **(do potwierdzenia)**; `app.py` rośnie przez wydzielanie do blueprintów, nie przez
   testowanie monolitu wprost.
4. **Pominięcia są widoczne** (`-rs` w CI). Pominięty test to dług, nie sukces: US-024 dodaje `pymupdf` i `trimesh`
   do lekkiego zestawu.
5. **Dane testowe wyłącznie syntetyczne.** Żadnych realnych PDF, numerów PO, nazw dostawców, cen.
6. **Testy nie wyłączają kontroli.** Zakaz `@pytest.mark.skip` bez issue i daty; zakaz modyfikacji asercji „żeby
   przeszło” (DoD).
7. **Determinizm.** Brak zależności od sieci (klucze API puste w `conftest.py`), brak wątków w tle w testach po US-020.
8. **Flaky = błąd.** Niestabilny test naprawiamy albo kwarantannujemy z issue i terminem; nie ponawiamy w pętli.

## 4. Priorytety uzupełnień (US-023)

| Kolejność | Obszar | Wymagania | Dlaczego najpierw |
|---|---|---|---|
| 1 | Bramki steppera: tworzenie, przypinanie PO, blokada `advance`, notatka przy nadpisaniu, CAS statusu, ETD | FR-017, 018, 020, 021, 023, 026 | największy skutek biznesowy błędu; w kodzie są obejścia |
| 2 | Testy bezpieczeństwa Sprintu 1 | SEC-005, 009, 015, 016 | zamykają R-01…R-04 |
| 3 | Zatwierdzanie i eksport | FR-013, FR-014 (formula injection) | kontrola i artefakt dla audytu |
| 4 | Portal agencji i dział | FR-038, FR-039 | izolacja danych |
| 5 | `export_engine`, `supplier_profiles` (moduły bez testów) | FR-006, FR-010, FR-014 | tolerancje i raporty decydują o wyniku |

## 5. Jak uruchomić

```bash
pip install -r dev-requirements.txt pytest-cov flask werkzeug pypdf reportlab pdfplumber rapidfuzz numpy "pandas>=2.0"
python -m pytest tests/ -q -rs --cov=. --cov-report=term-missing:skip-covered
python -m pytest tests/test_delivery_workflow.py -q          # jeden moduł
python -m pytest -k "SEC005" -q                              # po ID wymagania
```

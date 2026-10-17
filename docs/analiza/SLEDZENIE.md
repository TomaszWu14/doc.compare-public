# Macierz śledzenia: wymaganie → historyjka → test → PR

> [BA] Wersja 0.1. Dla FR-001…039 i NFR-001…013 mapowanie wymaganie → kod → test jest w `docs/05-wymagania.md`
> (kolumny „Gdzie zrealizowane” i „Test”). Tu prowadzimy ślad pracy zespołowej od PR #11 wzwyż.
> Konwencja nazw testów: `test_<ID wymagania>_<opis>` lub docstring z ID (np. `SEC-005`).

| Wymaganie | Historyjka | Test (plik::funkcja) | PR | Status |
|---|---|---|---|---|
| SEC-013, NFR-013 | US-005, US-017 | `.github/workflows/ci.yml`, `security.yml` (sam CI) | #11 | w przeglądzie |
| — (proces) | US-016 | `tests/test_hosting_docs.py` (istniejący strażnik dokumentów) — do rozszerzenia o `CONTRIBUTING.md`/`SECURITY.md` | #11 | w przeglądzie |
| SEC-005 | US-001 | `tests/test_palviz_roles.py` — 8 testów: user/forwarder → 403 bez zapisu, anonim → login, manager → 200/400, brak CSRF → 403, strażnik `test_SEC005_require_role_only_used_as_decorator` | #11 | w przeglądzie (odbiór BA ✅, SEC ✅) |
| SEC-009 | US-002 | planowany `tests/test_settings_encryption.py` | — | do realizacji |
| SEC-015 | US-003 | planowany `tests/test_auth_blueprint.py::test_SEC015_reset_link_uses_app_base_url` | — | do realizacji |
| SEC-016 | US-004 | `tests/test_artwork_report_access.py` — 19 testów: reguła (8 przypadków), builder, strona raportu, ZIP batcha, podgląd stron, zone-select, zone-compare, writer batcha, strażnik wzorca fail-open | #11 | w przeglądzie (odbiór BA ✅, SEC ✅) |
| SEC-017, NFR-009 | US-006 | planowany `tests/test_rate_limit_heavy.py` | — | do realizacji |
| SEC-011, NFR-018 | US-007 | planowany `tests/test_retention.py` | — | decyzja PO (Z-06) |
| FR-041 | US-008 | istniejący `tests/test_delivery_workflow.py` + nowy test hooków | — | decyzja PO |
| FR-040 | US-009 | `tests/test_api_dostawa_advance_customs_gate.py` (częściowo) + nowe | — | decyzja PO |
| FR-042 | US-010 | `tests/test_forwarding_order.py` (dziś sprawdza 409) | — | decyzja PO |
| FR-006, FR-012 | US-011 | `tests/test_business_logic.py` + nowy test waluty na pozycji | — | częściowo decyzja PO |
| SEC-008 | US-025 | `tests/test_integration.py` (nagłówki) — do rozszerzenia o CSP bez `unsafe-inline` | — | do realizacji |
| SEC-012 | US-026 | `tests/test_prompt_safety.py` — 11 testów: sanityzacja, blok danych niezaufanych, reguła systemowa, prompty `learn_from_document` i `learn_from_comparison`, wspólna funkcja w obu modułach | #11 | w przeglądzie (odbiór BA ✅, SEC ✅) |
| SEC-010 | US-027 | `tests/test_info_leaks.py` — 8 testów: 500 PalViz bez tracebacku (analyze, generate), brak fragmentu klucza (status, check), CSV bez formuł, helper `formula_safe`, podgląd szablonu własny/cudzy | #11 | w przeglądzie (odbiór BA ✅, SEC ✅) |
| SEC-010 | US-028 | planowany test: GET `/logout` nie wylogowuje, POST bez CSRF → 403 | — | do realizacji |
| NFR-024 | US-018 | `tests/test_backup_scripts.py`? nie — nowy test porównujący schematy SQLite/PG | — | do realizacji |
| NFR-013 | US-019 | zacieśnienie zapadki w `ci.yml` | — | do realizacji |
| NFR-025 | US-020 | planowany test startu bez wątków (`APP_BACKGROUND_THREADS=0`) | — | do realizacji |
| SEC-014 | US-022 | `security.yml` job `image` z `--exit-code 1` | — | do realizacji |
| FR-017…026, FR-013/014 | US-023 | nowe testy per wymaganie | — | do realizacji |

Wymagania bez historyjki (stan ✅ w `WYMAGANIA.md`, bez planowanych zmian) nie mają wiersza — dopóki nie powstanie zmiana lub regresja.

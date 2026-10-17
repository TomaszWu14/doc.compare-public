# API — konwencje i mapa

> [DEV] Wersja 0.1. Pełna lista ekranów i przejść: `docs/03-user-flow.md`. Liczby tras: `docs/AUDYT.md` §3.1.

## 1. Konwencje

| Aspekt | Zasada | Gdzie |
|---|---|---|
| Uwierzytelnianie przeglądarkowe | sesja Flask po `POST /login` (pole `identifier` = login lub e-mail) | `blueprints/auth.py` |
| Autoryzacja | `@login_required`, `@require_role("manager")` (lub `"superuser"`, `"admin"`); role zewnętrzne (`forwarder`, `customs_agent`) mają poziom 0 i są zamknięte prefiksami `/spedycja`, `/agencja` | `core/security.py`, `constants.py:150-168` |
| CSRF | każdy sesyjny `POST/PUT/DELETE/PATCH` z `@csrf_protect`: pole formularza `_csrf_token` lub nagłówek `X-CSRF-Token` (w szablonach `csrf_token()`) | `core/security.py:136-173` |
| API maszynowe | `X-Api-Key` = `INTEGRATION_API_KEY` (`/api/v1/*`), `Authorization: Bearer INTAKE_TOKEN` (`/api/intake/artwork`), token biblioteki (`/api/library/sync`, `needed-masters`, `search`) — porównania stałoczasowe, 503 gdy token nieskonfigurowany | `core/security.py:113-130`, `app.py:9917, 13758` |
| Format błędów | JSON `{"error": "<komunikat PL>"}`; kody: 400 walidacja, 401 brak/zły token, 403 brak uprawnień lub CSRF, 404, 409 konflikt stanu (`blocked`, `needs_confirm`, `need_note`), 413 za duży plik, 429 limit, 503 integracja wyłączona | `app.py:13701-13740` |
| Limity | logowanie 5/15 min/IP; reset hasła 3/15 min/IP i 3/15 min/konto; `/api/compare` i 11 innych ciężkich tras 30/60 s/użytkownika (US-006 rozszerza) | `constants.py`, `app.py:476-510` |
| Upload | tylko PDF (`validate_pdf_upload`), 200 MB, ZIP w batchu: 20 plików po ≤ 100 MB | `pdf_validation.py`, `constants.py` |
| Język | komunikaty PL; `lang=en` podmienia frazy w HTML (`translation_en.py`), odpowiedzi JSON pozostają PL (NFR-021) | `app.py:1513` |
| Wersjonowanie | brak wersji w ścieżkach poza `/api/v1/invoices`; zmiany łamiące opisujemy w `CHANGELOG.md` i ADR | — |

## 2. Mapa tras (408)

| Prefiks | Liczba | Obszar | Główne operacje |
|---|---|---|---|
| `/api/artwork`, `/artwork`, `/api/library`, `/library` | 118 | artwork, biblioteka wzorców | porównanie, raporty, batch, strefy, 3D, indeks, aliasy, materiały, profile pól, intake |
| `/api/compare`, `/api/comparison`, `/analyze`, `/history`, `/api/export`, `/api/templates`, `/api/doc-types`, `/api/products`, `/sad` | ~114 | porównania | porównanie, zatwierdzanie, komentarze, eksport PDF/Excel, szablony, typy dokumentów |
| `/dostawy`, `/api/dostawy` | 24 + strony | stepper dostawy | tworzenie, upload do slotów, `advance`/`revert`/`set-status`, weryfikacja PO↔PI i artworku, `confirm-departure`, stempel, zlecenie spedycyjne, zestaw celny |
| `/api/transport`, `/api/shipments`, `/api/transport-orders`, `/transport/*`, `/tracking`, `/warehouse`, `/calendar`, `/checklists` | ~67 | transport | kolejka, kontenery, tracking, demurrage, awizacja SMS, przyjęcia magazynowe |
| `/spedycja`, `/api/spedycja`, `/agencja`, `/api/agencja` | 4 | portale zewnętrzne | lista zleceń firmy, agent celny, `customs_status` |
| `/invoices/*`, `/api/v1/invoices` | 13 | Faktury → Excel / Draft SAD | upload, przegląd, potwierdzenie, eksport |
| `/api/ai/*`, `/api-costs` | 11 | AI | status, uczenie, oczekujące sugestie, zastosowanie (manager), koszty |
| `/admin`, `/api/admin`, `/api/users`, `/settings/*`, `/api/webhooks`, `/tickets`, `/kpi`, `/data`, `/api/materials` | ~40 | administracja i dane | użytkownicy, role, klucze integracji, webhooki, backup, status systemu, master data |
| `/login`, `/logout`, `/forgot-password`, `/reset-password`, `/set-language`, `/health`, `/` | 7 | publiczne / auth | — |

## 3. Zdarzenia wychodzące

| Kanał | Zdarzenie | Zabezpieczenie |
|---|---|---|
| Webhook HTTP POST | `comparison.completed` (payload JSON, nagłówek z sekretem webhooka) | tylko admin konfiguruje; blokada adresów prywatnych (`_is_ssrf_blocked_url`); luki: przekierowania, DNS rebinding (THREAT_MODEL F-6) |
| E-mail (Resend/SMTP) | reset hasła, PO do dostawcy, alerty managerów, alert demurrage `red` | brak treści dokumentów w mailach — do potwierdzenia |
| SMS | awizacja kierowcy z linkiem tokenowym | token `secrets.token_urlsafe(24)`, wygasa ze statusem |

## 4. Zasady zmian API

1. Nowa trasa = dekoratory auth/CSRF + test „rola bez dostępu → 403” + wiersz w tej mapie, jeśli otwiera nowy prefiks.
2. Zmiana kontraktu `/api/v1/*` lub webhooków = ADR + wpis w `CHANGELOG.md` + okres przejściowy.
3. Każdy endpoint przyjmujący plik przechodzi przez `validate_pdf_upload` i limit rozmiaru.

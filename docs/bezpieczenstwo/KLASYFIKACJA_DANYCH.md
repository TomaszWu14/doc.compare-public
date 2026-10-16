# Klasyfikacja danych

> [SEC] Wersja 0.1 (2026-10-16). Źródła: `docs/AUDYT.md` §4.4, `migrate_db.py`, `app.py`. Retencje „propozycja” wymagają potwierdzenia PO (Z-06).

## 1. Klasy

| Klasa | Definicja | Zasady postępowania |
|---|---|---|
| **Publiczne** | mogą być widoczne dla każdego | dokumentacja repo, dane syntetyczne demo |
| **Wewnętrzne** | dla pracowników ACME; ujawnienie niewygodne, nie szkodliwe | statusy dostaw, KPI, konfiguracja SLA, słowniki; dostęp po zalogowaniu |
| **Poufne** | ujawnienie szkodzi ACME lub kontrahentom | ceny, warunki płatności, profile dostawców z tolerancjami, master data, artworki wzorcowe, treść dokumentów handlowych; podział per dział; nie wysyłać do podmiotów trzecich poza listą w `RODO.md` §5; nie w logach |
| **Dane osobowe** | identyfikują osobę fizyczną | zbierane minimalnie, retencja określona, dostęp per rola, wpis w `RODO.md`, pseudonimizacja po usunięciu konta |
| **Sekrety** | klucze, tokeny, hasła | tylko env lub zaszyfrowane w bazie (US-002), nigdy w repo/logach/URL, rotacja wg runbooka |

## 2. Inwentarz

| Dane | Gdzie | Klasa | Kto ma dostęp | Wychodzi do | Retencja dziś → propozycja |
|---|---|---|---|---|---|
| Login, e-mail, rola, dział, ostatnie logowanie | `users` | osobowe | admin (zarządzanie), sam użytkownik | Sentry (`username`, IP) | bezterminowo → do usunięcia konta + pseudonimizacja |
| Hash hasła (pbkdf2:sha256) | `users.password_hash` | sekret | nikt (tylko weryfikacja) | — | jak konto |
| Tokeny resetu hasła | `password_reset_tokens` | sekret | — | link w e-mailu (Resend) | 24 h ważności, oznaczane jako użyte → usuwać po 30 dniach |
| Zdarzenia audytu: login, IP, akcja, szczegóły | `audit_log` | osobowe (IP, nazwa) + wewnętrzne | admin (`/activity`) | — | bezterminowo → 12 miesięcy |
| Imię i telefon kierowcy | `drivers`, `driver_notifications` | osobowe | manager | dostawca SMS | bezterminowo → 12 miesięcy od awizacji |
| E-maile i telefony spedytorów, agentów, kontakty dostawców | `freight_forwarders`, `customs_agencies`, `zlecenia_transportowe`, `suppliers` | osobowe (dane służbowe) | manager+ | e-mail (Resend/SMTP) | bezterminowo → do zakończenia współpracy |
| Treść dokumentów handlowych (PDF PO/PI/CI/PL/SAD) | `uploads/` lub `/data/uploads`, `shipment_documents`, sloty dostawy | poufne | user/manager swojego działu | Anthropic (walidacja, Vision), Mistral (OCR) | pliki tymczasowe 24 h; dokumenty dostawy bezterminowo → wg wymogów celnych (do potwierdzenia, zwykle 5 lat) |
| Wynik porównania (pozycje, ceny, różnice) | `comparisons.result_json` | poufne | autor, superuser+ , manager (zatwierdzanie) | Anthropic (ocena ryzyka), webhooki odbiorców | bezterminowo (soft delete) → do decyzji |
| Profile dostawców, tolerancje, warunki płatności | `suppliers`, `settings`, `supplier_profiles.py` | poufne | manager+ | Anthropic (uczenie: nagłówek i wiersze tabeli) | bezterminowo |
| Master data materiałów (REF, EAN, CN, opakowania) | `material_master`, `artwork_material` | poufne | user+ (odczyt), manager (edycja), admin (eksport CSV) | — | bezterminowo |
| Artworki wzorcowe i fabryczne, raporty | `/data`, cache raportów, `artwork_batch_jobs` | poufne | zalogowani wewnętrzni (własność raportu — R-04) | Anthropic/Mistral (OCR fragmentów) | cache 2 h; batch z `expires_at` |
| Statusy dostaw, kontenery, ETD/ETA, SLA | `kolejka_*`, `transport_queue`, `shipments` | wewnętrzne | wg roli i działu; spedytor/agencja tylko swoje | API trackingu (numer kontenera) | bezterminowo |
| Klucze API trackingu, SMS, Anthropic (z UI) | `settings` (jawny tekst) | sekret | manager+ (zapis!), proces | — | → zaszyfrowane, zapis tylko admin (US-002) |
| `SECRET_KEY`, `DATABASE_URL`, `INTAKE_TOKEN`, `INTEGRATION_API_KEY`, token biblioteki | env / `instance/.secret_key` | sekret | operator hostingu | — | rotacja wg runbooka |
| Koszty AI (tokeny, model, użytkownik) | `api_usage` | wewnętrzne | admin, manager | — | bezterminowo → 24 miesiące |
| Kopie zapasowe bazy i `/data` | VPS + offsite | poufne + osobowe | operator | — | 14 dziennych + 3 miesięczne (`BACKUP_RESTORE.md`) |

## 3. Przepływy poza ACME

| Odbiorca | Dane | Cel | Podstawa / umowa | Uwaga |
|---|---|---|---|---|
| Anthropic (Claude API) | treść dokumentów, wyniki porównań, nagłówki PDF, obrazy stron | ocena ryzyka, uczenie profili, Vision OCR | do potwierdzenia (umowa powierzenia, lokalizacja przetwarzania) | minimalizacja: bez danych osobowych w promptach (US-026); budżet |
| Mistral | obrazy stron PDF | OCR | do potwierdzenia | jw. |
| Resend / SMTP | adresy e-mail, treść powiadomień | reset hasła, alerty, PO do dostawcy | do potwierdzenia | bez załączników z dokumentami — do potwierdzenia |
| SafeCube, 17track, ShipsGo | numery kontenerów | tracking | do potwierdzenia | bez danych osobowych |
| textbelt, smsapi, twilio | telefon kierowcy, treść SMS | awizacja | do potwierdzenia | token w URL (R-02) |
| Sentry | nazwa użytkownika, IP, ślad błędu | monitoring | do potwierdzenia | rozważyć `send_default_pii=False` i bez IP |
| Odbiorcy webhooków | payload `comparison.completed` | integracje ACME | wewnętrzne | konfiguruje tylko admin |
| GitHub (repo publiczne) | kod, dokumentacja, dane syntetyczne | portfolio | — | zero danych produkcyjnych (gitleaks, przegląd PR) |

## 4. Zasady dla zespołu

1. Nowa tabela lub pole z danymi osobowymi → wiersz w sekcji 2 i w `RODO.md` przed merge (checklista PR).
2. Dane poufne nie trafiają do logów, komunikatów błędów ani tytułów issues/PR (repo publiczne).
3. Testy i dane demo wyłącznie syntetyczne (`README.md`: „dane demo i testowe są syntetyczne”).
4. Eksporty (PDF/Excel/CSV) dziedziczą klasę danych źródłowych; CSV z escape formuł (US-027).

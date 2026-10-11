# 05. Wymagania

Wymagania odtworzone z kodu (stan gałęzi `portfolio-cleanup`). Lista zawiera **tylko zachowanie,
które jest zaimplementowane**. Wartości progów pochodzą z kodu. Rzeczy opisane w innych dokumentach,
ale niezrealizowane, są w sekcji „Poza zakresem”.

Oznaczenia:
- **WF** – wymaganie funkcjonalne, **WN** – wymaganie niefunkcjonalne.
- Kolumna **Test**: plik w `tests/`, który automatycznie sprawdza dane zachowanie, albo `—`, gdy
  brak testu. „(częściowo)” = test sprawdza funkcję pomocniczą, a nie całą regułę.
- Statusy pozycji porównania: `ok`, `format` (różnica formatu/zaokrąglenia), `watpliwe`, `roznica`.
  Waga ustalenia (finding): `info`, `warning`, `error`.

## 1. Wymagania funkcjonalne

### 1.1 Porównanie dokumentów

| ID | Wymaganie | Kryterium akceptacji | Gdzie zrealizowane | Test |
|---|---|---|---|---|
| WF-01 | Użytkownik porównuje dwa dokumenty handlowe (PO, PI, CI, PL, SAD, BL, WZ, FV, CMR, artwork) i dostaje zapisany wynik. | Given zalogowany użytkownik, When wysyła `POST /api/compare` z `file_a` i `file_b`, Then powstaje rekord w `comparisons` z `result_json`, `status` i `diff_count`. | `app.py:2790-2800` (`api_compare`), `enhanced_comparator.compare_enhanced` | — |
| WF-02 | System nie liczy ponownie tego samego porównania. | Given użytkownik już porównał pliki A i B, When wgra te same pliki (ten sam SHA-256, ta sama kolejność), Then odpowiedź 200 z `duplicate: true` i `existing_id`, bez nowego rekordu. | `app.py:2828-2848` | — |
| WF-03 | Liczby w formatach EN i UE są rozpoznawane jednakowo. | `13,500.00` i `13.500,00` dają tę samą wartość 13500,00; `1.234` → 1234; ciąg dłuższy niż 50 znaków albo zakres cen (`1,2-3,4`) → brak wartości (`None`). | `normalizer.py:46-106` | `test_normalizer.py`, `test_business_logic.py` |
| WF-04 | Pozycje z dokumentów A i B są dopasowywane mimo różnych zapisów kodu (REF). | Dopasowanie przy podobieństwie REF ≥ 82 albo podobieństwie opisu ≥ 0,50 (np. `NL753-S-40` ≈ `NL753S40`). Pozycja bez pary w drugim dokumencie → finding `error`. | `enhanced_comparator.py:707-755`, `semantic_matcher.py` | `test_semantic_matcher.py` (częściowo) |
| WF-05 | Ilość musi być zgodna co do sztuki. | Given pozycja z ilością 100 w A i 99 w B (ta sama JM), Then status pozycji `roznica` i finding `error` „Rozbieżność ilości”. Tolerancja ilości = 0%. | `enhanced_comparator.py:788-798`, `constants.py:117-118` | — |
| WF-06 | Cena jest porównywana z tolerancją z profilu dostawcy. | Given profil dostawcy z `price_tolerance_pct = 1,0`, When cena A = 100,00, B = 100,80 (Δ 0,8%), Then ceny uznane za zgodne. Tolerancja jest przycinana do 0–100. Bez profilu tolerancja = 0%. | `enhanced_comparator.py:691-694`, `846`; `normalizer.numbers_equal` | `test_business_logic.py` (częściowo: `numbers_equal`) |
| WF-07 | Różnica ceny poza tolerancją jest klasyfikowana według wielkości. | Przy różnym net: Δ < 0,5% albo różnica tylko z zaokrąglenia do `po_rounding` (domyślnie 2 miejsca) → `format`; 0,5% ≤ Δ < 2% → `watpliwe` + `warning`; Δ ≥ 2% → `roznica` + `error`. Gdy net zgodny co do grosza → `format`. | `enhanced_comparator.py:860-893` | — |
| WF-08 | Różne jednostki miary są przeliczane przed porównaniem. | Przelicznik szukany najpierw dla danego REF, potem globalny (`*`); kierunek odwrotny = 1/factor. Gdy brak przelicznika i JM różne → `watpliwe` + `warning` „Różna jednostka miary”. | `uom.py:96-114`, `enhanced_comparator.py:800-845` | `test_uom.py` |
| WF-09 | Arytmetyka i suma dokumentu B są weryfikowane. | Given B typu PI, CI, CI_SET lub FV, When `qty × price` różni się od `net` o > 2% (np. 10 × 5,00 = 50,00 vs net 52,00), Then finding `warning` „arytmetyka”. Dla B = PO brak sprawdzenia; pozycje z wartością ≤ 0 pomijane. Suma pozycji vs suma dokumentu: tolerancja max(0,1%, tolerancja dostawcy), ostrzeżenie, gdy Δ > max(0,5%, tolerancja). | `enhanced_comparator.py:950-978`, `1660-1669`; `normalizer.validate_checksum` | `test_arithmetic_validation.py`, `test_business_logic.py` |
| WF-10 | Warunki płatności są porównywane semantycznie. | Kod SAP i tekst uznane za równoważne według `SAP_PAYMENT_MAP` (np. `IW04` = „30 days after shipment”). Rozbieżność: `error`, gdy zaliczkę wymaga tylko jedna strona albo różnica dni > 30 (np. 30 vs 90 dni); w pozostałych przypadkach `warning` (np. 30 vs 45 dni). | `enhanced_comparator.py:40-63`, `1103-1134` | `test_business_logic.py`, `test_payment_reverse.py` (równoważność; waga – brak testu) |
| WF-11 | System wykrywa pomyłki znaków I/1 i O/0. | `check_i_vs_1("INV1", "INVI")` zwraca opis z pozycją 4. Brakujący REF w B, który różni się tylko zamianą I↔1/O↔0, daje finding `error` kategorii `I_vs_1`. | `typo_detector.py:55-88`, `298-335` | `test_typo_detector.py`, `test_typo_learned.py` |
| WF-12 | Porównanie ma jeden poziom ryzyka. | `diff_count > 0` → `blad`; inaczej `warn_count > 0` → `ostrzezenie`; inaczej `format_count > 0` → `format`; inaczej `ok`. | `enhanced_comparator.py:199-203` | — |
| WF-13 | Manager zatwierdza lub odrzuca wynik porównania. | Given rola ≥ manager, When `POST /api/comparison/<id>/approve` ze `status` ∈ {approved, rejected, pending}, Then zapis `approval_status`, `approved_by`, `approved_at`, notatki (≤ 500 znaków). Inna wartość → 400; usunięte porównanie → 404. | `app.py:3520-3545` | — |
| WF-14 | Wynik porównania można wyeksportować do PDF i Excel. | `GET /api/export/pdf/<id>` i `/api/export/excel/<id>` zwracają plik. Użytkownik poniżej superusera, który nie jest autorem → 403. W Excelu komórki zaczynające się od `=`, `+`, `-`, `@` dostają prefiks `'`. | `app.py:5765-5813`, `export_engine.py:122-128`, `172`, `726` | — |
| WF-15 | Audyt kodu CN w porównaniu z SAD. | When jeden z dokumentów to SAD, Then kod CN pozycji porównywany z `material_master.tariff_cn`: zgodny przy równości albo wspólnym prefiksie ≥ 8 cyfr; inny kod → `blad` (`error`); brak kodu w SAD lub w kartotece → `uwaga` (`warning`). | `enhanced_comparator.py:1647-1650`, `cn_audit.py:122-155` | `test_cn_audit.py`, `test_enhanced_cn_reference.py` |
| WF-16 | Format kodu CN jest walidowany. | Dozwolone długości 6/8/10 cyfr; litery → błąd; dział `00` → błąd; dział `77` → uwaga; działy `98`/`99` → uwaga. | `cn_audit.py:157-198` | `test_cn_audit.py` |

### 1.2 Proces dostawy (stepper)

| ID | Wymaganie | Kryterium akceptacji | Gdzie zrealizowane | Test |
|---|---|---|---|---|
| WF-17 | Manager zakłada dostawę dla numeru PO. | Numer musi pasować do `^[45]\d{8,10}$` (inaczej 400); istniejący numer → 409. Nowa dostawa ma status `utworzone` i checklistę 6 dokumentów (PO, PI, CI, PL, SAD, BL) ze statusem `brak`. | `app.py:18566-18615`, `17528-17543` | — |
| WF-18 | Dokument z innym numerem PO nie jest przypinany do dostawy. | Given dostawa 4500000001, When wgrany PDF (PO/PI/CI/PL/SAD) zawiera wyraźny numer PO różny od 4500000001, Then 409 i plik usunięty. Brak numeru w pliku → plik przyjęty. | `app.py:18374-18386` | — |
| WF-19 | Wynik porównania PO↔PI ustawia status dostawy. | `error`/`critical`/`roznica`/`blad` → `sprawdzone_niezgodne`; `warning`/`watpliwe`/`ostrzezenie` → `sprawdzone_do_weryfikacji`; pozostałe → `sprawdzone_zgodne`. Artwork: krytyczne → `artwork_bledne`, ważne → `artwork_niezgodne`, brak → `artwork_zgodne`. | `delivery_workflow.py:370-401`, `app.py:19388-19395`, `19557-19562` | `test_delivery_workflow.py` |
| WF-20 | Negatywny wynik weryfikacji blokuje przejście dalej. | Given status `sprawdzone_niezgodne` lub `artwork_bledne`, When manager wywołuje `advance`, Then 409 z `blocked: true`. | `app.py:64`, `18790-18800` | — |
| WF-21 | Nadpisanie negatywnego wyniku wymaga uzasadnienia. | Given status `sprawdzone_niezgodne` lub `artwork_bledne`, When `set-status` bez notatki, Then 400 z `need_note: true`; z notatką → zmiana statusu. | `app.py:18973-18980` | — |
| WF-22 | Brak wymaganych dokumentów wymaga świadomego potwierdzenia. | Given wejście w status z listy `REQUIRED_DOCS` (np. `packing_list_otrzymany` wymaga PL), When brak dokumentu i `confirm` ≠ true, Then odpowiedź `needs_confirm: true` z listą braków; z `confirm: true` → przejście. | `delivery_workflow.py:305-311`, `app.py:18824-18833` | `test_delivery_workflow.py`, `test_api_dostawa_advance_customs_gate.py` |
| WF-23 | Równoległe zmiany statusu nie nadpisują się. | Given dwóch managerów zmienia status tej samej dostawy, When drugi zapis trafia po pierwszym, Then 409 „Status zmienił się w międzyczasie” z aktualnym statusem. Każda udana zmiana tworzy wpis w `kolejka_status_log` (stara/nowa wartość, kto). | `app.py:18837-18866` | — |
| WF-24 | Wgranie packing listy przesuwa dostawę automatycznie. | Upload `PL` → status `packing_list_otrzymany`, tylko w przód i nie przez krok zatwierdzenia `dostawa_magazyn`. | `delivery_workflow.py:269`, `314-316`, `344-356` | `test_delivery_workflow.py` |
| WF-25 | Dostawy przetrzymane w statusie są oznaczane (SLA). | Status przekroczony, gdy `dni_w_statusie >= limit`. Limity (dni): proforma_oczekiwana 7, proforma_otrzymana 5, sprawdzone_do_weryfikacji 5, artwork_oczekiwanie 7, etd_sap 3, zlecenie_spedycja 3, agent_przypisany 5, packing_list_oczekiwanie 30, dokumenty_odprawa 5, sad_draft 5, pzc_agencja 7, rozliczenie_fiori 14. Oznaczenie na liście `/dostawy`. Źródło wartości: `<DO UZUPEŁNIENIA: uzasadnienie biznesowe limitów SLA>` | `delivery_workflow.py:405-427`, `app.py:17696-17699` | — |
| WF-26 | Potwierdzenie wypłynięcia wymaga daty ETD. | `POST` potwierdzenia bez `etd_real` → 400. Z datą → `departure_confirmed = 1`, zapis kto/kiedy; kontener tworzony, jeśli go nie było. | `app.py:20236-20278` | — |

### 1.3 Odprawa celna i postój kontenera

| ID | Wymaganie | Kryterium akceptacji | Gdzie zrealizowane | Test |
|---|---|---|---|---|
| WF-27 | Dokumenty do odprawy można wysłać tylko z zatwierdzoną checklistą celną. | Given przejście do `dokumenty_wyslane_odprawa`, When którykolwiek z CI, PL, BL, SAD nie ma statusu dokładnie `zatwierdzono` (także `wgrano`/`oczekuje`/brak wiersza), Then 409 z listą braków. `confirm: true` nie omija bramki. | `customs_checklist.py:15-28`, `app.py:18810-18822` | `test_customs_checklist.py`, `test_api_dostawa_advance_customs_gate.py` |
| WF-28 | System ocenia ryzyko opłat za postój kontenera (demurrage/detention). | Domyślnie: demurrage 14 dni wolnych (rozładunek → odbiór), detention 7 dni (odbiór → zwrot pustego), ostrzeżenie 3 dni przed końcem, stawki 0. Faza otwarta: pozostało ≤ 0 → `red`, ≤ 3 → `amber`, inaczej `green`. Faza zamknięta: `red` tylko przy przekroczeniu. Ocena całości = najgorsza faza; `at_risk` = amber lub red. Ustawienia z UI nadpisują domyślne. Źródło wartości 14/7/3: `<DO UZUPEŁNIENIA: umowa z armatorem / decyzja biznesowa>` | `demurrage.py:33-39`, `150-219`; `app.py:16166-16172` | `test_demurrage.py` |
| WF-29 | Alert postojowy dla managerów. | Przy poziomie `amber` lub `red` powstaje powiadomienie (bez duplikatu dla tego samego poziomu); e-mail tylko przy `red`. | `app.py:16071-16116` | — |

### 1.4 Kody kreskowe (artwork)

| ID | Wymaganie | Kryterium akceptacji | Gdzie zrealizowane | Test |
|---|---|---|---|---|
| WF-30 | Kody EAN-13 i EAN-8 są walidowane sumą kontrolną GS1. | `4006381333931` → poprawny; zmieniona ostatnia cyfra → błąd sumy; za krótki, za długi, z literami → błąd. GTIN-14 z indykatorem `0` traktowany jak EAN-13. | `barcode_validator.py:48-104` | `test_barcode_validator.py`, `test_gs1_gtin.py` |
| WF-31 | Kody GS1-128 są parsowane i sprawdzane pod kątem UDI. | Z ciągu `(01)…(17)…(10)…` wyodrębnione GTIN, data ważności, LOT. Brak któregokolwiek z AI (01), (17), (10) → wpis w `missing_mandatory_ai`. Błędna cyfra kontrolna GTIN → błąd. Data `YYMMDD` z `DD=00` → ostatni dzień miesiąca; data niemożliwa → błąd. | `barcode_validator.py:168-222` | `test_barcode_validator.py`, `test_gs1_gtin.py` |

### 1.5 AI: ocena ryzyka i sugestie

| ID | Wymaganie | Kryterium akceptacji | Gdzie zrealizowane | Test |
|---|---|---|---|---|
| WF-32 | Ocena ryzyka AI dobiera model do trudności przypadku. | Haiku robi wstępną ocenę `risk_score`. Score ≥ 70 → Opus; `needs_deep_analysis` (score > 25) → Sonnet; inaczej wynik Haiku. Decyzja zapisana w `_ai_decision` (model, score, powód). | `ai_validator.py:23-24`, `387-421` | `test_ai_hybrid.py` |
| WF-33 | AI może tylko podnieść poziom ryzyka. | Given wynik regułowy `warning`, When AI zwraca `ok`, Then poziom zostaje `warning`; When AI zwraca `critical`, Then `risk_level = critical` i `ai_risk_changed = true`. Rekomendacja przyjmowana tylko z listy APPROVED, APPROVED_WITH_NOTES, HOLD_PENDING_CLARIFICATION, REJECT. | `ai_validator.py:636-650` | — |
| WF-34 | Sugestie AI nigdy nie są stosowane automatycznie. | Sugestie z nauki trafiają do `settings` (`category='ai_pending'`, maks. 200 najnowszych). Przegląd, odrzucenie (`/api/ai/pending-updates`) i zastosowanie (`/api/ai/apply-profile`, `/api/ai/apply-suggestions`) wymagają roli ≥ manager. | `ai_learning.py:453-470`, `app.py:8559`, `8589`, `8637`, `8657-8677` | — |

### 1.6 Role i portale zewnętrzne

| ID | Wymaganie | Kryterium akceptacji | Gdzie zrealizowane | Test |
|---|---|---|---|---|
| WF-35 | Dostęp zależy od hierarchii ról. | Poziomy: user 1 < manager 2 < superuser 3 < admin 4; forwarder i customs_agent = 0. Endpoint z `require_role("admin")` dla managera → odmowa. `can_see_all`/`can_delete` od superusera. | `constants.py:85-98`, `core/security.py:36-49` | `test_integration.py`, `test_integration_api.py` |
| WF-36 | Role zewnętrzne widzą tylko swój portal. | Given rola `forwarder` (lub `customs_agent`), When wejście na ścieżkę spoza `/spedycja` (`/agencja`) i kilku ścieżek technicznych, Then `/api/*` → 403 JSON, pozostałe → przekierowanie do portalu. | `constants.py:150-168`, `app.py:1443-1458` | `test_integration_api.py` |
| WF-37 | Spedytor obsługuje tylko przekazane mu zlecenia. | Widzi wiersze `transport_queue` swojej firmy z ustawionym `sent_to_forwarder_at`. Może zmienić agenta celnego i `customs_status` (oczekuje, w_odprawie, zatwierdzone, odrzucone, wydane). Inny status → 400; cudze zlecenie → 404; konto bez firmy → 403. | `app.py:16696-16770` | `test_api_forwarding_order.py` (częściowo: widoczność) |
| WF-38 | Agencja celna zmienia tylko status odprawy swoich zleceń. | Tylko rola `customs_agent` (inna → 403), konto z agencją (inaczej 403), status z listy 5 wartości (inaczej 400), wiersz przekazany do tej agencji (inaczej 404). | `app.py:16616-16640` | — |
| WF-39 | User i manager widzą tylko dostawy swojego działu. | Given dostawa działu A i manager działu B, When `GET /api/dostawy/<nr>`, Then 403 „inny dział”. Superuser/admin bez ograniczeń; dostawa bez działu widoczna dla wszystkich. | `app.py:1461-1492` | — |

## 2. Wymagania niefunkcjonalne

| ID | Wymaganie | Kryterium akceptacji | Gdzie zrealizowane | Test |
|---|---|---|---|---|
| WN-01 | Limit rozmiaru uploadu. | Plik > 200 MB → 413 „Plik jest zbyt duży. Maksymalny rozmiar to 200 MB.” (JSON dla `/api/*`). | `constants.py:107-108`, `app.py:183`, `13709-13713` | — |
| WN-02 | Walidacja zawartości PDF. | W endpointach batch i intake plik `.pdf` bez nagłówka `%PDF` albo z `/Encrypt` w ostatnich 4 KB → odrzucony. Dozwolone MIME: `application/pdf`, `application/x-pdf`, `application/octet-stream` (sprawdzane w `/artwork/3d`). | `constants.py:140-142`; `app.py:5891`, `7259`, `7825`, `13778` | — |
| WN-03 | Pliki tymczasowe nie są przechowywane długo. | Pliki w `uploads/` starsze niż 24 h usuwane przez wątek uruchamiany co 30 min. | `app.py:513-520` | — |
| WN-04 | Ochrona logowania przed zgadywaniem hasła. | Po 5 nieudanych próbach z jednego IP w ciągu 15 min kolejna próba → 429 „Zbyt wiele prób”. Licznik w `audit_log`, przy awarii bazy w pamięci. | `blueprints/auth.py:75-103`, `160-163` | `test_integration_api.py` |
| WN-05 | Bezpieczna sesja. | Sesja ważna 8 h; ciasteczko HttpOnly, SameSite=Strict, Secure przy HTTPS (auto, gdy ustawione `DATABASE_URL`, albo `FORCE_HTTPS`). Konto nieaktywne lub usunięte → sesja odrzucana przy każdym żądaniu. | `app.py:183-199`, `core/security.py:53-81` | `test_integration.py` (częściowo: wylogowanie, nagłówki) |
| WN-06 | Ochrona CSRF. | Każdy POST/PUT/DELETE/PATCH na chronionym endpoincie bez poprawnego tokenu (pole `_csrf_token` lub nagłówek `X-CSRF-Token`) → 403. Token z polskimi znakami → 403, nie 500. | `core/security.py:136-173` | `test_integration.py`, `test_integration_api.py` |
| WN-07 | Polityka haseł. | Hasło krótsze niż 8 znaków albo dłuższe niż 1000 → odrzucone (tworzenie konta, zmiana, reset), bez błędu 500. Przy zmianie hasła w profilu nowe hasło musi zawierać cyfrę. | `app.py:3798`, `4107-4112`; `blueprints/auth.py:51` | `test_auth_blueprint.py` |
| WN-08 | Limit wywołań API porównania. | Maks. 30 wywołań `/api/compare` na użytkownika w 60 s (licznik w `api_rate_events`, wspólny dla workerów); kolejne → 429. | `constants.py:102-103`, `app.py:476-510`, `2795-2796` | — |
| WN-09 | Miesięczny budżet AI. | Limit `budget_monthly_usd` w `settings`; 0 = brak limitu. `near` przy ≥ 80% limitu, `over` przy wydatkach ≥ limit. Po przekroczeniu walidacja AI jest pomijana z komunikatem, a wynik regułowy zostaje. | `api_usage_tracker.py:64-127`, `ai_validator.py:572-582` | `test_artwork_batch_concurrency.py` (częściowo: bramka w batchu artworków) |
| WN-10 | Rejestracja kosztu AI. | Każde wywołanie w `ai_validator`, `ai_learning`, `artwork_comparator`, `pdf_extractor` zapisuje tokeny i koszt w `api_usage`. Cennik USD/1M tokenów (wejście/wyjście): Haiku 1/5, Sonnet 3/15, Opus 5/25; nieznany model 3/15. | `api_usage_tracker.py:11-19`, `record_usage` | — |
| WN-11 | Aplikacja działa bez kluczy API. | Given brak `ANTHROPIC_API_KEY` i `MISTRAL_API_KEY`, Then aplikacja startuje; porównanie regułowe działa; walidacja AI zwraca „Walidacja AI niedostępna” z rekomendacją HOLD_PENDING_CLARIFICATION; warstwy OCR Claude/Mistral w kaskadzie są pomijane. | `ai_validator.py:199`, `652-662`; `table_extractor.py:592-593`, `654-656` | `test_app_boots.py` |
| WN-12 | Jedna baza kodu dla SQLite i PostgreSQL. | Te same zapytania działają na obu silnikach dzięki tłumaczeniu dialektu w `db.py`; na SQLite włączone `foreign_keys`. | `db.py:1-11`, `74-91`, `369` | — |
| WN-13 | Każda zmiana przechodzi automatyczną bramkę jakości. | Na push/PR GitHub Actions uruchamia `python -m compileall` (składnia wszystkich modułów) i `python -m pytest tests/`. | `.github/workflows/ci.yml:40`, `50` | (sam CI) |

## 3. Poza zakresem (opisane w dokumentach, niezaimplementowane)

- Integracja z SAP (porównanie z SAP BW, „ETD – SAP”) – referencją jest PDF zamówienia.
- Alert e-mail przy różnicy ilości > 5% lub zamianie I↔1 – moduł `alert_engine.py` nie jest wywoływany.
- Ustawianie „zgody na wypłynięcie” (`zgoda_wyplyniecie = 1`) – brak kodu, który to ustawia, więc
  generowanie zlecenia spedycyjnego wymagające tej zgody nie jest osiągalne w normalnym przepływie.
- Automatyczne tworzenie przyjęcia magazynowego i wpisu do kolejki transportowej przy zmianie statusu.
- Tracking Maersk i TrackCargo (zapisywany jest tylko klucz API).
- Kontrola ważności produktu ≥ 5 lat i wyliczanie daty dostawy jako ETD + czas tranzytu.
- Portal potwierdzania ETD dla oddziału w Chinach.
- Powiadomienia/eskalacja po przekroczeniu SLA (jest tylko oznaczenie na liście).
- Eksport raportu porównania do Word (DOCX istnieje tylko dla raportu artworku).

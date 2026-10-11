# 07. Ograniczenia i znane problemy

Stan kodu na gałęzi `portfolio-cleanup` (2026-10-11). Numery linii dotyczą tej wersji.
Problemy opisane tu są obserwacjami z analizy kodu; nie były naprawiane.

## 1. Czego aplikacja nie robi (świadomie poza zakresem)

| Poza zakresem | Źródło |
|---|---|
| Przepisanie na FastAPI/Django i wprowadzenie ORM | `docs/PLAN_REFAKTORU.md`, „Czego ŚWIADOMIE nie robimy” |
| Pełny async UX (spinner + polling) dla `/api/compare` i `/api/table_compare` | `docs/KOLEJKOWANIE.md` sekcja 12 („osobna decyzja produktowa”) |
| LLM-first ekstrakcja faktur i auto-generowanie profilu dostawcy (v1) | `docs/superpowers/specs/2026-09-12-faktury-excel-design.md` |
| Import draftu SAD bezpośrednio do programu celnego (XML) | `docs/superpowers/specs/2026-09-14-cipl-split-draft-sad-design.md` |
| Kursy walut i przeliczenia na PLN w drafcie SAD (liczy agencja) | jw. |
| OCR do klasyfikacji stron-skanów w zestawach CIPL | jw. |
| Konwersja jednostek wagi (kg↔g↔lb), rozbijanie sum zbiorczych z packing listy | `docs/superpowers/specs/2026-09-12-wagi-z-packing-listy-design.md` |
| Workflow deployu w kopii portfolio | `README.md`, „Limitations and next steps” |

## 2. Funkcje opisane w dokumentach, ale niezaimplementowane

| Dokument mówi | Stan w kodzie | Gdzie |
|---|---|---|
| Źródło prawdy dla PO↔PI to kostka SAP BW (live); ETD porównywane z SAP | Brak integracji z SAP. PDF PO porównywany z PDF PI; `etd_sap` to tylko nazwa statusu | `docs/PROCES_ZAKUPY_FLOW.md:16-17, 41, 73`; `app.py:19254-19258` |
| Moduł `/kolejka` + `/api/kolejka/*` (etapy 1-8: import z Excela, zgoda, kontener, tracking) | Brak tych tras; proces żyje w `/dostawy`. `templates/kolejka.html` jest osierocony i woła nieistniejące API | `docs/PROCES_ZAKUPY_FLOW.md:231-277`; `templates/kolejka.html:478-567` |
| Rola „specjalista” zatwierdza zgodę na wypłynięcie | Roli nie ma; nic nie ustawia `zgoda_wyplyniecie=1` | `constants.py:76-95`; `forwarding_order.py:31` |
| Alert e-mail przy różnicy ilości > 5% i zamianie I↔1 | `alert_engine.py` nie jest importowany nigdzie w repo | `alert_engine.py`; brak wywołań `send_alert(` / `should_alert(` |
| Kontrola ważności ≥ 5 lat, porównanie LOT, data produkcji = data wysyłki | Jest tylko kolejność dat MFG ≤ DELIVERY ≤ EXP; brak progu 5 lat; LOT nieporównywany | `docs/PROCES_ZAKUPY_FLOW.md:43-45`; `app.py:19099-19105, 19372` |
| `data_dostawy = ETD + transit_time` per dostawca/port | Nie liczone; `data_dostawy` nadpisuje ETA z trackingu, `transit_time_dni` nieużywane | `docs/PROCES_ZAKUPY_FLOW.md:50-51`; `app.py:15018-15060` |
| Checklista celna obejmuje fakturę transportową i tłumaczenia | Bramka celna = CI, PL, BL, SAD | `customs_checklist.py:15`; `docs/PROCES_ZAKUPY_FLOW.md:121` |
| Rozbieżność ponad tolerancję blokuje rozliczenie | Brak bramki na `rozliczenie_fiori` / `rozliczenie_transportu` | `delivery_workflow.py:78-81` |
| Cykl życia 16 statusów (`potwierdzone`, `w_spedycji`, `wyplynelo`…) | Stepper ok. 20 kroków o innych nazwach + statusy legacy | `docs/PROCES_ZAKUPY_FLOW.md:225-228`; `delivery_workflow.py:38-82`; `migrate_db.py:581` |
| Portal potwierdzenia ETD: decyzje accept/correct/reject, PDF potwierdzenia, SLA 24/48 h | Nic z tego; jest tylko `confirm-departure` (manager wpisuje ETD) | `docs/PROCES_POTWIERDZENIE_ETD.md`; `app.py:20236-20303` |
| Sugestie AI w tabeli `pending_updates` | Trzymane w `settings` (`category='ai_pending'`, limit 200) | `CLAUDE.md`; `ai_learning.py:453-470` |
| Eksport raportu porównania do Word | `export_engine.py` nie ma eksportu DOCX; DOCX ma tylko raport artworku | `CLAUDE.md`; `artwork_report_engine.py` |
| Tracking Maersk i TrackCargo | Zapisuje się tylko klucz; zapytanie idzie do 17track albo zwraca `no_api` | `app.py:15106-15118` |
| Dostawcy SMS `infobip`, `nexmo`, `vonage`, `test` | Walidacja konfiguracji je przyjmuje, wysyłka odrzuca („Nieznany provider”) | `app.py:17163` vs `17272-17273` |
| `ARTWORK_OCR_LOCAL` „Default on” (komentarz) | Wartość domyślna `"0"` (wyłączone) | `artwork_comparator.py:124-127` |

## 3. Znane problemy

### Proces i stepper dostawy

| Problem | Skutek | Gdzie |
|---|---|---|
| Przyjęcie magazynowe nigdy nie powstaje automatycznie. Hook jest tylko w `_set_dostawa_status`, a `advance` / `set-status` robią własny `UPDATE` i go nie wołają; ręczne dodanie zwraca 405 | Brak wpisu w `/warehouse` | `app.py:17575-17576`, `18842-18871`, `19004-19009`; `blueprints/warehouse.py:205-216` |
| Ten sam wzorzec dla kolejki transportowej: `confirm-departure` i `advance` ustawiają `etd_sap` bez hooka | Dostawa nie trafia sama do `transport_queue` | `app.py:17572-17573`, `20286-20292` |
| Zlecenie spedycyjne zawsze kończy się 409, bo nic nie ustawia `zgoda_wyplyniecie=1` | Funkcja niedostępna | `forwarding_order.py:29-33` |
| Obejście bramki: advance z `proforma_otrzymana` / `proforma_zaladowana` pomija weryfikację PO/PI | Dostawa przechodzi bez porównania | `delivery_workflow.py:205-208` |
| Obejście bramki: `confirm-departure` przenosi z `artwork_bledne` do `etd_sap` | Twarda bramka artworku nie działa na tej ścieżce | `app.py:20282-20292` |
| `GET /dostawy/<nr>` może zmienić status (auto-wczytanie mastera artworku) | Efekt uboczny przy samym otwarciu karty | `app.py:18129` |
| Udany e-mail do dostawcy, a błąd zmiany statusu połknięty | Mail wysłany, status bez zmian | `app.py:18761-18762` |

### Reguły porównania

| Problem | Skutek | Gdzie |
|---|---|---|
| Ceny i kwoty pozycji porównywane bez waluty; waluta sprawdzana tylko w nagłówku | 100 EUR vs 100 USD na pozycji = „ok” | `enhanced_comparator.py:831-832`, `1007-1016` |
| Tolerancja ceny 0 wpisana przez admina zamienia się w 0,5 (`or 0.5`) | Nie da się ustawić tolerancji 0% w szablonie | `app.py:9698` |
| Trzy różne domyślne tolerancje: 0,0 i 0,5 | Wynik zależy od ścieżki | `constants.py:106`, `enhanced_comparator.py:691`, `supplier_profiles.py:321, 473` |
| Arytmetyka qty×cena=netto pomijana, gdy któraś wartość ≤ 0 | Pozycja 0 szt. z netto > 0 nie zostanie oznaczona | `enhanced_comparator.py:963-964` |

### Bezpieczeństwo

| Problem | Skutek | Gdzie |
|---|---|---|
| Eksport CSV materiałów artworku bez escape formuł (`=`, `+`, `-`, `@`) | CSV formula injection przy otwarciu w arkuszu; eksport XLSX ma escape (`export_engine.py:125-128`) | `app.py:13505-13518` |
| Link resetu hasła budowany z nagłówka Host, gdy brak `APP_BASE_URL` | Link może wskazywać obcą domenę | `blueprints/auth.py:303` |
| Kontrola własności raportu artworku przepuszcza, gdy brak `_owner_id`; ustawienie właściciela w `except: pass` | Fail-open dostępu do cudzego raportu | `app.py:7589`, `7671`, `7882-7887` |
| Odpowiedź 500 z PalViz zawiera fragment tracebacku | Wyciek szczegółów implementacji | `blueprints/palviz.py:124-126`, `268-270` |
| Klucze SMS i trackingu w `settings` jawnym tekstem; token smsapi w query stringu | Klucze widoczne w bazie i logach proxy | `app.py:17161-17172`, `17234-17238` |

### Interfejs

| Problem | Skutek | Gdzie |
|---|---|---|
| `redirect(url_for("artwork_compare_page"))` do nieistniejącego endpointu | BuildError / 500 zamiast powrotu, gdy brak danych w cache | `app.py:8162` |
| `flash()` użyty raz, a `base.html` nie renderuje komunikatów flash (robi to tylko `artwork_admin.html`) | Komunikat z `app.py:8161` nie jest widoczny | `app.py:8161`; `templates/base.html` |
| Link `/history/<id>` do nieistniejącej trasy | 404 | `templates/checklists.html:573` |
| Data hub linkuje `/artwork/profiles`, który wymaga roli ≥ manager | Rola `user` dostaje surowy JSON 403 | `templates/data_hub.html:104` |
| Ekran kierowcy pokazuje „Potwierdzono!” mimo błędu serwera | Fałszywe potwierdzenie | `templates/driver_confirm.html:372-400` |
| Brak UI do przekazania zlecenia do portali spedytora i agencji (`sent_to_forwarder_at` / `sent_to_agency_at`) | Portale pokazują tylko to, co ustawiono przez API | `app.py:16461, 16496, 16510`; `blueprints/kolejka.py:107, 188` |

### Dane i obsługa błędów

| Problem | Skutek | Gdzie |
|---|---|---|
| Schemat w trzech miejscach (`migrate_db.py`, `app.py`, `supplier_profiles.py`); wygrywa definicja wykonana pierwsza | Na Dockerze giną CHECK-i (np. `warehouse_receipts.status`); `suppliers.updated_at` może nie istnieć, a kod do niej pisze | `Dockerfile:80`; `app.py:1105` vs `migrate_db.py:771`; `supplier_profiles.py:339, 499` |
| Moduł Kolejka/Transport bez żadnego `REFERENCES` | Usunięcie rodzica zostawia osierocone wiersze | `migrate_db.py:578`, `667-668` |
| Dwa równoległe modele transportu: `transport_queue` + `shipments` oraz `kolejka_*` | Te same dane (kontener, ETD/ETA, odprawa) w dwóch miejscach | `app.py:3551`, `17142`; `delivery_workflow.py:143-152` |
| `PROGRESS_ALLOWED_COLS` zawiera `result_id`, którego nie ma w `job_progress` | Wywołanie przejdzie walidację i padnie na SQL | `constants.py:168-170` |
| 130 bloków `except …:` z samym `pass` w `app.py` (policzone AST) | Błędy znikają bez śladu, np. alert krytyczny (`app.py:2737-2738`), auto-utworzenie dostawy (`:2743-2744`) | `app.py` |
| Licznik kosztu AI i zapis budżetu w `except: pass`; bramka budżetu przy błędzie przepuszcza | Budżet AI liczony za nisko | `api_usage_tracker.py:126-127`, `159-160` |
| Niepoprawna liczbowa zmienna środowiskowa wywraca start aplikacji | Np. `TRACKING_AUTO_REFRESH_HOURS`, `RQ_JOB_TIMEOUT` | `app.py:15220`; `jobs.py:26` |

## 4. Ograniczenia techniczne

- **Rozmiar `app.py`:** ok. 20,3 tys. linii i ponad 300 tras w jednym pliku; `artwork_comparator.py`
  ok. 7,5 tys. linii. Plan podziału: `docs/PLAN_REFAKTORU.md` #4.
- **Ciężkie zależności ML:** PyTorch to ok. 2 GB RAM na worker, Qwen2.5-VL ok. 12 GB. Lokalne
  silniki są domyślnie wyłączone (`ARTWORK_OCR_LOCAL`, `DISABLE_QWEN`).
- **Stan w pamięci procesu:** cache raportów artworku (`_artwork_cache`, `app.py:6219-6223`),
  zapamiętany endpoint SafeCube (`_SAFECUBE_BASE_OK`, `app.py:14803`), semafor `_HEAVY_SEM`
  (`app.py:6282`). Przy kilku workerach gunicorn każdy ma własną kopię.
- **CI sprawdza tylko lekką część:** `compileall` + `pytest tests/` z minimalnym zestawem pakietów
  (`.github/workflows/ci.yml:40-50`). Ścieżki ML/OCR i integracje zewnętrzne nie są testowane.
- **Integracje bez retry i bez sygnału dla użytkownika:** Vision tabel, Mistral, 17track, SMS,
  webhooki (szczegóły w analizie integracji).
- **PalViz:** eksport pliku (GLB + ZIP) do ręcznego przeniesienia, bez wywołań HTTP (`blueprints/palviz.py:78-138`).

## 5. Co dalej

Kierunki wynikające z dokumentów i z powyższych problemów. Priorytety biznesowe nie są ustalone.

| Kierunek | Źródło | Priorytet |
|---|---|---|
| Wołać hooki kolejki transportowej i przyjęcia magazynowego także z `advance` / `set-status` / `confirm-departure` | sekcja 3 | `<DO UZUPEŁNIENIA>` |
| Ustalić, kto i gdzie ustawia zgodę na wypłynięcie | sekcja 2 | `<DO UZUPEŁNIENIA>` |
| Domknąć obejścia bramek w stepperze | sekcja 3 | `<DO UZUPEŁNIENIA>` |
| Decyzja: SAP jako źródło prawdy, czy zostaje PDF PO | `06-decyzje.md` D-12 | `<DO UZUPEŁNIENIA>` |
| Włączyć `alert_engine` albo usunąć opis z dokumentacji | sekcja 2 | `<DO UZUPEŁNIENIA>` |
| Porównanie cen z walutą na pozycji; jedna wartość domyślna tolerancji | sekcja 3 | `<DO UZUPEŁNIENIA>` |
| Poprawki bezpieczeństwa: escape CSV, `APP_BASE_URL` obowiązkowy, fail-closed kontroli właściciela | sekcja 3 | `<DO UZUPEŁNIENIA>` |
| Jedno źródło schematu bazy | sekcja 3 | `<DO UZUPEŁNIENIA>` |
| Oznaczyć opis modułu `/kolejka` i `templates/kolejka.html` jako historyczne albo usunąć | sekcja 2 | `<DO UZUPEŁNIENIA>` |
| Backup PG + trwały storage | `docs/PLAN_REFAKTORU.md` faza 0 | WYSOKI (wg planu) |
| Kolejka RQ + worker | `docs/PLAN_REFAKTORU.md` faza 1 | WYSOKI (wg planu) |
| Blueprinty dla 2-3 domen, zrównoleglenie Claude, walidacja Pydantic | `docs/PLAN_REFAKTORU.md` fazy 2-4 | ŚREDNI (wg planu) |
| Wydzielenie serwisu ML | `docs/PLAN_REFAKTORU.md` faza 5 | ŚREDNI (wg planu) |

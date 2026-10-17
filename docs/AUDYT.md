# Audyt repozytorium DocCompare — stan na 2026-10-15

> Audyt otwierający pracę zespołową (role **[BA]** analityk biznesowy, **[DEV]** developer, **[SEC]** bezpieczeństwo).
> Stan kodu: gałąź `main`, commit `ef950bb` (2026-10-12). Żaden plik kodu nie został zmieniony — to wyłącznie analiza.
> Poprzedni audyt techniczny: `AUDIT_2026-06-08.md` (101 ustaleń). Dokumentacja analityczna z 2026-10: `docs/01…07-*.md`.
> Numery linii dotyczą commita `ef950bb`.

Legenda wag: 🔴 krytyczne · 🟠 wysokie · 🟡 średnie · ⚪ niskie · ℹ️ informacja.

## 0. Podsumowanie wykonawcze

| Perspektywa | Najważniejszy wniosek |
|---|---|
| **[BA]** | Aplikacja robi znacznie więcej, niż opisują wymagania: 9 obszarów biznesowych i 408 tras, a `docs/05-wymagania.md` pokrywa 52 wymagania, z czego 25 nie ma testu automatycznego, a ok. 19 dużych zachowań (Faktury → Excel, artwork wizualny, master data, powiadomienia, webhooki, SMS) nie ma wymagania w ogóle. 55 merytorycznych znaczników `<DO UZUPEŁNIENIA>` czeka na odpowiedzi PO (mierniki, reguły SLA/demurrage, uzasadnienia decyzji, mapowanie interesariuszy). Największe otwarte pytania biznesowe: źródło prawdy (SAP vs PDF PO), kto nadaje zgodę na wypłynięcie, czy bramki steppera są kontrolami, czy podpowiedziami. |
| **[DEV]** | Baza jest zdrowa: 607 testów przechodzi w 11 s, `compileall` czysty, CI blokuje pushe na `main`. Dług: monolit `app.py` (20 315 linii, 336 tras, funkcja migracyjna 592 linie), schemat bazy w 12 plikach i trzech źródłach (46 vs 33 tabele, 19 wspólnych), 251 bloków `except: pass` (130 w `app.py`), stan w pamięci procesu przy 2 workerach gunicorna, 2 wątki startowane przy imporcie, brak pinów wersji i locka, lint nieegzekwowany, pokrycie niemierzone, 2 164 linie osieroconych szablonów i 2 moduły opisane jako żywe, a nieimportowane. Brak `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, szablonów issue/PR, CODEOWNERS, Dependabota. |
| **[SEC]** | Fundamenty są dobre: CSRF na wszystkich trasach sesyjnych zmieniających stan, nagłówki bezpieczeństwa (CSP, HSTS, nosniff, Referrer-Policy, Permissions-Policy), bezpieczne ciasteczka, poprawne zarządzanie `SECRET_KEY` z twardym stopem w produkcji, limit logowania, porównania stałoczasowe, walidacja PDF, brak SQL injection i sekretów w historii, Bandit bez ustaleń Medium+ w kodzie produkcyjnym, pip-audit 0 CVE w zestawie prod. Top ryzyka: 🟠 `require_role` użyte jako wartość logiczna (dwa endpointy PalViz „tylko dla managera” dostępne dla każdego zalogowanego), 🟡 klucze API/SMS jawnym tekstem w `settings` i token SMSAPI w query stringu, 🟡 link resetu hasła z nagłówka Host za `ProxyFix(x_host)`, 🟡 fail-open właściciela raportu artworku, 🟡 CSP z `unsafe-inline`/`unsafe-eval`, 🟡 22 ciężkie endpointy bez limitu, 🟡 kontener jako root i brak locka zależności, 🟡 prompt injection w `ai_learning.py`, 🟡 RODO bez retencji i anonimizacji. |

Z 10 ustaleń bezpieczeństwa z czerwca, które sprawdzono ponownie: 4 naprawione, 1 częściowo, 5 nadal otwartych (sekcja 4.5).

## 1. Baza faktów (zmierzone lokalnie 2026-10-15)

| Miara | Wartość | Jak zmierzono |
|---|---|---|
| Python | ok. 54 600 linii, 66 modułów w katalogu głównym + `blueprints/` (9) + `core/` (4) | `wc -l` |
| `app.py` | 20 315 linii, 336 `@app.route`, 482 funkcje | `grep -c`, AST |
| Trasy HTTP łącznie | 408 (336 + 62 blueprinty + 10 `invoice_routes.py`), 221 zmieniających stan | AST po dekoratorach |
| Szablony | 84 (35 920 linii), 15 101 linii inline JS, 5 nierenderowanych | `grep render_template` |
| Testy | 83 pliki, 597 `def test_`; **607 passed, 12 skipped, 11 s** | `python -m pytest tests/ -q` (Python 3.13, lekki zestaw) |
| Składnia | `compileall` czysty | `python -m compileall -q .` |
| ruff (konfiguracja repo `F,E9,W6`) | 90 ustaleń: F841 41, F541 31, F601 17, F811 1 | `ruff check .` |
| Bandit (`-r .` bez `tests/`, `static/`) | 225 ustaleń: 220 LOW, 1 MEDIUM + 1 HIGH — oba w `tools/generate_voiceover.py` (`:47` SHA1 bez `usedforsecurity=False`, `:83` `urlopen`), kod produkcyjny bez Medium+ | `bandit -r . -f json` |
| pip-audit | `requirements-prod.txt`: 81 pakietów, **0 znanych CVE**; `requirements.txt` nierozwiązywalny na Python 3.13 (`rapidocr-onnxruntime`) — do powtórzenia na 3.11 | `pip-audit -r … --no-deps` |
| Sekrety w historii gita | brak wzorców `sk-ant-`, `AKIA`, `re_…`, `ghp_` | `git log --all -p \| grep` |
| GitHub | 0 otwartych issues, 0 otwartych PR; `ci.yml` ostatnie 5 przebiegów zielone; `security.yml` ostatni ręczny przebieg (2026-10-08) zielony | API GitHub |
| Artefakty procesu | są: `README.md`, `LICENSE`, `CLAUDE.md`, `AGENTS.md`, `.pre-commit-config.yaml`, `pyproject.toml`; **brak:** `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `pull_request_template.md`, `dependabot.yml` | `ls` |
| Konwencja commitów | Conventional Commits po angielsku (`feat:`, `fix:`, `ci:`, `docs:`, `build:`) w 9 z 10 commitów | `git log` |
## 2. [BA] Perspektywa analityka biznesowego

### 2.1 Co aplikacja robi (stan kodu)

| Obszar | Wartość dla użytkownika / aktor | Gdzie |
|---|---|---|
| **Zakupy – porównania** | `user` wgrywa dwa PDF (PO/PI/CI/PL/SAD/BL/WZ/FV/CMR) i dostaje wynik linia po linii (`ok/format/watpliwe/roznica`), kontrolę arytmetyki i sum, równoważność warunków płatności, wykrywanie literówek I/1 i O/0, audyt kodów CN; wynik zapisany, eksport PDF/Excel. `manager` zatwierdza lub odrzuca wynik. Profile dostawców (mapowanie kolumn, tolerancja ceny) w kreatorze. | `/analyze` (`app.py:4184`), `POST /api/compare` (`app.py:2790`), `/history`, `/sad`, eksport `app.py:5765-5813`, `blueprints/suppliers.py:99-268` |
| **Dostawy – stepper** | `manager` prowadzi jeden rekord na numer PO przez 20 kroków od `utworzone` do `rozliczenie_transportu`; `user` wgrywa dokumenty do slotów. Twarda bramka po `sprawdzone_niezgodne`/`artwork_bledne`, miękka po brakujących dokumentach, bramka checklisty celnej przed `dokumenty_wyslane_odprawa`; znaczniki SLA; widoczność per dział. | `/dostawy` (`app.py:17726`), `/dostawy/<nr>` (`app.py:18260`), 24 trasy `/api/dostawy/*`, `delivery_workflow.py:38-82`, `customs_checklist.py` |
| **Transport – kolejka / tracking / demurrage** | Przypisanie kontenera do dostawy, śledzenie przez API (SafeCube/17track/ShipsGo), mapa, ETA jako data magazynu; ocena ryzyka demurrage/detention (zielony/bursztynowy/czerwony); SMS do kierowcy z linkiem potwierdzenia; kalendarz, checklisty dokumentów, rejestr przyjęć magazynowych. | `/transport/queue` (`app.py:16187`), `/tracking` (`app.py:14595`), `/settings/demurrage` (`demurrage.py`), `/transport/dispatch` + SMS (`app.py:16781, 16989, 17217-17248`), `/warehouse` (`blueprints/warehouse.py:184`) |
| **Portal Spedycja** | Zewnętrzny `forwarder` widzi tylko wiersze `transport_queue` przekazane jego firmie; wpisuje agenta celnego i ustawia `customs_status`. | `/spedycja` (`app.py:16683`), `/api/spedycja` (`app.py:16696-16770`) |
| **Portal Agencja** | Zewnętrzny `customs_agent` widzi wiersze przekazane jego agencji i zmienia wyłącznie `customs_status`. Draft SAD nie jest dostarczany przez portal (decyzja 2026-09-16). | `/agencja` (`app.py:16573`), `/api/agencja` (`app.py:16616-16640`), `docs/WORKFLOW_AGENCJA_CELNA.md` |
| **Artwork** | Porównanie artworku fabrycznego z wzorcem (piksele/ΔE/OCR, pola strukturalne, EAN-13/GS1-128); raport PDF/DOCX/HTML; batch do 50 par; strefy; model 3D z wykrojnika; PalViz; indeks biblioteki wzorców z dysku `Z:` przez API z tokenem; aliasy, grupy mapowań, rewizje, materiały, profile pól. | `/artwork` + 19 stron, 84 trasy `/api/artwork/*`, `/artwork/3d` (`app.py:7237`), `blueprints/palviz.py`, `/library` (`app.py:9948`), `/api/intake/artwork` (`app.py:13758`) |
| **Faktury → Excel / Draft SAD** | Operator wgrywa CI/PL/proformy (zestawy CIPL są dzielone), pipeline mapuje pozycje na master data, operator przegląda (dopasowania `ambiguous` blokują potwierdzenie), pobiera Excel zbiorczy i dwuarkuszowy Draft SAD wysyłany do agencji ręcznie. | `invoice_routes.py:38-247`, `blueprints/api_invoices.py`, `invoice_pipeline.py`, `doc_splitter.py` |
| **AI** | Opcjonalna ocena ryzyka gotowego porównania (Haiku→Sonnet→Opus; AI może tylko podnieść ryzyko), „uczenie” z dokumentu proponujące zmiany profilu dostawcy do zatwierdzenia przez `managera`, miesięczny budżet USD i strona kosztów. | `ai_validator.py`, `ai_learning.py`, 10 tras `/api/ai/*` (`app.py:8500-8680`), `/api-costs` (`app.py:9549`) |
| **Admin / master data** | `admin` zarządza użytkownikami, rolami, działami, modułami per użytkownik (zapisywane, nieegzekwowane), kluczami e-mail/SMS/tracking, webhookami, zgłoszeniami, limitami, statusem systemu, backupem SQLite; `/data` spina materiały, master dostawców, Incoterms, kraje tranzytu, słownik tłumaczeń, stany magazynowe; importy XLSX/CSV. | `/admin` (`app.py:2436`), `/api/admin/backup` (`app.py:1585`), `/api/admin/system-status` (`app.py:13528`), `/data` (`app.py:14407`), importy `app.py:12601`, `blueprints/suppliers.py:534`, `blueprints/warehouse.py:69` |

Uwaga nawigacyjna: `/home` pokazuje tylko trzy kafelki (Zakupy, Transport, Spedycja — `templates/home.html:136-184`), menu boczne ok. 20 pozycji (`base.html:112-288`), a 12 ekranów jest osiągalnych wyłącznie z adresu URL (`docs/03-user-flow.md:494-502`).

### 2.2 Aktorzy: w kodzie vs w dokumentach

W kodzie (`constants.py:78-98`): `user`(1) < `manager`(2) < `superuser`(3) < `admin`(4); zewnętrzni `forwarder` i `customs_agent` (poziom 0, zamknięci listami prefiksów). Dwaj aktorzy bez logowania: kierowca (jednorazowy token `/transport/confirm/<token>`) i agent skanujący dysk `Z:` (`INTAKE_TOKEN`). Kolumna `users.department` ogranicza widoczność dostaw (`app.py:1461-1492`), ale lista działów nie istnieje nigdzie w kodzie.

W dokumentach procesu bez odpowiednika w kodzie: Asystenci Zakupów, Specjalista (jedyny zatwierdzający zgodę na wypłynięcie), Transport, Oddział Chiny (wpisuje ETD), Magazyn, Księgowość (`docs/PROCES_ZAKUPY_FLOW.md`); Dostawca/Spedytor Chiny, Akceptujący (`docs/PROCES_POTWIERDZENIE_ETD.md` §2).

Otwarte pytania o model ról:
1. `PROCES_ZAKUPY_FLOW.md` („Implementacja — Etap 1”) twierdzi, że dodano rolę `SPECJALISTA` na poziomie 2; `constants.py` jej nie ma. Usunięta czy nigdy nie scalona?
2. Wszystkie decyzje wewnętrzne wykonuje `manager` (`docs/01-problem-i-zakres.md:115`). Czy Zakupy, Transport, Magazyn i Oddział Chiny mają dzielić jedną rolę, czy rozdzielać je działy?
3. `allowed_modules` per użytkownik jest zapisywane, ale nieegzekwowane (`docs/03-user-flow.md:522`).
4. `api_spedycja_update` przyjmuje każdą rolę zewnętrzną (`docs/06-decyzje.md`, D-10) — czy izolacja między portalami jest wymaganiem?
5. Czy Magazyn i Księgowość mają kiedykolwiek się logować (kroki 21–25 procesu docelowego)?

### 2.3 Czego brakuje w wymaganiach (baza: `docs/05-wymagania.md`)

**(a) Wymagania bez testu automatycznego — 25 z 52:**
- WF (19/39): WF-01, 02, 05, 07, 12, 13, 14, 17, 18, 20, 21, 23, 25, 26, 29, 33, 34, 38, 39.
- WN (6/13): WN-01, 02, 03, 08, 10, 12.
- Tylko częściowo (6): WF-04, 06, 10, 37, WN-05, WN-09.

Luka koncentruje się w bramkach steppera (WF-17/18/20/21/23/25/26), zatwierdzeniach i eksportach (WF-13/14) oraz portalu agencji (WF-38/39) — czyli tam, gdzie skutek biznesowy błędu jest największy.

**(b) Zachowania w kodzie bez wymagania w `05` (kandydaci na identyfikatory):**

| Kandydat | Zachowanie | Dowód |
|---|---|---|
| WF-40..43 | Faktury → Excel: upload + podział CIPL; `ambiguous` blokuje potwierdzenie; Excel zbiorczy; Draft SAD 409 dopóki nie wszystkie CI potwierdzone | `invoice_routes.py:102-256`, `invoice_mapper.py:73-75` |
| WF-44 | Reguły porównania wizualnego artworku (ΔE 7,0 tekst / 18,0 grafika; klasy critical/important) | `constants.py:111-114`, `app.py:19557-19574` |
| WF-45 | Eksport raportu artworku PDF/DOCX/HTML, batch (≤50 par), strefy | `/artwork/report/export-*`, `/artwork/batch`, `artwork_batch_processor.py` |
| WF-46 | Model 3D z wykrojnika; eksport PalViz; szablony wykrojników | `app.py:7237`, `blueprints/palviz.py:72-283` |
| WF-47 | Indeks biblioteki wzorców, aliasy, grupy mapowań, rewizje, intake z tokenem | `/library`, `app.py:13758` |
| WF-48 | Import/edycja master data (materiały, master dostawców, stany magazynowe) | `app.py:12601`, `blueprints/suppliers.py:534`, `blueprints/warehouse.py:69` |
| WF-49 | Kreator dostawcy: detekcja, podgląd tabeli, reguły, audyt | `blueprints/suppliers.py:241-440` |
| WF-50 | Centrum powiadomień in-app + e-mail do managerów | `app.py:4234-4415`, `kolejka_powiadomienia` |
| WF-51 | Słowniki: tłumaczeń (z „zastosuj”), Incoterms, kraje tranzytu | `blueprints/translation_dict.py`, `incoterms.py`, `transit_countries.py` |
| WF-52 | Kompletowanie zestawu celnego i stemplowanie PDF numerem MIR7 | `blueprints/kolejka.py:44, 202`, `pdf_stamper.py` |
| WF-53 | Generowanie zlecenia spedycyjnego (obecnie zawsze 409) i API zleceń transportowych | `blueprints/kolejka.py:107`, `app.py:19668-20180` |
| WF-54 | Dostawcy trackingu, auto-odświeżanie, mapa, ustawienia demurrage | `app.py:15083-15095, 16193, 16144` |
| WF-55 | SMS do kierowcy (textbelt/smsapi/twilio) i strona potwierdzenia z tokenem | `app.py:16989, 17217-17248` |
| WF-56 | Webhooki wychodzące (`comparison.completed`) | `app.py:13884-13942` |
| WF-57 | Zgłoszenia, KPI, wyszukiwarka, scorecard, wersje/duplikaty, porównanie bundle i literówek, `/scan` | `app.py:9386-9513, 1918, 2095-2342, 14074, 3067, 6291` |
| WF-58 | Reset hasła e-mailem z limitem 3/15 min | `blueprints/auth.py:250-317` |
| WN-14 | Backup: dzienna kopia SQLite w aplikacji (7 sztuk) + runbook `pg_dump` | `app.py:540-586`, `docs/BACKUP_RESTORE.md` |
| WN-15 | Przełącznik PL/EN | `blueprints/auth.py:222-225`, `translation_en.py` |

**(c) Znaczniki `<DO UZUPEŁNIENIA>` — 57 wystąpień (55 merytorycznych):**

| Klasa | Liczba | Gdzie |
|---|---|---|
| Miernik biznesowy | 7 | `01:31-35`, `01:77`, `02:23` |
| Reguła biznesowa | 3 | `05:49` (limity SLA), `05:57` (demurrage 14/7/3), `02:232` (czy obejścia bramek 1–6 są zamierzone) |
| Uzasadnienie decyzji | 23 | `01:98-107`; `06:34, 39, 59, 63, 85, 107, 175, 177, 193, 195, 218, 234, 237, 277` |
| Mapowanie interesariuszy | 2 | `01:60`, `01:115` |
| Inne (priorytety, weryfikacja, meta) | 20 | `03:502, 521-523`; `04:411, 430, 435`; `06:159`; `07:116-124` (9 priorytetów); `README:9, 11, 96` |

Wymagania z progami bez źródła biznesowego: WF-25 (SLA), WF-28 (demurrage 14/7/3), WF-32/33 (progi AI 25/70, `06:63`).

### 2.4 Wymagania niefunkcjonalne — luki

| Temat | Co repo mówi | Czego brakuje |
|---|---|---|
| Wydajność | gunicorn 2×3, timeout 300 s, RAM ≥ 8 GB (`docs/DOKUMENTACJA_IT.md` §5, §10); 30 porównań/60 s/użytkownika (WN-08); upload 200 MB (WN-01) | Cel czasu odpowiedzi, maks. liczba stron PDF, liczba równoczesnych użytkowników, budżet czasu per warstwa ekstrakcji |
| Dostępność / RTO / RPO | Nocny `pg_dump -Fc` + tar `DATA_DIR`, retencja 14 dziennych + 3 miesięczne, kopia offsite po SSH, test odtworzenia ręczny (`docs/BACKUP_RESTORE.md` §1–4; `scripts/`); health check `/login` | RPO domyślnie ≤ 24 h, ale niezapisane; RTO, procent dostępności, okna serwisowe, częstotliwość prób odtworzenia; `uploads/` jawnie bez kopii |
| RODO | Jedna linia ryzyka (`docs/DOKUMENTACJA_IT.md:83`) | Inwentarz danych osobowych (e-mail użytkownika, telefon kierowcy `app.py:16989`, kontakty dostawców `blueprints/suppliers.py:513`, `audit_log` po nazwie użytkownika, Sentry `set_user` `app.py:1540`), retencja (brak `DELETE` dla `audit_log`/powiadomień), podstawy prawne, umowy powierzenia (Anthropic, Mistral, Resend, API trackingu); usunięcie użytkownika to twardy `DELETE` mogący paść na FK (`app.py:3885`) |
| Użyteczność / dostępność | `lang` z sesji, skip link, ok. 10 atrybutów aria w `base.html`; `/help` z 9 sekcjami; ślepe zaułki skatalogowane (`docs/03-user-flow.md` §6) | Poziom WCAG, kryteria użyteczności, standard komunikatu o nieudanej akcji |
| Przeglądarki | nic | Lista wspieranych przeglądarek; Tailwind/Alpine z CDN |
| Język | PL domyślnie; EN przez `session["lang"]`, 38 kluczy w `translations.py` + 429 fraz w post-procesorze HTML `translation_en.py`; błędy API po polsku | Cel pokrycia, test; EN to podmiana fraz, nie i18n; portale dla partnerów zagranicznych częściowo po polsku |
| Audyt / śledzenie | `audit_log` przez `core.audit.log_audit` (61 wywołań w `app.py`, 24 w blueprintach), `kolejka_status_log`, `supplier_audit_log`, `/activity` | Retencja, odporność na manipulację, użytkownik po nazwie, a nie po id |
| Obserwowalność | Sentry opcjonalny, log plikowy `LOG_DIR`, `loglevel=warning`, `/api/admin/system-status`, licznik kosztów AI | SLO/alerty; integracje bez retry i bez sygnału dla użytkownika (`docs/07-ograniczenia.md` §4) |

### 2.5 Spójność procesu — tematy i pytania do PO

| Temat (z `07` §2–3, `02` §7) | Pytanie do PO |
|---|---|
| **Źródło prawdy dla zamówienia** — dokumenty chcą kostki SAP BW, kod porównuje PDF PO z PDF PI; `etd_sap` to tylko etykieta (D-12) | Czy PDF PO jest wzorcem kontraktowym, czy ma być (tylko do odczytu) integracja z SAP? |
| **Władza zatwierdzania** („zgoda na wypłynięcie”, Specjalista) — kolumna istnieje, nic jej nie ustawia, zlecenie spedycyjne zawsze 409 | Kto nadaje zgodę, czy to osobna rola, czy manager może ją nadpisać? |
| **Szczelność bramek vs elastyczność** — `advance` omija porównanie PO↔PI, `confirm-departure` omija `artwork_bledne`, `set-status` omija checklistę celną, `GET` zmienia status | Czy bramki to kontrole zgodności (nieomijalne, audytowane), czy podpowiedzi? |
| **Jeden rekord dostawy vs modele równoległe** — `kolejka_*` vs `transport_queue/shipments/warehouse_receipts`; hooki kolejki i przyjęcia nigdy nie odpalają; porzucony `/kolejka` | Który model jest systemem zapisu i czy dostawa ma automatycznie przepływać do kolejki transportowej i magazynu? |
| **Zakres kontroli celnej i rozliczenia** — checklista = CI/PL/BL/SAD, dokumenty dodają fakturę transportową i tłumaczenia; brak bramki MIR7; `customs_status` oderwany od statusu dostawy | Jaki jest pełny zestaw celny i czy rozbieżność wartości ma blokować rozliczenie (MIR7)? |
| **Powiadomienia i SLA** — `alert_engine` nieużywany, SLA tylko jako znacznik, dostawcy SMS obsłużeni połowicznie, wizja portalu potwierdzeń ETD | Które zdarzenia wymagają aktywnego powiadomienia (in-app/e-mail/SMS) i które eskalują po przekroczeniu SLA? |

### 2.6 Słownik i śledzenie

Słownika nie ma: `grep -il "słownik|glossary"` trafia tylko w strony funkcji (słownik tłumaczeń, Incoterms, hub danych); `templates/help.html` ma 9 sekcji i żadna nie jest słownikiem. Terminy, których potrzebuje nowa osoba: PO, PI/proforma, CI, PL, CIPL, SAD, Draft SAD, PZC, B/L, WZ, FV, CMR, ZS/FO, Incoterms, ETD/ETA/`etd_real`/`etd_plan`, czas tranzytu, demurrage vs detention, dni wolne, MIR7, Fiori, dostawa 18\*, ME22N, SAP BW, REF, EAN-13/GTIN-14/GS1-128 i AI (01)(10)(17), UDI/MDR, LOT/EXP/MFG, kod CN / `tariff_cn`, UOM (PCS/CTN/OP/OPZ/PAL), artwork wzorzec vs fabryczny, wykrojnik, PalViz/GROOVE, intake, agent synchronizacji biblioteki, profil dostawcy i tolerancja, `diff_count`/`warn_count`/`format_count`, waga ustalenia vs `critical/important` artworku, wartości `customs_status`, spedytor vs agencja celna, dział, SLA, `sent_to_forwarder_at`, kolejka (dwa znaczenia: `kolejka_zlecenia` vs `transport_queue`).

Śledzenie: jedyna macierz to `05-wymagania.md` (wymaganie → kod → test). Testy nie nazywają identyfikatorów wymagań. Brak identyfikatorów historyjek i issues w `docs/`; historia gita spłaszczona (10 commitów, PR #2–#10 dotyczą przygotowania portfolio). Specyfikacje w `docs/superpowers/specs/` i decyzje w `06-decyzje.md` nie są powiązane z wymaganiami. Do pełnej macierzy brakuje: ID historyjek, ID wymagań w nazwach testów, odwołań do PR/commitów, dowodów akceptacji dla 25 nietestowanych wymagań, CHANGELOG powiązanego z `APP_VERSION`.
## 3. [DEV] Perspektywa developera

### 3.1 Rozmiar i kształt

Łącznie ok. 54,6 tys. linii Pythona (66 modułów w katalogu głównym + `blueprints/` + `core/`), 84 szablony (35,9 tys. linii), 408 tras HTTP.

| Moduł | Linie | | Moduł | Linie |
|---|---|---|---|---|
| `app.py` | 20 315 | | `supplier_profiles.py` | 892 |
| `artwork_comparator.py` | 7 579 | | `artwork_index.py` | 878 |
| `enhanced_comparator.py` | 1 782 | | `typo_detector.py` | 785 |
| `artwork_report_engine.py` | 1 464 | | `comparator.py` | 777 |
| `table_extractor.py` | 1 356 | | `pdf_extractor.py` | 711 |
| `barcode_validator.py` | 1 016 | | `ai_validator.py` | 665 |
| `export_engine.py` | 945 | | `migrate_db.py` | 914 |

Trasy: 336 `@app.route` w `app.py` + 62 w blueprintach (suppliers 18, palviz 10, warehouse 8, translation_dict 6, auth 5, incoterms 5, transit_countries 4, api_invoices 3, kolejka 3) + 10 w `invoice_routes.py`. `CLAUDE.md` mówi o „~360”.

`app.py`: 482 funkcji najwyższego poziomu (519 z zagnieżdżonymi). Najdłuższe: `_db_run_migrations` 592 linie (`app.py:650-1241`), `api_analyze` 264 (`:5256`), `api_artwork_split_compare` 257 (`:6801`), `_perform_po_pi_verification` 249 (`:19228`), `api_compare` 218 (`:2793`), `api_kpi_data` 217 (`:3567`).

Największe szablony: `artwork.html` 4 434 linie (w tym 3 599 linii inline JS), `dostawa_detail.html` 2 624, `artwork_report.html` 2 581, `artwork_profiles.html` 1 640.

### 3.2 Modularność

Wydzielone: `core/` (security 173, audit 59, validation 32, timeutil 18 linii) i 9 blueprintów (2 605 linii) — ok. 5% kodu tras; 336 z 408 tras nadal w `app.py`. Grupy tras w `app.py` wg prefiksu: `/api/artwork` 84, `/api/dostawy` 24, `/artwork` 20, `/api/transport` 16, `/api/ai` 10, `/api/library` 9, `/api/admin` 8, `/api/shipments` 8. W ujęciu obszarów: artwork/biblioteka 118, porównania i pozostałe 114, transport/dostawy 67, admin 16, AI 10, cło 9.

Cykle importu: `core/` nigdy nie importuje `app` (czysto). **`blueprints/kolejka.py:53, 117, 213` robi `import app as _app_mod`** (lokalnie w funkcji) i woła `_save_doc_to_shipment`, `_ensure_shipment_folder`, `_ensure_transport_queue_for_delivery` — odwraca udokumentowaną regułę „blueprint → core/db, nigdy → app”.

### 3.3 Obsługa błędów

AST po całym repo: 1 016 handlerów `except`; 0 gołych `except:`; 717 łapie `Exception`/`BaseException`; **251 handlerów z samym `pass`** (187 z nich szerokich). W `app.py`: 458 handlerów, 319 szerokich, **130 z `pass`**. Dla kontrastu `logger.exception` w `app.py`: 41. Ciche połknięcia przeważają nad logowaniem wyjątków 3:1 — to źródło objawów z `docs/07-ograniczenia.md` §3 („integracje bez sygnału dla użytkownika”). `print(` w kodzie produkcyjnym: 211 linii.

### 3.4 Typowanie i lint

| Moduł | Funkcje | W pełni anotowane |
|---|---|---|
| `normalizer.py` | 16 | 15 (93%) |
| `enhanced_comparator.py` | 39 | 27 (69%) |
| `table_extractor.py` | 35 | 22 (62%) |
| `core/security.py` | 16 | 7 (43%) |
| `delivery_workflow.py` | 12 | 4 (33%) |
| `db.py` | 31 | 5 (16%) |
| `export_engine.py` | 21 | 3 (14%) |
| `app.py` | 519 | 44 (8%) |

mypy: nieskonfigurowany. ruff (`pyproject.toml:8-24`): `select = ["F","E9","W6"]`, `ignore = ["F401"]`; **ruff nie jest uruchamiany w żadnym workflow**. Wynik lokalny z konfiguracją repo: 90 ustaleń (F841 41, F541 31, F601 17, F811 1). Z regułami `F,E,W,B`: E501 1 033, E702 152, E701 147, B033 66, E401 64, F401 49.

### 3.5 Testy

`tests/`: 83 pliki `test_*.py`, 597 funkcji `def test_`; **lokalny przebieg: 607 passed, 12 skipped w 11 s** (Python 3.13, lekki zestaw zależności). `conftest.py` ustawia `SECRET_KEY`/`SQLITE_PATH` przed `import app` (import ma efekty uboczne: tworzy tabele, zakłada użytkowników), zakłada `it_admin`/`it_manager`/`it_forwarder` i daje klientów z prawdziwym logowaniem przez CSRF. 16 plików używa `test_client`, 31 różnych ścieżek URL jest wywoływanych. `pytest.importorskip` występuje **136 razy** — brak opcjonalnej zależności cicho usuwa testy, a CI nie drukuje podsumowania pominięć. Pokrycie: **niemierzone** (brak pytest-cov i konfiguracji).

Moduły produkcyjne bez żadnego testu: `export_engine.py` (945 linii), `supplier_profiles.py` (892), `ai_learning.py` (594), `translation_en.py` (640), `alert_engine.py` (475), `scan_extractor.py`, `batch_processor.py`, `pdf_annotator.py`, `artwork_zone_comparator.py`, `yolo_detector.py`, `library_sync.py`. Trasy w `app.py` testowane tylko wyrywkowo (14 plików, lekkie ścieżki).

### 3.6 Baza danych i schemat

Schemat jest definiowany w **12 plikach i trzech konkurujących źródłach**: `migrate_db.py` (34 `CREATE TABLE`, 94 `add_column`), `app.py` (47 `CREATE TABLE` + `init_db()` wywoływane przy imporcie `app.py:1404` + `_db_run_migrations` z 69 `ALTER TABLE`) oraz moduły (`supplier_profiles.py`, `material_master.py`, `artwork_index.py`, `uom.py`, `invoice_jobs.py`, `warehouse_stock.py`, `blueprints/incoterms.py`, `palviz.py`, `transit_countries.py`). Różnica zbiorów: `app.py` tworzy 46 tabel, `migrate_db.py` 33, wspólnych tylko 19; `users` zdefiniowane dwa razy (`app.py:1358`, `migrate_db.py:141`). `Dockerfile:85` uruchamia `migrate_db.py`, a potem import aplikacji ponownie `init_db()`.

Klucze obce: 11 `FOREIGN KEY` w całym repo (wszystkie do `users(id)`); relacje shipments ↔ documents ↔ queue bez FK. `db.py` (`_pg_sql`) tłumaczy `datetime('now')`, `?`→`%s`, `INSERT OR IGNORE`, `AUTOINCREMENT`, `BLOB` itd.; `INSERT OR REPLACE` ma 0 użyć (ustalenie z czerwca naprawione). **Shim `lastrowid` (`db.py:167-180`) używa `SELECT lastval()` i wg własnego komentarza jest nieaktualny po `ON CONFLICT DO NOTHING`; polega na nim 26 wywołań.** Transakcje: `autocommit=False` z ręcznym cyklem życia — `app.py` ma 319 `get_db()`, 175 `.commit()`, 13 `.rollback()`, 300 `.close()`; brak `teardown_appcontext`/menedżera kontekstu, więc niedomknięte wywołania wyciekają połączenia z puli.

### 3.7 Zadania w tle i stan w pamięci procesu

`jobs.py` używa RQ, gdy ustawiono `REDIS_URL`, inaczej wątku-demona; `app.py` woła `jobs` 11 razy i ma 9 własnych `threading.Thread`. Trzy tabele postępu: `job_progress`, `async_jobs` (tylko w `app.py`), `artwork_batch_jobs`.

Stan modułowy w `app.py`, który psuje się przy `workers=2, threads=3`: `_api_attempts` (`:339`), `_kpi_cache` (`:443`), `_artwork_cache`/`_rpt_cache_lock` (`:6219-6221`), `_HEAVY_SEM = Semaphore(3)` (`:6282`, efektywnie 6 przy 2 workerach), `_SAFECUBE_BASE_OK` (`:14749`), `blueprints/auth.py:73 _login_attempts` (fallback). **`_cleanup_thread.start()` (`:535`) i `_backup_thread.start()` (`:585`) są bezwarunkowe przy imporcie** — każdy worker gunicorna, `worker.py` i każdy przebieg pytest startuje te wątki.

### 3.8 Zależności, obraz, CI/CD

| Plik | Pakiety | `==` | Zakresy | Bez wersji | git+ |
|---|---|---|---|---|---|
| `requirements.txt` | 50 | 0 | 47 | 2 (`paddlepaddle`, `qwen-vl-utils`) | 1 (`lightglue @ git+…@eb42fee`) |
| `requirements-prod.txt` | 34 | 0 | 34 (same `>=`, bez górnej granicy) | 0 | 0 |
| `requirements-pilot.txt` | 5 | 0 | 0 | 5 | 0 |
| `dev-requirements.txt` | 7 | 0 | 7 | 0 | 0 |

Brak pliku lock; 13 pakietów ma inne granice w `requirements.txt` i `-prod`. Python: `3.11` w Dockerfile/CI/pyproject, ale `security.yml` używa `3.12`. Dockerfile: brak `USER` nie-root (proces działa jako root), obraz `python:3.11-slim` bez przypięcia digestu, `HEALTHCHECK` jest.

CI (`ci.yml`): `compileall` → `pip install` 12 pakietów z listy inline bez wersji → `pytest`. `deploy.yml`: po zielonym CI na `main` wywołuje API Coolify; bez testu dymnego po wdrożeniu i bez kroku wycofania. `security.yml`: cron miesięczny (komentarz mówi „cotygodniowe”), bandit `-ll` blokuje przy ≥ medium, ale tylko w harmonogramie; trivy `--exit-code 0`, pip-audit `|| true` — doradcze. Ostatni ręczny przebieg (2026-10-08) zielony; **od tego czasu dodano `tools/generate_voiceover.py`, w którym bandit lokalnie zgłasza 1 HIGH (B324, SHA1 bez `usedforsecurity=False`, `:47`) i 1 MEDIUM (B310, `:83`) — następny przebieg harmonogramu będzie czerwony.** Brak: bramki lint, bramki pokrycia, SAST na PR, `dependabot.yml`, CODEOWNERS, szablonów PR/issue, pre-commit w CI.

### 3.9 Dokumentacja i artefakty procesu

Obecne: `README.md`, `LICENSE`, `CLAUDE.md`, `AGENTS.md`, `README.txt` (legacy), `AUDIT_2026-06-08.md`, `docs/` (16 md, 3 236 linii, specyfikacje w `superpowers/`). **Brak: `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `pull_request_template.md`, `dependabot.yml`.**

Nieaktualne lub sprzeczne: `AGENTS.md:9` „no Docker” (są 3 Dockerfile) i `:33` „no test suite or linter” (83 pliki testów, ruff skonfigurowany); `README.txt` wymienia `column_parser.py` (nie istnieje); `CLAUDE.md:65` „~35 plików testów” (83) i „~360 tras” (408); `CLAUDE.md` opisuje `alert_engine.py` i `yolo_detector.py` jako żywe (patrz 3.10); `docs/07:102` nieaktualny numer linii; `security.yml:3` tygodniowo/miesięcznie; komentarz w `pyproject.toml` „15k linii”.

### 3.10 Martwy kod i sieroty

Szablony nigdy nie renderowane ani nie dołączane: **`agent_proforma.html` (359), `artwork_reports.html` (79), `kolejka.html` (696), `products.html` (494), `shipments.html` (536) = 2 164 linie.** `kolejka.html` woła 7 endpointów `/api/kolejka/*`, **których nie ma nigdzie w repo**. Moduły nieimportowane przez kod produkcyjny: **`alert_engine.py` (475 linii, 0 importów, 0 testów)**, **`yolo_detector.py` (392, 0 importów)**, `generate_process_map.py` (743, CLI), `install.py`, `deploy.py`, `library_sync.py` (CLI), `check_db.py`.

### 3.11 Frontend i i18n

15 101 linii inline `<script>` w szablonach; brak kroku budowania. CDN w `base.html`: `cdn.tailwindcss.com` (Play CDN, JIT w przeglądarce na produkcji, `:18`), `lucide@latest` bez wersji (`:20`), Alpine 3.13.0 (`:76-77`); `artwork_report.html:527-529` React 18 + `@babel/standalone` (transpilacja JSX w przeglądarce); `chart.js@4` vs `@4.4.4` w różnych szablonach. **0 atrybutów `integrity=` (SRI).**

`translation_en.py`: 415 fraz PL→EN, `str.replace` po węzłach tekstowych i atrybutach w `@app.after_request` dla `lang=en` — podmiana podciągów może przepisać dane użytkownika (nazwy dostawców/produktów zawierające polskie frazy), 0 testów.

### 3.12 Ranking długu technicznego

| # | Dług | Wpływ | Nakład |
|---|---|---|---|
| 1 | Monolit `app.py`: 20 315 linii, 336 tras, 482 funkcje, migracja 592 linie; wydzielanie blueprintów stanęło na ~5% | Wysoki: tarcie w review, efekty uboczne importu, trasy nietestowalne | L (przyrostowo) |
| 2 | Schemat w 12 plikach / 3 źródłach; 46 vs 33 tabele, 19 wspólnych, `users` dwa razy; `init_db()` przy każdym imporcie | Wysoki: dryf SQLite/PG, migracje nieśledzone | M |
| 3 | 251 `except …: pass` (130 w `app.py`) vs 41 `logger.exception` | Wysoki: awarie niewidoczne | M |
| 4 | Cache, limity i semafor per proces oraz 2 wątki przy imporcie przy 2 workerach | Wysoki: niespójne limity, zdublowane pętle backupu, wątki w testach | M |
| 5 | 0 testów dla `export_engine`, `supplier_profiles`, `ai_learning`, `translation_en`, batch/scan/annotator; 136 `importorskip`; brak pomiaru pokrycia | Średnio-wysoki | M |
| 6 | Brak pinów i locka; rozjazd prod vs pełne (13); zależność z commita git; skany miesięczne i doradcze; brak Dependabota | Średnio-wysoki: odtwarzalność, łańcuch dostaw | S–M |
| 7 | Bramka CI = compileall + pytest; ruff nieegzekwowany; zależności CI bez wersji; deploy bez testu dymnego | Średni | S |
| 8 | Martwy kod opisany jako żywy: `alert_engine.py`, `yolo_detector.py`, 5 szablonów (2 164 linie), `kolejka.html` → 7 brakujących endpointów | Średni: wprowadza w błąd | S |
| 9 | 15 tys. linii inline JS; Tailwind Play CDN, `lucide@latest`, Babel w przeglądarce; brak SRI | Średni: wydajność, odtwarzalność, powierzchnia XSS | M–L |
| 10 | `blueprints/kolejka.py` importuje `app`; `lastrowid` na PG zawodny (26 wywołań); typowanie 8% w `app.py`, brak mypy | Średni | M |

### 3.13 Szybkie wygrane (< 1 dzień każda)

1. Poprawić nieaktualne dokumenty: `AGENTS.md:9/33`, `CLAUDE.md:65` (liczba testów, tras, status `alert_engine`/`yolo_detector`), `README.txt` (`column_parser.py`), `security.yml:3`, `docs/07:102`, komentarz w `pyproject.toml`.
2. Dodać `ruff check .` do `ci.yml`, `.github/dependabot.yml` (pip + github-actions), instalować w CI `-r dev-requirements.txt` zamiast listy inline.
3. Usunąć lub zarchiwizować sieroty: 5 szablonów, `alert_engine.py` (albo podpiąć tam, gdzie `CLAUDE.md` twierdzi, że działa), przenieść `generate_process_map.py`/`install.py`/`deploy.py`/`library_sync.py` do `tools/`.
4. Start `_cleanup_thread`/`_backup_thread` (`app.py:535, 585`) za flagą env (wyłączone w workerze i testach), rozmiar `_HEAVY_SEM` z env, przypiąć `lucide` i `chart.js`, dodać SRI w `base.html`.
5. Wyrównać górne granice w `requirements-prod.txt`, dodać `pytest-cov` i `pytest --cov -rs` w CI (tylko raport), by pominięcia i pokrycie stały się widoczne.
## 4. [SEC] Perspektywa bezpieczeństwa

### 4.1 Co działa poprawnie (zweryfikowane w kodzie)

| Kontrola | Dowód |
|---|---|
| CSRF: token per sesja, porównanie stałoczasowe, pole `_csrf_token` lub nagłówek `X-CSRF-Token`; **żadna sesyjna trasa zmieniająca stan nie jest bez `csrf_protect`** (3 wyjątki uwierzytelniane tokenem Bearer) | `core/security.py:136-173`; enumeracja 408 tras |
| Nagłówki: `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, CSP, HSTS (przy HTTPS), `Cache-Control: no-store` dla HTML zalogowanych, usunięty `Server` | `app.py:234-268` |
| Sesja: `HttpOnly`, `SameSite=Strict`, `Secure` auto przy `DATABASE_URL`/`FORCE_HTTPS`, 8 h; `session.clear()` przy logowaniu; dezaktywacja konta odcina sesję | `app.py:184-199`, `core/security.py:53-92`, `blueprints/auth.py` |
| `SECRET_KEY`: env → trwały losowy plik `instance/.secret_key` (0600, O_EXCL) → `SystemExit` w produkcji; walidator startowy odrzuca znane słabe wartości | `app.py:143-164, 309-330` |
| Logowanie: limit 5/15 min per IP w `audit_log` (wspólny dla workerów), wyrównanie czasu przez atrapę hasha, brak enumeracji użytkowników; reset hasła 3/15 min + limit per konto, tokeny 24 h, unieważnianie starych, atomowe użycie | `blueprints/auth.py:75-103, 180-186, 250-375` |
| Odwrócone proxy: `ProxyFix` sterowany `PROXY_COUNT` | `app.py:104-110` |
| Portale zewnętrzne: `before_request` z listą prefiksów, fail-closed (`//admin`, `/SPEDYCJA`, `/spedycja/../admin` → przekierowanie lub 404); bramka działu dla `/dostawy/<nr>` i `/api/dostawy/<nr>` | `app.py:1444-1495`, `constants.py:150-168` |
| Upload: rozszerzenie, MIME, magic `%PDF`, `/Encrypt`; 200 MB globalnie; ZIP: 20 plików, 100 MB per plik, `secure_filename`; sprzątanie po 24 h | `pdf_validation.py:18-63`, `app.py:183, 513-520, 3290-3340` |
| Serwowanie plików: `send_from_directory` + `secure_filename` + prefiks `{uid}_`; `safe_join`; `realpath` w synchronizacji biblioteki | `app.py:5522-5533, 6550-6553, 7307-7318, 10071-10074` |
| SQL: 27 f-stringów w `execute(` składają stałe fragmenty, wartości przez parametry; brak `shell=True`, `eval`, `pickle`, `yaml.load` | przegląd `app.py:3975, 9483, 12455-12507` |
| Integracje maszynowe: `X-Api-Key` / `Bearer` przez `hmac.compare_digest` | `core/security.py:113-130`, `app.py:9917-9923, 13758-13766` |
| Webhooki wychodzące: tylko admin, blokada adresów prywatnych/loopback | `app.py:13819-13836` |
| Szablony: 0 `\|safe`, 0 `Markup(`, 0 `render_template_string`; Excel: prefiks apostrofu dla `= + - @ \t \r` | `templates/`, `export_engine.py:123-128` |
| Ostatni admin nie może być usunięty; `delete_user` chroniony | `app.py:3880-3884` |

### 4.2 Wyniki narzędzi

Bandit: 225 ustaleń, 220 LOW (w większości `try/except/pass` i `subprocess` z argv stałym); jedyne Medium+ w narzędziu pomocniczym `tools/generate_voiceover.py`. **Konsekwencja: zaplanowany na 1 listopada przebieg `security.yml` (bandit `-ll`) będzie czerwony** — poprawka to `hashlib.sha1(..., usedforsecurity=False)` i walidacja schematu URL. pip-audit: 0 CVE w 81 pakietach prod. gitleaks/trivy/semgrep nie były dostępne lokalnie; gitleaks działa w `security.yml` (ostatni przebieg zielony).

### 4.3 Top 10 ryzyk

| # | Waga | Ryzyko | Dowód | Zalecenie |
|---|---|---|---|---|
| 1 | 🟠 | **`require_role("manager")` użyte jako wartość logiczna — kontrola nigdy się nie wykonuje.** `require_role` to fabryka dekoratorów zwracająca funkcję (zawsze prawdziwą), więc `if not require_role(...)` jest zawsze fałszywe. `/api/artwork/templates/analyze` (upload + render PDF) i `/api/artwork/templates/save` (zapis szablonów wykrojników) są dostępne dla każdego zalogowanego użytkownika wewnętrznego. | `blueprints/palviz.py:236, 287`; `core/security.py:95-109` | Zamienić na dekorator `@require_role("manager")` lub `role_level(session["role"]) >= role_level("manager")`; dodać test „user dostaje 403”; grep po repo za `if not require_role`. |
| 2 | 🟡 | Klucze zewnętrzne (tracking, SMS, Anthropic) zapisywane jawnym tekstem w tabeli `settings`, zapisywalne przez rolę `manager`; token SMSAPI przekazywany w query stringu URL (logi proxy, historia). Brak helpera szyfrującego w repo. | `app.py:16005-16013, 17167-17173, 8526-8530, 17234-17238` | Szyfrowanie kopertowe `settings.value` (Fernet, klucz z env), token SMSAPI w nagłówku `Authorization`, zapis kluczy tylko dla admina. |
| 3 | 🟡 | Link resetu hasła budowany z `request.host_url`, gdy brak `APP_BASE_URL`; za `ProxyFix(x_host=…)` nagłówek `X-Forwarded-Host` jest zaufany → zatrucie nagłówka Host wysyła ofierze link do obcej domeny. | `blueprints/auth.py:303`, `app.py:110` | `APP_BASE_URL` obowiązkowy (błąd startu w produkcji), fail-closed przy braku. |
| 4 | 🟡 | Fail-open własności raportu artworku: warunek `owner_id is not None and owner_id != uid` przepuszcza raport bez właściciela; writer zadań asynchronicznych nie ustawia `_owner_id`. Id cache ma 16 znaków hex, więc wymaga wycieku identyfikatora. | `app.py:7584-7598, 7666-7671, 8090-8097` | Ustawiać `_owner_id` w obu writerach, odwrócić warunek (brak właściciela = odmowa). |
| 5 | 🟡 | CSP ze `script-src 'unsafe-inline' 'unsafe-eval'` + 3 CDN, `style-src 'unsafe-inline'`; 244 użyć `innerHTML`, 11 szablonów literałowych bez `escHtml`, `escHtml` nie escapuje cudzysłowów; 0 atrybutów SRI, `lucide@latest` bez wersji, Babel w przeglądarce. CSP nie chroni przed XSS. | `app.py:242-249`, `templates/base.html:18-20, 484`, `artwork_report.html:527-529` | CSP z nonce, Alpine w wersji CSP, zasoby z przypiętą wersją + SRI lub vendorowane; jeden `escHtml` z 5 zamianami. |
| 6 | 🟡 | 22 ciężkie endpointy (Claude Vision, batch artworków, upload wzorców, cały PalViz) bez limitu wywołań; limiter 30/60 s działa na 12 trasach. Bramka budżetu AI (`budget_allows_optional_ai`) woła tylko `artwork_comparator` i `ai_validator`; `table_extractor`/`scan_extractor` nie rejestrują kosztu. | `app.py:476-510, 6297, 7524, 6798, 7957, 8064, 8607, 11002`, `api_usage_tracker.py:111-122` | Dekorator limitu dla tras AI/upload; jeden klient Claude, który bramkuje i rejestruje każde wywołanie. |
| 7 | 🟡 | Łańcuch dostaw: 0 przypiętych wersji, brak locka, zależność z commita git; kontenery działają jako root (brak `USER` w 3 Dockerfile), obraz bazowy bez digestu; skany bezpieczeństwa tylko miesięcznie i doradczo (trivy `--exit-code 0`, pip-audit `\|\| true`). | `requirements*.txt`, `Dockerfile:5`, `Dockerfile.slim`, `Dockerfile.base`, `security.yml` | `pip-compile` z hashami, `USER` nie-root, digest obrazu, SAST/SCA na PR z progiem HIGH, Dependabot. |
| 8 | 🟡 | Prompt injection: surowy nagłówek PDF (`header[:3000]`) i wiersze tabeli trafiają do promptu uczenia bez sanityzacji, w przeciwieństwie do `ai_validator._fmt_findings`. Mitygacja: wynik parsowany jako JSON, zapis do oczekujących, zastosowanie wymaga managera. | `ai_learning.py:205-211` vs `ai_validator.py:434-459` | Delimitować treść dokumentu, usuwać znaki sterujące, instrukcja „traktuj jako dane”; ta sama funkcja sanityzująca w obu modułach. |
| 9 | 🟡 | RODO: dane osobowe w `users` (e-mail, dział), `audit_log` (nazwa użytkownika, IP, bez retencji), `drivers` (imię, telefon), `zlecenia_transportowe` (e-maile, telefon agenta), Sentry (`username`, IP). Brak retencji, anonimizacji, eksportu danych osoby; `delete_user` twardo usuwa tylko wiersz `users`, zostawiając `comparisons.user_id` i `audit_log`. | `migrate_db.py:141-148, 413-417, 787-790`, `app.py:693-703, 1049-1050, 1543-1549, 3885` | Zadanie TTL dla `audit_log` (okres do decyzji PO), pseudonimizacja przy usuwaniu konta, inwentarz danych i podstawy prawne w `docs/bezpieczenstwo/RODO.md`, endpoint eksportu danych. |
| 10 | ⚪/🟡 | Drobne wycieki: traceback w odpowiedziach 500 PalViz; prefiks klucza API (16 znaków) przez `/api/ai/status` dla każdego zalogowanego; CSV eksport materiałów artworku bez escape formuł (manager-only); `str(e)` w 3 odpowiedziach; wylogowanie przez GET. | `blueprints/palviz.py:126, 207, 270`; `ai_validator.py:141, 156`; `app.py:13489-13523, 2854, 7296, 14101`; `blueprints/auth.py:242` | Generyczny komunikat 500 + log; zwracać tylko `api_key_set`; wspólny `_csv_safe`; POST dla logout. |

Pozycje ℹ️ do świadomej akceptacji: brak globalnej bramki auth (ochrona opt-in per trasa — 15 tras bez dekoratora, wszystkie publiczne z założenia lub uwierzytelniane inline); rola i dział cache'owane w sesji (degradacja roli działa od następnego logowania); `check_session_active` fail-open przy awarii bazy (celowe); joby faktur bez właściciela (współdzielone z założenia); produkcja rozpoznawana wyłącznie po `DATABASE_URL`.

### 4.4 Klasyfikacja danych (wstępna, do potwierdzenia w `KLASYFIKACJA_DANYCH.md`)

| Klasa | Przykłady w systemie |
|---|---|
| Dane osobowe | `users.email/username`, `audit_log.username/ip`, `drivers.name/phone`, kontakty spedytorów i agentów, kontakty dostawców (`blueprints/suppliers.py:513`) |
| Poufne handlowo | ceny i warunki płatności z PO/PI/CI, profile dostawców z tolerancjami, master data materiałów (EAN, CN), artworki wzorcowe (zasada „nie opuszczają Z:” z `AUDIT_2026-06-08.md`, pyt. 59) |
| Wewnętrzne | statusy dostaw, KPI, konfiguracja SLA/demurrage, słowniki |
| Sekrety | `SECRET_KEY`, klucze API w env i w `settings` (patrz ryzyko 2), tokeny intake/biblioteki, token kierowcy |

Dane poufne i osobowe wychodzą do podmiotów trzecich: Anthropic (treść dokumentów do walidacji i uczenia, obrazy do Vision), Mistral (OCR), Resend (e-maile), API trackingu (numery kontenerów), dostawcy SMS (telefony kierowców), Sentry (nazwa użytkownika, IP). Umowy powierzenia i minimalizacja danych do decyzji PO.

### 4.5 Status ustaleń bezpieczeństwa z `AUDIT_2026-06-08.md`

| Czerwiec | Ustalenie | Status 2026-10-15 | Dowód |
|---|---|---|---|
| #4 | Hardcoded `SECRET_KEY` nie przerywa startu w prod | **naprawione** (szczątkowo ⚪: literał zostaje dla nie-prod; „prod” = `DATABASE_URL`) | `app.py:152-164, 309-330` |
| #6 | KPI bez filtra użytkownika | **naprawione** (`_scope_sql` we wszystkich trzech agregatach, klucz cache z uid) | `app.py:3693-3756` |
| #3 | Excel formula injection bez `-` | **naprawione w XLSX**, **otwarte w CSV** materiałów | `export_engine.py:123`; `app.py:13489-13523` |
| #2 | `INSERT OR REPLACE` nietłumaczone na PG | **naprawione** (0 użyć) | `grep` |
| #76 | Można usunąć ostatniego admina | **naprawione** | `app.py:3880-3884` |
| #84 | Tokeny resetu nie unieważniają poprzednich | **naprawione** | `blueprints/auth.py:290-293` |
| #83 | `library sync` POST z sesją bez CSRF | **naprawione** (tylko Bearer) | `app.py:10019-10028` |
| 07 §3 | Link resetu z nagłówka Host | **otwarte** | `blueprints/auth.py:303` |
| 07 §3 | Kontrola właściciela raportu artworku fail-open | **otwarte** | `app.py:7590, 7671, 8097` |
| 07 §3 | Traceback w 500 PalViz | **otwarte** | `blueprints/palviz.py:126, 270` |
| 07 §3 | Klucze SMS/tracking jawnym tekstem, token w query stringu | **otwarte** | `app.py:17167-17238` |
| #39 | Prompt injection w `ai_learning` | **otwarte** | `ai_learning.py:205-211` |
| #81 | `str(exc)` do klienta | **w większości naprawione** (3 miejsca + PalViz) | `app.py:2854, 7296, 14101` |
## 5. Pytania do Product Ownera

**[BA] Pierwsza seria (wizja, użytkownicy, priorytety):**

1. **Wzorzec danych.** Czy PDF zamówienia jest wiążącym wzorcem do kontroli PI/CI, czy planowany jest odczyt z SAP BW? Od tego zależy, czy `etd_sap`, czas tranzytu i porównanie ETD są funkcjami, czy tylko etykietami (`docs/06-decyzje.md` D-12, `01:98`).
2. **Kto pracuje w systemie.** Które grupy (Asystenci Zakupów, Specjalista, Transport, Oddział Chiny, Magazyn, Księgowość) logują się dziś, na jakiej roli i w jakim dziale? Czy spedytorzy i agencje celne są realnymi użytkownikami portali? (`01:60`, `01:115`; decyduje o modelu ról i języku portali.)
3. **Charakter bramek.** Czy bramki steppera i checklista celna to obowiązkowe kontrole zgodności (nieomijalne, audytowane), czy wsparcie decyzji? (`02:232`; rozstrzyga, czy 6 znanych obejść to błędy, czy akceptowane zachowanie.)
4. **Granica zakresu.** Czy celem jest pełny 27-krokowy proces (centrum powiadomień, portal potwierdzeń ETD, bramka MIR7, komplety dokumentów), czy zakres kończy się na „dokumenty zweryfikowane przed odprawą”? (`PROCES_ZAKUPY_FLOW.md`, `PROCES_POTWIERDZENIE_ETD.md` vs `README.md` „Poza zakresem”.)
5. **Mierniki i wolumeny.** Jakie są wartości bazowe i docelowe: czas kontroli kompletu dokumentów, liczba rozbieżności wykrytych za późno, liczba PO/kontenerów miesięcznie, liczba równoczesnych użytkowników? (`01:31-35`, `01:77`; potrzebne do celów wydajności, wartości SLA `05:49` i domyślnych demurrage `05:57`.)

**Decyzje potrzebne od PO poza pytaniami BA:**

- **[SEC]** Zgoda na natychmiastową poprawkę ryzyka 🟠 #1 (PalViz) jako pierwszej historyjki bezpieczeństwa, oraz czy ryzyka 🟡 #2–#4 wchodzą do pierwszego sprintu, czy do rejestru ryzyk z datą przeglądu.
- **[SEC]** Okres retencji `audit_log` i powiadomień (propozycja: 12 miesięcy) oraz zasada anonimizacji po usunięciu konta.
- **[SEC]** Czy treść dokumentów handlowych może nadal trafiać do Anthropic/Mistral (umowy powierzenia, minimalizacja), czy potrzebny tryb „bez chmury”.
- **[DEV]** Próg pokrycia testami do bramki CI (domyślnie 80% dla logiki domenowej wg promptu; realistycznie start od raportu bez progu, potem próg per moduł).
- **[DEV]** Czy martwe elementy (`alert_engine.py`, `yolo_detector.py`, 5 szablonów, `/kolejka`) usuwamy, czy któryś ma wrócić do życia.
- **[DEV]** Język commitów: w repo obowiązuje Conventional Commits po angielsku — proponuję to utrzymać (dokumentacja po polsku).
- **Proces** Zgoda na push gałęzi roboczych i otwieranie PR w trybie draft bez pytania przy każdej zmianie (merge nadal tylko po akceptacji PO).

## 6. Proponowany backlog startowy (do zatwierdzenia po odpowiedziach)

Kolejność: najpierw pilne poprawki bezpieczeństwa, potem błędy bramek procesu, potem higiena inżynierska. Każda pozycja stanie się historyjką w `docs/analiza/HISTORYJKI.md` po przejściu kroków 1–2 procesu.

| # | Historyjka (skrót) | MoSCoW | Typ | Wymaga decyzji PO |
|---|---|---|---|---|
| S-01 | Jako admin chcę, aby endpointy szablonów PalViz wymagały roli manager (poprawka `require_role` + test 403). | Must | security | nie |
| S-02 | Jako admin chcę, aby klucze API i tokeny SMS były szyfrowane w bazie i nie trafiały do URL. | Must | security | nie |
| S-03 | Jako użytkownik chcę, aby link resetu hasła zawsze prowadził do domeny aplikacji (`APP_BASE_URL` obowiązkowy). | Must | security | nie |
| S-04 | Jako właściciel raportu artworku chcę, aby raport bez właściciela nie był widoczny dla innych (fail-closed). | Must | security | nie |
| S-05 | Jako SEC chcę, aby skan bezpieczeństwa (bandit/pip-audit/gitleaks) działał na każdym PR i blokował ustalenia HIGH, a Dependabot pilnował zależności. | Must | security | nie |
| S-06 | Jako operator chcę, aby ciężkie endpointy AI/upload miały limit wywołań i aby każde wywołanie Claude było bramkowane budżetem. | Should | security | nie |
| S-07 | Jako administrator danych chcę retencji `audit_log`, anonimizacji po usunięciu konta i inwentarza danych osobowych. | Should | security | tak (okresy) |
| B-01 | Jako manager chcę, aby `advance`, `set-status` i `confirm-departure` wywoływały te same hooki co `_set_dostawa_status` (kolejka transportowa, przyjęcie magazynowe). | Must | bug | tak (temat 4) |
| B-02 | Jako właściciel procesu chcę, aby twardych bramek nie dało się ominąć inną trasą. | Must | bug | tak (temat 3) |
| B-03 | Jako specjalista chcę nadać zgodę na wypłynięcie w aplikacji, aby zlecenie spedycyjne dało się wygenerować. | Must | feature | tak (temat 2) |
| B-04 | Jako kupiec chcę porównania cen z walutą na pozycji i jednej domyślnej tolerancji. | Must | bug | częściowo |
| B-05 | Jako kierownik zakupów chcę decyzji: SAP (odczyt) czy PDF PO jako wzorzec. | Must | decyzja | tak (temat 1) |
| B-06 | Jako manager chcę przekazać zlecenie do portalu spedytora/agencji z karty dostawy. | Should | feature | tak |
| B-07 | Jako manager chcę alertów e-mail/in-app po przekroczeniu SLA (podpięcie lub usunięcie `alert_engine`). | Should | feature | tak (temat 6) |
| B-08 | Jako księgowość chcę blokady rozliczenia przy rozbieżności > tolerancja i zapisu numeru MIR7. | Should | feature | tak (temat 5) |
| D-01 | Jako zespół chcę `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, szablonów issue/PR i CODEOWNERS (szkielet z sekcji 2 promptu). | Must | proces | nie |
| D-02 | Jako zespół chcę lintu w CI, zależności CI z `dev-requirements.txt`, raportu pokrycia i podsumowania pominiętych testów. | Must | chore | próg pokrycia |
| D-03 | Jako zespół chcę jednego źródła schematu bazy (`migrate_db.py`) i wyłączenia `init_db()` z importu. | Should | refactor | nie |
| D-04 | Jako zespół chcę, aby wątki sprzątania/backupu i semafor były sterowane env, a stan per proces przeniesiony do bazy/Redis. | Should | refactor | nie |
| D-05 | Jako zespół chcę usunąć martwy kod i poprawić nieaktualne dokumenty (`AGENTS.md`, `CLAUDE.md`, `README.txt`). | Could | chore | tak (co zostaje) |
| D-06 | Jako zespół chcę przypiętych zależności (lock z hashami), obrazu nie-root i digestu obrazu bazowego. | Should | chore | nie |
| D-07 | Jako zespół chcę testów dla 25 wymagań bez testu, zaczynając od bramek steppera (WF-17..26) i eksportów (WF-13/14). | Should | test | nie |

## 7. Metoda i powtarzalność

Audyt wykonano w trzech równoległych przeglądach (BA/DEV/SEC) plus weryfikacja każdego ustalenia o wadze ≥ średniej bezpośrednio w kodzie. Komendy do powtórzenia:

```bash
python -m compileall -q . -x 'static/design|\.git'
python -m pytest tests/ -q
ruff check . --output-format concise
bandit -r . -x ./tests,./static,./.git -f json -o bandit.json
pip-audit -r requirements-prod.txt --no-deps
git log --all -p | grep -E -o "sk-ant-[A-Za-z0-9_-]{10,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}"
```

Następne kroki wg procesu: odpowiedzi PO na sekcję 5 → szkielet struktury dokumentów (`docs/analiza/`, `docs/architektura/`, `docs/bezpieczenstwo/`, szablony `.github/`) → `WIZJA.md`, `WYMAGANIA.md` 0.1, `KLASYFIKACJA_DANYCH.md`, `THREAT_MODEL.md` 0.1, CI z sekcji 5 promptu → backlog z sekcji 6 → praca funkcja po funkcji.

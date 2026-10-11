# 06. Dziennik decyzji

Decyzje odtworzone z kodu, komentarzy i dokumentów w repo. Przy każdej podane jest źródło.
Tam, gdzie powód nie jest nigdzie zapisany, stoi `<DO UZUPEŁNIENIA>`; nie zgadujemy go.

| ID | Decyzja | Źródło |
|---|---|---|
| D-01 | Reguły deterministyczne najpierw, AI jako doradca | `README.md` („Why this stack”), `ai_validator.py`, `ai_learning.py` |
| D-02 | Walidacja AI hybrydowa: Haiku → Sonnet → Opus | `ai_validator.py:18-24`, `:364-420` |
| D-03 | Kaskada ekstrakcji PDF/OCR | `table_extractor.py:25-50`, `:834`, `README.md` |
| D-04 | Jedna warstwa `db.py` dla SQLite i PostgreSQL, bez ORM | `db.py:1-11`, `docs/PLAN_REFAKTORU.md` |
| D-05 | Monolit Flask, stopniowe wydzielanie blueprintów | `docs/PLAN_REFAKTORU.md` |
| D-06 | Zadania w tle: wątki + kolejka RQ z fallbackiem | `docs/KOLEJKOWANIE.md`, `jobs.py` |
| D-07 | Twarda i miękka bramka w stepperze dostawy | `app.py:60-64`, `:19302`, `:19554-19562` |
| D-08 | Profile dostawców z tolerancjami zamiast reguł globalnych | `supplier_profiles.py:1-12`, `constants.py:105-107` |
| D-09 | Faktury → Excel: osobny moduł, profil obowiązkowy, bez LLM | `docs/superpowers/specs/2026-09-12-…`, `2026-09-14-…` |
| D-10 | Role zewnętrzne z poziomem 0, zamknięte w portalach | `constants.py:86-98`, `:149-165` |
| D-11 | Leniwe importy ciężkich bibliotek ML | `CLAUDE.md` (Key Conventions), `docs/PLAN_REFAKTORU.md` #2 |
| D-12 | PDF zamówienia jako wzorzec porównania (zamiast SAP) | kod `app.py:19254-19258` vs `docs/PROCES_ZAKUPY_FLOW.md:16-17, 41` |

---

### D-01 Reguły deterministyczne najpierw, AI jako doradca

**Decyzja.** Wynik porównania liczy silnik regułowy (`enhanced_comparator.py`, `typo_detector.py`,
`normalizer.py`). Walidacja AI (`ai_validator.py`) jest opcjonalna i działa na gotowym wyniku.
Sugestie AI do profili dostawców (`ai_learning.py`) nie są zapisywane automatycznie, tylko czekają
na akceptację managera (`/api/ai/pending-updates`).

**Kontekst.** Dokumenty od dostawców mają różne układy, a koszt i dostępność API Claude są zmienne.
Docstring `ai_learning.py:9`: „Proponuje aktualizację profilu (NIE zapisuje bez zatwierdzenia)”;
`ai_learning.py:340`: „NIE zapisuje automatycznie”.

**Rozważane opcje.** `<DO UZUPEŁNIENIA: czy rozważano AI jako główny silnik porównania>`.
W specyfikacji modułu faktur wariant „LLM-first” jest wprost odrzucony dla v1 (zob. D-09).

**Dlaczego ta.** README: „LLM validation is optional and runs behind deterministic rules, so the app
still works without an API key”. Powód ręcznej akceptacji sugestii:
`<DO UZUPEŁNIENIA: dlaczego sugestie AI wymagają zatwierdzenia managera>`.

**Skutki.**
- (+) Aplikacja działa bez klucza API. Brak klucza daje w raporcie `HOLD_PENDING_CLARIFICATION`
  z komunikatem „Walidacja AI niedostępna” (`ai_validator.py:652-662`).
- (+) AI nie zmienia po cichu profili, od których zależą tolerancje.
- (−) Alert e-mail „krytyczny” odpala się tylko wtedy, gdy AI podniesie ryzyko do `critical`.
  Silnik regułowy tego statusu nie zwraca (`enhanced_comparator.py:199-203`, `app.py:2723`).
- (−) Sugestie leżą w `settings` (`category='ai_pending'`, limit 200), a nie w tabeli
  `pending_updates`, jak podaje CLAUDE.md (`ai_learning.py:453-470`).

### D-02 Walidacja AI hybrydowa: Haiku → Sonnet → Opus

**Decyzja.** Każdy wynik najpierw ocenia tani model (Haiku). Gdy `risk_score ≤ 25`, zostaje jego
wynik; powyżej 25 idzie pełna analiza Sonnetem; od 70 eskalacja do Opusa
(`ai_validator.py:18-24`, `HYBRID_THRESHOLD`, `OPUS_THRESHOLD`).

**Kontekst.** Komentarz `ai_validator.py:18`: Haiku „fast/cheap — pre-screen”. Aplikacja ma
miesięczny budżet USD na API (`api_usage_tracker.py`).

**Rozważane opcje.** `<DO UZUPEŁNIENIA: czy rozważano jeden model dla wszystkich porównań>`.

**Dlaczego ta.** Wnioskowane z komentarzy: niższy koszt dla prostych przypadków. Każda decyzja
dostaje ślad `_ai_decision`, „so a manager can see *why* a comparison was or wasn't escalated”
(`ai_validator.py:388-390`). Wartości progów 25 i 70: `<DO UZUPEŁNIENIA: skąd te progi>`.

**Skutki.**
- (+) Mniej wywołań drogich modeli; manager widzi powód eskalacji. Logikę pokrywa `tests/test_ai_hybrid.py`.
- (−) Błąd pre-screenu zwraca `risk_score=100`, czyli wymusza eskalację (`ai_validator.py:383`).
- (−) Część wywołań Claude poza walidatorem nie jest liczona do budżetu
  (`table_extractor.py:612`, `scan_extractor.py:189`, `app.py:10914`).

### D-03 Kaskada ekstrakcji PDF/OCR

**Decyzja.** Pozycje z PDF wyciąga kaskada: pdfplumber → Camelot → Claude Vision → Mistral OCR →
img2table → Tesseract. Kolejna warstwa rusza tylko wtedy, gdy poprzednia nic nie zwróci
(`table_extractor.py:28`, `:834`).

**Kontekst.** Dostawcy przysyłają PDF-y wektorowe i skany o różnym układzie tabel.

**Rozważane opcje.** Pojedynczy silnik zamiast kaskady. Kod pozwala go wymusić per żądanie
(`set_ocr_engine`, `table_extractor.py:25-50`) „do testów A/B: kaskada vs GLM-OCR vs pojedyncza
biblioteka” (`:837-838`).

**Dlaczego ta.** README: „no single extractor handles every supplier's layout”. CLAUDE.md opisuje
kaskadę jako wodospad koszt/dokładność: darmowe biblioteki najpierw, płatne API dalej.
Wyniki testów A/B: `<DO UZUPEŁNIENIA: czy A/B dało liczby, które potwierdzają kolejność warstw>`.

**Skutki.**
- (+) Tanie warstwy obsługują PDF-y wektorowe, płatne API tylko skany.
- (+) Bez kluczy API zostaje Tesseract jako ostatnia warstwa.
- (−) Każda warstwa przy błędzie zwraca `[]` bez sygnału dlaczego (`table_extractor.py:633`, `685`, `706`).
  Użytkownik nie wie, czy PDF jest pusty, czy padło API.
- (−) Mistral jest wołany dwoma różnymi kontraktami: `/v1/ocr` w artworkach i `/v1/chat/completions`
  w tabelach (`artwork_comparator.py:1203-1235`, `table_extractor.py:654-686`).

### D-04 Jedna warstwa `db.py` dla SQLite i PostgreSQL, bez ORM

**Decyzja.** Cały kod woła `db.get_db()`. Warstwa tłumaczy dialekt (`?` → `%s`,
`datetime('now')` → `NOW()`, `INSERT OR IGNORE` → `ON CONFLICT DO NOTHING`) (`db.py:1-11`).
SQLite lokalnie, PostgreSQL na produkcji.

**Kontekst.** Surowy SQL w całej aplikacji, praca lokalna bez serwera bazy.

**Rozważane opcje.** ORM, odrzucony: „`db.py` (surowy SQL, dual SQLite/PG) działa; ORM = duży
przepis bez korzyści” (`docs/PLAN_REFAKTORU.md`, sekcja „Czego ŚWIADOMIE nie robimy”).

**Dlaczego ta.** Jak wyżej: koszt przepisania bez zysku. Powód dwóch baz zamiast jednej:
`<DO UZUPEŁNIENIA: dlaczego dev na SQLite, a nie na PostgreSQL>`.

**Skutki.**
- (+) Start bez instalacji bazy; jeden kod dla obu silników.
- (−) Schemat powstaje w trzech miejscach (`migrate_db.py`, `app.py`, `supplier_profiles.py`);
  wygrywa definicja wykonana jako pierwsza (zob. [07-ograniczenia.md](07-ograniczenia.md)).
- (−) Różnice silników przeciekają: `users.email` jest unikalny tylko na PG (`migrate_db.py:884`),
  `datetime('now')` w SQLite to UTC, a część kodu liczy datę lokalną (`demurrage.py:199-200`).

### D-05 Monolit Flask, stopniowe wydzielanie blueprintów

**Decyzja.** Zostaje Flask i jeden proces. `app.py` jest dzielony na blueprinty po jednej domenie,
przez mechaniczne przeniesienie tras bez zmiany logiki (`docs/PLAN_REFAKTORU.md` #4).

**Kontekst.** `app.py` ma ok. 20 tys. linii i ponad 300 tras; pierwsze blueprinty już działają
(`blueprints/`: incoterms, translation_dict, transit_countries i inne).

**Rozważane opcje.** Przepisanie na FastAPI lub Django, odrzucone (`docs/PLAN_REFAKTORU.md`).

**Dlaczego ta.** „Wąskie gardła (CPU/ML/RAM, koszt API) pozostałyby te same, a koszt i ryzyko
regresji ogromne. Async nie przyspiesza zadań CPU-bound.” Każdy krok jest mały i odwracalny,
za bramką testów.

**Skutki.**
- (+) Brak „wielkiego przepisania”, refaktor da się robić przyrostowo.
- (−) Do czasu podziału `app.py` jest trudny w nawigacji i review; zawiera 130 bloków `except …:`
  z samym `pass` (policzone AST).

### D-06 Zadania w tle: wątki + kolejka RQ z fallbackiem

**Decyzja.** Ciężkie operacje idą przez `jobs.enqueue` / `jobs.run`. Gdy jest ustawiony `REDIS_URL`,
liczy osobny worker RQ; bez niego liczy wątek w procesie web pod semaforem `_HEAVY_SEM`
(`docs/KOLEJKOWANIE.md` sekcje 10-12, `jobs.py:49-123`). Postęp trafia do tabel `async_jobs` / `job_progress`.

**Kontekst.** Liczenie w procesie web blokuje workery HTTP, grozi timeoutem 300 s i ginie przy
deployu (`docs/KOLEJKOWANIE.md` sekcja 1).

**Rozważane opcje.** Celery („overkill”, `docs/PLAN_REFAKTORU.md` #1). Pełny async UX
(spinner + polling) dla `/api/compare` i `/api/table_compare` odłożony jako „osobna decyzja
produktowa” (`docs/KOLEJKOWANIE.md` sekcja 12).

**Dlaczego ta.** RQ jest „lekkie, proste, idealne do CPU-bound”. Fallback daje odwracalność:
„bez `REDIS_URL` aplikacja działa dokładnie jak dotąd”. `_HEAVY_SEM` zostaje jako bezpiecznik
ścieżki inline (ochrona przed OOM).

**Skutki.**
- (+) Brak twardej zależności od Redis; każdy endpoint da się cofnąć osobno.
- (−) Gdy zadanie RQ padnie albo przekroczy czas, `jobs.run` liczy je drugi raz inline:
  podwójny koszt CPU/AI (`jobs.py:104-121`).
- (−) Worker importuje cały `app`, więc ładuje ok. 2 GB modeli i potrzebuje wspólnego wolumenu
  `uploads/` z web (`docs/KOLEJKOWANIE.md` sekcja 10).
- (−) CLAUDE.md nadal opisuje RQ jako „planned but not yet deployed”, a `docs/KOLEJKOWANIE.md`
  jako zaimplementowane fazy 1-3. Stan wdrożenia na produkcji: `<DO UZUPEŁNIENIA>`.

### D-07 Twarda i miękka bramka w stepperze dostawy

**Decyzja.** Statusy `sprawdzone_niezgodne` i `artwork_bledne` blokują przejście dalej (`advance`);
zostaje tylko ręczna „Zmień status” z uzasadnieniem (`app.py:60-64`, `_DELIVERY_BLOCKED_ADVANCE`).
`artwork_niezgodne` to bramka miękka: advance z potwierdzeniem. Podział według ważności różnic
w artworku („decyzja #7”, `app.py:19554-19562`):
- kody i tekst (EAN, LOT, data, REF, oznaczenia MDR; severity `critical`) → `artwork_bledne`;
- grafika, kolory, wymiary (severity `important`) → `artwork_niezgodne`.

Różnica sumy pozycji względem zadeklarowanej sumy (checksum) daje status „niezgodne” jak twarda
różnica („decyzja produktowa”, `app.py:19302`).

**Kontekst.** Artworki to opakowania wyrobów medycznych; kody i teksty są weryfikowane jako pola krytyczne.

**Rozważane opcje.** `<DO UZUPEŁNIENIA: jakie warianty bramki rozważano, np. blokada każdej różnicy>`.

**Dlaczego ta.** `<DO UZUPEŁNIENIA: dlaczego różnice graficzne nie blokują, a tekstowe tak>`.

**Skutki.**
- (+) Błąd w kodzie EAN/LOT nie przejdzie dalej „jednym kliknięciem”.
- (−) Bramkę da się obejść: advance z `proforma_otrzymana` / `zaladowana` pomija weryfikację
  (`delivery_workflow.py:207-208`), a `confirm-departure` przenosi z `artwork_bledne` do `etd_sap`
  bez sprawdzenia (`app.py:20282-20292`).

### D-08 Profile dostawców z tolerancjami zamiast reguł globalnych

**Decyzja.** Każdy dostawca ma profil: mapowanie kolumn per typ dokumentu, tolerancję ceny w %,
równoważniki warunków płatności, synonimy produktów, historię zmian (`supplier_profiles.py:1-12`).
Domyślnie, bez profilu, tolerancja ceny i ilości wynosi 0% (`constants.py:105-107`).

**Kontekst.** Dostawcy różnią się układem dokumentów i nazewnictwem kodów (np. `NL753-S-40` ≈ `NL753S40`).

**Rozważane opcje.** `<DO UZUPEŁNIENIA>`.

**Dlaczego ta.** `<DO UZUPEŁNIENIA: dlaczego tolerancje per dostawca, a nie jedna reguła globalna>`.

**Skutki.**
- (+) Tolerancja i mapowanie kolumn ustawiane w kreatorze (`/suppliers/wizard`), bez zmian w kodzie.
- (−) Trzy różne wartości domyślne tolerancji: 0,0 (`constants.py:106`, `enhanced_comparator.py:691`)
  i 0,5 (`supplier_profiles.py:321`, `473`, `app.py:9698`).
- (−) Profil wybierany już przy jednym trafieniu słowa kluczowego (`supplier_profiles.py:587-594`);
  błąd detekcji jest połykany, a porównanie idzie bez profilu z tolerancją 0% (`app.py:5307-5315`).

### D-09 Faktury → Excel: osobny moduł, profil obowiązkowy, bez LLM

**Decyzja.** Moduł faktur jest osobny, nie jest rozszerzeniem porównywarki. Ekstrakcja = kaskada
generyczna + profil dostawcy. Brak profilu = brak generowania. Bez LLM w pętli. Zapis do Excela
dopiero po ręcznym potwierdzeniu operatora (`docs/superpowers/specs/2026-09-12-faktury-excel-design.md`).
Zestawy dokumentów w jednym PDF (CIPL) cięte splitterem stron, bez zmian w pipeline
(`docs/superpowers/specs/2026-09-14-cipl-split-draft-sad-design.md`).

**Kontekst.** Ok. 100 formatów faktur; QA na realnych PDF-ach: 4 z 5 plików to dokumenty połączone.

**Rozważane opcje.** LLM-first ekstrakcja i auto-generowanie profilu (poza zakresem v1, „rozważyć
w v2”); multi-table w kaskadzie (odrzucone).

**Dlaczego ta.** Multi-table odrzucone z powodu „ryzyka regresji porównywarki”. Decyzja „bez LLM
w pętli” podtrzymana, ale jej powód nie jest zapisany: `<DO UZUPEŁNIENIA: dlaczego bez LLM w pętli>`.

**Skutki.**
- (+) Porównywarka bez zmian; dane do Excela zawsze widział człowiek.
- (+) Pozycja bez dopasowania do master data zostaje w Excelu z flagą („nic nie ginie”).
- (−) Każdy nowy dostawca wymaga profilu, czyli pracy operatora w kreatorze.

### D-10 Role zewnętrzne z poziomem 0, zamknięte w portalach

**Decyzja.** `forwarder` (spedytor) i `customs_agent` (agencja celna) celowo nie mają wpisu
w `ROLE_LEVEL` (poziom 0), więc `require_role` blokuje im strony wewnętrzne (`constants.py:86-98`).
Dostęp mają tylko do ścieżek z `FORWARDER_ALLOWED_PREFIXES` / `CUSTOMS_AGENT_ALLOWED_PREFIXES`,
a po logowaniu trafiają do swojego portalu (`EXTERNAL_ROLE_HOME`, `constants.py:149-165`).

**Kontekst.** Firmy zewnętrzne logują się do tej samej aplikacji co pracownicy.

**Rozważane opcje.** `<DO UZUPEŁNIENIA: czy rozważano osobną aplikację albo osobny login dla partnerów>`.

**Dlaczego ta.** Komentarz opisuje mechanizm, nie powód biznesowy:
`<DO UZUPEŁNIENIA: dlaczego portale w tej samej aplikacji>`.

**Skutki.**
- (+) Jedna lista dozwolonych prefiksów zamiast sprawdzania roli w każdej trasie.
- (−) `api_spedycja_update` wpuszcza każdą rolę zewnętrzną, także agencję celną; ogranicza dopiero
  wymóg `forwarder_id` (`app.py:16740-16744`).
- (−) Admin w podglądzie portalu nie ma linku powrotu do aplikacji.

### D-11 Leniwe importy ciężkich bibliotek ML

**Decyzja.** torch, paddleocr, transformers i podobne są importowane wewnątrz funkcji, nie na
początku modułu (CLAUDE.md, „Heavy/ML imports”). Lokalne silniki OCR są domyślnie wyłączone
(`ARTWORK_OCR_LOCAL="0"`, `artwork_comparator.py:127`; Qwen za `DISABLE_QWEN`).

**Kontekst.** PyTorch to ok. 2 GB RAM na worker; Qwen2.5-VL ok. 12 GB (`docs/PLAN_REFAKTORU.md`, CLAUDE.md).

**Rozważane opcje.** Wydzielenie ML do osobnego serwisu `artwork-engine`
(`docs/PLAN_REFAKTORU.md` #2, priorytet średni). Klient już istnieje (`artwork_engine_client.py`,
włączany przez `ARTWORK_ENGINE_URL`).

**Dlaczego ta.** CLAUDE.md: żeby CI i start aplikacji były szybkie, a bramka `compileall`
przechodziła bez zainstalowanych zależności ML.

**Skutki.**
- (+) Testy w CI trwają sekundy; aplikacja startuje bez ML.
- (−) Ścieżki ML/OCR nie są sprawdzane w CI (`.github/workflows/ci.yml:47` instaluje tylko lekkie pakiety).
- (−) Gdy zdalny `artwork-engine` zawiedzie, porównanie liczy się lokalnie bez informacji dla użytkownika
  (`artwork_engine_client.py:61-71`).

### D-12 PDF zamówienia jako wzorzec porównania (zamiast SAP)

**Decyzja.** Weryfikacja PO↔PI porównuje PDF zamówienia z PDF proformy
(`app.py:19254-19258`: `compare_tables` + `compare_enhanced`). Nie ma integracji z SAP;
krok `etd_sap` to tylko etykieta statusu.

**Kontekst.** `docs/PROCES_ZAKUPY_FLOW.md:16-17, 41` zakłada źródło prawdy w kostce SAP BW (live),
„NIE PDF zamówienia (PO mógł się zmienić w ME22N)”.

**Rozważane opcje.** Kostka SAP BW (opis w dokumencie procesu, niezaimplementowana).

**Dlaczego ta.** `<DO UZUPEŁNIENIA: dlaczego PDF PO, a nie SAP; czy SAP jest planowany, czy porzucony>`.

**Skutki.**
- (+) Brak zależności od dostępu do SAP; wystarczą dwa pliki.
- (−) Zmiana zamówienia w SAP po wysłaniu PDF nie zostanie wykryta (ryzyko opisane w dokumencie procesu).

# Backlog — historyjki użytkownika

> [BA] Wersja 0.1 (2026-10-16). Kolejność: pilne poprawki bezpieczeństwa z audytu → błędy bramek procesu →
> higiena inżynierska. Priorytety MoSCoW są propozycją do potwierdzenia przez PO. Historyjki oznaczone
> „decyzja PO” nie spełniają Definition of Ready, dopóki PO nie odpowie (`ZALOZENIA.md`).
> Pełne kryteria Given/When/Then mają historyjki pierwszego sprintu; pozostałe rozpisujemy w kroku 1 procesu.

## Sprint 1 — bezpieczeństwo (Must)

### US-001 · Rola managera na endpointach szablonów PalViz
**Jako** administrator **chcę**, aby analiza i zapis szablonów wykrojników wymagały roli `manager`, **aby** zwykły użytkownik nie zmieniał danych referencyjnych.
Wymaganie: SEC-005. Ryzyko: R-01 (🟠). Typ: security. Dowód: `blueprints/palviz.py:236, 287`.
**Status: zrealizowane w PR #11** (commit `security(palviz)`), czeka na akceptację PO.

```gherkin
Given zalogowany użytkownik z rolą user
When  wysyła POST /api/artwork/templates/analyze lub /api/artwork/templates/save z poprawnym tokenem CSRF
Then  odpowiedź ma status 403 i treść "Brak uprawnień", a żaden szablon nie zostaje zapisany

Given zalogowany użytkownik z rolą manager
When  wysyła te same żądania
Then  działają jak dotychczas

Given repozytorium
When  uruchamiam grep "if not require_role"
Then  nie ma żadnego trafienia (wzorzec zakazany, test strażnik w tests/)
```
[SEC] dodatkowo: wpis `audit_log` przy zapisie szablonu.

### US-002 · Sekrety integracji poza jawnym tekstem
**Jako** administrator **chcę**, aby klucze API (tracking, SMS, Anthropic) były szyfrowane w bazie i nie trafiały do adresów URL, **aby** zrzut bazy lub log proxy nie ujawniał sekretów.
Wymaganie: SEC-009. Ryzyko: R-02. Typ: security. Dowód: `app.py:16005-16013, 17167-17173, 8526-8530, 17234-17238`.

```gherkin
Given klucz zapisany przez UI ustawień
When  odczytuję wiersz tabeli settings bezpośrednio z bazy
Then  wartość jest zaszyfrowana (Fernet, klucz z env SETTINGS_ENC_KEY), a aplikacja odszyfrowuje ją tylko w pamięci

Given wysyłka SMS przez smsapi
When  budowane jest żądanie HTTP
Then  token jest w nagłówku Authorization, nie w query stringu

Given użytkownik z rolą manager
When  próbuje zapisać klucz API
Then  dostaje 403 (zapis kluczy tylko admin)

Given brak SETTINGS_ENC_KEY w produkcji (DATABASE_URL ustawione)
When  aplikacja startuje
Then  start kończy się błędem konfiguracji (fail-closed), a w dev działa z ostrzeżeniem
```
Projekt: ADR-0002 (migracja istniejących wartości, rotacja klucza).

### US-003 · Link resetu hasła tylko z zaufanej domeny
**Jako** użytkownik **chcę**, aby link resetu hasła zawsze prowadził do domeny aplikacji, **aby** nikt nie podstawił obcego adresu przez nagłówek Host.
Wymaganie: SEC-015. Ryzyko: R-03. Typ: security. Dowód: `blueprints/auth.py:303`, `app.py:110`.

```gherkin
Given produkcja (DATABASE_URL ustawione) i brak APP_BASE_URL
When  aplikacja startuje
Then  start kończy się komunikatem o brakującej konfiguracji

Given żądanie resetu z nagłówkiem X-Forwarded-Host: zly.example
When  generowany jest e-mail
Then  link zaczyna się od APP_BASE_URL, a nie od wartości z nagłówka
```

### US-004 · Raport artworku bez właściciela jest niedostępny
**Jako** właściciel raportu artworku **chcę**, aby raport bez przypisanego właściciela nie był widoczny dla innych, **aby** kontrola dostępu była fail-closed.
Wymaganie: SEC-016. Ryzyko: R-04. Typ: security. Dowód: `app.py:7584-7598, 7666-7671, 8090-8097`.

```gherkin
Given raport w cache bez pola _owner_id
When  użytkownik inny niż superuser/admin prosi o raport po identyfikatorze
Then  odpowiedź 403 (lub 404), bez treści raportu

Given raport utworzony przez zadanie asynchroniczne (batch)
When  trafia do cache
Then  ma ustawione _owner_id równe identyfikatorowi zlecającego
```

### US-005 · Skany bezpieczeństwa na każdym PR
**Jako** [SEC] **chcę**, aby bandit, pip-audit, gitleaks i trivy działały na każdym PR i blokowały ustalenia wysokie, a Dependabot pilnował zależności, **aby** nowe ryzyka nie trafiały do `main`.
Wymaganie: SEC-013, NFR-013. Typ: security. **Status: dostarczone w PR #11** (`security.yml`, `dependabot.yml`, `.trivyignore`, `pre-commit`).

```gherkin
Given PR z nowym ustaleniem Bandit o wadze MEDIUM lub wyższej
When  uruchamia się security.yml
Then  job bandit kończy się błędem i PR nie może być scalony

Given PR z zależnością produkcyjną mającą znaną podatność
When  uruchamia się pip-audit na requirements-prod.txt
Then  job kończy się błędem

Given commit zawierający sekret (np. klucz API)
When  uruchamia się gitleaks (pre-commit lub CI)
Then  commit/PR jest odrzucony
```

## Sprint 2 — bezpieczeństwo (Should)

| ID | Historyjka | Wymaganie | Ryzyko | Decyzja PO |
|---|---|---|---|---|
| US-006 | Jako operator chcę limitu wywołań na ciężkich endpointach AI/upload (22 trasy) i jednego klienta Claude, który bramkuje budżetem i rejestruje koszt każdego wywołania (także `table_extractor`, `scan_extractor`). | SEC-017, NFR-009, NFR-010 | R-06 | nie |
| US-007 | Jako administrator danych chcę inwentarza danych osobowych, zadania retencji dla `audit_log` i powiadomień oraz pseudonimizacji po usunięciu konta, aby spełnić RODO. | SEC-011, NFR-018 | R-09 | tak (okresy — Z-06) |
| US-025 | Jako [SEC] chcę CSP z nonce (bez `unsafe-inline`/`unsafe-eval`), zasobów CDN z przypiętą wersją i SRI oraz jednego `escHtml`, aby CSP realnie chroniło przed XSS. | SEC-008 | R-05 | nie |
| US-026 | Jako [SEC] chcę, aby `ai_learning.py` delimitował i sanityzował treść PDF tak samo jak `ai_validator`, aby spreparowany dokument nie sterował sugestiami profilu. | SEC-012 | R-08 | nie |
| US-027 | Jako użytkownik chcę generycznych komunikatów 500 w PalViz, odpowiedzi `/api/ai/status` bez prefiksu klucza, escape formuł w eksporcie CSV materiałów i wylogowania przez POST. | SEC-010 | R-10 | nie |

## Błędy i luki procesu dostawy

| ID | Historyjka | Wymaganie | MoSCoW | Typ | Decyzja PO |
|---|---|---|---|---|---|
| US-008 | Jako manager chcę, aby `advance`, `set-status` i `confirm-departure` wywoływały te same hooki co `_set_dostawa_status`, aby dostawa sama trafiała do kolejki transportowej i rejestru przyjęć. | FR-041 | Must | bug | tak (temat 4) |
| US-009 | Jako właściciel procesu chcę, aby twardych bramek nie dało się ominąć inną trasą (proforma→dalej bez porównania, `confirm-departure` z `artwork_bledne`, `set-status` bez checklisty, `GET` zmieniający status), aby kontrola była skuteczna i audytowana. | FR-040 | Must | bug | tak (temat 3, Z-03) |
| US-010 | Jako specjalista chcę nadać zgodę na wypłynięcie w aplikacji (kto, kiedy, notatka), aby zlecenie spedycyjne dało się wygenerować. | FR-042 | Must | feature | tak (temat 2) |
| US-011 | Jako kupiec chcę porównania cen z walutą na pozycji i jednej domyślnej tolerancji (0 zamiast 0/0,5 zależnie od ścieżki), aby 100 EUR vs 100 USD nie było „ok”. | FR-006, FR-012 | Must | bug | częściowo (tolerancja domyślna) |
| US-012 | Jako kierownik zakupów chcę decyzji: SAP (odczyt) czy PDF PO jako wzorzec, aby plan rozwoju był jednoznaczny. | — | Must | decyzja | tak (temat 1, Z-01) |
| US-013 | Jako manager chcę przekazać zlecenie do portalu spedytora/agencji z karty dostawy (`sent_to_forwarder_at`, `sent_to_agency_at`), aby portale pokazywały realne zlecenia. | FR-043 | Should | feature | tak |
| US-014 | Jako manager chcę alertów e-mail/in-app po przekroczeniu SLA i dla reguł `alert_engine` (albo usunięcia opisu z dokumentacji), aby nie sprawdzać listy ręcznie. | FR-029, FR-056 | Should | feature | tak (temat 6) |
| US-015 | Jako księgowość chcę blokady rozliczenia przy rozbieżności > tolerancja i zapisu numeru MIR7, aby domknąć pętlę wartości. | FR-044 | Should | feature | tak (temat 5) |

## Proces i inżynieria

| ID | Historyjka | Wymaganie | MoSCoW | Typ | Status / decyzja |
|---|---|---|---|---|---|
| US-016 | Jako zespół chcę `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, szablonów issue/PR i CODEOWNERS, aby proces był widoczny w repo. | — | Must | proces | **dostarczone w PR #11** |
| US-017 | Jako zespół chcę lintu w CI (zapadka), raportu pokrycia i listy pominiętych testów, aby jakość była mierzona przy każdym PR. | NFR-013, NFR-023 | Must | chore | **dostarczone w PR #11** |
| US-018 | Jako zespół chcę jednego źródła schematu bazy (`migrate_db.py`) i wyłączenia `init_db()` z importu, aby SQLite i PostgreSQL nie dryfowały. | NFR-024 | Should | refactor | nie |
| US-019 | Jako zespół chcę spłaty długu lint (F841 41, F541 31, F601 17 w `translation_en.py` — zduplikowane klucze nadpisują tłumaczenia, F811 1) i zacieśnienia zapadki ruff, aby bramka obejmowała pełną konfigurację. | NFR-013 | Should | chore | nie |
| US-020 | Jako zespół chcę, aby wątki sprzątania/backupu i semafor były sterowane env, a cache/limity per proces przeniesione do bazy lub Redis, aby 2 workery gunicorna dawały spójne wyniki. | NFR-025 | Should | refactor | nie |
| US-021 | Jako zespół chcę usunąć martwy kod (`alert_engine.py`, `yolo_detector.py`, 5 szablonów, `/kolejka`) i poprawić nieaktualne dokumenty (`AGENTS.md`, `CLAUDE.md`, `README.txt`), aby nowa osoba nie była wprowadzana w błąd. | — | Could | chore | tak (Z-09) |
| US-022 | Jako zespół chcę przypiętych zależności (lock z hashami), obrazu nie-root, digestu obrazu bazowego i blokującego skanu obrazu, aby łańcuch dostaw był odtwarzalny. | SEC-014 | Should | chore | nie |
| US-023 | Jako zespół chcę testów dla 25 wymagań bez testu, zaczynając od bramek steppera (FR-017…026) i eksportów (FR-013/014), aby kontrole o największym skutku były chronione przed regresją. | NFR-023 | Should | test | nie |
| US-024 | Jako zespół chcę `pymupdf` i `trimesh` w lekkim zestawie CI, aby 12 pomijanych testów artworku wykonywało się w CI. | NFR-023 | Could | chore | nie |

## Zasady utrzymania backlogu

- Nowa historyjka = issue z szablonu `user_story` + wiersz tutaj + wiersz w `SLEDZENIE.md`.
- Historyjka wchodzi do sprintu tylko po Definition of Ready (`CONTRIBUTING.md` §3).
- Zamknięcie historyjki = PR scalony po akceptacji PO + wpis w `CHANGELOG.md`.

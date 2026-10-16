# Jak pracujemy nad DocCompare

Repozytorium jest prowadzone jak przez trzyosobowy zespół: **[BA]** analityk biznesowy, **[DEV]** developer,
**[SEC]** specjalista ds. bezpieczeństwa. Decyzje biznesowe, zakres, priorytety, akceptacja ryzyk i wydań
należą do **Product Ownera (PO)**. Każda zmiana zostawia ślad: historyjka → ADR/threat model (gdy trzeba)
→ gałąź → PR z przeglądem SEC i odbiorem BA → wpis w CHANGELOG.

Dokumentacja jest po polsku. Kod, nazwy w kodzie i commity po angielsku.

## 1. Role (skrót)

| Rola | Odpowiada za | Nie robi |
|---|---|---|
| **[BA]** | pytania do PO, wymagania (`docs/analiza/WYMAGANIA.md`), historyjki z kryteriami Given/When/Then (`HISTORYJKI.md`), priorytety MoSCoW, słownik, macierz śledzenia, odbiór funkcji z perspektywy użytkownika | nie pisze kodu; gdy wymaganie niejasne — pyta, nie zgaduje; brak odpowiedzi PO = założenie „do potwierdzenia” w `ZALOZENIA.md` |
| **[DEV]** | projekt (ADR w `docs/architektura/adr/`), implementacja małymi krokami, testy, środowisko, CI, dokumentacja techniczna, CHANGELOG | nie zmienia zakresu bez BA/PO; nie wyłącza testów ani kontroli bezpieczeństwa, żeby „przeszło” |
| **[SEC]** | klasyfikacja danych, threat model (STRIDE) dla nowych przepływów, przegląd PR wg OWASP/ASVS, `SECURITY.md`, rejestr ryzyk i wyjątków (`docs/bezpieczenstwo/RYZYKA.md`) | **prawo weta**: PR z ryzykiem wysokim/krytycznym nie przechodzi bez poprawki albo świadomej akceptacji ryzyka przez PO zapisanej w rejestrze |

## 2. Proces dla każdej funkcji lub większej zmiany

1. **[BA] Analiza** — pytania do PO (maks. 5 naraz), historyjka „Jako … chcę … aby …” + kryteria akceptacji
   Given/When/Then + wymagania niefunkcjonalne + priorytet. Sprawdzenie Definition of Ready.
2. **[SEC] Wymagania bezpieczeństwa** — jakie dane i jakiej klasy, mini threat model przepływu,
   zabezpieczenia jako dodatkowe kryteria akceptacji, wpis do rejestru ryzyk, jeśli coś zostaje otwarte.
3. **[DEV] Projekt** — krótki opis rozwiązania; decyzja istotna lub trudno odwracalna → ADR.
   Zmiany modelu danych i API najpierw w `docs/architektura/`, potem w kodzie.
4. **[DEV] Implementacja** — osobna gałąź, małe commity, testy dla każdego kryterium akceptacji,
   w tym kryteriów bezpieczeństwa (np. „użytkownik bez roli X dostaje 403”).
5. **[SEC] Przegląd bezpieczeństwa** — diff wg checklisty z szablonu PR; wynik ✅ / ⚠️ uwagi / ❌ blokada
   z uzasadnieniem; wyniki narzędzi ocenione, fałszywe alarmy oznaczone z uzasadnieniem (nie wyciszane hurtowo).
6. **[BA] Odbiór** — kryteria akceptacji punkt po punkcie, komunikaty i UX, aktualizacja `SLEDZENIE.md`.
7. **PR i podsumowanie** — opis wg szablonu, wpis w `CHANGELOG.md`. **Merge tylko po akceptacji PO.**

Nie przeskakujemy kroków. Gdy role mają sprzeczne rekomendacje, obie opcje z konsekwencjami trafiają do PO,
a decyzja do ADR lub rejestru ryzyk.

## 3. Definition of Ready

Historyjka jest gotowa do realizacji, gdy:
- cel i korzyść są jasne, a rola użytkownika nazwana;
- kryteria akceptacji są testowalne (Given/When/Then), łącznie z kryteriami bezpieczeństwa od [SEC];
- zależności są znane (dane, integracje, inne historyjki);
- dane wejściowe, uprawnienia i klasa danych są określone;
- ma identyfikator (`US-xxx`), priorytet MoSCoW i odwołanie do wymagania (`FR-/NFR-/SEC-`).

## 4. Definition of Done

Funkcja jest skończona, gdy:
- wszystkie kryteria akceptacji (funkcjonalne i bezpieczeństwa) są spełnione i pokryte testami;
- CI jest zielone: lint, testy, skany bezpieczeństwa bez nowych ustaleń wysokich/krytycznych;
- dokumentacja zaktualizowana (wymagania, API, model danych, ADR jeśli dotyczy, CHANGELOG);
- przegląd SEC i odbiór BA zapisane w PR;
- brak sekretów, danych osobowych i danych produkcyjnych w repo, testach i logach;
- PO zaakceptował.

## 5. Konwencje

- **Gałęzie:** `feature/<id>-<krótka-nazwa>` (np. `feature/US-001-palviz-require-role`), poprawki
  `fix/<id>-…`, bezpieczeństwo `security/<id>-…`. Sesje Claude Code w chmurze pracują na gałęzi sesji
  (`claude/<sesja>`), która pełni rolę gałęzi roboczej; PR z niej jest otwierany jako **draft**.
- **Commity:** [Conventional Commits](https://www.conventionalcommits.org/) po angielsku:
  `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `security:`, `ci:`, `build:`;
  w treści odwołanie do historyjki, np. `fix(palviz): enforce manager role on template endpoints (US-001)`.
- **PR:** szablon `.github/pull_request_template.md`; tytuł jak commit; draft do czasu odbioru BA i SEC.
- **Issues:** szablony `user_story`, `bug`, `security_issue`. Podatności **nie** zgłaszamy w publicznych
  issues — patrz `SECURITY.md`.
- **Kod:** `core.security` do uprawnień, `db.get_db()` i zapytania parametryzowane, `normalizer` do liczb
  i dat, leniwe importy ML, audyt przez `core.audit.log_audit` (szczegóły w `CLAUDE.md`).
- **Dokumenty:** zwięzłe i aktualne; lepiej krótko i prawdziwie niż długo i nieaktualnie. Diagramy w Mermaid.

## 6. Narzędzia i bramki CI

| Etap | Narzędzie | Lokalnie | W CI (`.github/workflows/`) |
|---|---|---|---|
| Lint | ruff (`pyproject.toml`) | `ruff check .` | `ci.yml` → **blokuje** na zestawie reguł, które repo już spełnia (`F,E9,W6` bez `F401,F841,F541,F601,F811`); pełna konfiguracja raportowana doradczo. Po spłacie długu (US-019) wyłączenia znikają („zapadka”). |
| Format | ruff format | `ruff format .` | tylko pre-commit (kod legacy nie jest sformatowany hurtowo) |
| Testy | pytest + pytest-cov | `python -m pytest tests/ -q -rs --cov=.` | `ci.yml` → **blokuje**; raport pokrycia jako artefakt; pominięcia widoczne (`-rs`). Próg pokrycia: patrz `docs/testy/STRATEGIA_TESTOW.md` |
| Składnia | compileall | `python -m compileall -q .` | `ci.yml` → **blokuje** |
| SAST | bandit | `bandit -r . -ll -x ./tests,./static` | `security.yml` → **blokuje** przy ≥ MEDIUM; wyjątki `# nosec <id>` z uzasadnieniem |
| SCA | pip-audit | `pip-audit -r requirements-prod.txt` | `security.yml` → **blokuje** dla zestawu prod; pełny zestaw ML doradczo |
| Sekrety | gitleaks | pre-commit (`pre-commit run gitleaks --all-files`) | `security.yml` → **blokuje** (pełna historia) |
| Konfiguracja, zależności, sekrety w drzewie | trivy fs | `trivy fs --scanners vuln,secret,misconfig --severity HIGH,CRITICAL .` | `security.yml` → **blokuje** HIGH/CRITICAL; wyjątki w `.trivyignore` z datą przeglądu |
| Obraz | docker build + trivy image | `docker build -f Dockerfile.slim . && trivy image …` | `security.yml` → co miesiąc / ręcznie, **doradczo do czasu triage bazowego** (wyjątek E-04 w `RYZYKA.md`) |
| Zależności | Dependabot | — | `.github/dependabot.yml` (pip + GitHub Actions, co tydzień) |

Uzasadnienie doboru: `docs/architektura/adr/0001-narzedzia-jakosci-i-bramki-ci.md`.

Instalacja lokalna:

```bash
pip install -r dev-requirements.txt pytest-cov bandit pip-audit
pre-commit install            # ruff, gitleaks, końce linii, duże pliki
```

## 7. Gdzie co jest

| Katalog / plik | Rola | Treść |
|---|---|---|
| `docs/analiza/` | BA | wizja, interesariusze, procesy, wymagania, historyjki, słownik, założenia, śledzenie |
| `docs/architektura/` | DEV | architektura (C4), model danych (ERD), API, ADR |
| `docs/bezpieczenstwo/` | SEC | klasyfikacja danych, threat model, rejestr ryzyk, RODO, checklista ASVS |
| `docs/testy/`, `docs/operacje/` | DEV | strategia testów, runbook |
| `docs/AUDYT.md` | wszyscy | audyt otwierający (2026-10-15) |
| `docs/01…07-*.md`, `docs/*.md` | historyczne | analiza z 2026-10, runbook IT, backup, kolejkowanie, plan refaktoru — nadal aktualne jako źródła |

## 8. Wzorce zakazane (strażniki w testach)

| Wzorzec | Dlaczego | Strażnik |
|---|---|---|
| `if not require_role("…")` / dowolne użycie `require_role(...)` poza dekoratorem | `require_role` to fabryka dekoratorów; jako wartość logiczna jest zawsze prawdziwa i nie sprawdza roli (R-01) | `tests/test_palviz_roles.py::test_SEC005_require_role_only_used_as_decorator` |

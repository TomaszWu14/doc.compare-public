# ADR-0001: Narzędzia jakości i bramki CI

- **Status:** zaakceptowane przez zespół, do potwierdzenia przez PO (progi pokrycia — Z-08, zapadki — Z-14)
- **Data:** 2026-10-16
- **Role:** [DEV] propozycja, [SEC] wymagania skanów, [BA] kryteria widoczności
- **Historyjki:** US-005, US-017; dług: US-019, US-022, US-024

## Kontekst

Przed PR #11 bramką CI było tylko `compileall` + `pytest` (`ci.yml`), a skany bezpieczeństwa działały raz w miesiącu
i doradczo (`security.yml`). Ruff był skonfigurowany, ale nigdzie nie uruchamiany; repo ma 90 ustaleń lint
(F841/F541/F601/F811), 251 bloków `except: pass`, 0 przypiętych wersji, kontener jako root i 35% pokrycia testami
(`docs/AUDYT.md` §3). Prompt zespołu wymaga: lint → testy → SAST → SCA → skan sekretów → build obrazu → skan obrazu,
z blokadą na ustaleniach wysokiej wagi, bez wyłączania kontroli „żeby przeszło”.

Ograniczenia: (1) bramka blokująca od pierwszego dnia na pełnej konfiguracji ruff zablokowałaby każdy PR;
(2) pełny obraz ML ma kilka GB i buduje się 7–8 min — nie nadaje się na każdy PR; (3) kontener root wymaga
sprawdzenia uprawnień wolumenu `/data` przed zmianą; (4) część testów pomija się cicho przy braku zależności
(136 `importorskip`).

## Rozważane opcje

| Opcja | Za | Przeciw |
|---|---|---|
| A. Wszystko blokujące od razu | zgodne z literą wymagania | CI czerwone na każdym PR do czasu spłaty długu; presja na wyłączanie reguł |
| B. Wszystko doradcze, zaostrzać później | zero tarcia | „później” nie nadchodzi; nie spełnia wymagania blokady HIGH |
| **C. Zapadka (ratchet)** — blokada na wszystkim, co repo już spełnia; dług jawnie wyłączony z historyjką i datą; każde zaostrzenie tylko w jedną stronę | uczciwe wobec stanu kodu, nie luzuje nic względem dziś, spełnia blokadę HIGH tam, gdzie to możliwe od razu | wymaga dyscypliny przy spłacie długu (rejestr wyjątków) |

## Decyzja

Opcja **C**:

| Etap | Narzędzie | Tryb | Uzasadnienie wyboru |
|---|---|---|---|
| Lint | **ruff** 0.16.8 (pin w CI) | blokuje `F,E9,W6` bez `F401,F841,F541,F601,F811`; pełna konfiguracja doradczo | jedyny linter już w repo; szybki; `F` = realne błędy. Wyłączone reguły mają dług w US-019 |
| Testy | **pytest + pytest-cov** | blokuje; `-rs` pokazuje pominięcia; raport XML jako artefakt | pokrycie jest mierzone, próg per moduł w `STRATEGIA_TESTOW.md` (zapadka), a nie globalny próg od razu (Z-08) |
| SAST | **bandit** `-ll` | blokuje ≥ MEDIUM | już w repo, baza czysta po adnotacjach w `tools/generate_voiceover.py`; `# nosec` tylko z uzasadnieniem |
| SCA | **pip-audit** | blokuje dla `requirements-prod.txt`; pełny zestaw ML doradczo | zestaw prod to to, co trafia do obrazu; zestaw ML nie rozwiązuje się na każdym runnerze |
| Sekrety | **gitleaks** | blokuje (CI, pełna historia) + pre-commit | skanuje też stare commity; repo publiczne |
| Konfiguracja/zależności/sekrety w drzewie | **trivy fs** | blokuje HIGH/CRITICAL z poprawką; wyjątki `.trivyignore` z datą | jedno narzędzie do misconfig Dockerfile i IaC; root w Dockerfile = wyjątek E-01 do US-022 |
| Obraz | **docker build + trivy image** | co miesiąc / ręcznie, doradczo do triage'u bazowego (E-04) | obraz bazowy ML za ciężki na każdy PR; baseline CVE OS/ML wymaga przeglądu zanim zablokuje |
| Zależności | **Dependabot** | pip + GitHub Actions co tydzień | darmowy, natywny; lock z hashami w US-022 |
| Pre-commit | ruff, ruff-format, gitleaks, końce linii, duże pliki, YAML, klucze prywatne | lokalnie | zatrzymuje sekret przed commitem |

Nie wprowadzamy teraz: **mypy** (8% anotacji w `app.py` — gradual typing w osobnym ADR), **semgrep** (do rozważenia po
stabilizacji bandita; reguły OWASP dla Flask — kandydat na ADR-0003), **globalnego progu pokrycia**.

## Konsekwencje

- (+) Każdy PR dostaje lint, testy, SAST, SCA, skan sekretów i konfiguracji; ustalenia HIGH blokują.
- (+) Nic nie jest luźniejsze niż przed PR #11; wyjątki są jawne (`RYZYKA.md` sekcja „Wyjątki”, `.trivyignore`, `# nosec`).
- (−) Dwie zapadki do zacieśnienia: ruff (US-019) i trivy image (US-022); daty przeglądu 2026-11-30.
- (−) `security.yml` na każdym PR zużywa minuty Actions (ok. 3–5 min/PR); akceptowalne dla repo publicznego.
- (−) `deploy.yml` zależy od nazwy workflow „CI — testy jednostkowe” — nazwa pozostaje; nowy job `lint` też blokuje deploy.

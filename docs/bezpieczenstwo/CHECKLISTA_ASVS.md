# Checklista OWASP ASVS

> [SEC] Wersja 0.1. Poziom docelowy: **ASVS 4.0 L1 jako baza, L2 dla V2 (uwierzytelnianie), V3 (sesje), V4 (kontrola
> dostępu)** — założenie Z-12. Status: ✅ spełnione · ⚠️ częściowo · ❌ brak · ➖ nie dotyczy. Dowody w `docs/AUDYT.md` §4.

| Rozdział | Wymaganie (skrót) | Poziom | Status | Dowód / luka | Historyjka |
|---|---|---|---|---|---|
| V1 Architektura | threat model dla przepływów, klasyfikacja danych | L2 | ⚠️ | `THREAT_MODEL.md` 0.1, `KLASYFIKACJA_DANYCH.md` 0.1 | aktualizować per funkcja |
| V1.14 | separacja komponentów, zależności zarządzane | L2 | ⚠️ | brak locka, Dependabot od PR #11 | US-022 |
| V2.1 | hasła ≥ 12 znaków (L1: ≥ 8 po zmianie 4.0.3?), bez limitu górnego < 64 | L1 | ⚠️ | ≥ 8, ≤ 1000; cyfra przy zmianie w profilu | decyzja PO |
| V2.2 | ochrona przed automatyzacją (limit, opóźnienia) | L1 | ✅ | 5/15 min/IP, atrapa hasha | — |
| V2.4 | hashowanie haseł (bcrypt/argon2/pbkdf2 z parametrami) | L1 | ⚠️ | pbkdf2:sha256 (werkzeug, 600k iteracji w nowszych wersjach) | E-07 |
| V2.5 | reset hasła: tokeny losowe, jednorazowe, ograniczone czasowo | L1 | ✅ | 24 h, atomowe użycie, unieważnianie starych | — |
| V2.5.x | link resetu z zaufanej domeny | L1 | ❌ | `request.host_url` fallback | US-003 |
| V2.8 | 2FA | L2 | ❌ | brak | decyzja PO (SEC-004) |
| V3.2 | nowa sesja po logowaniu, losowy identyfikator | L1 | ✅ | `session.clear()`, podpis Flask | — |
| V3.3 | wylogowanie unieważnia sesję; bezczynność/limit absolutny | L1 | ⚠️ | 8 h absolutne; logout przez GET | US-028 |
| V3.4 | atrybuty ciasteczek Secure, HttpOnly, SameSite | L1 | ✅ | `app.py:197-199` | — |
| V3.5 | tokeny API: losowe, porównanie stałoczasowe | L2 | ✅ | `require_api_key`, intake, biblioteka | — |
| V4.1 | kontrola dostępu po stronie serwera, deny by default | L1 | ⚠️ | opt-in per trasa (brak deny by default); błąd PalViz naprawiony w US-001, strażnik statyczny w testach | checklista PR |
| V4.1.3 | zasada najmniejszych uprawnień | L1 | ⚠️ | manager zapisuje klucze API | US-002 |
| V4.2 | kontrola na poziomie obiektu (IDOR) | L1 | ⚠️ | 12 tras OK; cache artworków fail-closed od US-004; joby faktur bez właściciela (z założenia) | — |
| V4.2.2 | CSRF | L1 | ✅ | token per sesja, wszystkie sesyjne zapisy | — |
| V4.3 | ochrona panelu admina | L1 | ✅ | `require_role("admin")`, brak 2FA (L2) | — |
| V5.1 | walidacja wejścia (allow-list, długości) | L1 | ⚠️ | Pydantic w auth/suppliers/warehouse; reszta ręcznie | stopniowo |
| V5.2 | sanityzacja (HTML, SQL, LDAP, OS, prompty LLM) | L1 | ✅ | brak `\|safe`, parametryzowane SQL, brak `shell=True`; treść dokumentów w promptach przez `core.prompt_safety` (US-026) | — |
| V5.3 | kodowanie wyjścia, CSP | L1 | ⚠️ | Jinja autoescape; CSP `unsafe-inline` | US-025 |
| V5.5 | bezpieczne deserializowanie | L1 | ✅ | brak pickle/yaml.load | — |
| V6 Kryptografia | sekrety w env, losowość CSPRNG | L1 | ⚠️ | `secrets.*` tak; klucze w `settings` jawnym tekstem | US-002 |
| V7.1 | logi bez sekretów i PII poza potrzebą | L1 | ⚠️ | brak sekretów; IP + nazwa w każdym wpisie | US-007 |
| V7.2 | zdarzenia bezpieczeństwa logowane (login, dostęp odrzucony) | L1 | ✅ | `audit_log`, logger dla CSRF/401 | — |
| V7.4 | obsługa błędów bez wycieku szczegółów | L1 | ✅ | generyczny 500; PalViz z identyfikatorem błędu (US-027); 3× `str(ValueError)` to komunikaty walidacji dla użytkownika — przejrzane, bez zmian | — |
| V8.1 | ochrona danych wrażliwych w cache i backupach | L1 | ⚠️ | `no-store` dla HTML; backup bez szyfrowania (do potwierdzenia) | RUNBOOK |
| V8.3 | retencja i usuwanie danych osobowych | L1 | ❌ | brak retencji | US-007 |
| V9 Komunikacja | TLS, HSTS | L1 | ✅ | HSTS przy HTTPS; TLS terminuje Coolify/Traefik | — |
| V10 Złośliwy kod | integralność zależności (lock/hash), SRI | L2 | ❌ | brak locka, brak SRI | US-022, US-025 |
| V11 Logika biznesowa | sekwencja kroków, limity, brak obejść | L1 | ⚠️ | stepper z bramkami; znane obejścia | US-008, US-009 |
| V12.1 | upload: rozmiar, typ, walidacja | L1 | ⚠️ | `validate_pdf_upload` nie wszędzie | checklista PR |
| V12.3 | pobieranie plików bez traversal | L1 | ✅ | `send_from_directory`, prefiks uid | — |
| V12.5 | pliki serwowane z poprawnym typem, poza katalogiem publicznym | L1 | ✅ | `/data/uploads` | — |
| V13.1 | API: uwierzytelnienie, autoryzacja, CSRF dla sesyjnych | L1 | ✅ | enumeracja 408 tras | — |
| V13.2 | REST: walidacja JSON, limity | L1 | ⚠️ | limit na 12 trasach | US-006 |
| V14.1 | build odtwarzalny, bez zbędnych komponentów, nie-root | L2 | ❌ | root, brak pinów | US-022 (E-01) |
| V14.2 | zależności aktualne, skanowane | L1 | ✅ | pip-audit, trivy, Dependabot (PR #11) | — |
| V14.3 | brak debug/tracebacków w produkcji | L1 | ✅ | `app.py` debug tylko lokalnie; PalViz bez tracebacku od US-027 | — |
| V14.4 | nagłówki HTTP bezpieczeństwa | L1 | ✅ | CSP, HSTS, nosniff, Referrer-Policy, Permissions-Policy, `X-Frame-Options` | — |
| V14.5 | walidacja nagłówka Host / origin | L1 | ⚠️ | `ProxyFix(x_host)` bez listy dozwolonych hostów | US-003 |

Podsumowanie: L1 ✅ 17 · ⚠️ 17 · ❌ 5 (po Sprincie 1 i 2: ❌ → 1, ⚠️ → 9 — prognoza).

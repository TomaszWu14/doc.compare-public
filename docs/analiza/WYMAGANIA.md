# Wymagania — rejestr (wersja 0.1)

> [BA] 2026-10-16. Rejestr identyfikatorów. Szczegółowe kryteria akceptacji, miejsca w kodzie i testy dla FR-001…039
> i NFR-001…013 są w `docs/05-wymagania.md` (aliasy WF-xx / WN-xx zachowane, żeby nie psuć odwołań).
> Nowe pozycje (FR-040+, NFR-014+, SEC-xxx) pochodzą z `docs/AUDYT.md`; ich kryteria powstaną w historyjkach.
>
> Status: ✅ zaimplementowane · ⚠️ częściowo · ❌ brak. Test: ✅ jest · ⚠️ częściowy · — brak.
> Priorytet MoSCoW jest propozycją BA do potwierdzenia przez PO.

## 1. Wymagania funkcjonalne

### 1.1 Porównanie dokumentów

| ID | Alias | Wymaganie (skrót) | Status | Test | MoSCoW |
|---|---|---|---|---|---|
| FR-001 | WF-01 | Porównanie dwóch dokumentów handlowych z zapisem wyniku | ✅ | — | Must |
| FR-002 | WF-02 | Brak ponownego liczenia tego samego porównania (SHA-256) | ✅ | — | Should |
| FR-003 | WF-03 | Liczby EN/UE rozpoznawane jednakowo | ✅ | ✅ | Must |
| FR-004 | WF-04 | Dopasowanie pozycji mimo różnych zapisów REF | ✅ | ⚠️ | Must |
| FR-005 | WF-05 | Ilość zgodna co do sztuki (tolerancja 0) | ✅ | — | Must |
| FR-006 | WF-06 | Cena z tolerancją z profilu dostawcy | ✅ | ⚠️ | Must |
| FR-007 | WF-07 | Klasyfikacja różnicy ceny wg wielkości | ✅ | — | Should |
| FR-008 | WF-08 | Przeliczanie jednostek miary przed porównaniem | ✅ | ✅ | Should |
| FR-009 | WF-09 | Weryfikacja arytmetyki i sumy dokumentu | ✅ | ✅ | Must |
| FR-010 | WF-10 | Semantyczne porównanie warunków płatności | ✅ | ⚠️ | Should |
| FR-011 | WF-11 | Wykrywanie pomyłek I/1 i O/0 | ✅ | ✅ | Should |
| FR-012 | WF-12 | Jeden poziom ryzyka porównania | ✅ | — | Must |
| FR-013 | WF-13 | Manager zatwierdza lub odrzuca wynik | ✅ | — | Must |
| FR-014 | WF-14 | Eksport wyniku do PDF i Excel (escape formuł) | ✅ | — | Should |
| FR-015 | WF-15 | Audyt kodu CN względem SAD | ✅ | ✅ | Should |
| FR-016 | WF-16 | Walidacja formatu kodu CN | ✅ | ✅ | Should |

### 1.2 Proces dostawy

| ID | Alias | Wymaganie (skrót) | Status | Test | MoSCoW |
|---|---|---|---|---|---|
| FR-017 | WF-17 | Manager zakłada dostawę dla numeru PO | ✅ | — | Must |
| FR-018 | WF-18 | Dokument z innym numerem PO nie jest przypinany | ✅ | — | Must |
| FR-019 | WF-19 | Wynik PO↔PI i artworku ustawia status dostawy | ✅ | ✅ | Must |
| FR-020 | WF-20 | Negatywny wynik blokuje `advance` | ✅ | — | Must |
| FR-021 | WF-21 | Nadpisanie negatywnego wyniku wymaga uzasadnienia | ✅ | — | Must |
| FR-022 | WF-22 | Brak wymaganych dokumentów wymaga potwierdzenia | ✅ | ✅ | Should |
| FR-023 | WF-23 | Równoległe zmiany statusu nie nadpisują się; log zmian | ✅ | — | Must |
| FR-024 | WF-24 | Upload packing listy przesuwa dostawę | ✅ | ✅ | Should |
| FR-025 | WF-25 | Oznaczenie przekroczonego SLA | ✅ | — | Should |
| FR-026 | WF-26 | Potwierdzenie wypłynięcia wymaga ETD | ✅ | — | Must |
| FR-040 | — | Bramki nieomijalne inną trasą (`advance`, `confirm-departure`, `set-status`, `GET`) | ❌ | — | Must (Z-03) |
| FR-041 | — | Hooki kolejki transportowej i przyjęcia magazynowego z każdej ścieżki zmiany statusu | ❌ | — | Must |
| FR-042 | — | Zgoda na wypłynięcie nadawana w systemie (kto, kiedy) | ❌ | — | Must (decyzja PO) |
| FR-043 | — | Przekazanie zlecenia do portalu spedytora/agencji z karty dostawy | ❌ | — | Should |
| FR-044 | — | Bramka rozliczenia przy rozbieżności > tolerancja; zapis numeru MIR7 | ❌ | — | Should (decyzja PO) |

### 1.3 Odprawa, transport, portale

| ID | Alias | Wymaganie (skrót) | Status | Test | MoSCoW |
|---|---|---|---|---|---|
| FR-027 | WF-27 | Wysyłka do odprawy tylko z zatwierdzoną checklistą | ✅ | ✅ | Must |
| FR-028 | WF-28 | Ocena ryzyka demurrage/detention | ✅ | ✅ | Should |
| FR-029 | WF-29 | Alert postojowy dla managerów | ✅ | — | Should |
| FR-035 | WF-35 | Dostęp zależny od hierarchii ról | ✅ | ✅ | Must |
| FR-036 | WF-36 | Role zewnętrzne widzą tylko swój portal | ✅ | ✅ | Must |
| FR-037 | WF-37 | Spedytor obsługuje tylko przekazane zlecenia | ✅ | ⚠️ | Must |
| FR-038 | WF-38 | Agencja zmienia tylko status odprawy swoich zleceń | ✅ | — | Must |
| FR-039 | WF-39 | User i manager widzą tylko dostawy swojego działu | ✅ | — | Must |
| FR-045 | — | Tracking kontenerów (dostawcy, auto-odświeżanie, mapa), ustawienia demurrage | ✅ | — | Should |
| FR-046 | — | SMS do kierowcy i strona potwierdzenia z tokenem | ✅ | — | Could |
| FR-047 | — | Generowanie zlecenia spedycyjnego i API zleceń transportowych (dziś zawsze 409) | ⚠️ | ✅ | Should |
| FR-048 | — | Kompletowanie zestawu celnego i stemplowanie PDF numerem MIR7 | ✅ | ✅ | Should |

### 1.4 Artwork, faktury, AI, dane

| ID | Alias | Wymaganie (skrót) | Status | Test | MoSCoW |
|---|---|---|---|---|---|
| FR-030 | WF-30 | Walidacja EAN-13/EAN-8 sumą kontrolną GS1 | ✅ | ✅ | Must |
| FR-031 | WF-31 | Parsowanie GS1-128 i kontrola UDI | ✅ | ✅ | Must |
| FR-032 | WF-32 | Dobór modelu AI do trudności przypadku | ✅ | ✅ | Could |
| FR-033 | WF-33 | AI może tylko podnieść poziom ryzyka | ✅ | — | Must |
| FR-034 | WF-34 | Sugestie AI nigdy nie są stosowane automatycznie | ✅ | — | Must |
| FR-049 | — | Faktury → Excel: upload + podział CIPL; `ambiguous` blokuje; Excel zbiorczy; Draft SAD | ✅ | ✅ | Should |
| FR-050 | — | Porównanie wizualne artworku (ΔE 7,0 tekst / 18,0 grafika, klasy critical/important) | ✅ | ⚠️ | Should |
| FR-051 | — | Raport artworku PDF/DOCX/HTML, batch ≤ 50 par, strefy | ✅ | ⚠️ | Should |
| FR-052 | — | Model 3D z wykrojnika, PalViz, szablony wykrojników | ✅ | ⚠️ | Could |
| FR-053 | — | Indeks biblioteki wzorców, aliasy, grupy, rewizje, intake z tokenem | ✅ | ✅ | Should |
| FR-054 | — | Import i edycja master data (materiały, dostawcy, stany magazynowe) | ✅ | ✅ | Should |
| FR-055 | — | Kreator profilu dostawcy | ✅ | ⚠️ | Should |
| FR-056 | — | Centrum powiadomień in-app i e-mail do managerów | ✅ | — | Should |
| FR-057 | — | Słowniki: tłumaczeń, Incoterms, krajów tranzytu | ✅ | — | Could |
| FR-058 | — | Webhooki wychodzące (`comparison.completed`) | ✅ | — | Could |

## 2. Wymagania niefunkcjonalne

| ID | Alias | Wymaganie | Wartość | Status | Test | MoSCoW |
|---|---|---|---|---|---|---|
| NFR-001 | WN-01 | Limit rozmiaru uploadu | 200 MB → 413 | ✅ | — | Must |
| NFR-002 | WN-02 | Walidacja zawartości PDF | magic `%PDF`, bez `/Encrypt` | ✅ | — | Must |
| NFR-003 | WN-03 | Pliki tymczasowe krótko | 24 h | ✅ | — | Should |
| NFR-004 | WN-04 | Ochrona logowania | 5 prób / 15 min / IP | ✅ | ✅ | Must |
| NFR-005 | WN-05 | Bezpieczna sesja | HttpOnly, SameSite=Strict, Secure, 8 h | ✅ | ⚠️ | Must |
| NFR-006 | WN-06 | Ochrona CSRF | każdy sesyjny zapis | ✅ | ✅ | Must |
| NFR-007 | WN-07 | Polityka haseł | ≥ 8 znaków | ✅ | ✅ | Should |
| NFR-008 | WN-08 | Limit wywołań porównania | 30 / 60 s / użytkownika | ✅ | — | Should |
| NFR-009 | WN-09 | Miesięczny budżet AI | `budget_monthly_usd` | ⚠️ (2 z kilku wywołujących) | ⚠️ | Must |
| NFR-010 | WN-10 | Rejestracja kosztu AI | każde wywołanie | ⚠️ | — | Should |
| NFR-011 | WN-11 | Działanie bez kluczy API | tryb regułowy | ✅ | ✅ | Must |
| NFR-012 | WN-12 | Jedna baza kodu dla SQLite i PostgreSQL | `db.py` | ✅ | — | Must |
| NFR-013 | WN-13 | Bramka jakości w CI | lint, testy, skany | ✅ (PR #11) | CI | Must |
| NFR-014 | — | Czas odpowiedzi stron list | p95 < 2 s **(do potwierdzenia)** | ? | — | Should |
| NFR-015 | — | Czas porównania pary dokumentów | ≤ 60 s dla PDF tekstowego ≤ 20 stron **(do potwierdzenia)** | ? | — | Should |
| NFR-016 | — | Równoczesni użytkownicy | 10 przy 2×3 wątkach **(do potwierdzenia)** | ? | — | Should |
| NFR-017 | — | RPO / RTO | ≤ 24 h / ≤ 4 h **(do potwierdzenia)** | ⚠️ (RPO tak, RTO nieopisane) | ✅ (runbook) | Must |
| NFR-018 | — | Retencja danych | `audit_log` 12 mies., powiadomienia 6 mies., uploads 24 h **(do potwierdzenia)** | ❌ | — | Must |
| NFR-019 | — | Dostępność interfejsu | WCAG 2.1 AA dla portali zewnętrznych **(do potwierdzenia)** | ❌ | — | Could |
| NFR-020 | — | Przeglądarki | 2 ostatnie wersje Chrome/Edge/Firefox **(do potwierdzenia)** | ? | — | Should |
| NFR-021 | — | Język | PL; EN w 100% dla portali zewnętrznych | ⚠️ | — | Should |
| NFR-022 | — | Obserwowalność | błędy do Sentry, alert przy wzroście 5xx **(do potwierdzenia)** | ⚠️ | — | Should |
| NFR-023 | — | Pokrycie testami | raport w CI, zapadka, cel 80% logiki domenowej **(do potwierdzenia)** | ⚠️ (35%) | CI | Should |
| NFR-024 | — | Jedno źródło schematu bazy | `migrate_db.py` | ❌ | — | Should |
| NFR-025 | — | Brak stanu per proces wpływającego na wynik | cache/limity w DB lub Redis | ❌ | — | Should |

## 3. Wymagania bezpieczeństwa (punkt wyjścia [SEC], sekcja 6 promptu)

| ID | Wymaganie | Stan | Dowód / luka | MoSCoW |
|---|---|---|---|---|
| SEC-001 | Hasła hashowane argon2/bcrypt | ⚠️ pbkdf2:sha256 (werkzeug) | `blueprints/auth.py`; decyzja: zostawić czy migrować | Could |
| SEC-002 | Limit prób logowania | ✅ | 5/15 min per IP w `audit_log` | Must |
| SEC-003 | Bezpieczne sesje (HttpOnly, Secure, SameSite) | ✅ | `app.py:184-199` | Must |
| SEC-004 | 2FA dla administratorów | ❌ | brak; decyzja PO | Could |
| SEC-005 | Autoryzacja po stronie serwera dla każdego endpointu + test „brak dostępu” per rola | ⚠️ | dekoratory są; `require_role` jako bool w PalViz (R-01); testów 403 brakuje dla większości tras | Must |
| SEC-006 | Walidacja wejścia, parametryzowane SQL, escapowanie, CSRF | ✅ | brak `\|safe`, parametry przez `db.get_db()` | Must |
| SEC-007 | Upload: limit, MIME, losowe nazwy, poza katalogiem publicznym | ⚠️ | walidator nie we wszystkich 49 miejscach `.save(` | Should |
| SEC-008 | Nagłówki CSP, HSTS, X-Content-Type-Options, Referrer-Policy | ⚠️ | są; CSP z `unsafe-inline`/`unsafe-eval` (R-05) | Should |
| SEC-009 | Sekrety tylko w env; `.env.example` bez wartości | ⚠️ | klucze API/SMS w `settings` jawnym tekstem (R-02) | Must |
| SEC-010 | Logi bez haseł/tokenów; audit log operacji wrażliwych | ⚠️ | jest; brak retencji; traceback w PalViz | Should |
| SEC-011 | RODO: minimalizacja, retencja, eksport danych osoby, rejestr czynności | ❌ | `RODO.md` 0.1 | Should |
| SEC-012 | AI: treść użytkownika jako dane, minimalizacja PII, limity kosztów | ⚠️ | `ai_learning.py` bez sanityzacji (R-08); budżet niepełny (R-06) | Should |
| SEC-013 | Skany bezpieczeństwa blokujące HIGH/CRITICAL w CI | ⚠️ | `security.yml`; pip-audit blokuje `requirements-prod.txt`, a obraz instaluje `requirements.txt` (tylko doradczo) — R-15, US-029 | Must |
| SEC-014 | Zależności przypięte (lock), obraz nie-root, digest obrazu | ❌ | R-07, US-022 | Should |
| SEC-015 | Link resetu hasła tylko z zaufanej domeny (`APP_BASE_URL` obowiązkowy) | ❌ | R-03 | Must |
| SEC-016 | Dostęp do obiektów fail-closed (brak właściciela = odmowa) | ❌ | R-04 | Must |
| SEC-017 | Limit wywołań na ciężkich endpointach AI/upload | ⚠️ | 12 z ~34 tras (R-06) | Should |

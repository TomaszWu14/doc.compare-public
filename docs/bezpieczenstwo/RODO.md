# RODO — dane osobowe w DocCompare

> [SEC] Wersja 0.1 (2026-10-16). Dokument roboczy do potwierdzenia z PO i (jeśli istnieje) Inspektorem Ochrony Danych.
> Inwentarz danych: `KLASYFIKACJA_DANYCH.md` §2. Pozycje „do potwierdzenia” są założeniami.

## 1. Role

| Rola | Kto | Uwaga |
|---|---|---|
| Administrator danych | ACME (pracodawca użytkowników, zleceniodawca spedytorów) | do potwierdzenia |
| Podmioty przetwarzające | Hetzner/Coolify (hosting), Anthropic, Mistral, Resend, dostawcy trackingu i SMS, Sentry | umowy powierzenia do potwierdzenia; transfery poza EOG (Anthropic, Resend — USA) wymagają podstawy (np. DPF/SCC) |
| Repozytorium publiczne (portfolio) | brak danych osobowych i produkcyjnych; dane syntetyczne | gitleaks + przegląd PR |

## 2. Kategorie osób i dane

| Kategoria osób | Dane | Cel | Podstawa (propozycja) | Retencja (propozycja) |
|---|---|---|---|---|
| Pracownicy ACME (użytkownicy) | login, e-mail służbowy, rola, dział, IP i zdarzenia w `audit_log`, ostatnie logowanie | dostęp do narzędzia, rozliczalność działań | art. 6 ust. 1 lit. f (uzasadniony interes: bezpieczeństwo i rozliczalność) lub lit. b/c w zależności od stosunku pracy — do potwierdzenia | konto: do zakończenia uprawnień + pseudonimizacja; `audit_log`: 12 miesięcy (Z-06) |
| Pracownicy spedytorów i agencji (użytkownicy zewnętrzni) | login, e-mail, przypisanie do firmy | obsługa zleceń | art. 6 ust. 1 lit. b/f — do potwierdzenia | do zakończenia współpracy |
| Kierowcy | imię, numer telefonu, potwierdzenie awizacji | awizacja dostawy | art. 6 ust. 1 lit. f — do potwierdzenia | 12 miesięcy od awizacji |
| Osoby kontaktowe u dostawców, spedytorów, agencji | imię/nazwisko, e-mail, telefon służbowy | kontakt operacyjny | art. 6 ust. 1 lit. f | do zakończenia współpracy |
| Osoby widoczne w dokumentach handlowych (podpisy, kontakty na fakturach) | fragmenty w PDF i OCR | kontrola dokumentów | art. 6 ust. 1 lit. c/f (obowiązki celne i księgowe) | zgodnie z przepisami celnymi/księgowymi — do potwierdzenia (zwykle 5 lat) |

## 3. Zasady

| Zasada | Stan | Działanie |
|---|---|---|
| Minimalizacja | IP i nazwa użytkownika w każdym wpisie audytu; Sentry otrzymuje `username` + IP | rozważyć `send_default_pii=False`, skracanie IP (US-007) |
| Ograniczenie przechowywania | brak retencji `audit_log`, powiadomień, tokenów resetu, kosztów AI | zadanie TTL (US-007) |
| Integralność i poufność | sesje, role, CSRF, nagłówki, backup szyfrowany? (do potwierdzenia) | US-002 (sekrety), US-022 (obraz) |
| Rozliczalność | `audit_log`, `kolejka_status_log`, `supplier_audit_log` | retencja + ochrona przed modyfikacją (append-only) |
| Prawa osób: dostęp, sprostowanie | admin edytuje konto; brak eksportu danych osoby | endpoint eksportu (US-007) |
| Prawa osób: usunięcie | `delete_user` usuwa wiersz `users`, zostawia `comparisons.user_id`, `audit_log.username` | pseudonimizacja (`user_<id>`), zachowanie rozliczalności (US-007) |
| Przejrzystość | brak klauzuli informacyjnej w aplikacji | tekst w `/help` lub przy pierwszym logowaniu — do decyzji PO |

## 4. Rejestr czynności przetwarzania (szkic)

| Czynność | Kategorie osób | Dane | Odbiorcy | Transfer poza EOG | Retencja | Zabezpieczenia |
|---|---|---|---|---|---|---|
| Uwierzytelnianie i audyt użytkowników | pracownicy, użytkownicy zewnętrzni | login, e-mail, IP, zdarzenia | Sentry | tak (Sentry — zależnie od regionu) | 12 mies. (propozycja) | hash haseł, sesje, limity, role |
| Kontrola dokumentów handlowych z użyciem AI/OCR | osoby w dokumentach | fragmenty dokumentów | Anthropic, Mistral | tak (USA) | pliki 24 h, wyniki bezterminowo | tryb bez AI, budżet, sanityzacja (US-026) |
| Awizacja kierowców | kierowcy | imię, telefon | dostawca SMS | zależnie od dostawcy | 12 mies. (propozycja) | token jednorazowy |
| Powiadomienia e-mail | pracownicy, kontakty | e-mail, treść | Resend / SMTP | tak (Resend — USA) | wg skrzynki | — |
| Kopie zapasowe | wszystkie powyższe | zrzut bazy, `/data` | operator | nie | 14 dni + 3 mies. | dostęp SSH; szyfrowanie do potwierdzenia |

## 5. Incydent naruszenia ochrony danych

Procedura: `docs/operacje/RUNBOOK.md` §6 (izolacja, rotacja sekretów, zakres danych z `KLASYFIKACJA_DANYCH.md`,
zgłoszenie do UODO w 72 h, jeśli ryzyko dla praw osób — decyzja administratora).

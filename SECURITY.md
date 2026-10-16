# Polityka bezpieczeństwa

## Zgłaszanie podatności

**Nie zgłaszaj podatności w publicznych issues ani PR.** Użyj prywatnego zgłoszenia:

1. GitHub → zakładka **Security** → **Report a vulnerability** (prywatne zgłoszenie do właściciela repozytorium).
2. Jeśli ta opcja jest niedostępna: wiadomość do właściciela repozytorium (`@TomaszWu14`) z prośbą
   o kanał prywatny. Adres e-mail do zgłoszeń: `<DO POTWIERDZENIA przez PO>`.

Podaj: opis, wersję/commit, kroki odtworzenia, wpływ, ewentualną propozycję poprawki. Prosimy nie testować
na instancji demo (`doc.compare.twapp.pl`) metodami, które mogą zakłócić jej działanie (DoS, masowe skany).

## Czego się spodziewać (cele, do potwierdzenia przez PO)

| Etap | Cel |
|---|---|
| Potwierdzenie przyjęcia | 3 dni robocze |
| Wstępna ocena wagi | 7 dni roboczych |
| Poprawka dla ryzyka wysokiego/krytycznego | 30 dni |
| Skoordynowane ujawnienie | po poprawce, domyślnie do 90 dni od zgłoszenia |

## Zakres

- Kod w tym repozytorium (`main`) i obraz budowany z `Dockerfile*`.
- Poza zakresem: usługi zewnętrzne (Anthropic, Mistral, Resend, API trackingu, dostawcy SMS, Sentry, Coolify/Hetzner),
  inżynieria społeczna, ataki fizyczne.

## Zasady, których pilnujemy

- Sekrety wyłącznie w zmiennych środowiskowych (`.env.example` bez wartości); gitleaks w pre-commit i CI.
- Uprawnienia sprawdzane po stronie serwera dla każdego endpointu (`core.security`); role zewnętrzne zamknięte w portalach.
- Zapytania parametryzowane przez `db.get_db()`; walidacja uploadu PDF (`pdf_validation.py`); nagłówki CSP/HSTS/nosniff.
- Logi bez haseł, tokenów i zbędnych danych osobowych; audyt operacji wrażliwych w `audit_log`.
- Treść dokumentów użytkownika wysyłana do modeli AI jest danymi, nie instrukcjami; budżet kosztów AI jest limitowany.
- Każde ustalenie skanera HIGH/CRITICAL blokuje CI; wyjątki tylko z uzasadnieniem i datą przeglądu
  (`docs/bezpieczenstwo/RYZYKA.md`, `.trivyignore`, `# nosec <id>`).

## Dokumenty

- `docs/bezpieczenstwo/KLASYFIKACJA_DANYCH.md` — klasy danych i inwentarz.
- `docs/bezpieczenstwo/THREAT_MODEL.md` — STRIDE per przepływ.
- `docs/bezpieczenstwo/RYZYKA.md` — rejestr ryzyk i wyjątków.
- `docs/bezpieczenstwo/RODO.md` — dane osobowe, retencja, prawa osób.
- `docs/bezpieczenstwo/CHECKLISTA_ASVS.md` — poziom ASVS i status.
- `docs/AUDYT.md` sekcja 4 — audyt bezpieczeństwa z 2026-10-15.

## Wersje wspierane

Tylko gałąź `main` (wersja `constants.APP_VERSION`). Wydania są opisane w `CHANGELOG.md`.

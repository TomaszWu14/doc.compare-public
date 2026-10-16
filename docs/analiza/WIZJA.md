# Wizja produktu — DocCompare

> [BA] Wersja 0.1 (2026-10-16). Źródła: `README.md`, `docs/01-problem-i-zakres.md`, `docs/AUDYT.md`.
> Wartości oznaczone **(do potwierdzenia)** są założeniami BA zapisanymi w `ZALOZENIA.md`; PO je potwierdza lub zmienia.

## 1. Problem

Jedna dostawa importowa to kilka dokumentów od różnych stron (zamówienie PO, proforma PI, faktura CI, lista pakowa PL,
zgłoszenie celne SAD, konosament B/L), każdy w innym układzie. Przed aplikacją zespół sprawdzał je ręcznie, a stan
dostawy żył w Excelu, mailach i Teams. Rozbieżność ilości, ceny, warunków płatności czy Incoterms wychodziła dopiero
przy odprawie albo rozliczeniu, czyli wtedy, gdy jej naprawa jest najdroższa.

## 2. Cel

Wykryć rozbieżności w dokumentach handlowych **zanim** dotrą do odprawy lub rozliczenia, i prowadzić dostawę jako
**jeden rekord** od PO do rozliczenia, z bramkami, które zatrzymują proces przy niezgodności.

Cel dla produktu w horyzoncie najbliższych iteracji: domknąć bramki procesu (żadna ścieżka nie omija weryfikacji),
usunąć znane ryzyka bezpieczeństwa i zbudować proces pracy widoczny w repozytorium.

## 3. Użytkownicy

| Grupa | Rola w systemie | Co robi | Pewność |
|---|---|---|---|
| Zakupy (asystenci, kupcy) | `user`, `manager` | wgrywa dokumenty, porównuje PO↔PI, zakłada dostawę, zatwierdza wynik | wysoka (kod + docs) |
| Transport / logistyka | `manager` | kolejka transportowa, kontenery, tracking, demurrage, zlecenia spedycyjne | wysoka |
| Przełożeni, kontrola | `superuser`, `admin` | widok wszystkich działów, KPI, konfiguracja, użytkownicy | wysoka |
| Spedytorzy | `forwarder` (portal `/spedycja`) | agent celny, status odprawy dla swoich zleceń | średnia — czy używany produkcyjnie **(do potwierdzenia)** |
| Agencje celne | `customs_agent` (portal `/agencja`) | status odprawy swoich zleceń | średnia **(do potwierdzenia)** |
| Kierowcy | brak konta (link z tokenem) | potwierdzenie awizacji | wysoka |
| Oddział Chiny, Magazyn, Księgowość, Specjalista | brak roli | w procesie docelowym: ETD, przyjęcie, rozliczenie, zgoda na wypłynięcie | niska — poza systemem **(do potwierdzenia)** |

## 4. Zakres

**W zakresie (działa):** porównania PO/PI/CI/PL/SAD, stepper dostawy z bramkami, checklista celna, kolejka
transportowa z trackingiem i demurrage, portale spedytora i agencji, porównanie artworków z walidacją EAN/GS1,
Faktury → Excel i Draft SAD, ocena ryzyka AI z ręczną akceptacją sugestii, master data.

**Poza zakresem do odwołania (założenie Z-01, Z-04):** integracja z SAP (wzorcem jest PDF PO), portal potwierdzeń ETD,
bramka rozliczenia MIR7, automatyczne alerty e-mail, import z poczty.

## 5. Mierniki sukcesu (propozycja do potwierdzenia)

| Miernik | Baza | Cel | Skąd dane |
|---|---|---|---|
| Odsetek kompletów PO/PI/CI/PL sprawdzonych w aplikacji przed odprawą | `<DO UZUPEŁNIENIA>` | 100% dostaw z bramką | `comparisons`, `kolejka_zlecenia` |
| Czas ręcznej kontroli jednego kompletu | `<DO UZUPEŁNIENIA>` min | −50% | pomiar u użytkowników |
| Rozbieżności wykryte dopiero przy odprawie lub rozliczeniu | `<DO UZUPEŁNIENIA>` / rok | 0 | zgłoszenia Transportu / Księgowości |
| Dostawy zatrzymane przez bramkę `sprawdzone_niezgodne` / `artwork_bledne` | — | raportowane co miesiąc | `kolejka_status_log` |
| Ryzyka bezpieczeństwa wysokie/krytyczne otwarte | 1 (2026-10-15) | 0 | `RYZYKA.md` |
| Testy automatyczne dla wymagań Must | 27/52 wymagań z testem | 100% Must | `SLEDZENIE.md` |

## 6. Zasady produktu

1. Reguły deterministyczne decydują o zgodności; AI tylko podnosi ryzyko i proponuje, nigdy nie zapisuje (D-01, D-02).
2. Bramki procesu są kontrolami, nie podpowiedziami: obejście = błąd (założenie Z-03).
3. Aplikacja działa bez kluczy API i bez Redis; integracje są opcjonalne i degradują się czytelnie (D-06, WN-11).
4. Dane poufne handlowo i osobowe są minimalizowane w integracjach zewnętrznych (RODO.md).

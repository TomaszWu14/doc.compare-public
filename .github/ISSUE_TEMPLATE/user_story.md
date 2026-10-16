---
name: "[BA] Historyjka użytkownika"
about: Nowa funkcja lub zmiana opisana z perspektywy użytkownika (krok 1 procesu)
title: "US-xxx: Jako <rola> chcę <cel>, aby <korzyść>"
labels: ["historyjka", "BA"]
---

## Historyjka

**Jako** <rola>
**chcę** <cel>
**aby** <korzyść>

- Wymaganie: `FR-xxx` / `NFR-xxx` / `SEC-xxx` (`docs/analiza/WYMAGANIA.md`)
- Priorytet (MoSCoW): Must / Should / Could / Won't
- Obszar: Zakupy / Dostawy / Transport / Spedycja / Agencja / Artwork / Faktury / AI / Admin

## Kryteria akceptacji

```gherkin
Given <stan początkowy>
When  <akcja>
Then  <oczekiwany wynik>
```

(dodaj kolejne scenariusze, w tym negatywne i brzegowe)

## Wymagania niefunkcjonalne

- Wydajność / wolumen:
- Użyteczność / komunikaty:
- Dostępność / język (PL/EN):

## [SEC] Bezpieczeństwo i dane (wypełnia SEC w kroku 2)

- Klasa danych (publiczne / wewnętrzne / poufne / osobowe):
- Role z dostępem i test „brak dostępu → 403”:
- Zagrożenia (STRIDE) i zabezpieczenia jako dodatkowe kryteria:
- Wpis do rejestru ryzyk (jeśli coś zostaje otwarte): `R-xx`

## Definition of Ready

- [ ] cel i korzyść jasne, rola nazwana
- [ ] kryteria testowalne (Given/When/Then), łącznie z kryteriami SEC
- [ ] zależności znane
- [ ] dane, uprawnienia i klasa danych określone
- [ ] ma ID, priorytet i odwołanie do wymagania

## Pytania do PO / założenia

- (jeśli PO nie odpowie, założenie trafia do `docs/analiza/ZALOZENIA.md` jako „do potwierdzenia”)

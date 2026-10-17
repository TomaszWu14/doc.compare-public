---
name: "[SEC] Zadanie bezpieczeństwa (bez szczegółów exploita)"
about: Utwardzenie, luka w kontroli, dług ASVS, wyjątek do przeglądu — NIE zgłoszenie podatności
title: "security: <krótki opis>"
labels: ["security", "SEC"]
---

> Repozytorium jest publiczne. **Nie umieszczaj tu szczegółów umożliwiających wykorzystanie podatności**
> (payloadów, ścieżek ataku krok po kroku, danych z produkcji). Podatności zgłaszaj zgodnie z `SECURITY.md`.
> Ten szablon służy do zadań utwardzających, które można opisać na poziomie kontroli.

## Kontrola lub wymaganie

- Wymaganie: `SEC-xxx` (`docs/analiza/WYMAGANIA.md`) / punkt ASVS: `Vx.y.z`
- Przepływ z threat modelu: `F-x` (`docs/bezpieczenstwo/THREAT_MODEL.md`)
- Powiązane ryzyko: `R-xx` (`docs/bezpieczenstwo/RYZYKA.md`)

## Stan obecny (na poziomie kontroli, bez exploita)

## Stan docelowy

## Kryteria akceptacji

```gherkin
Given <rola / dane / konfiguracja>
When  <akcja>
Then  <oczekiwana reakcja systemu, np. 403, odrzucenie, wpis w audit_log>
```

## Waga i termin

- [ ] krytyczna  - [ ] wysoka  - [ ] średnia  - [ ] niska
- Termin przeglądu (jeśli to wyjątek): RRRR-MM-DD

# Interesariusze

> [BA] Wersja 0.1. Źródła: `docs/01-problem-i-zakres.md` §2, `docs/PROCES_ZAKUPY_FLOW.md`, `docs/PROCES_POTWIERDZENIE_ETD.md`, `constants.py`.

| Interesariusz | Rola w procesie | Rola w systemie | Potrzeby | Wpływ | Do potwierdzenia |
|---|---|---|---|---|---|
| Product Owner (właściciel repozytorium) | decyzje o zakresie, priorytetach, ryzykach, wydaniach | `admin` (demo) | przejrzysty proces, widoczne ryzyka | decydujący | — |
| Asystenci Zakupów | wysyłka PO, odbiór PI, wgrywanie dokumentów | `user` | szybkie porównanie, czytelne różnice | wysoki | czy mają rolę `user` czy `manager` |
| Kupcy / kierownik Zakupów | zatwierdzanie wyniku, decyzja o dostawie | `manager` | bramka, która zatrzymuje błędne dostawy; raport PDF | wysoki | — |
| Specjalista (zgoda na wypłynięcie) | jedyny zatwierdzający wypłynięcie w procesie docelowym | brak roli | formalna zgoda w systemie | wysoki | czy rola ma powstać (US-010) |
| Transport / logistyka | kontener, spedytor, agencja, ETA, demurrage | `manager` | jedna kolejka, tracking, alerty | wysoki | czy rozdzielić od Zakupów działem |
| Oddział Chiny | ETD, kontakt z dostawcą | brak roli (e-mail) | portal potwierdzeń ETD (wizja) | średni | czy w zakresie |
| Magazyn | przyjęcie dostawy, kontrola | brak roli | automatyczne przyjęcie z dostawy | średni | czy loguje się |
| Księgowość | rozliczenie frachtu, MIR7 | brak roli | bramka rozliczenia przy rozbieżności | średni | czy loguje się |
| Spedytorzy (firmy zewnętrzne) | odprawa, agent celny | `forwarder` | portal w języku partnera, tylko swoje zlecenia | średni | czy używany produkcyjnie |
| Agencje celne | status odprawy, Draft SAD | `customs_agent` | prosty portal; Draft SAD mailem (decyzja 2026-09-16) | średni | czy używany produkcyjnie |
| Kierowcy | awizacja | link z tokenem | potwierdzenie z telefonu | niski | — |
| Dostawcy | odbiór PO, wysyłka PI | brak (e-mail) | — | niski | — |
| IT / utrzymanie (Coolify, Hetzner) | hosting, backup, incydenty | `admin` | runbook, monitoring, alerty | wysoki | kontakt dyżurny |
| Inspektor Ochrony Danych (jeśli jest) | RODO | — | inwentarz danych, retencja, umowy powierzenia | średni | czy istnieje w ACME |
| Rekruterzy / audytorzy (repo publiczne) | ocena dojrzałości procesu | — | czytelna dokumentacja, ślad decyzji | niski | — |

Mapowanie grup biznesowych na role `user`/`manager` i działy pozostaje otwarte (`docs/01-problem-i-zakres.md:60, 115`; pytanie 2 w `docs/AUDYT.md` §5).

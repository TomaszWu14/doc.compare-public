# 01. Problem i zakres

> Dokument analityczny. Opisuje to, co **faktycznie robi kod** (stan gałęzi `portfolio-cleanup`).
> Rzeczy opisane w innych dokumentach, ale niezaimplementowane, są w sekcji „Poza zakresem”.
> Brakujące dane biznesowe są oznaczone `<DO UZUPEŁNIENIA: …>`. Firma = ACME, dane demo są syntetyczne.

## 1. Problem

### 1.1 Jak to działało przed aplikacją

Poniższy opis pochodzi wyłącznie z dokumentów w repo (`docs/PROCES_ZAKUPY_FLOW.md`, `README.md`,
`docs/WORKFLOW_AGENCJA_CELNA.md`). Nie jest to wynik obserwacji procesu.

| Obszar | Jak było | Źródło |
|---|---|---|
| Tablica zleceń Zakupy ↔ Transport | wspólny Excel na SharePoint (przypisanie dostawy do kontenera, FO, daty) | `PROCES_ZAKUPY_FLOW.md`, kroki 10, 16–18 |
| Lista ETD | Excel od Oddziału Chiny, ręcznie porównywany z SAP | `PROCES_ZAKUPY_FLOW.md`, krok 9 |
| Zgoda na wypłynięcie | łańcuch maili: Oddział Chiny → asystenci → specjalista → Transport | `PROCES_ZAKUPY_FLOW.md`, krok 10 |
| Wysyłka PO do dostawcy | ręczny mail z Outlooka | `PROCES_ZAKUPY_FLOW.md`, krok 2 |
| Kontrola dokumentów | ręczne krzyżowe sprawdzanie PO ↔ PI ↔ CI ↔ PL ↔ SAD; rozbieżności ceny, ilości i Incoterms wychodziły dopiero przy odprawie albo rozliczeniu | `README.md`, tabela „At a glance” |
| Przechowywanie plików | dysk sieciowy Z: (folder per PO) | `PROCES_ZAKUPY_FLOW.md`, krok 1 |
| Numery rozliczenia na fakturze | ręczne wklejanie numeru rozliczenia frachtu i MIR7 na PDF | `PROCES_ZAKUPY_FLOW.md`, krok 24 |
| Potwierdzenie rozliczenia transportu | wiadomość na Teams | `PROCES_ZAKUPY_FLOW.md`, krok 25 |
| Dokumenty do agencji celnej | mail z załącznikami (tak jest nadal, także z aplikacją) | `WORKFLOW_AGENCJA_CELNA.md`, „Decyzje” |

### 1.2 Skutki (czego brakuje do oceny)

Dokumenty opisują problem jakościowo: informacja rozproszona między Excel, maile, Outlook i Teams,
brak jednego rekordu dostawy, błędy w dokumentach wykrywane późno. Liczb w repo nie ma:

- Czas obsługi jednej dostawy od PO do rozliczenia: `<DO UZUPEŁNIENIA: mediana dni PO → rozliczenie przed wdrożeniem>`
- Wolumen: `<DO UZUPEŁNIENIA: liczba PO / kontenerów miesięcznie>`
- Czas ręcznej kontroli jednego kompletu dokumentów: `<DO UZUPEŁNIENIA: minuty na komplet PO+PI+CI+PL+SAD>`
- Rozbieżności wykryte za późno: `<DO UZUPEŁNIENIA: liczba i koszt rozbieżności wykrytych dopiero przy odprawie lub rozliczeniu, np. za rok>`
- Liczba osób w procesie: `<DO UZUPEŁNIENIA: liczba osób per dział (Zakupy, Transport, Oddział Chiny, Magazyn, Księgowość)>`

## 2. Interesariusze i role

### 2.1 Role w systemie (z kodu)

Hierarchia wewnętrzna `user(1) < manager(2) < superuser(3) < admin(4)`; role zewnętrzne mają poziom 0
i są zamknięte w swoich portalach (`constants.py`, `core/security.py`).

| Rola | Typ | Co realnie robi w aplikacji |
|---|---|---|
| `user` | wewnętrzna | wgrywa dokumenty do dostawy, robi porównania ad-hoc, korzysta z modułu Faktury → Excel / Draft SAD (`invoice_routes.py`), wysyła dokument do „uczenia” AI. **Nie zmienia statusu dostawy.** |
| `manager` | wewnętrzna | tworzy dostawę, wysyła PO do dostawcy, przesuwa / cofa / ustawia status, uruchamia weryfikację PO↔PI i artworku, potwierdza wypłynięcie, zatwierdza checklistę celną, przypisuje spedytora i agencję w kolejce transportowej, zatwierdza porównania, akceptuje sugestie AI. Dostaje powiadomienia o niezgodnościach. |
| `superuser` | wewnętrzna | jak manager, ale widzi dostawy wszystkich działów; podgląd portali zewnętrznych |
| `admin` | wewnętrzna | jak superuser + usuwanie dostawy, zakładanie agencji celnych |
| `forwarder` (spedytor) | zewnętrzna | portal `/spedycja`: widzi tylko wiersze kolejki transportowej przypisane do swojej firmy; wpisuje agenta celnego i status odprawy |
| `customs_agent` (agencja celna) | zewnętrzna | portal `/agencja`: widzi tylko wiersze przypisane do swojej agencji; zmienia wyłącznie status odprawy (`app.py:16621`) |

`user` i `manager` widzą tylko dostawy swojego działu; dostawy bez działu widzą wszyscy (`app.py:1461-1470`).

### 2.2 Interesariusze z dokumentów, bez odpowiednika w kodzie

`PROCES_ZAKUPY_FLOW.md` wymienia asystentów Zakupów, specjalistę (zgoda na wypłynięcie), Transport,
Oddział Chiny, Magazyn i Księgowość. W kodzie nie ma takich ról: wszystkie kroki procesu dostawy
wykonuje `manager`, a roli „specjalista” nie ma w `constants.py`.
Kto z tych grup faktycznie pracuje w aplikacji i na jakiej roli: `<DO UZUPEŁNIENIA: mapowanie grup biznesowych na role user/manager>`.

### 2.3 Systemy zewnętrzne

| System | Do czego |
|---|---|
| Claude API | opcjonalna ocena ryzyka wyniku porównania, uczenie profili dostawców, warstwa Vision w kaskadzie ekstrakcji |
| Mistral OCR | warstwa kaskady ekstrakcji tabel i OCR artworku |
| Tracking kontenerów (SafeCube/Sinay, 17track, ShipsGo) | status i ETA kontenera; ETA nadpisuje datę dostawy |
| SMTP | wysyłka PO do dostawcy, maile do managerów |
| Resend | reset hasła, alert przy porównaniu o statusie `critical` |

## 3. Cel

Z `README.md`: wykryć rozbieżności ceny, ilości i Incoterms w dokumentach handlowych **zanim**
dotrą do odprawy lub rozliczenia, oraz prowadzić jedną dostawę jako jeden rekord od PO do rozliczenia.

Mierniki sukcesu w repo nie występują: `<DO UZUPEŁNIENIA: docelowe wartości, np. czas kontroli kompletu, odsetek rozbieżności wykrytych przed odprawą>`.

## 4. W zakresie (działa w kodzie)

| Moduł | Co robi | Gdzie |
|---|---|---|
| Porównanie dokumentów | PO↔PI, CI↔PL, SAD↔CI (oraz ad-hoc dowolna para): ekstrakcja tabel kaskadą, dopasowanie pozycji, tolerancje z profilu dostawcy, kontrola sum i arytmetyki, wykrywanie literówek I/1, O/0 | `enhanced_comparator.py`, `table_extractor.py`, `typo_detector.py` |
| Audyt kodów CN | w porównaniu z SAD: kod CN z SAD vs `material_master.tariff_cn` | `cn_audit.py` |
| Stepper dostawy z bramkami | 20 kroków od PO do rozliczenia transportu; twarda bramka po wyniku `sprawdzone_niezgodne` / `artwork_bledne`; miękka bramka brakujących dokumentów | `delivery_workflow.py`, `app.py:18766-18880` |
| Bramka checklisty celnej | przejście do „dokumenty wysłane do odprawy” wymaga statusu `zatwierdzono` dla CI, PL, BL, SAD | `customs_checklist.py` |
| Portale zewnętrzne | `/spedycja` dla spedytora, `/agencja` dla agencji celnej | `app.py` (sekcje portali), `constants.py` |
| Porównanie artworku + kody kreskowe | wzorzec vs artwork fabryczny; EAN-13 (suma kontrolna GS1), GS1-128 (GTIN, LOT, EXP) | `artwork_comparator.py`, `barcode_validator.py` |
| Faktury → Excel / Draft SAD | upload CI/PL/proform, mapowanie na master data, przegląd, eksport Excel i Draft SAD | `invoice_routes.py`, `invoice_pipeline.py` |
| Ocena ryzyka AI | opcjonalna (`use_ai`); AI może tylko podnieść poziom ryzyka, nigdy go obniżyć | `ai_validator.py` |
| Sugestie AI do zatwierdzenia | sugestie profilu dostawcy zapisywane jako „oczekujące”; stosuje je dopiero manager | `ai_learning.py`, `app.py:8589-8670` |
| Kolejka transportowa | kontenery, tracking, demurrage/detention, przypisanie spedytora i agencji | `app.py`, `demurrage.py` |

## 5. Poza zakresem (nie zaimplementowane)

| Element | Gdzie opisany | Stan w kodzie | Dlaczego poza zakresem |
|---|---|---|---|
| Integracja z SAP (kostka SAP BW jako źródło prawdy dla PO, porównanie ETD z SAP) | `PROCES_ZAKUPY_FLOW.md`, kroki 4 i 9 | brak; PO↔PI porównuje PDF PO z PDF PI, krok `etd_sap` to tylko nazwa statusu | `<DO UZUPEŁNIENIA: powód, np. brak dostępu do SAP BW / decyzja>` |
| Automatyczne alerty e-mail (różnica ilości > 5%, zamiana I↔1) | `CLAUDE.md`, `alert_engine.py` | moduł `alert_engine` istnieje, ale nikt go nie wywołuje | `<DO UZUPEŁNIENIA: powód>` |
| Portal potwierdzania ETD przez dostawcę (akceptuj / koryguj / odrzuć, PDF Shipment Confirmation, SLA) | `PROCES_POTWIERDZENIE_ETD.md` | brak; jest tylko ręczne potwierdzenie wypłynięcia przez managera | `<DO UZUPEŁNIENIA: powód>` |
| Zgoda na wypłynięcie i rola „specjalista” | `PROCES_ZAKUPY_FLOW.md`, krok 10 | kolumna `zgoda_wyplyniecie` istnieje, ale nic jej nie ustawia; roli nie ma | `<DO UZUPEŁNIENIA: powód>` |
| Wyliczenie daty dostawy `ETD + transit time` | `PROCES_ZAKUPY_FLOW.md`, krok 5 | brak; data dostawy pochodzi z ETA trackingu | `<DO UZUPEŁNIENIA: powód>` |
| Kontrola ważności ≥ 5 lat | `PROCES_ZAKUPY_FLOW.md`, krok 4 | jest tylko kolejność dat MFG ≤ DELIVERY ≤ EXP | `<DO UZUPEŁNIENIA: powód>` |
| Bramka rozliczenia MIR7 (rozbieżność > tolerancja blokuje rozliczenie) | `PROCES_ZAKUPY_FLOW.md`, krok 27 | brak bramki na krokach rozliczenia; numer MIR7 jest tylko czytany przez stempel PDF, kod go nie zapisuje | `<DO UZUPEŁNIENIA: powód>` |
| Faktura transportowa i tłumaczenia w checkliście celnej | `PROCES_ZAKUPY_FLOW.md`, krok 19 | bramka obejmuje tylko CI, PL, BL, SAD | `<DO UZUPEŁNIENIA: powód>` |
| Draft SAD w portalu agencji, eksport XML/Huzar, auto-mail do agencji | `WORKFLOW_AGENCJA_CELNA.md` | brak | decyzja z 2026-09-16 zapisana w dokumencie: Excel wystarcza, XML dopiero na prośbę agencji, wysyłka ręczna |
| Moduł „Kolejka / Tablica zleceń” (`/kolejka`, import z Excela) | `PROCES_ZAKUPY_FLOW.md`, Etapy 1–8 | brak tras; proces działa w `/dostawy`; szablon `templates/kolejka.html` woła nieistniejące API | `<DO UZUPEŁNIENIA: czy porzucony na rzecz /dostawy>` |

## 6. Założenia

1. Rekord procesu to jedna dostawa = jeden numer PO (`kolejka_zlecenia.nr_zamowienia`), w formacie `4` lub `5` + 8–10 cyfr (`app.py:18574`).
2. Dokumenty wchodzą do systemu jako pliki PDF wgrywane ręcznie. Nie ma importu z poczty ani z SAP (wyjątek: przyjmowanie artworków przez `/api/intake/artwork` z tokenem).
3. Wzorcem do porównania z proformą jest PDF zamówienia, nie dane z SAP.
4. Moduły AI i OCR w chmurze są opcjonalne; bez kluczy API reguły deterministyczne nadal działają, a AI zwraca komunikat o niedostępności.
5. Wszystkie decyzje wewnętrzne w procesie dostawy podejmuje rola `manager` (lub wyższa). Czy to odpowiada podziałowi pracy w ACME: `<DO UZUPEŁNIENIA: potwierdzenie przez właściciela procesu>`.
6. Status odprawy w portalach (`customs_status`) jest niezależny od statusu dostawy; zmiana jednego nie zmienia drugiego.

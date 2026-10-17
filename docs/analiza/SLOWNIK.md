# Słownik pojęć

> [BA] Wersja 0.1. Terminy z kodu i dokumentów, które nowa osoba w zespole musi znać. Nazwy w kodzie w `monospace`.

## Dokumenty handlowe i celne

| Termin | Znaczenie w DocCompare |
|---|---|
| **PO** (Purchase Order) | zamówienie zakupu; numer `4`/`5` + 8–10 cyfr (`^[45]\d{8,10}$`) identyfikuje dostawę (`kolejka_zlecenia.nr_zamowienia`). Według założenia Z-01 PDF PO jest wzorcem porównania. |
| **PI** (Proforma Invoice) | proforma od dostawcy; porównywana z PO (ilości, ceny, warunki płatności, Incoterms). Proforma `-S` = próbki. |
| **CI** (Commercial Invoice) | faktura handlowa; porównywana z PL i PO; w module Faktury → Excel mapowana na master data. |
| **PL** (Packing List) | lista pakowa; źródło wag i kartonów; upload przesuwa dostawę do `packing_list_otrzymany`. |
| **CIPL** | jeden PDF zawierający CI i PL (i inne strony); `doc_splitter.py` dzieli go na dokumenty. |
| **SAD** | jednolity dokument administracyjny (zgłoszenie celne); porównywany z CI; źródło kodów CN. |
| **Draft SAD** | roboczy arkusz (Excel) z danymi do zgłoszenia celnego, generowany dla agencji celnej (`sad_draft_export.py`). |
| **PZC** | poświadczone zgłoszenie celne; status dostawy `pzc_agencja`. |
| **B/L** (Bill of Lading) | konosament morski; wymagany w checkliście celnej. |
| **WZ**, **FV**, **CMR** | wydanie zewnętrzne, faktura VAT, list przewozowy drogowy — typy dokumentów w `constants.DocType`. |
| **ZS / zlecenie spedycyjne** | zlecenie dla spedytora generowane z dostawy (`forwarding_order.py`); dziś blokowane brakiem zgody na wypłynięcie. |
| **FO** | numer i status zlecenia u spedytora (`kolejka_kontenery.fo_number`, `fo_status`). |
| **Incoterms** | reguły dostawy (EXW, FOB, CIF…); słownik w `blueprints/incoterms.py`; porównywane między PO i PI. |
| **Kod CN** | kod Nomenklatury Scalonej (8 cyfr; TARIC 10); audyt wobec `material_master.tariff_cn` (`cn_audit.py`). |
| **MIR7** | transakcja SAP do zaksięgowania (parkowania) faktury dostawcy; numer stemplowany na PDF (`pdf_stamper.py`); status `rozliczenie_fiori`. |
| **Fiori** | interfejs SAP, w którym Księgowość rozlicza dostawę; w aplikacji tylko nazwa statusu. |
| **ME22N**, **SAP BW** | zmiana zamówienia w SAP i hurtownia danych SAP; występują wyłącznie w dokumentach procesu docelowego. |

## Logistyka

| Termin | Znaczenie |
|---|---|
| **ETD / ETA** | planowana data wypłynięcia / przybycia; `etd_plan`, `etd_real`, `eta` w `kolejka_kontenery`; ETA z trackingu nadpisuje datę dostawy. |
| **Czas tranzytu** | dni od ETD do dostawy (`transit_time_dni`, nieużywane w obliczeniach); kraje tranzytu w `blueprints/transit_countries.py`. |
| **Demurrage** | opłata za przetrzymanie kontenera w porcie (rozładunek → odbiór); domyślnie 14 dni wolnych. |
| **Detention** | opłata za przetrzymanie kontenera poza portem (odbiór → zwrot pustego); domyślnie 7 dni. |
| **Dni wolne (free days)** | okres bez opłat; ostrzeżenie 3 dni przed końcem; poziomy green/amber/red (`demurrage.py`). |
| **Spedytor (`forwarder`)** | firma zewnętrzna organizująca transport; rola zewnętrzna z portalem `/spedycja`. |
| **Agencja celna (`customs_agent`)** | podmiot zgłaszający towar do odprawy; portal `/agencja`; zmienia tylko `customs_status`. |
| **`customs_status`** | status odprawy: `oczekuje`, `w_odprawie`, `zatwierdzone`, `odrzucone`, `wydane`; niezależny od statusu dostawy. |
| **Kolejka** | dwa znaczenia: (1) stepper dostaw `kolejka_zlecenia` + `kolejka_kontenery`, (2) kolejka transportowa `transport_queue` używana przez portale. Porzucony moduł `/kolejka` to trzecie, historyczne. |
| **Awizacja / dispatch** | powiadomienie kierowcy SMS-em z linkiem potwierdzenia (`/transport/confirm/<token>`). |
| **Przyjęcie magazynowe** | rejestr `warehouse_receipts`; w zamierzeniu tworzone automatycznie przy odpowiednim statusie. |

## Proces dostawy

| Termin | Znaczenie |
|---|---|
| **Stepper** | ok. 20 kroków od `utworzone` do `rozliczenie_transportu` (`delivery_workflow.py`), z fazami i limitami SLA. |
| **Bramka twarda** | status `sprawdzone_niezgodne` lub `artwork_bledne`: `advance` zwraca 409; nadpisanie wymaga notatki. |
| **Bramka miękka** | brak wymaganych dokumentów: przejście wymaga `confirm: true`. |
| **Checklista celna** | CI, PL, B/L, SAD muszą mieć status `zatwierdzono` przed `dokumenty_wyslane_odprawa` (`customs_checklist.py`). |
| **Zgoda na wypłynięcie** | kolumna `zgoda_wyplyniecie`; w procesie docelowym nadaje ją Specjalista; w kodzie nic jej nie ustawia. |
| **SLA** | limit dni w statusie (np. `proforma_oczekiwana` 7); przekroczenie jest tylko oznaczane na liście. |
| **Dział (`department`)** | ogranicza widoczność dostaw dla `user`/`manager`; dostawy bez działu widzą wszyscy. |
| **`sent_to_forwarder_at` / `sent_to_agency_at`** | znaczniki przekazania zlecenia do portalu; dziś ustawiane tylko przez API. |

## Porównanie i jakość danych

| Termin | Znaczenie |
|---|---|
| **REF** | kod referencyjny produktu; dopasowywany rozmyto (`NL753-S-40` ≈ `NL753S40`) przez `semantic_matcher.py`. |
| **Profil dostawcy** | mapowanie kolumn per typ dokumentu, tolerancja ceny, równoważne warunki płatności, synonimy (`supplier_profiles.py`). |
| **Tolerancja** | dopuszczalna różnica ceny w % z profilu; ilość zawsze 0%. |
| **Status pozycji** | `ok`, `format` (różnica tylko formatu/zaokrąglenia), `watpliwe`, `roznica`; liczniki `format_count`, `warn_count`, `diff_count`. |
| **Waga ustalenia (finding)** | `info`, `warning`, `error`; w artworku osobna skala `critical` / `important`. |
| **Poziom ryzyka porównania** | `ok`, `format`, `ostrzezenie`, `blad`; AI może go tylko podnieść. |
| **UOM** | jednostka miary: `PCS` sztuki, `CTN` kartony, `OP`/`OPZ` opakowania, `PAL` palety; przeliczniki w `uom.py`. |
| **Master data** | kartoteka materiałów (`material_master`: REF, EAN, CN, opakowania) i dostawców (`supplier_master.py`). |

## Artwork i kody kreskowe

| Termin | Znaczenie |
|---|---|
| **Artwork wzorcowy (master)** | zatwierdzony projekt opakowania z biblioteki (dysk `Z:`, indeks `artwork_index.py`). |
| **Artwork fabryczny** | wersja od producenta porównywana z wzorcem (piksele, ΔE, OCR, pola strukturalne). |
| **Wykrojnik (dieline)** | rysunek siatki opakowania; źródło wymiarów W×H×D dla modelu 3D (`artwork_3d.py`). |
| **PalViz** | moduł wizualizacji opakowania: eksport ścian i modelu 3D, szablony wykrojników (`blueprints/palviz.py`). |
| **Intake** | API przyjmowania artworków z agenta skanującego dysk `Z:` (`/api/intake/artwork`, token `INTAKE_TOKEN`). |
| **EAN-13 / EAN-8 / GTIN-14** | kody produktu z cyfrą kontrolną GS1 (`barcode_validator.py`). |
| **GS1-128 i AI (01)(10)(17)(11)** | kod z identyfikatorami zastosowania: GTIN, LOT, data ważności, data produkcji. |
| **UDI / MDR** | unikalna identyfikacja wyrobu medycznego; kontrola obowiązkowych AI. |
| **LOT / EXP / MFG** | numer partii, data ważności, data produkcji; kolejność MFG ≤ wysyłka ≤ EXP jest sprawdzana. |
| **ΔE** | różnica koloru; progi 7,0 (tekst) i 18,0 (grafika) w `constants.py`. |

## Organizacja

| Termin | Znaczenie |
|---|---|
| **ACME** | fikcyjna nazwa firmy w kopii portfolio. |
| **Oddział Chiny, Specjalista, Asystent Zakupów** | aktorzy procesu docelowego bez roli w systemie (`INTERESARIUSZE.md`). |
| **PO (Product Owner)** | właściciel repozytorium podejmujący decyzje biznesowe (nie mylić z PO = Purchase Order). |

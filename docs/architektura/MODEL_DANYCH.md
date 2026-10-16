# Model danych (rdzeń)

> [DEV] Wersja 0.1. Pełne diagramy (17 + 21 encji), opis encji i reguły integralności: `docs/04-model-danych.md`.
> Tu: rdzeń potrzebny do zrozumienia procesu oraz lista problemów schematu z audytu.

## 1. ERD rdzenia

```mermaid
erDiagram
    users ||--o{ comparisons : "user_id"
    users ||--o{ kolejka_zlecenia : "created_by (logiczny)"
    kolejka_kontenery ||--o{ kolejka_zlecenia : "kontener_id (logiczny)"
    kolejka_zlecenia ||--o{ kolejka_status_log : "zlecenie_id (logiczny)"
    kolejka_zlecenia ||--o| comparisons : "comparison_id (logiczny)"
    kolejka_zlecenia ||--o{ kolejka_powiadomienia : "zlecenie_id (logiczny)"
    transport_queue ||--o{ shipments : "transport_queue_id (logiczny)"
    warehouse_receipts ||--o{ shipments : "warehouse_receipt_id (logiczny)"
    shipments ||--o{ shipment_documents : "po_number (logiczny)"
    users ||--o{ audit_log : "username (tekst)"

    users {
        INTEGER id PK
        TEXT username UK
        TEXT email
        TEXT role "user/manager/superuser/admin/forwarder/customs_agent"
        TEXT department
        INTEGER forwarder_id
        INTEGER customs_agency_id
        INTEGER is_active
        TEXT last_login
    }
    comparisons {
        INTEGER id PK
        INTEGER user_id FK
        TEXT doc_type
        TEXT status
        INTEGER diff_count
        TEXT po_number
        TEXT supplier_code
        TEXT approval_status
        TEXT file_hash_a
        TEXT file_hash_b
        INTEGER is_deleted
        TEXT result_json
    }
    kolejka_zlecenia {
        INTEGER id PK
        TEXT nr_zamowienia UK "nr PO"
        INTEGER kontener_id
        TEXT supplier_code
        TEXT status "ok. 20 krokow steppera + legacy"
        TEXT department
        INTEGER comparison_id
        TEXT planowane_etd
        TEXT data_dostawy
        INTEGER zgoda_wyplyniecie "nic nie ustawia"
        TEXT artwork_status
        INTEGER transit_time_dni "nieuzywane"
    }
    kolejka_kontenery {
        INTEGER id PK
        TEXT numer_kontenera UK
        INTEGER forwarder_id
        TEXT etd_plan
        TEXT etd_real
        TEXT eta
        TEXT fo_number
        TEXT customs_status
        INTEGER departure_confirmed
    }
    kolejka_status_log {
        INTEGER id PK
        INTEGER zlecenie_id
        TEXT pole
        TEXT stara_wartosc
        TEXT nowa_wartosc
        INTEGER changed_by
        TEXT changed_at
    }
    kolejka_powiadomienia {
        INTEGER id PK
        INTEGER user_id
        TEXT rola
        INTEGER zlecenie_id
        TEXT typ
        TEXT tresc
        INTEGER przeczytane
    }
    transport_queue {
        INTEGER id PK
        TEXT container_number
        TEXT po_numbers "lista w tekscie"
        TEXT etd
        TEXT eta
        TEXT customs_status
        INTEGER forwarder_id
        TEXT sent_to_forwarder_at
        TEXT sent_to_agency_at
    }
    shipments {
        INTEGER id PK
        TEXT shipment_ref
        TEXT po_number
        TEXT status
        INTEGER comparison_id
        INTEGER transport_queue_id
        INTEGER warehouse_receipt_id
    }
    shipment_documents {
        INTEGER id PK
        TEXT po_number
        TEXT doc_type
        TEXT filename
        INTEGER uploaded_by
    }
    warehouse_receipts {
        INTEGER id PK
        TEXT container_number
        TEXT po_numbers
        TEXT received_date
        TEXT status
        TEXT sap_document
    }
    audit_log {
        INTEGER id PK
        TEXT event
        TEXT username
        TEXT detail
        TEXT ip
        INTEGER duration_ms
        TEXT extra
        TEXT created_at
    }
```

Legenda: „logiczny” = powiązanie tylko w kodzie, bez `REFERENCES`. Jedyne zadeklarowane klucze obce w repo (11)
wskazują na `users(id)`; `PRAGMA foreign_keys=ON` działa tylko na SQLite (`db.py:369`).

## 2. Dwa równoległe modele transportu

`kolejka_zlecenia` + `kolejka_kontenery` (stepper dostaw) oraz `transport_queue` + `shipments` + `warehouse_receipts`
(kolejka transportowa używana przez portale) opisują te same fakty (kontener, ETD/ETA, odprawa). Hooki, które miały
je synchronizować, są wołane tylko z `_set_dostawa_status` (US-008). Decyzja, który model jest systemem zapisu,
należy do PO (temat 4 w `docs/AUDYT.md` §2.5).

## 3. Źródła schematu (problem do rozwiązania w US-018)

| Źródło | Co tworzy | Uwagi |
|---|---|---|
| `migrate_db.py` | 34 `CREATE TABLE`, 94 `add_column` | uruchamiany przy starcie kontenera (`Dockerfile:85`) |
| `app.py` (`init_db()` przy imporcie + `_db_run_migrations`) | 47 `CREATE TABLE`, 69 `ALTER TABLE` | 27 tabel istnieje tylko tu (m.in. `audit_log`, `transport_queue`, `shipments`, `webhooks`, `password_reset_tokens`) |
| moduły domenowe | 10 plików z własnym `CREATE TABLE IF NOT EXISTS` | `supplier_profiles.py`, `material_master.py`, `artwork_index.py`, `uom.py`, `invoice_jobs.py`, `warehouse_stock.py`, `blueprints/incoterms.py`, `palviz.py`, `transit_countries.py` |

Wspólnych tabel między `app.py` a `migrate_db.py` jest 19; `users` jest zdefiniowane dwa razy. Zmiany modelu danych
opisujemy najpierw tutaj (sekcja 1 lub `docs/04-model-danych.md`), potem w `migrate_db.py` jako idempotentną migrację.

## 4. Klasy danych w modelu

Dane osobowe: `users` (e-mail, nazwa), `audit_log` (nazwa użytkownika, IP), `drivers` (imię, telefon),
`zlecenia_transportowe` (e-maile, telefon agenta). Poufne handlowo: `comparisons.result_json` (ceny, warunki),
profile dostawców, `material_master`. Szczegóły i retencja: `docs/bezpieczenstwo/KLASYFIKACJA_DANYCH.md`.

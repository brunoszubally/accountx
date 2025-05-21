# NAV Online Számla API (Python)

Ez az API lehetővé teszi a NAV Online Számla rendszerben lévő számlák lekérdezését. A rendszer Flask alapú és render.com-ról futtatható.

## Telepítés

1. Függőségek telepítése:
```bash
pip install -r requirements.txt
```

2. Környezeti változók beállítása:
```bash
export ADALO_API_KEY="your_api_key_here"
export PORT=5000
```

## API Használat

### Számlák lekérdezése

```
POST /query_invoice
```

#### Kérés fejlécek

- `Authorization`: Az API kulcs (kötelező)
- `Content-Type`: application/json

#### Kérés törzs

```json
{
    "dateFrom": "2024-01-01",
    "dateTo": "2024-01-31",
    "direction": "OUTBOUND",
    "page": 1
}
```

#### Paraméterek

- `dateFrom` (kötelező): Kezdő dátum (YYYY-MM-DD formátumban)
- `dateTo` (kötelező): Záró dátum (YYYY-MM-DD formátumban)
- `direction` (opcionális): A keresés iránya (OUTBOUND vagy INBOUND, alapértelmezett: OUTBOUND)
- `page` (opcionális): Oldalszám (alapértelmezett: 1)

#### Példa válasz

```json
{
    "success": true,
    "data": {
        "currentPage": 1,
        "availablePage": 5,
        "invoices": [
            {
                "invoiceNumber": "SZML-2024-001",
                "customerName": "Vevő Kft.",
                "customerTaxNumber": "12345678",
                "invoiceIssueDate": "2024-01-15",
                "invoiceNetAmountHUF": 100000,
                "invoiceVatAmountHUF": 27000,
                "supplierName": "Eladó Kft.",
                "supplierTaxNumber": "87654321",
                "transactionId": "123456789"
            }
        ]
    }
}
```

#### Hiba esetén

```json
{
    "success": false,
    "error": "Hibaüzenet"
}
```

## Render.com Telepítés

1. Hozz létre egy új Web Service-t a Render.com-on
2. Kapcsold össze a GitHub repository-val
3. Állítsd be a következő környezeti változókat:
   - `ADALO_API_KEY`: Az API kulcs
   - `PORT`: 10000 (Render.com alapértelmezett port)

4. Build parancs:
```bash
pip install -r requirements.txt
```

5. Start parancs:
```bash
python app.py
``` 
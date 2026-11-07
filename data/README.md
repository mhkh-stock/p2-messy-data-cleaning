# Data dictionary — P2 Messy Data Cleaning (DEMO / SAMPLE DATA)

**Raw file:** `data/raw/orders_dirty_SAMPLE.csv` — 10,000 rows, dirty, untouched.
**Clean file:** `data/processed/orders_clean_SAMPLE.csv` — 9,258 rows, cleaned.
Both files share the same 13 columns, in the same order. All rows are
fictional sample orders for a fictional shop (ShopKart) — no real customers.

## Columns

| Column | Type (clean) | Meaning | Raw-file dirt it carried |
|---|---|---|---|
| order_id | Text `ORD-00001` … | Unique order reference | Duplicated (exact + re-used IDs) |
| order_date | Date `yyyy-mm-dd` | Date of the order | 4 formats mixed: `yyyy-mm-dd`, `dd/mm/yyyy`, `dd Mon yyyy`, `mm-dd-yyyy` |
| customer_name | Text | Customer name (invented) | Extra spaces |
| email | Text or blank | Customer email (invented, `@example.com`) | Blank, or invalid (`user example.com`, `user@@example.com`) |
| phone | Text `+92…` or blank | Customer phone (invented) | Blank, too short, letters, or `03…` local format |
| city | Text | Order city | Blank, mixed case, extra spaces |
| product | Text | Product sold | Extra spaces |
| category | Text | Product category | Mixed case, synonyms (`Elec`, `Home and Kitchen`, `Home/Kitchen`, `Personal-Care`) |
| quantity | Whole number ≥ 1 | Units on this line | Blank, zero, negative |
| unit_price | Number, 2 decimals (PKR) | Price per unit | `Rs 1,250`, `PKR 1250`, `1,250.00` text |
| total_amount | Number, 2 decimals (PKR) | Line total = quantity × unit_price | Currency text, or simply wrong arithmetic |
| payment_method | Text | How the order was paid | Mixed case, `COD` vs `Cash on Delivery` |
| status | Text | Order status | Mixed case, `in-transit` vs `In Transit` |

## Cleaning rules (in order, see `src/generate_and_clean.py`)

1. Drop exact duplicate rows (first copy kept).
2. Drop later rows re-using an order ID (first copy kept).
3. Standardise text: trim, collapse spaces, map synonyms to one label,
   title-case city and status ("LAHORE"/"lahore" → "Lahore").
4. Parse dates to ISO; drop rows with an unparseable date (none in this sample).
5. Drop rows with a missing, zero or negative quantity.
6. Strip currency symbols/commas from prices; drop rows with an unparseable price (none in this sample).
7. Recompute every total as quantity × price.
8. Blank invalid emails/phones (never invent contact data); reformat valid phones to +92.
9. Fill missing city / payment / status with "Unknown" (label only, not invented data).
10. Sort by order_date, then order_id.

## Quality notes (verified by reopening the clean file)

- No duplicate rows, no duplicate order IDs.
- No blank order ID, date, product, category, quantity, price or total.
- Every date ISO; every total equals quantity × price.
- No `Rs`/`PKR` text, no synonym labels, no mixed-case city/status values,
  no invalid emails or non-+92 phones remain.
- Clean totals: 9,258 orders, PKR 36,080,444, 2026-01-01 to 2026-06-30.
- Drop reconciliation: 93 + 307 + 342 = 742 dropped; 10,000 − 742 = 9,258 clean.

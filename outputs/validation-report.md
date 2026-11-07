# Validation Report — P2 Messy Data Cleaning (SAMPLE)

**Source:** `data/raw/orders_dirty_SAMPLE.csv` — 10,000 dirty rows
(SAMPLE / DEMO data for a fictional shop, ShopKart — no real customers).
**Deliverable:** `data/processed/orders_clean_SAMPLE.csv` — 9,258 clean rows.
**Method:** `src/clean_data.py` (pandas, reproducible — same input, same output).

## What was wrong, and what was done

| Issue found | Rows affected | Action |
|---|---:|---|
| Exact duplicate rows | 93 | Dropped, first copy kept |
| Duplicate order ID (different content) | 307 | Dropped, first copy kept |
| Unparseable order date | 0 | Dropped — a dateless order cannot be placed in time |
| Missing / zero / negative quantity | 342 | Dropped — an order line without a valid quantity cannot be totalled |
| Unparseable unit price | 0 | Dropped — a line without a price cannot be totalled |
| Total did not equal quantity × price | 435 | Recomputed from quantity × price |
| Invalid email (no @, double @@) | 452 | Blanked — contact data is never invented |
| Invalid phone (too short, letters) | 240 | Blanked — contact data is never invented |
| Phone in a different format | 8,704 | Reformatted to +92 standard |
| Messy case / spacing / synonym labels | 2,193 | Standardised (e.g. COD → Cash on Delivery, Elec → Electronics) |
| Missing city / payment / status | 234 | Filled with "Unknown" (label only, not invented data) |
| Unit-price outliers (IQR rule) | 479 | Flagged only — NOT deleted, so real high-value sales are not hidden |
| **Total rows changed in any way** | **9,258** | |
| **Total rows dropped** | **742** | |

## Checks passed on the clean file (verified by reopening it)

- No duplicate rows, no duplicate order IDs.
- No blank order ID, order date, product, category, quantity, price or total.
- Every date is ISO format (YYYY-MM-DD); every total equals quantity × price.
- No currency symbols, commas-in-numbers, synonym labels, or mixed-case
  city/status values remain.
- Clean totals: 9,258 orders, PKR 36,080,444.00
  total sales, 2026-01-01 to 2026-06-30.

## What was NOT done (on purpose)

- No contact details were invented: bad emails/phones were blanked, not guessed.
- No outlier prices were deleted: unusually high prices are flagged to the
  business, not silently removed — deleting them would hide real sales.
- No rows were "fixed" by guessing: anything unrecoverable (no date, no
  quantity, no price) was dropped and counted above, not patched.

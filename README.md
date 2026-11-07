# P2 — Messy Data Cleaning: 10,000 Dirty Rows → Clean File + Validation Report

**Repo:** https://github.com/mhkh-stock/p2-messy-data-cleaning

**Shop:** ShopKart (fictional) · **Period:** Jan–Jun 2026 · **Status: SAMPLE delivery on DEMO data**
**Tools:** Python (pandas — the reusable cleaner in `src/clean_data.py`)
**Deliverable:** `data/processed/orders_clean_SAMPLE.csv` (9,258 clean rows)
**Report:** `outputs/validation-report.md` (every fix, counted) + `outputs/cleaning-summary.json`

> ⚠️ **Demo data only.** Every row in this project comes from a seeded generator
> in `src/generate_and_clean.py` for a fictional shop. It is **not** real client
> data and no real customer is named. The cleaning skill and the report format
> are real; the client history is not claimed.

## Business question it answers

> "My data is a mess — duplicates, mixed date formats, prices with 'Rs' in
> them, wrong totals. Can you give me one clean file I can actually use,
> and tell me exactly what was wrong with it?"

That is the job clients pay for most often before any dashboard or analysis:
a file they can trust, plus a report that proves what changed — not a silent
overwrite where nobody knows what was deleted.

## What is inside

| File | What it does |
|---|---|
| `data/raw/orders_dirty_SAMPLE.csv` | 10,000 dirty rows, untouched — the "before" |
| `data/processed/orders_clean_SAMPLE.csv` | 9,258 clean rows — the "after", the deliverable |
| `outputs/validation-report.md` | What was fixed, with counts, and what was deliberately NOT done |
| `outputs/cleaning-summary.json` | The same counts, machine-readable |
| `src/clean_data.py` | The reusable pandas cleaner: dirty CSV → clean CSV + report, same counts every run |
| `src/checks.py` | Independent data-quality checks (22 checks, stdlib only — reopens both CSVs and verifies every headline number without running the cleaner) |
| `src/generate_and_clean.py` | Seeded demo generator (regenerates the dirty file and the clean file with the same counts; re-run `clean_data.py` for the pandas report) |
| `data/README.md` | Data dictionary: every column, raw vs clean |

## 3 key findings (from the demo data)

1. **7.4% of the file was unusable:** 742 of 10,000 rows were dropped —
   93 exact duplicates, 307 rows re-using an order ID, and 342 lines with a
   missing, zero or negative quantity. *So what:* a dashboard built on the raw
   file would have double-counted orders and shown impossible quantities.
2. **The money columns could not be trusted as typed:** 435 totals did not
   equal quantity × price, and 1,316 price cells carried "Rs"/"PKR" text or
   thousand-commas (1,421 total cells the same). Every total in the clean
   file is recomputed and verified.
   *So what:* any revenue total from the raw file was wrong by an unknown amount.
3. **Contact data was the weakest part — and it was not guessed:**
   452 invalid emails and 240 bad phone numbers were blanked, never invented.
   Phones that were valid but messy (03xx…) were reformatted to +92 standard
   (8,704 rows). *So what:* the client gets a file that is honest about what
   it does not know, instead of a file full of invented contacts.

Note on "rows changed": all 9,258 clean rows differ from their raw version in
at least one character — phone reformatting to +92 and price formatting to
two decimals touch nearly every row. That is formatting, not content change;
the content fixes are the counts in the validation report.

## Verified clean-file numbers

| KPI | Value |
|---|---|
| Rows in (dirty) | 10,000 |
| Rows out (clean) | 9,258 |
| Rows dropped | 742 (7.4%) |
| Clean total sales | PKR 36,080,444 |
| Unit-price outliers flagged (IQR, NOT deleted) | 479 |
| Clean orders | 9,258 |
| Date range | 2026-01-01 to 2026-06-30 |

Verification was done by reopening both CSVs independently of the cleaning
script: no duplicate rows or order IDs, no blank key fields, every date in
ISO format, every total equal to quantity × price, no currency symbols,
synonym labels or mixed-case city/status values left, and the drop counts
reconcile exactly (93 + 307 + 342 = 742).

## How to run it (under 5 steps)

1. Open `data/processed/orders_clean_SAMPLE.csv` — that is the deliverable.
2. Read `outputs/validation-report.md` for what was fixed and why.
3. To rebuild from scratch: `pip install -r requirements.txt` then
   `python3 src/clean_data.py` (same input gives same output).
4. To reuse it for a real file: point the cleaner at the real CSV, keep the
   same columns, and adjust the synonym maps (`CATEGORY_MAP`, `PAYMENT_MAP`)
   to that client's labels.
5. Check the clean file yourself: `python3 src/checks.py` (stdlib only,
   22 checks — no duplicates, ISO dates, totals reconciled, canonical
   city/status/payment/category values, every headline number re-verified
   against the summary). The report lists every check.

## Tools

- Python 3 + pandas (`pip install -r requirements.txt`) for the reusable
  cleaner in `src/clean_data.py`. The demo generator in
  `src/generate_and_clean.py` uses only the standard library.

## Data source note

**Demo/sample data, generated for this project** (seeded generator, seed 42:
9,600 base orders + 400 duplicated rows = 10,000 dirty rows, Jan–Jun 2026,
20 products across 5 categories, 10 Pakistani cities, 4 payment methods).
Names, emails and phones are invented. No real customer data exists here —
by design.

## Repo standard note

This paid project follows the portfolio repo standard (Master Plan §3.2),
slimmed for a cleaning deliverable: README + data dictionary
(`data/README.md`) + the deliverable itself (clean CSV) + the validation
report (`outputs/validation-report.md`) + a Fiverr-ready package note
(`PACKAGE-NOTE.md`) + a reproducible script. The raw file is kept alongside
the clean file so a buyer can see the before/after — that is the proof.

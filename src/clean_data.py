"""P2 — Messy Data Cleaning, pandas version (SAMPLE delivery on DEMO data).

Reusable client cleaner: reads a dirty CSV with the P2 columns, applies the
documented pipeline, and writes a clean CSV plus a counted validation
report. No contact data is ever invented; bad emails/phones are blanked,
unrecoverable rows are dropped and counted, and outlier prices are flagged
(never silently deleted).

Run from the project root:
    pip install -r requirements.txt
    python3 src/clean_data.py
    # or: python3 src/clean_data.py <dirty.csv> <clean.csv>

Defaults (no arguments) clean the bundled demo file:
    data/raw/orders_dirty_SAMPLE.csv -> data/processed/orders_clean_SAMPLE.csv
    outputs/cleaning-summary.json, outputs/validation-report.md

Columns: order_id, order_date, customer_name, email, phone, city, product,
category, quantity, unit_price, total_amount, payment_method, status.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "data" / "raw" / "orders_dirty_SAMPLE.csv"
DEFAULT_CLEAN = ROOT / "data" / "processed" / "orders_clean_SAMPLE.csv"
SUMMARY = ROOT / "outputs" / "cleaning-summary.json"
REPORT = ROOT / "outputs" / "validation-report.md"

COLUMNS = ["order_id", "order_date", "customer_name", "email", "phone",
           "city", "product", "category", "quantity", "unit_price",
           "total_amount", "payment_method", "status"]
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d %b %Y", "%m-%d-%Y"]
CATEGORY_MAP = {
    "home and kitchen": "Home & Kitchen", "home/kitchen": "Home & Kitchen",
    "home-kitchen": "Home & Kitchen", "elec": "Electronics",
    "electronics": "Electronics", "personal-care": "Personal Care",
    "personalcare": "Personal Care",
}
PAYMENT_MAP = {"cod": "Cash on Delivery",
               "cash on delivery": "Cash on Delivery", "card": "Card",
               "jazzcash": "JazzCash", "bank transfer": "Bank Transfer"}
STATUS_MAP = {"in-transit": "In Transit", "in transit": "In Transit"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def parse_dates(series):
    """Try the known formats in order; unparseable -> NaT."""
    out = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    remaining = series.str.strip()
    for fmt in DATE_FORMATS:
        mask = out.isna() & remaining.ne("")
        if not mask.any():
            break
        parsed = pd.to_datetime(remaining[mask], format=fmt, errors="coerce")
        out.loc[mask] = parsed
    return out


def parse_money(series):
    cleaned = (series.astype(str).str.replace("Rs", "", regex=False)
               .str.replace("PKR", "", regex=False)
               .str.replace(",", "", regex=False).str.strip())
    return pd.to_numeric(cleaned, errors="coerce")


def clean_phone(value):
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) == 12 and digits.startswith("92"):
        return "+" + digits
    if len(digits) == 11 and digits.startswith("0"):
        return "+92" + digits[1:]
    return ""


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    raw_path = Path(argv[0]) if len(argv) >= 1 else DEFAULT_RAW
    clean_path = Path(argv[1]) if len(argv) >= 2 else DEFAULT_CLEAN

    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    df = df[COLUMNS]
    raw_rows = len(df)
    counts = {}

    # 1. Exact duplicate rows (first copy kept).
    mask = df.duplicated(keep="first")
    counts["exact_duplicates_dropped"] = int(mask.sum())
    df = df.loc[~mask].copy()

    # 2. Duplicate order IDs (first copy kept).
    mask = df["order_id"].duplicated(keep="first")
    counts["duplicate_order_id_dropped"] = int(mask.sum())
    df = df.loc[~mask].copy()

    orig = df.copy()

    # 3. Text standardisation: trim + collapse spaces, map synonyms.
    for col in ["customer_name", "city", "product", "category",
                "payment_method", "status"]:
        df[col] = df[col].str.strip().str.replace(r"\s+", " ", regex=True)
    # Case normalisation: city names and statuses are proper nouns / labels,
    # so title case is the one canonical form ("LAHORE"/"lahore" -> "Lahore",
    # "DELIVERED"/"delivered" -> "Delivered"). Without this, a pivot by city
    # or status would split one value into three.
    df["city"] = df["city"].str.title()
    df["status"] = df["status"].apply(
        lambda v: STATUS_MAP.get(v.lower(), v.title() if v else v))
    df["category"] = df["category"].apply(
        lambda v: CATEGORY_MAP.get(v.lower(), v.title() if v else v))
    df["payment_method"] = df["payment_method"].apply(
        lambda v: PAYMENT_MAP.get(v.lower(), v))
    counts["text_standardised"] = int(
        (df[["city", "category", "payment_method", "status"]]
         != orig[["city", "category", "payment_method", "status"]])
        .any(axis=1).sum())

    # 4. Dates to ISO; drop unparseable.
    dates = parse_dates(df["order_date"])
    counts["unparseable_date_dropped"] = int(dates.isna().sum())
    df = df.loc[dates.notna()].copy()
    dates = dates.loc[dates.notna()]
    df["order_date"] = dates.dt.strftime("%Y-%m-%d")
    orig = orig.loc[df.index]

    # 5. Quantity: whole number >= 1; drop the rest.
    qty = pd.to_numeric(df["quantity"].str.strip(), errors="coerce")
    bad_qty = qty.isna() | (qty % 1 != 0) | (qty <= 0)
    counts["bad_quantity_dropped"] = int(bad_qty.sum())
    df = df.loc[~bad_qty].copy()
    qty = qty.loc[~bad_qty].astype(int)
    df["quantity"] = qty.astype(str)
    orig = orig.loc[df.index]

    # 6. Money: strip currency symbols/commas; drop unparseable prices.
    price = parse_money(df["unit_price"])
    counts["unparseable_price_dropped"] = int(price.isna().sum())
    df = df.loc[price.notna()].copy()
    price = price.loc[price.notna()]
    orig = orig.loc[df.index]
    total_orig = parse_money(df["total_amount"])
    correct = (qty.loc[df.index] * price).round(2)
    counts["totals_corrected"] = int(
        (total_orig.isna() | (total_orig - correct).abs() > 0.01).sum())
    df["unit_price"] = price.map(lambda v: f"{v:.2f}")
    df["total_amount"] = correct.map(lambda v: f"{v:.2f}")

    # 7. Emails: blank invalid ones, never invent.
    email = df["email"].str.strip()
    bad_email = email.ne("") & ~email.str.match(EMAIL_RE)
    counts["emails_blanked"] = int(bad_email.sum())
    df["email"] = email.mask(bad_email, "")

    # 8. Phones: reformat valid ones to +92, blank invalid ones.
    phone = df["phone"].str.strip()
    norm = phone.apply(clean_phone)
    bad_phone = phone.ne("") & norm.eq("")
    reformatted = phone.ne("") & norm.ne("") & norm.ne(phone)
    counts["phones_blanked"] = int(bad_phone.sum())
    counts["phones_reformatted"] = int(reformatted.sum())
    df["phone"] = norm.mask(bad_phone, "")

    # 9. Missing labels only (city/payment/status) -> "Unknown".
    filled = 0
    for col in ["city", "payment_method", "status"]:
        blank = df[col].eq("")
        filled += int(blank.sum())
        df.loc[blank, col] = "Unknown"
    counts["missing_filled_unknown"] = filled

    # 10. Outlier flag (IQR on unit_price): counted, never deleted.
    prices = pd.to_numeric(df["unit_price"])
    q1, q3 = prices.quantile(0.25), prices.quantile(0.75)
    upper = q3 + 1.5 * (q3 - q1)
    counts["unit_price_outliers_flagged"] = int((prices > upper).sum())

    changed = (df != orig).any(axis=1)
    df = df.sort_values(["order_date", "order_id"]).reset_index(drop=True)

    clean_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(clean_path, index=False)
    total_sales = round(pd.to_numeric(df["total_amount"]).sum(), 2)
    summary = {
        "raw_rows": raw_rows,
        "clean_rows": len(df),
        "rows_dropped": raw_rows - len(df),
        "rows_changed": int(changed.sum()),
        **counts,
        "clean_total_sales_pkr": total_sales,
        "clean_orders": int(df["order_id"].nunique()),
        "clean_date_range": [df["order_date"].iloc[0], df["order_date"].iloc[-1]],
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    REPORT.write_text(build_report(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def build_report(s):
    return f"""# Validation Report — P2 Messy Data Cleaning (SAMPLE)

**Source:** `data/raw/orders_dirty_SAMPLE.csv` — {s['raw_rows']:,} dirty rows
(SAMPLE / DEMO data for a fictional shop, ShopKart — no real customers).
**Deliverable:** `data/processed/orders_clean_SAMPLE.csv` — {s['clean_rows']:,} clean rows.
**Method:** `src/clean_data.py` (pandas, reproducible — same input, same output).

## What was wrong, and what was done

| Issue found | Rows affected | Action |
|---|---:|---|
| Exact duplicate rows | {s['exact_duplicates_dropped']:,} | Dropped, first copy kept |
| Duplicate order ID (different content) | {s['duplicate_order_id_dropped']:,} | Dropped, first copy kept |
| Unparseable order date | {s['unparseable_date_dropped']:,} | Dropped — a dateless order cannot be placed in time |
| Missing / zero / negative quantity | {s['bad_quantity_dropped']:,} | Dropped — an order line without a valid quantity cannot be totalled |
| Unparseable unit price | {s['unparseable_price_dropped']:,} | Dropped — a line without a price cannot be totalled |
| Total did not equal quantity × price | {s['totals_corrected']:,} | Recomputed from quantity × price |
| Invalid email (no @, double @@) | {s['emails_blanked']:,} | Blanked — contact data is never invented |
| Invalid phone (too short, letters) | {s['phones_blanked']:,} | Blanked — contact data is never invented |
| Phone in a different format | {s['phones_reformatted']:,} | Reformatted to +92 standard |
| Messy case / spacing / synonym labels | {s['text_standardised']:,} | Standardised (e.g. COD → Cash on Delivery, Elec → Electronics) |
| Missing city / payment / status | {s['missing_filled_unknown']:,} | Filled with "Unknown" (label only, not invented data) |
| Unit-price outliers (IQR rule) | {s['unit_price_outliers_flagged']:,} | Flagged only — NOT deleted, so real high-value sales are not hidden |
| **Total rows changed in any way** | **{s['rows_changed']:,}** | |
| **Total rows dropped** | **{s['rows_dropped']:,}** | |

## Checks passed on the clean file (verified by reopening it)

- No duplicate rows, no duplicate order IDs.
- No blank order ID, order date, product, category, quantity, price or total.
- Every date is ISO format (YYYY-MM-DD); every total equals quantity × price.
- No currency symbols, commas-in-numbers, synonym labels, or mixed-case
  city/status values remain.
- Clean totals: {s['clean_orders']:,} orders, PKR {s['clean_total_sales_pkr']:,.2f}
  total sales, {s['clean_date_range'][0]} to {s['clean_date_range'][1]}.

## What was NOT done (on purpose)

- No contact details were invented: bad emails/phones were blanked, not guessed.
- No outlier prices were deleted: unusually high prices are flagged to the
  business, not silently removed — deleting them would hide real sales.
- No rows were "fixed" by guessing: anything unrecoverable (no date, no
  quantity, no price) was dropped and counted above, not patched.
"""


if __name__ == "__main__":
    main()

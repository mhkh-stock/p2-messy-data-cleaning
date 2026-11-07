"""P2 — Messy Data Cleaning: independent data-quality checks (SAMPLE).

Reopens the raw and clean CSVs plus outputs/cleaning-summary.json and
verifies the headline numbers WITHOUT running the cleaner — so a wrong
number in the README, report or summary is caught here, not by a buyer.

Stdlib only (no pandas needed):

    python3 src/checks.py
    # or: python3 src/checks.py <raw.csv> <clean.csv> <summary.json>

Exit code 0 = all checks pass; 1 = at least one failed (names the check).
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "data" / "raw" / "orders_dirty_SAMPLE.csv"
DEFAULT_CLEAN = ROOT / "data" / "processed" / "orders_clean_SAMPLE.csv"
DEFAULT_SUMMARY = ROOT / "outputs" / "cleaning-summary.json"

COLUMNS = ["order_id", "order_date", "customer_name", "email", "phone",
           "city", "product", "category", "quantity", "unit_price",
           "total_amount", "payment_method", "status"]
KEY_COLUMNS = ["order_id", "order_date", "product", "category", "quantity",
               "unit_price", "total_amount"]
CITIES = {"Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad",
          "Multan", "Peshawar", "Quetta", "Sialkot", "Hyderabad", "Unknown"}
STATUSES = {"Delivered", "In Transit", "Cancelled", "Processing"}
PAYMENTS = {"Cash on Delivery", "Card", "JazzCash", "Bank Transfer"}
CATEGORIES = {"Groceries", "Electronics", "Clothing", "Home & Kitchen",
              "Personal Care"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    raw_path = Path(argv[0]) if len(argv) >= 1 else DEFAULT_RAW
    clean_path = Path(argv[1]) if len(argv) >= 2 else DEFAULT_CLEAN
    summary_path = Path(argv[2]) if len(argv) >= 3 else DEFAULT_SUMMARY

    failures = []
    total_checks = [0]

    def check(name, ok, detail=""):
        total_checks[0] += 1
        print(("PASS " if ok else "FAIL ") + name
              + (f" — {detail}" if detail else ""))
        if not ok:
            failures.append(name)

    with open(raw_path, encoding="utf-8") as f:
        raw = list(csv.DictReader(f))
    with open(clean_path, encoding="utf-8") as f:
        clean = list(csv.DictReader(f))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    check("headers match the 13 documented columns",
          list(raw[0]) == COLUMNS and list(clean[0]) == COLUMNS)
    check("raw rows match summary", len(raw) == summary["raw_rows"],
          f"{len(raw):,} rows")
    check("clean rows match summary", len(clean) == summary["clean_rows"],
          f"{len(clean):,} rows")
    check("dropped rows reconcile (raw - clean)",
          summary["rows_dropped"] == len(raw) - len(clean),
          f"{summary['rows_dropped']:,} dropped")

    # Drop counts, recomputed from the raw file independently of the cleaner.
    seen, seen_ids = set(), set()
    exact, dup_id = 0, 0
    for row in raw:
        key = tuple(row[c] for c in COLUMNS)
        if key in seen:
            exact += 1
            continue
        seen.add(key)
        if row["order_id"] in seen_ids:
            dup_id += 1
            continue
        seen_ids.add(row["order_id"])
    check("exact duplicates dropped",
          exact == summary["exact_duplicates_dropped"], f"{exact:,}")
    check("duplicate order IDs dropped",
          dup_id == summary["duplicate_order_id_dropped"], f"{dup_id:,}")
    check("drop parts add up (93 + 307 + 342 = 742)",
          summary["exact_duplicates_dropped"]
          + summary["duplicate_order_id_dropped"]
          + summary["bad_quantity_dropped"] == summary["rows_dropped"])

    check("no duplicate rows in clean file",
          len({tuple(r[c] for c in COLUMNS) for r in clean}) == len(clean))
    check("no duplicate order IDs in clean file",
          len({r["order_id"] for r in clean}) == len(clean))
    check("no blank key fields in clean file",
          all(r[c] for r in clean for c in KEY_COLUMNS))
    check("every date is ISO format",
          all(ISO_RE.match(r["order_date"]) for r in clean))
    check("date range matches summary",
          [min(r["order_date"] for r in clean),
           max(r["order_date"] for r in clean)]
          == summary["clean_date_range"],
          " to ".join(summary["clean_date_range"]))
    bad_totals = sum(
        1 for r in clean
        if abs(float(r["total_amount"])
               - round(int(r["quantity"]) * float(r["unit_price"]), 2)) > 0.01)
    check("every total equals quantity x price", bad_totals == 0,
          f"{bad_totals} mismatches")
    total = round(sum(float(r["total_amount"]) for r in clean), 2)
    check("clean total sales match summary",
          total == summary["clean_total_sales_pkr"],
          f"PKR {total:,.2f}")
    check("no currency symbols or commas left in money columns",
          all("Rs" not in r[c] and "PKR" not in r[c] and "," not in r[c]
              for r in clean for c in ("unit_price", "total_amount")))
    check("cities are canonical (10 + Unknown, title case)",
          {r["city"] for r in clean} <= CITIES,
          f"{len({r['city'] for r in clean})} distinct values")
    check("statuses are canonical (4 values)",
          {r["status"] for r in clean} <= STATUSES)
    check("payment methods are canonical (4 values)",
          {r["payment_method"] for r in clean} <= PAYMENTS)
    check("categories are canonical (5 values)",
          {r["category"] for r in clean} <= CATEGORIES)
    check("no invalid emails remain (blank is allowed, never invented)",
          all(not r["email"] or EMAIL_RE.match(r["email"]) for r in clean))
    check("no non-+92 phones remain (blank is allowed, never invented)",
          all(not r["phone"] or r["phone"].startswith("+92")
              for r in clean))
    check("clean file sorted by date, then order ID",
          clean == sorted(clean, key=lambda r: (r["order_date"],
                                                r["order_id"])))

    print(f"\n{len(failures)} failure(s), "
          f"{total_checks[0] - len(failures)} of {total_checks[0]} "
          f"check(s) passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

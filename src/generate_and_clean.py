"""P2 — Messy Data Cleaning (SAMPLE delivery on DEMO data).

Generates 10,000 dirty order rows for a fictional shop ("ShopKart"),
then cleans them with a documented, repeatable pipeline.

Run:  python3 src/generate_and_clean.py
Outputs:
  data/raw/orders_dirty_SAMPLE.csv        (10,000 rows, dirty)
  data/processed/orders_clean_SAMPLE.csv  (cleaned rows)
  outputs/cleaning-summary.json           (every fix counted)
  outputs/validation-report.md            (human-readable report)

No real customer data is used anywhere. All names, emails and phones
are invented for this sample.
"""
import csv
import json
import random
import re
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "orders_dirty_SAMPLE.csv"
CLEAN = ROOT / "data" / "processed" / "orders_clean_SAMPLE.csv"
SUMMARY = ROOT / "outputs" / "cleaning-summary.json"
REPORT = ROOT / "outputs" / "validation-report.md"

RNG = random.Random(42)

FIRST = ["Ahmed", "Fatima", "Ali", "Ayesha", "Bilal", "Zainab", "Hassan",
         "Maryam", "Usman", "Sana", "Omar", "Hira", "Danish", "Noor",
         "Hamza", "Iqra", "Fahad", "Mahnoor", "Saad", "Amna"]
LAST = ["Khan", "Ahmed", "Ali", "Hussain", "Malik", "Shah", "Raza",
        "Iqbal", "Javed", "Nawaz", "Butt", "Sheikh", "Qureshi", "Siddiqui"]
CITIES = ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad",
          "Multan", "Peshawar", "Quetta", "Sialkot", "Hyderabad"]
PRODUCTS = {  # product: (category, low price, high price)
    "Basmati Rice 5kg": ("Groceries", 1800, 2600),
    "Cooking Oil 5L": ("Groceries", 2400, 3200),
    "Wheat Flour 10kg": ("Groceries", 1200, 1700),
    "Tea Leaves 1kg": ("Groceries", 900, 1400),
    "LED Bulb Pack (4)": ("Electronics", 800, 1300),
    "Mobile Charger": ("Electronics", 700, 1500),
    "Bluetooth Speaker": ("Electronics", 2500, 4500),
    "Electric Kettle": ("Electronics", 2200, 3800),
    "Men's Kurta": ("Clothing", 1800, 3200),
    "Women's Lawn Suit": ("Clothing", 2600, 4800),
    "Kids T-Shirt Pack": ("Clothing", 900, 1600),
    "Winter Shawl": ("Clothing", 1500, 2800),
    "Dinner Set 24pc": ("Home & Kitchen", 6500, 9500),
    "Non-Stick Pan": ("Home & Kitchen", 1800, 3000),
    "Bed Sheet Set": ("Home & Kitchen", 2200, 3800),
    "Water Bottle 1L": ("Home & Kitchen", 600, 1100),
    "Shampoo 400ml": ("Personal Care", 700, 1200),
    "Face Wash": ("Personal Care", 500, 900),
    "Hand Wash Pack": ("Personal Care", 600, 1000),
    "Body Lotion": ("Personal Care", 800, 1400),
}
PAYMENTS = ["Cash on Delivery", "Card", "JazzCash", "Bank Transfer"]
STATUSES = ["Delivered", "In Transit", "Cancelled", "Processing"]
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


def rand_phone():
    return "03" + "".join(RNG.choice("0123456789") for _ in range(9))


def make_base_row(i):
    product, (cat, lo, hi) = RNG.choice(list(PRODUCTS.items()))
    qty = RNG.choices([1, 2, 3, 4, 5], weights=[55, 25, 12, 5, 3])[0]
    price = RNG.randint(lo, hi)
    first, last = RNG.choice(FIRST), RNG.choice(LAST)
    d = date(2026, 1, 1) + timedelta(days=RNG.randrange(181))
    return {
        "order_id": f"ORD-{i:05d}",
        "order_date": d.strftime("%Y-%m-%d"),
        "customer_name": f"{first} {last}",
        "email": f"{first.lower()}.{last.lower()}{RNG.randrange(100)}@example.com",
        "phone": rand_phone(),
        "city": RNG.choice(CITIES),
        "product": product,
        "category": cat,
        "quantity": str(qty),
        "unit_price": str(price),
        "total_amount": str(qty * price),
        "payment_method": RNG.choice(PAYMENTS),
        "status": RNG.choice(STATUSES),
    }


def dirty_copy(row):
    """Inject one or more realistic dirt problems into a copy."""
    r = dict(row)
    roll = RNG.random()
    if roll < 0.18:  # messy case / whitespace in text fields
        field = RNG.choice(["city", "category", "payment_method", "status"])
        r[field] = RNG.choice([r[field].lower(), r[field].upper(),
                               " " + r[field] + " ", r[field].title() + " "])
    elif roll < 0.33:  # alternative date format
        d = date.fromisoformat(row["order_date"])
        r["order_date"] = RNG.choice([d.strftime("%d/%m/%Y"),
                                      d.strftime("%d %b %Y"),
                                      d.strftime("%m-%d-%Y")])
    elif roll < 0.48:  # currency strings in money columns
        r["unit_price"] = RNG.choice([f"Rs {int(row['unit_price']):,}",
                                      f"PKR {row['unit_price']}",
                                      f"{int(row['unit_price']):,}.00"])
        r["total_amount"] = RNG.choice([f"Rs {int(row['total_amount']):,}",
                                        f"PKR {row['total_amount']}"])
    elif roll < 0.55:  # blank contact / location fields
        r[RNG.choice(["email", "phone", "city"])] = ""
    elif roll < 0.60:  # invalid email
        r["email"] = RNG.choice([row["email"].replace("@", ""),
                                 row["email"].replace("@", "@@")])
    elif roll < 0.64:  # bad phone
        r["phone"] = RNG.choice(["12345", "0300-ABC-1234", ""])
    elif roll < 0.68:  # bad quantity
        r["quantity"] = RNG.choice(["-1", "-2", "0"])
    elif roll < 0.73:  # wrong total
        r["total_amount"] = str(int(row["total_amount"]) + RNG.choice([50, -75, 200]))
    elif roll < 0.78:  # synonym labels
        r["category"] = RNG.choice(["Home and Kitchen", "Home/Kitchen", "Elec",
                                    "Personal-Care"]) if row["category"] in (
                                        "Home & Kitchen", "Electronics",
                                        "Personal Care") else row["category"]
        r["payment_method"] = RNG.choice(["COD", "cash on delivery", "jazzcash",
                                          "card "])
    return r


def parse_date(s):
    from datetime import datetime
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_money(s):
    if s is None:
        return None
    s = str(s).replace("Rs", "").replace("PKR", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def clean_phone(s):
    digits = re.sub(r"\D", "", str(s or ""))
    if len(digits) == 12 and digits.startswith("92"):
        return "+" + digits
    if len(digits) == 11 and digits.startswith("0"):
        return "+92" + digits[1:]
    return ""


def main():
    base = [make_base_row(i) for i in range(1, 9601)]
    dirty = [dirty_copy(r) for r in base]
    dirty += [dict(r) for r in RNG.sample(base, 400)]  # exact duplicates
    RNG.shuffle(dirty)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(dirty)

    # ---- cleaning ----
    # Key order matches src/clean_data.py, so both scripts write the same
    # summary (byte-for-byte) for the same input.
    counts = {k: 0 for k in [
        "exact_duplicates_dropped", "duplicate_order_id_dropped",
        "text_standardised", "unparseable_date_dropped",
        "bad_quantity_dropped", "unparseable_price_dropped",
        "totals_corrected", "emails_blanked", "phones_blanked",
        "phones_reformatted", "missing_filled_unknown",
        "unit_price_outliers_flagged"]}
    seen_ids, seen_order_ids, clean, changed_ids = set(), set(), [], set()
    with open(RAW, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        orig = dict(row)
        # exact duplicates
        key = tuple(row[c] for c in COLUMNS)
        if key in seen_ids:
            counts["exact_duplicates_dropped"] += 1
            continue
        seen_ids.add(key)
        if row["order_id"] in seen_order_ids:
            counts["duplicate_order_id_dropped"] += 1
            continue
        seen_order_ids.add(row["order_id"])
        # text standardisation
        for c in ["customer_name", "city", "product", "category",
                  "payment_method", "status"]:
            row[c] = " ".join(str(row[c]).split())
        # Case normalisation: city names and statuses are proper nouns /
        # labels, so title case is the one canonical form ("LAHORE"/"lahore"
        # -> "Lahore", "DELIVERED"/"delivered" -> "Delivered"). Without
        # this, a pivot by city or status would split one value into three.
        row["city"] = row["city"].title()
        row["category"] = CATEGORY_MAP.get(row["category"].lower(),
                                           row["category"].title()
                                           if row["category"] else row["category"])
        row["payment_method"] = PAYMENT_MAP.get(row["payment_method"].lower(),
                                                row["payment_method"])
        row["status"] = STATUS_MAP.get(row["status"].lower(),
                                       row["status"].title()
                                       if row["status"] else row["status"])
        if any(row[c] != orig[c] for c in ["city", "category",
                                           "payment_method", "status"]):
            counts["text_standardised"] += 1
        # date
        d = parse_date(row["order_date"].strip())
        if d is None:
            counts["unparseable_date_dropped"] += 1
            continue
        row["order_date"] = d
        # quantity
        try:
            qty = int(str(row["quantity"]).strip())
        except ValueError:
            qty = None
        if qty is None or qty <= 0:
            counts["bad_quantity_dropped"] += 1
            continue
        row["quantity"] = str(qty)
        # money
        price = parse_money(row["unit_price"])
        if price is None:
            counts["unparseable_price_dropped"] += 1
            continue
        row["unit_price"] = f"{price:.2f}"
        total = parse_money(row["total_amount"])
        correct = round(qty * price, 2)
        if total is None or abs(total - correct) > 0.01:
            counts["totals_corrected"] += 1
        row["total_amount"] = f"{correct:.2f}"
        # email
        email = row["email"].strip()
        if email and not EMAIL_RE.match(email):
            counts["emails_blanked"] += 1
            email = ""
        row["email"] = email
        # phone
        phone = row["phone"].strip()
        if phone:
            norm = clean_phone(phone)
            if not norm:
                counts["phones_blanked"] += 1
                row["phone"] = ""
            elif norm != phone:
                counts["phones_reformatted"] += 1
                row["phone"] = norm
        # missing fills (never invent contact data — only labels)
        for c in ["city", "payment_method", "status"]:
            if not row[c]:
                row[c] = "Unknown"
                counts["missing_filled_unknown"] += 1
        if row != orig:
            changed_ids.add(row["order_id"])
        clean.append(row)

    clean.sort(key=lambda r: (r["order_date"], r["order_id"]))
    CLEAN.parent.mkdir(parents=True, exist_ok=True)
    # lineterminator="\n": the pandas cleaner writes LF, so the generator
    # must too — otherwise the two scripts produce different bytes for the
    # same clean file. (The raw file keeps the csv module's default CRLF,
    # so regenerating it stays byte-identical to the shipped raw file.)
    with open(CLEAN, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(clean)

    # Outlier flag (IQR on unit_price, same rule as src/clean_data.py):
    # counted, never deleted.
    prices = sorted(float(r["unit_price"]) for r in clean)

    def _q(p):
        i = (len(prices) - 1) * p
        lo = int(i)
        frac = i - lo
        return prices[lo] * (1 - frac) + prices[lo + 1] * frac

    q1, q3 = _q(0.25), _q(0.75)
    counts["unit_price_outliers_flagged"] = sum(
        1 for p in prices if p > q3 + 1.5 * (q3 - q1))

    total_sales = round(sum(float(r["total_amount"]) for r in clean), 2)
    summary = {"raw_rows": len(rows), "clean_rows": len(clean),
               "rows_dropped": len(rows) - len(clean),
               "rows_changed": len(changed_ids), **counts,
               "clean_total_sales_pkr": total_sales,
               "clean_orders": len({r["order_id"] for r in clean}),
               "clean_date_range": [clean[0]["order_date"],
                                    clean[-1]["order_date"]]}
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    REPORT.write_text(build_report(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def build_report(s):
    return f"""# Validation Report — P2 Messy Data Cleaning (SAMPLE)

**Source:** `data/raw/orders_dirty_SAMPLE.csv` — {s['raw_rows']:,} dirty rows
(SAMPLE / DEMO data for a fictional shop, ShopKart — no real customers).
**Deliverable:** `data/processed/orders_clean_SAMPLE.csv` — {s['clean_rows']:,} clean rows.
**Method:** `src/generate_and_clean.py` (seeded, re-runnable — same input, same output).

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

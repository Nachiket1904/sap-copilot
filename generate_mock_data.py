"""
Generates mock SAP-style Purchase Order data for SAP Copilot (Day 3).
Produces:
  - vendors.csv
  - purchase_orders.csv
  - payments.csv
Deliberately includes:
  - a handful of delayed payments (payment_date well after due_date)
  - a couple of outlier PO amounts (well above category norms)
  - 1-2 missing/null fields (missing delivery_date, missing category)
  - a couple of duplicate-looking POs (same vendor+amount+date) for
    anomaly-detection test cases in Week 3
"""

import csv
import random
from datetime import date, timedelta

random.seed(42)  # reproducible dataset

# OUT_DIR = "/home/data/mock_sap"
from pathlib import Path
OUT_DIR = Path(__file__).resolve().parent / "data" / "mock_sap"


# ---------------------------------------------------------------------------
# Vendors
# ---------------------------------------------------------------------------

VENDOR_NAMES = [
    "Apex Steel Works", "Bluewave Logistics", "Cedar Point Supplies",
    "Delta Industrial Components", "Evergreen Packaging Co", "Falcon Electronics",
    "Granite Office Solutions", "Horizon Raw Materials", "Ironclad Fasteners",
    "Junction Freight Services", "Keystone Manufacturing", "Lakeside Chemicals",
    "Meridian IT Hardware", "Northgate Stationery", "Orion Safety Equipment",
    "Pinnacle MRO Supply", "Quantum Circuit Traders", "Redwood Facilities Mgmt",
    "Summit Consulting Services", "Titan Machine Parts", "Unity Print & Signage",
    "Vertex Software Solutions", "Westbrook Textiles", "Yellowline Transport",
    "Zenith Energy Systems", "Ashford Packaging", "Brightline Electricals",
    "Coastal Tools & Equipment", "Dockyard Marine Supplies", "Elmwood Furniture Co",
]

COUNTRIES = ["India", "India", "India", "Germany", "USA", "China", "UAE", "Singapore"]

VENDOR_CATEGORIES = [
    "Raw Materials", "IT Hardware", "Office Supplies", "Packaging",
    "Services", "MRO", "Logistics",
]

vendors = []
for i, name in enumerate(VENDOR_NAMES, start=1):
    vendor_id = f"V{i:03d}"
    vendors.append({
        "vendor_id": vendor_id,
        "vendor_name": name,
        "vendor_category": random.choice(VENDOR_CATEGORIES),
        "country": random.choice(COUNTRIES),
        "contact_email": name.lower().replace(" ", ".").replace("&", "and") + "@example.com",
        "payment_terms_days": random.choice([15, 30, 30, 30, 45, 60]),
    })

# ---------------------------------------------------------------------------
# Purchase Orders
# ---------------------------------------------------------------------------

PO_CATEGORIES = [
    "Raw Materials", "IT Hardware", "Office Supplies", "Packaging",
    "Services", "MRO",
]

STATUS_VALUES = ["Pending", "Approved", "Rejected", "Closed"]
STATUS_WEIGHTS = [0.20, 0.55, 0.05, 0.20]

# rough "typical" amount range per category, used to seed realistic amounts
# and then deliberately blow past for outliers
CATEGORY_AMOUNT_RANGE = {
    "Raw Materials": (40_000, 300_000),
    "IT Hardware": (25_000, 220_000),
    "Office Supplies": (2_000, 40_000),
    "Packaging": (10_000, 90_000),
    "Services": (15_000, 250_000),
    "MRO": (5_000, 60_000),
}

START_DATE = date(2026, 1, 5)
END_DATE = date(2026, 9, 20)


def random_date(start, end):
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


N_PO = 220
purchase_orders = []
po_rows_for_duplication = []  # collect a few rows to duplicate later

for i in range(1, N_PO + 1):
    po_id = f"PO{i:05d}"
    vendor = random.choice(vendors)
    category = random.choice(PO_CATEGORIES)
    lo, hi = CATEGORY_AMOUNT_RANGE[category]
    amount = round(random.uniform(lo, hi), 2)

    po_date = random_date(START_DATE, END_DATE)
    delivery_offset = random.randint(7, 45)
    delivery_date = po_date + timedelta(days=delivery_offset)

    status = random.choices(STATUS_VALUES, weights=STATUS_WEIGHTS, k=1)[0]

    row = {
        "po_id": po_id,
        "vendor_id": vendor["vendor_id"],
        "category": category,
        "po_date": po_date.isoformat(),
        "delivery_date": delivery_date.isoformat(),
        "amount": amount,
        "status": status,
    }
    purchase_orders.append(row)
    po_rows_for_duplication.append(row)

# --- inject messiness -------------------------------------------------

# 1) A couple of outlier amounts (5-8x category norm) - anomaly test cases
outlier_indices = random.sample(range(len(purchase_orders)), 3)
for idx in outlier_indices:
    row = purchase_orders[idx]
    lo, hi = CATEGORY_AMOUNT_RANGE[row["category"]]
    row["amount"] = round(hi * random.uniform(5, 8), 2)

# 2) Missing delivery_date on a few rows (still-in-transit / data gap)
missing_delivery_indices = random.sample(range(len(purchase_orders)), 4)
for idx in missing_delivery_indices:
    purchase_orders[idx]["delivery_date"] = ""

# 3) Missing category on a couple of rows
missing_category_indices = random.sample(
    [i for i in range(len(purchase_orders)) if i not in missing_delivery_indices], 2
)
for idx in missing_category_indices:
    purchase_orders[idx]["category"] = ""

# 4) Duplicate-looking POs: same vendor + amount + date, different po_id
#    (classic "did someone double-enter this" anomaly case)
dup_sources = random.sample(
    [r for r in po_rows_for_duplication if r["amount"] and r["status"] != "Rejected"], 2
)
next_po_num = N_PO + 1
for src in dup_sources:
    dup = dict(src)
    dup["po_id"] = f"PO{next_po_num:05d}"
    next_po_num += 1
    purchase_orders.append(dup)

# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

# Only POs that are Approved or Closed get a payment record; Pending/Rejected
# don't (nothing to pay yet / payment never happened).
payable_pos = [
    po for po in purchase_orders
    if po["status"] in ("Approved", "Closed") and po["delivery_date"]
]

PAYMENT_STATUS_VALUES = ["Paid", "Scheduled"]

payments = []
delayed_target_count = 12  # deliberate delayed-payment test cases

payable_indices = list(range(len(payable_pos)))
delayed_indices = set(random.sample(payable_indices, min(delayed_target_count, len(payable_indices))))

for i, po in enumerate(payable_pos, start=1):
    vendor = next(v for v in vendors if v["vendor_id"] == po["vendor_id"])
    delivery = date.fromisoformat(po["delivery_date"])
    terms = vendor["payment_terms_days"]
    due_date = delivery + timedelta(days=terms)

    is_delayed = (i - 1) in delayed_indices

    if is_delayed:
        # delayed anywhere from 5 to 35 days past due
        payment_date = due_date + timedelta(days=random.randint(5, 35))
        pay_status = "Paid"
    else:
        # paid on time or early: 0 to terms-2 days before/at due date
        offset = random.randint(-3, max(0, terms - 5))
        payment_date = due_date - timedelta(days=offset) if offset > 0 else due_date
        # small chance it's still scheduled (not yet paid), only for recent POs
        if payment_date > date(2026, 9, 15) and random.random() < 0.3:
            pay_status = "Scheduled"
        else:
            pay_status = "Paid"

    payments.append({
        "payment_id": f"PMT{i:05d}",
        "po_id": po["po_id"],
        "vendor_id": po["vendor_id"],
        "due_date": due_date.isoformat(),
        "payment_date": payment_date.isoformat() if pay_status == "Paid" else "",
        "amount": po["amount"],
        "status": pay_status,
    })

# a couple of payments with a missing amount field (data-entry gap)
missing_amount_idx = random.sample(range(len(payments)), 2)
for idx in missing_amount_idx:
    payments[idx]["amount"] = ""

# ---------------------------------------------------------------------------
# Write CSVs
# ---------------------------------------------------------------------------

import os
os.makedirs(OUT_DIR, exist_ok=True)


def write_csv(filename, rows, fieldnames):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path} ({len(rows)} rows)")


write_csv("vendors.csv", vendors,
          ["vendor_id", "vendor_name", "vendor_category", "country",
           "contact_email", "payment_terms_days"])

write_csv("purchase_orders.csv", purchase_orders,
          ["po_id", "vendor_id", "category", "po_date", "delivery_date",
           "amount", "status"])

write_csv("payments.csv", payments,
          ["payment_id", "po_id", "vendor_id", "due_date", "payment_date",
           "amount", "status"])

print("\nSummary:")
print(f"  vendors: {len(vendors)}")
print(f"  purchase_orders: {len(purchase_orders)} "
      f"(outliers={len(outlier_indices)}, missing_delivery={len(missing_delivery_indices)}, "
      f"missing_category={len(missing_category_indices)}, duplicates={len(dup_sources)})")
print(f"  payments: {len(payments)} (delayed={len(delayed_indices)}, missing_amount={len(missing_amount_idx)})")

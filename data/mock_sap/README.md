# Mock SAP Dataset — Schema Reference

Mock data simulating SAP-style Purchase Order records. Generated
deterministically (`generate_mock_data.py`, seed=42) — rerun it to get an
identical dataset, or change the seed for a fresh variant.

All three files share `vendor_id` as a join key; `purchase_orders` and
`payments` additionally share `po_id`. Both are consistent across files —
every `vendor_id` in `purchase_orders.csv`/`payments.csv` exists in
`vendors.csv`, and every `po_id` in `payments.csv` exists in
`purchase_orders.csv`.

## vendors.csv (30 rows)

| Column | Type | Notes |
|---|---|---|
| `vendor_id` | string | Primary key. Format `V001`–`V030`. |
| `vendor_name` | string | Display name. |
| `vendor_category` | string | One of: `Raw Materials`, `IT Hardware`, `Office Supplies`, `Packaging`, `Services`, `MRO`, `Logistics`. Vendor-level category — not always the same as a given PO's `category` (a Logistics vendor can still be issued an Office Supplies PO). |
| `country` | string | Free text (e.g. `India`, `USA`, `Germany`). |
| `contact_email` | string | Synthetic, `@example.com`. |
| `payment_terms_days` | integer | Contractual payment window used to derive `payments.due_date`. One of: 15, 30, 45, 60. |

## purchase_orders.csv (222 rows)

| Column | Type | Notes |
|---|---|---|
| `po_id` | string | Primary key. Format `PO00001`–`PO00222`. |
| `vendor_id` | string | FK → `vendors.vendor_id`. |
| `category` | string | One of: `Raw Materials`, `IT Hardware`, `Office Supplies`, `Packaging`, `Services`, `MRO`. **2 rows have this blank** (missing-data test case). |
| `po_date` | date (`YYYY-MM-DD`) | Date PO was raised. Range: 2026-01-05 to 2026-09-20. |
| `delivery_date` | date (`YYYY-MM-DD`) | Expected/actual delivery date. **4 rows have this blank** (in-transit / data-gap test case). |
| `amount` | float | PO value. **3 rows are deliberate outliers** (5–8x the category's typical range) for anomaly-detection test cases. |
| `status` | string | Fixed vocabulary: `Pending`, `Approved`, `Rejected`, `Closed`. Only `Approved`/`Closed` POs get a payment record. |

**Duplicate test cases:** 2 rows (`po_id` near the end of the file) share
identical `vendor_id` + `amount` + `po_date` with an earlier PO but a
different `po_id` — simulates an accidental double-entry, for duplicate-PO
detection.

## payments.csv (163 rows)

| Column | Type | Notes |
|---|---|---|
| `payment_id` | string | Primary key. Format `PMT00001`–`PMT00163`. |
| `po_id` | string | FK → `purchase_orders.po_id`. Only present for POs with status `Approved`/`Closed` and a non-blank `delivery_date` — not every PO has a payment row. |
| `vendor_id` | string | FK → `vendors.vendor_id`. Denormalized here so payment-delay questions don't require a join back through `purchase_orders`. |
| `due_date` | date (`YYYY-MM-DD`) | `delivery_date + vendor.payment_terms_days`. This is the field `docs/seed_questions.md` flagged as needed for delay calculations. |
| `payment_date` | date (`YYYY-MM-DD`) or blank | Actual payment date. Blank when `status = Scheduled` (not yet paid). |
| `amount` | float | Mirrors the PO amount. **2 rows have this blank** (data-entry-gap test case). |
| `status` | string | Fixed vocabulary: `Paid`, `Scheduled`. |

**Delay test cases:** 12 payments are deliberately delayed 5–35 days past
`due_date` — `payment_date - due_date` is the delay calculation seed
question 1 and 4 both need.

## Query-ability check against seed questions

| # | Seed question | Answerable with this schema? |
|---|---|---|
| 1 | Delayed payments this month | Yes — `payments.payment_date`, `payments.due_date`, join to `vendors.vendor_name` via `payments.vendor_id` |
| 2 | Q3 POs by category | Yes — `purchase_orders.po_date`, `.category`, `.amount` (note: 2 rows have blank category, will need a `WHERE category != ''` or an "Uncategorized" bucket) |
| 3 | Unusual transactions this week | Yes for data support (amount outliers + duplicates are seeded) — but the "unusual" **rule itself is not yet defined** (threshold vs. duplicate detection); still an open decision, not a schema gap |
| 4 | Avg payment delay by vendor | Yes — same fields as Q1, aggregated by `vendor_id` |
| 5 | Pending POs above ₹1,00,000 | Yes — `purchase_orders.status = 'Pending'`, `.amount > 100000` |

## Known open item

Question 3's "unusual" threshold is still undefined (flagged back in the
Day 1 open-decisions list). The data now supports either approach — a
statistical outlier rule (e.g. amount > mean + 2×stddev per category) or a
duplicate-detection rule (matching vendor_id + amount + po_date) — but
picking one is a Day 4 architecture decision, not a data problem.

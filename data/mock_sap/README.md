# Mock SAP Dataset — Schema Reference

Mock data simulating SAP-style Purchase Order records. Generated
deterministically (`generate_mock_data.py`, seed=42) — rerun it to get an
identical dataset, or change the seed for a fresh variant.

All three files share `vendor_id` as a join key; `purchase_orders` and
`payments` additionally share `po_id`. Both are consistent across files —
every `vendor_id` in `purchase_orders.csv`/`payments.csv` exists in
`vendors.csv`, and every `po_id` in `payments.csv` exists in
`purchase_orders.csv`.

**Blank cells load as `NULL` in SQLite**, not empty strings. Filter with `IS NULL` / `IS NOT NULL`. `tests/test_seed_questions.py` checks this.

## vendors.csv (30 rows)

| Column | Type | Notes |
|---|---|---|
| `vendor_id` | string | Primary key. Format `V001`–`V030`. |
| `vendor_name` | string | Display name. |
| `vendor_category` | string | One of: `Raw Materials`, `IT Hardware`, `Office Supplies`, `Packaging`, `Services`, `MRO`, `Logistics`. Vendor-level category — not always the same as a given PO's `category` (a Logistics vendor can still be issued an Office Supplies PO). |
| `country` | string | Free text (e.g. `India`, `USA`, `Germany`). |
| `contact_email` | string | Synthetic, `@example.com`. |
| `payment_terms_days` | integer | Contractual payment window used to derive `payments.due_date`. One of: 15, 30, 45, 60. |

## purchase_orders.csv (228 rows)

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

## payments.csv (168 rows)

| Column | Type | Notes |
|---|---|---|
| `payment_id` | string | Primary key. Format `PMT00001`–`PMT00163`. |
| `po_id` | string | FK → `purchase_orders.po_id`. Only present for POs with status `Approved`/`Closed` and a non-blank `delivery_date` — not every PO has a payment row. |
| `vendor_id` | string | FK → `vendors.vendor_id`. Denormalized here so payment-delay questions don't require a join back through `purchase_orders`. |
| `due_date` | date (`YYYY-MM-DD`) | `delivery_date + vendor.payment_terms_days`. This is the field `docs/seed_questions.md` flagged as needed for delay calculations. |
| `payment_date` | date (`YYYY-MM-DD`) or blank | Actual payment date. Blank when `status = Scheduled` (not yet paid). |
| `amount` | float | Mirrors the PO amount. **2 rows have this blank**, and **1 row (PMT00168) is the text `TBD`** (data-entry-gap test cases). The loader stores both as `NULL`. |
| `status` | string | Fixed vocabulary: `Paid`, `Scheduled`. |

**Delay test cases:** 12 random payments (plus 4 from Scenario A below) are deliberately delayed 5–35 days past
`due_date` — `payment_date - due_date` is the delay calculation seed
question 1 and 4 both need.

## Week 2 scenarios

Appended by hand-written (non-random) code at the end of `generate_mock_data.py`,
so the original seeded rows are unchanged. Each stresses a seed question in a way
the random data doesn't.

| Scenario | Rows | What it tests |
|---|---|---|
| **A. Repeat-late vendor** | V019 Summit Consulting Services: PO00223–PO00226 / PMT00164–PMT00167, each paid 15–24 days late, all paid in Sep 2026 | **Q1** finally returns several September rows (previously 1). **Q4**: Summit has 4 late payments vs 1 for every other vendor (highest *count*), while its average delay (19.5 days) is not the highest, so "worst vendor" depends on whether count or average is meant. |
| **B. Near-duplicate PO** | PO00227: same vendor (V014) and amount as an existing PO, raised **one day later** | **Q3**. The rule in `docs/architecture.md` needs the *same* `po_date`, so it does **not** flag this. It documents the rule's blind spot, and `tests/test_seed_questions.py` still expects exactly 2 duplicates. |
| **C. Malformed amount** | PMT00168 (PO00228, V005): `amount` is the text `TBD`, not blank | Loader robustness. A naive load makes the whole `amount` column TEXT, which breaks `SUM`/`AVG`. The loader coerces it to `NULL` and prints a warning. `tests/test_loader.py` checks it. |

## Query-ability check against seed questions

| # | Seed question | Answerable with this schema? |
|---|---|---|
| 1 | Delayed payments this month | Yes — `payments.payment_date`, `payments.due_date`, join to `vendors.vendor_name` via `payments.vendor_id` |
| 2 | Q3 POs by category | Yes — `purchase_orders.po_date`, `.category`, `.amount` (note: 2 rows have NULL category. Use `COALESCE(category, 'Uncategorized')` to bucket them, or `WHERE category IS NOT NULL` to drop them) |
| 3 | Unusual transactions this week | Yes for data support (amount outliers + duplicates are seeded) — but the "unusual" **rule itself is not yet defined** (threshold vs. duplicate detection); still an open decision, not a schema gap |
| 4 | Avg payment delay by vendor | Yes — same fields as Q1, aggregated by `vendor_id` |
| 5 | Pending POs above ₹1,00,000 | Yes — `purchase_orders.status = 'Pending'`, `.amount > 100000` |

## Known open item

Question 3's "unusual" threshold is still undefined (flagged back in the
Day 1 open-decisions list). The data now supports either approach — a
statistical outlier rule (e.g. amount > mean + 2×stddev per category) or a
duplicate-detection rule (matching vendor_id + amount + po_date) — but
picking one is a Day 4 architecture decision, not a data problem.

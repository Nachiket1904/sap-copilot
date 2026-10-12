# Data-quality notes (Week 3 Day 2)

Draft prepared from the current mock data; the collaborator should add real-SAP experience.

## Current validation (`flag_bad_rows`, `src/data_layer/loader.py`)
Flags, never drops: negative amounts, missing vendor IDs, payment before PO date, Paid with no amount, vendor not in master.
On the current data it flags 3 rows: PMT00012, PMT00113, PMT00168 (Paid but amount missing; PMT00168 was the "TBD" value).

## Three bad rows to add later (not added to CSVs yet, so tests stay in sync)
1. Backdated payment: `PMT00200, PO00050, V??, due 2026-03-01, paid 2026-02-01` where PO00050 is dated 2026-03-10.
2. PO with an unknown vendor: `PO00300, vendor_id V999, ...` (vendor missing from the vendor master).
3. Negative amount: a credit-note-like PO of `-12,500.00`.

## Extra rules a real report would have
1. Payment made without a goods receipt or invoice (3-way match): needs an invoices/receipts table we do not have.
2. Same invoice number paid twice for the same vendor.

## False positives
None on current data. Duplicate-PO detection could wrongly flag legitimate repeat orders on the same day for the same
amount; real systems also compare line items.

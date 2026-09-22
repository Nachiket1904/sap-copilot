# Seed Business Questions

For each question, note the fields it needs — this drives the Day 3 schema.

1. "Which vendors had delayed payments this month?"
   - Fields needed:
     - `payments.payment_date`, `payments.due_date` (or `expected_payment_date`) — to compute delay
     - `payments.po_id` — link back to the PO
     - `purchase_orders.vendor_id` → `vendors.vendor_name` — to identify the vendor
     - `payments.amount` — for context (usually reported alongside the delay)
     - Date filter on `payments.payment_date` (or due date) falling in "this month"

2. "Summarize Q3 purchase orders by category."
   - Fields needed:
     - `purchase_orders.category`
     - `purchase_orders.amount`
     - `purchase_orders.po_date` — to filter to Q3
     - Aggregation: `COUNT(*)` and `SUM(amount)` grouped by `category`

3. "Flag any transactions that look unusual this week."
   - Fields needed:
     - `purchase_orders.amount` — to detect outliers (e.g. vs. vendor/category average)
     - `purchase_orders.po_date` — to scope to "this week"
     - `purchase_orders.vendor_id`, `purchase_orders.category` — grouping context for what "unusual" means
     - `purchase_orders.status` — duplicates/anomalies often show up as repeated status changes
     - Possibly `payments.payment_date` vs `purchase_orders.po_date` — for delay-based anomalies too
     - Note: "unusual" needs a defined rule (e.g. > 2 std dev from vendor/category mean, or duplicate PO detection on matching vendor+amount+date) — this is the one question that needs an explicit threshold decided before Day 3

4. "What's the average payment delay by vendor?"
   - Fields needed:
     - `payments.payment_date`, `payments.due_date` — to compute delay per payment
     - `payments.po_id` → `purchase_orders.vendor_id` → `vendors.vendor_name`
     - Aggregation: `AVG(delay)` grouped by `vendor_id`/`vendor_name`

5. "Show me all pending purchase orders above ₹1,00,000."
   - Fields needed:
     - `purchase_orders.status` — filter to "pending" (need to confirm the exact status value used in mock data, e.g. `Pending` vs `Open`)
     - `purchase_orders.amount` — filter `> 100000`
     - `purchase_orders.po_id`, `purchase_orders.vendor_id`, `purchase_orders.po_date` — to display in the result

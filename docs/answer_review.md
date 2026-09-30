# Answer review (run date 2026-09-30)

Score each answer: **Right / Partial / Wrong**, with a note. Check against the CSVs (or your own pandas/Excel calculation), not against how plausible the text sounds.

| # | Question | Score | Note |
|---|---|---|---|
| 1 | Which vendors had delayed payments this month? |  |  |
| 2 | Summarize Q3 purchase orders by category. |  |  |
| 3 | Flag any transactions that look unusual this week. |  |  |
| 4 | What's the average payment delay by vendor? |  |  |
| 5 | Show me all pending purchase orders above ₹1,00,000. |  |  |

## 1. Which vendors had delayed payments this month?

**Answer:**

The vendors that had delayed payments in September 2026 are:

- Quantum Circuit Traders (Vendor ID: V017)
- Summit Consulting Services (Vendor ID: V019)

**SQL:**
```sql
SELECT DISTINCT v.vendor_id, v.vendor_name
FROM payments p
JOIN vendors v ON p.vendor_id = v.vendor_id
WHERE p.payment_date IS NOT NULL
  AND julianday(p.payment_date) >= julianday('2026-09-01')
  AND julianday(p.payment_date) <= julianday('2026-09-30')
  AND julianday(p.payment_date) > julianday(p.due_date)
```

**Rows (2):**
```
vendor_id | vendor_name
V017 | Quantum Circuit Traders
V019 | Summit Consulting Services
```

## 2. Summarize Q3 purchase orders by category.

**Answer:**

**Q3 Purchase Orders Summary (July – September 2026)**  

| Category | Orders | Total Amount (INR) | Avg. Order (INR) |
|----------|--------|--------------------|------------------|
| **NULL** | 1 | 32,260.53 | 32,260.53 |
| **IT Hardware** | 8 | 896,136.52 | 112,017.07 |
| **MRO** | 13 | 448,391.71 | 34,491.67 |
| **Office Supplies** | 16 | 595,536.31 | 37,221.02 |
| **Packaging** | 10 | 1,047,600.24 | 1,047,600.02 |
| **Raw Materials** | 14 | 2,232,098.64 | 159,435.62 |
| **Services** | 10 | 1,223,087.51 | 122,308.75 |

- The largest volume of orders was in **Office Supplies** (16 orders) and **Raw Materials** (14 orders).  
- **Packaging** had the highest average order value (~₹1.05 M).  
- **IT Hardware** and **Services** each had 8 and 10 orders respectively, with average values of ~₹112 k and ~₹122 k.  
- The single **NULL** category order had a value of ₹32,260.53.

**SQL:**
```sql
SELECT category, COUNT(*) AS order_count, SUM(amount) AS total_amount, AVG(amount) AS avg_amount
FROM purchase_orders
WHERE po_date >= '2026-07-01' AND po_date <= '2026-09-30'
GROUP BY category
ORDER BY category
```

**Rows (7):**
```
category | order_count | total_amount | avg_amount
NULL | 1 | 32260.53 | 32260.53
IT Hardware | 8 | 896136.52 | 112017.065
MRO | 13 | 448391.71 | 34491.67
Office Supplies | 16 | 595536.3099999999 | 37221.019374999996
Packaging | 10 | 1047600.24 | 104760.024
Raw Materials | 14 | 2232098.64 | 159435.61714285714
Services | 10 | 1223087.51 | 122308.751
```

## 3. Flag any transactions that look unusual this week.

**Answer:**

**Unusual transactions flagged by the query**

| PO ID | Vendor | Amount (INR) | Date | Reason |
|-------|--------|--------------|------|--------|
| PO00020 | V003 | 377,271.17 | 2026‑05‑02 | Amount outlier for category |
| PO00081 | V012 | 248,530.75 | 2026‑08‑07 | Amount outlier for category |
| PO00148 | V028 | 622,838.25 | 2026‑09‑04 | Amount outlier for category |
| PO00221 | V014 | 50,191.21 | 2026‑05‑02 | Possible duplicate of PO00219 |
| PO00222 | V029 | 40,548.73 | 2026‑06‑12 | Possible duplicate of PO00168 |

These are the only transactions identified as unusual by the query. No other records matched.

**SQL:**
```sql
WITH s AS (
  SELECT category, AVG(amount) AS m,
         AVG(amount * amount) - AVG(amount) * AVG(amount) AS var
  FROM purchase_orders WHERE category IS NOT NULL GROUP BY category
)
SELECT po.po_id, po.vendor_id, po.category, po.amount, po.po_date, 'amount outlier for category' AS reason
FROM purchase_orders po JOIN s ON s.category = po.category
WHERE po.amount > s.m + 2 * sqrt(s.var)
UNION
SELECT a.po_id, a.vendor_id, a.category, a.amount, a.po_date, 'possible duplicate of ' || b.po_id
FROM purchase_orders a JOIN purchase_orders b
  ON a.vendor_id = b.vendor_id AND a.amount = b.amount
 AND a.po_date = b.po_date AND a.po_id > b.po_id
```

**Rows (5):**
```
po_id | vendor_id | category | amount | po_date | reason
PO00020 | V003 | MRO | 377271.17 | 2026-05-02 | amount outlier for category
PO00081 | V012 | Office Supplies | 248530.75 | 2026-08-07 | amount outlier for category
PO00148 | V028 | Packaging | 622838.25 | 2026-09-04 | amount outlier for category
PO00221 | V014 | IT Hardware | 50191.21 | 2026-05-02 | possible duplicate of PO00219
PO00222 | V029 | MRO | 40548.73 | 2026-06-12 | possible duplicate of PO00168
```

## 4. What's the average payment delay by vendor?

**Answer:**

The average payment delay for each vendor is:

- Bluewave Logistics (V002): 11.0 days  
- Cedar Point Supplies (V003): 24.0 days  
- Junction Freight Services (V010): 32.0 days  
- Keystone Manufacturing (V011): 23.0 days  
- Lakeside Chemicals (V012): 33.0 days  
- Northgate Stationery (V014): 28.0 days  
- Pinnacle MRO Supply (V016): 18.5 days  
- Quantum Circuit Traders (V017): 35.0 days  
- Summit Consulting Services (V019): 19.33 days (rounded)

**SQL:**
```sql
SELECT v.vendor_id, v.vendor_name, AVG(julianday(p.payment_date) - julianday(p.due_date)) AS avg_delay_days
FROM payments p
JOIN vendors v ON p.vendor_id = v.vendor_id
WHERE p.payment_date IS NOT NULL
  AND p.due_date IS NOT NULL
  AND julianday(p.payment_date) > julianday(p.due_date)
GROUP BY v.vendor_id, v.vendor_name
```

**Rows (9):**
```
vendor_id | vendor_name | avg_delay_days
V002 | Bluewave Logistics | 11.0
V003 | Cedar Point Supplies | 24.0
V010 | Junction Freight Services | 32.0
V011 | Keystone Manufacturing | 23.0
V012 | Lakeside Chemicals | 33.0
V014 | Northgate Stationery | 28.0
V016 | Pinnacle MRO Supply | 18.5
V017 | Quantum Circuit Traders | 35.0
V019 | Summit Consulting Services | 19.333333333333332
```

## 5. Show me all pending purchase orders above ₹1,00,000.

**Answer:**

**Pending purchase orders above ₹1,00,000**

| PO number | Vendor | Amount (₹) | Delivery delay |
|-----------|--------|------------|----------------|
| PO00013 | V001 | 281,565.64 | 22 days |
| PO00031 | V024 | 170,539.76 | 16 days |
| PO00032 | V007 | 190,586.88 | 27 days |
| PO00051 | V008 | 215,360.18 | 33 days |
| PO00057 | V009 | 138,215.00 | 9 days |
| PO00059 | V017 | 140,150.81 | 23 days |
| PO00091 | V019 | 115,681.63 | 30 days |
| PO00104 | V029 | 179,778.18 | – (delivery date missing) |
| PO00123 | V006 | 146,214.57 | 25 days |
| PO00131 | V025 | 116,747.66 | 24 days |
| PO00136 | V027 | 210,991.70 | 33 days |
| PO00151 | V015 | 227,835.40 | 16 days |
| PO00178 | V002 | 119,134.79 | 14 days |

All listed purchase orders are currently in **Pending** status and exceed ₹1,00,000. The delivery delay is calculated as the difference between the delivery date and the PO date; for PO00104 the delivery date is missing, so the delay is unknown.

**SQL:**
```sql
SELECT * FROM purchase_orders WHERE status = 'Pending' AND amount > 100000
```

**Rows (13):**
```
po_id | vendor_id | category | po_date | delivery_date | amount | status
PO00013 | V001 | Raw Materials | 2026-06-11 | 2026-07-03 | 281565.64 | Pending
PO00031 | V024 | Services | 2026-09-11 | 2026-09-27 | 170539.76 | Pending
PO00032 | V007 | Raw Materials | 2026-02-05 | 2026-03-04 | 190586.88 | Pending
PO00051 | V008 | IT Hardware | 2026-04-05 | 2026-05-08 | 215360.18 | Pending
PO00057 | V009 | IT Hardware | 2026-05-20 | 2026-05-29 | 138215.0 | Pending
PO00059 | V017 | Raw Materials | 2026-04-12 | 2026-05-05 | 140150.81 | Pending
PO00091 | V019 | IT Hardware | 2026-05-16 | 2026-06-15 | 115681.63 | Pending
PO00104 | V029 | Services | 2026-05-26 | NULL | 179778.18 | Pending
PO00123 | V006 | Raw Materials | 2026-09-02 | 2026-09-27 | 146214.57 | Pending
PO00131 | V025 | IT Hardware | 2026-08-19 | 2026-09-12 | 116747.66 | Pending
PO00136 | V027 | Raw Materials | 2026-08-29 | 2026-10-01 | 210991.7 | Pending
PO00151 | V015 | Raw Materials | 2026-08-02 | 2026-08-18 | 227835.4 | Pending
PO00178 | V002 | Raw Materials | 2026-09-14 | 2026-09-28 | 119134.79 | Pending
```
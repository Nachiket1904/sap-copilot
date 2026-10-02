# Answer review (run date 2026-09-30)

Check each answer against `python -m tests.check_answers` (independent pandas calculation), not against how plausible the text sounds.

Three things can fail independently: SQL correct? Answer matches the data? Phrasing clear and free of invented numbers?

| # | Question | SQL ok? | Answer ok? | Phrasing ok? | Overall (Right/Partial/Wrong) | Note |
|---|---|---|---|---|---|---|
| 1 | Which vendors had delayed payments this month? |  |  |  |  |  |
| 2 | Summarize Q3 purchase orders by category. |  |  |  |  |  |
| 3 | Flag any transactions that look unusual this week. |  |  |  |  |  |
| 4 | What's the average payment delay by vendor? |  |  |  |  |  |
| 5 | Show me all pending purchase orders above ₹1,00,000. |  |  |  |  |  |

## 1. Which vendors had delayed payments this month?

**Answer:**

The vendors that had delayed payments this month were **Quantum Circuit Traders** and **Summit Consulting Services**.

**SQL:**
```sql
SELECT DISTINCT v.vendor_name
FROM payments p
JOIN vendors v ON v.vendor_id = p.vendor_id
WHERE p.status = 'Paid'
  AND p.payment_date BETWEEN '2026-09-01' AND '2026-09-30'
  AND julianday(p.payment_date) > julianday(p.due_date)
ORDER BY v.vendor_name
```

**Rows (2):**
```
vendor_name
Quantum Circuit Traders
Summit Consulting Services
```

## 2. Summarize Q3 purchase orders by category.

**Answer:**

**Q3 Purchase Order Summary**

- **Raw Materials** – 14 orders, total ₹2,232,098.64, average ₹159,435.62 per order.  
- **Office Supplies** – 16 orders, total ₹595,536.31, average ₹37,221.02 per order.  
- **MRO** – 13 orders, total ₹448,391.71, average ₹34,491.67 per order.  
- **Services** – 10 orders, total ₹1,223,087.51, average ₹122,308.75 per order.  
- **Packaging** – 10 orders, total ₹1,047,600.24, average ₹104,760.02 per order.  
- **IT Hardware** – 8 orders, total ₹896,136.52, average ₹112,017.07 per order.  
- **Uncategorized** – 1 order, total ₹32,260.53, average ₹32,260.53 per order.

**SQL:**
```sql
SELECT COALESCE(po.category, 'Uncategorized') AS category,
       COUNT(*) AS po_count,
       ROUND(SUM(po.amount), 2) AS total_amount,
       ROUND(AVG(po.amount), 2) AS avg_amount
FROM purchase_orders po
WHERE po.po_date BETWEEN '2026-07-01' AND '2026-09-30'
GROUP BY category
ORDER BY po_count DESC
```

**Rows (7):**
```
category | po_count | total_amount | avg_amount
Office Supplies | 16 | 595536.31 | 37221.02
Raw Materials | 14 | 2232098.64 | 159435.62
MRO | 13 | 448391.71 | 34491.67
Services | 10 | 1223087.51 | 122308.75
Packaging | 10 | 1047600.24 | 104760.02
IT Hardware | 8 | 896136.52 | 112017.07
Uncategorized | 1 | 32260.53 | 32260.53
```

## 3. Flag any transactions that look unusual this week.

**Answer:**

**Unusual transactions flagged for this week**

| PO ID | Vendor | Amount (INR) | Reason |
|-------|--------|--------------|--------|
| PO00020 | V003 | 377,271.17 | Amount outlier for category (MRO) |
| PO00081 | V012 | 248,530.75 | Amount outlier for category (Office Supplies) |
| PO00148 | V028 | 622,838.25 | Amount outlier for category (Packaging) |
| PO00221 | V014 | 50,191.21 | Possible duplicate of PO00219 |
| PO00222 | V029 | 40,548.73 | Possible duplicate of PO00168 |

These five purchase orders were identified by the query as either statistical outliers in their category or potential duplicates. No additional delay information is available in the results.

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

- Bluewave Logistics: 11.0 days  
- Cedar Point Supplies: 24.0 days  
- Junction Freight Services: 32.0 days  
- Keystone Manufacturing: 23.0 days  
- Lakeside Chemicals: 33.0 days  
- Northgate Stationery: 28.0 days  
- Pinnacle MRO Supply: 18.5 days  
- Quantum Circuit Traders: 35.0 days  
- Summit Consulting Services: 19.33 days

**SQL:**
```sql
SELECT v.vendor_name, ROUND(AVG(julianday(p.payment_date) - julianday(p.due_date)), 2) AS avg_payment_delay_days
FROM payments p
JOIN vendors v ON v.vendor_id = p.vendor_id
WHERE p.payment_date > p.due_date
GROUP BY v.vendor_name
```

**Rows (9):**
```
vendor_name | avg_payment_delay_days
Bluewave Logistics | 11.0
Cedar Point Supplies | 24.0
Junction Freight Services | 32.0
Keystone Manufacturing | 23.0
Lakeside Chemicals | 33.0
Northgate Stationery | 28.0
Pinnacle MRO Supply | 18.5
Quantum Circuit Traders | 35.0
Summit Consulting Services | 19.33
```

## 5. Show me all pending purchase orders above ₹1,00,000.

**Answer:**

Here are all the pending purchase orders with amounts above ₹1,00,000:

| PO Number | Vendor | Category | PO Date | Delivery Date | Amount (₹) |
|-----------|--------|----------|---------|---------------|------------|
| PO00013 | Apex Steel Works | Raw Materials | 2026‑06‑11 | 2026‑07‑03 | 281,565.64 |
| PO00031 | Yellowline Transport | Services | 2026‑09‑11 | 2026‑09‑27 | 170,539.76 |
| PO00032 | Granite Office Solutions | Raw Materials | 2026‑02‑05 | 2026‑03‑04 | 190,586.88 |
| PO00051 | Horizon Raw Materials | IT Hardware | 2026‑04‑05 | 2026‑05‑08 | 215,360.18 |
| PO00057 | Ironclad Fasteners | IT Hardware | 2026‑05‑20 | 2026‑05‑29 | 138,215.00 |
| PO00059 | Quantum Circuit Traders | Raw Materials | 2026‑04‑12 | 2026‑05‑05 | 140,150.81 |
| PO00091 | Summit Consulting Services | IT Hardware | 2026‑05‑16 | 2026‑06‑15 | 115,681.63 |
| PO00104 | Dockyard Marine Supplies | Services | 2026‑05‑26 | **NULL** | 179,778.18 |
| PO00123 | Falcon Electronics | Raw Materials | 2026‑09‑02 | 2026‑09‑27 | 146,214.57 |
| PO00131 | Zenith Energy Systems | IT Hardware | 2026‑08‑19 | 2026‑09‑12 | 116,747.66 |
| PO00136 | Brightline Electricals | Raw Materials | 2026‑08‑29 | 2026‑10‑01 | 210,991.70 |
| PO00151 | Orion Safety Equipment | Raw Materials | 2026‑08‑02 | 2026‑08‑18 | 227,835.40 |
| PO00178 | Bluewave Logistics | Raw Materials | 2026‑09‑14 | 2026‑09‑28 | 119,134.79 |

All listed purchase orders are currently in the **Pending** status and exceed ₹1,00,000. The only order with a missing delivery date is PO00104.

**SQL:**
```sql
SELECT po.po_id, po.vendor_id, v.vendor_name, COALESCE(po.category, 'Uncategorized') AS category, po.po_date, po.delivery_date, po.amount, po.status
FROM purchase_orders po
JOIN vendors v ON v.vendor_id = po.vendor_id
WHERE po.status = 'Pending' AND po.amount > 100000
```

**Rows (13):**
```
po_id | vendor_id | vendor_name | category | po_date | delivery_date | amount | status
PO00013 | V001 | Apex Steel Works | Raw Materials | 2026-06-11 | 2026-07-03 | 281565.64 | Pending
PO00031 | V024 | Yellowline Transport | Services | 2026-09-11 | 2026-09-27 | 170539.76 | Pending
PO00032 | V007 | Granite Office Solutions | Raw Materials | 2026-02-05 | 2026-03-04 | 190586.88 | Pending
PO00051 | V008 | Horizon Raw Materials | IT Hardware | 2026-04-05 | 2026-05-08 | 215360.18 | Pending
PO00057 | V009 | Ironclad Fasteners | IT Hardware | 2026-05-20 | 2026-05-29 | 138215.0 | Pending
PO00059 | V017 | Quantum Circuit Traders | Raw Materials | 2026-04-12 | 2026-05-05 | 140150.81 | Pending
PO00091 | V019 | Summit Consulting Services | IT Hardware | 2026-05-16 | 2026-06-15 | 115681.63 | Pending
PO00104 | V029 | Dockyard Marine Supplies | Services | 2026-05-26 | NULL | 179778.18 | Pending
PO00123 | V006 | Falcon Electronics | Raw Materials | 2026-09-02 | 2026-09-27 | 146214.57 | Pending
PO00131 | V025 | Zenith Energy Systems | IT Hardware | 2026-08-19 | 2026-09-12 | 116747.66 | Pending
PO00136 | V027 | Brightline Electricals | Raw Materials | 2026-08-29 | 2026-10-01 | 210991.7 | Pending
PO00151 | V015 | Orion Safety Equipment | Raw Materials | 2026-08-02 | 2026-08-18 | 227835.4 | Pending
PO00178 | V002 | Bluewave Logistics | Raw Materials | 2026-09-14 | 2026-09-28 | 119134.79 | Pending
```
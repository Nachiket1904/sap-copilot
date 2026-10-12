# Answer review (run date 2026-09-30)

Scored 2026-10-12 against `python -m tests.check_answers`. Result: **5/5 Right**. Two runs gave identical answers for all 5 questions.
Caveat: LLM wording varies between runs; the eval (`tests/eval_answers.py`) checks key values, not wording.

Check each answer against `python -m tests.check_answers` (independent pandas calculation), not against how plausible the text sounds.

Three things can fail independently: SQL correct? Answer matches the data? Phrasing clear and free of invented numbers?

| # | Question | SQL ok? | Answer ok? | Phrasing ok? | Overall (Right/Partial/Wrong) | Note |
|---|---|---|---|---|---|---|
| 1 | Which vendors had delayed payments this month? | Y | Y | Y | Right | V017, V019 match ground truth (Sep 2026, payment_date > due_date). |
| 2 | Summarize Q3 purchase orders by category. | Y | Y | Y | Right | 7 categories, counts/totals/averages match; missing category shown as Uncategorized. Fixed earlier bug (Packaging avg was 10x). |
| 3 | Flag any transactions that look unusual this week. | Y | Y | Y | Right | 11 flags: 3 amount outliers + 2 duplicates + 6 late payments. Scans all records, not one week (stated in answer). Earlier run labelled days under an INR column; fixed with a unit column. |
| 4 | What's the average payment delay by vendor? | Y | Y | Y | Right | 9 vendors, averages over delayed payments only; match ground truth. |
| 5 | Show me all pending purchase orders above ₹1,00,000. | Y | Y | Y | Right | 13 pending POs > 100000, all match; NULL delivery date on PO00104 mentioned. |

## 1. Which vendors had delayed payments this month?

**Answer:**

The vendors that had delayed payments this month were **Quantum Circuit Traders** and **Summit Consulting Services**.

**SQL:**
```sql
SELECT DISTINCT v.vendor_name
FROM payments p
JOIN vendors v ON v.vendor_id = p.vendor_id
WHERE p.payment_date IS NOT NULL
  AND p.payment_date > p.due_date
  AND p.payment_date BETWEEN '2026-09-01' AND '2026-09-30'
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

In Q3 (July‑September 2026) the purchase orders were distributed across seven categories:

- **Raw Materials** – 14 orders, totaling ₹2,232,098.64  
- **Office Supplies** – 16 orders, totaling ₹595,536.31  
- **MRO** – 13 orders, totaling ₹448,391.71  
- **Services** – 10 orders, totaling ₹1,223,087.51  
- **Packaging** – 10 orders, totaling ₹1,047,600.24  
- **IT Hardware** – 8 orders, totaling ₹896,136.52  
- **Uncategorized** – 1 order, totaling ₹32,260.53  

These figures show the volume and monetary value of orders by category for the quarter.

**SQL:**
```sql
SELECT COALESCE(category, 'Uncategorized') AS category,
       COUNT(*) AS po_count,
       ROUND(SUM(amount), 2) AS total_amount
FROM purchase_orders
WHERE po_date BETWEEN '2026-07-01' AND '2026-09-30'
GROUP BY category
ORDER BY po_count DESC
```

**Rows (7):**
```
category | po_count | total_amount
Office Supplies | 16 | 595536.31
Raw Materials | 14 | 2232098.64
MRO | 13 | 448391.71
Services | 10 | 1223087.51
Packaging | 10 | 1047600.24
IT Hardware | 8 | 896136.52
Uncategorized | 1 | 32260.53
```

## 3. Flag any transactions that look unusual this week.

**Answer:**

The anomaly scan flagged the following transactions (across all time, not just this week):

- **Payment delay outliers**  
  - PMT00028 – Quantum Circuit Traders – 35.0 days late  
  - PMT00093 – Northgate Stationery – 30.0 days late  
  - PMT00102 – Junction Freight Services – 32.0 days late  
  - PMT00103 – Pinnacle MRO Supply – 26.0 days late  
  - PMT00112 – Northgate Stationery – 26.0 days late  
  - PMT00151 – Lakeside Chemicals – 33.0 days late  

- **Amount outliers for category**  
  - PO00020 – Cedar Point Supplies – 377,271.17 INR (MRO)  
  - PO00081 – Lakeside Chemicals – 248,530.75 INR (Office Supplies)  
  - PO00148 – Coastal Tools & Equipment – 622,838.25 INR (Packaging)  

- **Possible duplicate purchase orders**  
  - PO00221 – Northgate Stationery – 50,191.21 INR (same vendor, amount and date as PO00219)  
  - PO00222 – Dockyard Marine Supplies – 40,548.73 INR (same vendor, amount and date as PO00168)

**SQL:**
```sql
-- deterministic rules in src/data_layer/anomaly.py (no SQL)
```

**Rows (11):**
```
rule | record_id | vendor_id | vendor_name | value | unit | detail
payment delay outlier | PMT00028 | V017 | Quantum Circuit Traders | 35.0 | days late | paid 35 days after due date (mean -10.8, flag above 24.6)
payment delay outlier | PMT00093 | V014 | Northgate Stationery | 30.0 | days late | paid 30 days after due date (mean -10.8, flag above 24.6)
payment delay outlier | PMT00102 | V010 | Junction Freight Services | 32.0 | days late | paid 32 days after due date (mean -10.8, flag above 24.6)
payment delay outlier | PMT00103 | V016 | Pinnacle MRO Supply | 26.0 | days late | paid 26 days after due date (mean -10.8, flag above 24.6)
payment delay outlier | PMT00112 | V014 | Northgate Stationery | 26.0 | days late | paid 26 days after due date (mean -10.8, flag above 24.6)
payment delay outlier | PMT00151 | V012 | Lakeside Chemicals | 33.0 | days late | paid 33 days after due date (mean -10.8, flag above 24.6)
amount outlier for category | PO00020 | V003 | Cedar Point Supplies | 377271.17 | INR | MRO: 377,271.17 vs category mean 41,561.74
amount outlier for category | PO00081 | V012 | Lakeside Chemicals | 248530.75 | INR | Office Supplies: 248,530.75 vs category mean 25,885.00
amount outlier for category | PO00148 | V028 | Coastal Tools & Equipment | 622838.25 | INR | Packaging: 622,838.25 vs category mean 61,335.40
possible duplicate PO | PO00221 | V014 | Northgate Stationery | 50191.21 | INR | same vendor, amount and date as PO00219
possible duplicate PO | PO00222 | V029 | Dockyard Marine Supplies | 40548.73 | INR | same vendor, amount and date as PO00168
```

## 4. What's the average payment delay by vendor?

**Answer:**

The average payment delays for each vendor are:

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
SELECT v.vendor_name, ROUND(AVG(julianday(p.payment_date)-julianday(p.due_date)), 2) AS avg_delay
FROM payments p
JOIN vendors v ON v.vendor_id = p.vendor_id
WHERE p.payment_date IS NOT NULL
  AND p.due_date IS NOT NULL
  AND p.payment_date > p.due_date
GROUP BY v.vendor_id, v.vendor_name
```

**Rows (9):**
```
vendor_name | avg_delay
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

**Pending purchase orders above ₹1,00,000**

| PO ID | Vendor | Amount (INR) | Delivery date | Note |
|-------|--------|--------------|---------------|------|
| PO00013 | Apex Steel Works | 281,565.64 | 2026‑07‑03 | – |
| PO00151 | Orion Safety Equipment | 227,835.40 | 2026‑08‑18 | – |
| PO00051 | Horizon Raw Materials | 215,360.18 | 2026‑05‑08 | – |
| PO00136 | Brightline Electricals | 210,991.70 | 2026‑10‑01 | – |
| PO00032 | Granite Office Solutions | 190,586.88 | 2026‑03‑04 | – |
| PO00104 | Dockyard Marine Supplies | 179,778.18 | NULL | Delivery date not set |
| PO00031 | Yellowline Transport | 170,539.76 | 2026‑09‑27 | – |
| PO00123 | Falcon Electronics | 146,214.57 | 2026‑09‑27 | – |
| PO00059 | Quantum Circuit Traders | 140,150.81 | 2026‑05‑05 | – |
| PO00057 | Ironclad Fasteners | 138,215.00 | 2026‑05‑29 | – |
| PO00178 | Bluewave Logistics | 119,134.79 | 2026‑09‑28 | – |
| PO00131 | Zenith Energy Systems | 116,747.66 | 2026‑09‑12 | – |
| PO00091 | Summit Consulting Services | 115,681.63 | 2026‑06‑15 | – |

All listed purchase orders are currently **Pending** and exceed ₹1,00,000. The only order without a specified delivery date is **PO00104** (Dockyard Marine Supplies).

**SQL:**
```sql
SELECT po.po_id, v.vendor_name, COALESCE(po.category, 'Uncategorized') AS category, po.po_date, po.delivery_date, po.amount, po.status
FROM purchase_orders po
JOIN vendors v ON v.vendor_id = po.vendor_id
WHERE po.status = 'Pending' AND po.amount > 100000
ORDER BY po.amount DESC
```

**Rows (13):**
```
po_id | vendor_name | category | po_date | delivery_date | amount | status
PO00013 | Apex Steel Works | Raw Materials | 2026-06-11 | 2026-07-03 | 281565.64 | Pending
PO00151 | Orion Safety Equipment | Raw Materials | 2026-08-02 | 2026-08-18 | 227835.4 | Pending
PO00051 | Horizon Raw Materials | IT Hardware | 2026-04-05 | 2026-05-08 | 215360.18 | Pending
PO00136 | Brightline Electricals | Raw Materials | 2026-08-29 | 2026-10-01 | 210991.7 | Pending
PO00032 | Granite Office Solutions | Raw Materials | 2026-02-05 | 2026-03-04 | 190586.88 | Pending
PO00104 | Dockyard Marine Supplies | Services | 2026-05-26 | NULL | 179778.18 | Pending
PO00031 | Yellowline Transport | Services | 2026-09-11 | 2026-09-27 | 170539.76 | Pending
PO00123 | Falcon Electronics | Raw Materials | 2026-09-02 | 2026-09-27 | 146214.57 | Pending
PO00059 | Quantum Circuit Traders | Raw Materials | 2026-04-12 | 2026-05-05 | 140150.81 | Pending
PO00057 | Ironclad Fasteners | IT Hardware | 2026-05-20 | 2026-05-29 | 138215.0 | Pending
PO00178 | Bluewave Logistics | Raw Materials | 2026-09-14 | 2026-09-28 | 119134.79 | Pending
PO00131 | Zenith Energy Systems | IT Hardware | 2026-08-19 | 2026-09-12 | 116747.66 | Pending
PO00091 | Summit Consulting Services | IT Hardware | 2026-05-16 | 2026-06-15 | 115681.63 | Pending
```
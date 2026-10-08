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
WHERE p.payment_date BETWEEN '2026-09-01' AND '2026-09-30'
  AND p.payment_date > p.due_date
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

- **Raw Materials**: 14 orders, totaling ₹2,232,098.64, with an average of ₹159,435.62 per order.  
- **Office Supplies**: 16 orders, totaling ₹595,536.31, average ₹37,221.02.  
- **Packaging**: 10 orders, totaling ₹1,047,600.24, average ₹104,760.02.  
- **Services**: 10 orders, totaling ₹1,223,087.51, average ₹122,308.75.  
- **MRO**: 13 orders, totaling ₹448,391.71, average ₹34,491.67.  
- **IT Hardware**: 8 orders, totaling ₹896,136.52, average ₹112,017.07.  
- **Uncategorized**: 1 order, totaling ₹32,260.53, average ₹32,260.53.

**SQL:**
```sql
SELECT COALESCE(po.category, 'Uncategorized') AS category,
       COUNT(*) AS po_count,
       ROUND(SUM(po.amount), 2) AS total_amount,
       ROUND(AVG(po.amount), 2) AS avg_amount
FROM purchase_orders po
WHERE po.po_date BETWEEN '2026-07-01' AND '2026-09-30'
GROUP BY COALESCE(po.category, 'Uncategorized')
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

The anomaly scan flagged the following transactions across the entire dataset (not limited to this week):

- **Payment delay outliers**  
  - PMT00028 – Quantum Circuit Traders – 35 days late (mean –10.8, flag > 24.6)  
  - PMT00093 – Northgate Stationery – 30 days late (mean –10.8, flag > 24.6)  
  - PMT00102 – Junction Freight Services – 32 days late (mean –10.8, flag > 24.6)  
  - PMT00103 – Pinnacle MRO Supply – 26 days late (mean –10.8, flag > 24.6)  
  - PMT00112 – Northgate Stationery – 26 days late (mean –10.8, flag > 24.6)  
  - PMT00151 – Lakeside Chemicals – 33 days late (mean –10.8, flag > 24.6)

- **Amount outliers for category**  
  - PO00020 – Cedar Point Supplies – ₹377,271.17 (MRO: ₹377,271.17 vs category mean ₹41,561.74)  
  - PO00081 – Lakeside Chemicals – ₹248,530.75 (Office Supplies: ₹248,530.75 vs category mean ₹25,885.00)  
  - PO00148 – Coastal Tools & Equipment – ₹622,838.25 (Packaging: ₹622,838.25 vs category mean ₹61,335.40)

- **Possible duplicate purchase orders**  
  - PO00221 – Northgate Stationery – ₹50,191.21 (same vendor, amount and date as PO00219)  
  - PO00222 – Dockyard Marine Supplies – ₹40,548.73 (same vendor, amount and date as PO00168)

These are the transactions flagged as unusual by the deterministic rules.

**SQL:**
```sql
-- deterministic rules in src/data_layer/anomaly.py (no SQL)
```

**Rows (11):**
```
rule | record_id | vendor_id | vendor_name | value | detail
payment delay outlier | PMT00028 | V017 | Quantum Circuit Traders | 35.0 | paid 35 days after due date (mean -10.8, flag above 24.6)
payment delay outlier | PMT00093 | V014 | Northgate Stationery | 30.0 | paid 30 days after due date (mean -10.8, flag above 24.6)
payment delay outlier | PMT00102 | V010 | Junction Freight Services | 32.0 | paid 32 days after due date (mean -10.8, flag above 24.6)
payment delay outlier | PMT00103 | V016 | Pinnacle MRO Supply | 26.0 | paid 26 days after due date (mean -10.8, flag above 24.6)
payment delay outlier | PMT00112 | V014 | Northgate Stationery | 26.0 | paid 26 days after due date (mean -10.8, flag above 24.6)
payment delay outlier | PMT00151 | V012 | Lakeside Chemicals | 33.0 | paid 33 days after due date (mean -10.8, flag above 24.6)
amount outlier for category | PO00020 | V003 | Cedar Point Supplies | 377271.17 | MRO: 377,271.17 vs category mean 41,561.74
amount outlier for category | PO00081 | V012 | Lakeside Chemicals | 248530.75 | Office Supplies: 248,530.75 vs category mean 25,885.00
amount outlier for category | PO00148 | V028 | Coastal Tools & Equipment | 622838.25 | Packaging: 622,838.25 vs category mean 61,335.40
possible duplicate PO | PO00221 | V014 | Northgate Stationery | 50191.21 | same vendor, amount and date as PO00219
possible duplicate PO | PO00222 | V029 | Dockyard Marine Supplies | 40548.73 | same vendor, amount and date as PO00168
```

## 4. What's the average payment delay by vendor?

**Answer:**

The average payment delays (in days) for each vendor are:

- Quantum Circuit Traders – 35.0 days  
- Lakeside Chemicals – 33.0 days  
- Junction Freight Services – 32.0 days  
- Northgate Stationery – 28.0 days  
- Cedar Point Supplies – 24.0 days  
- Keystone Manufacturing – 23.0 days  
- Summit Consulting Services – 19.33 days  
- Pinnacle MRO Supply – 18.5 days  
- Bluewave Logistics – 11.0 days

**SQL:**
```sql
SELECT v.vendor_name, ROUND(AVG(julianday(p.payment_date) - julianday(p.due_date)), 2) AS avg_delay
FROM payments p
JOIN vendors v ON v.vendor_id = p.vendor_id
WHERE p.payment_date IS NOT NULL
  AND p.due_date IS NOT NULL
  AND p.payment_date > p.due_date
GROUP BY v.vendor_name
ORDER BY avg_delay DESC
```

**Rows (9):**
```
vendor_name | avg_delay
Quantum Circuit Traders | 35.0
Lakeside Chemicals | 33.0
Junction Freight Services | 32.0
Northgate Stationery | 28.0
Cedar Point Supplies | 24.0
Keystone Manufacturing | 23.0
Summit Consulting Services | 19.33
Pinnacle MRO Supply | 18.5
Bluewave Logistics | 11.0
```

## 5. Show me all pending purchase orders above ₹1,00,000.

**Answer:**

Here are the pending purchase orders above ₹1,00,000:

- **PO00013** – Apex Steel Works – ₹281,565.64 – Delivery: 2026‑07‑03  
- **PO00031** – Yellowline Transport – ₹170,539.76 – Delivery: 2026‑09‑27  
- **PO00032** – Granite Office Solutions – ₹190,586.88 – Delivery: 2026‑03‑04  
- **PO00051** – Horizon Raw Materials – ₹215,360.18 – Delivery: 2026‑05‑08  
- **PO00057** – Ironclad Fasteners – ₹138,215.00 – Delivery: 2026‑05‑29  
- **PO00059** – Quantum Circuit Traders – ₹140,150.81 – Delivery: 2026‑05‑05  
- **PO00091** – Summit Consulting Services – ₹115,681.63 – Delivery: 2026‑06‑15  
- **PO00104** – Dockyard Marine Supplies – ₹179,778.18 – Delivery: NULL  
- **PO00123** – Falcon Electronics – ₹146,214.57 – Delivery: 2026‑09‑27  
- **PO00131** – Zenith Energy Systems – ₹116,747.66 – Delivery: 2026‑09‑12  
- **PO00136** – Brightline Electricals – ₹210,991.70 – Delivery: 2026‑10‑01  
- **PO00151** – Orion Safety Equipment – ₹227,835.40 – Delivery: 2026‑08‑18  
- **PO00178** – Bluewave Logistics – ₹119,134.79 – Delivery: 2026‑09‑28

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
"""Pre-built, deterministic query for Q3 ("unusual transactions").

Rule from docs/architecture.md (Decision 2): flag a PO if its amount is more
than 2 standard deviations above its category mean, or if another PO has the
same vendor_id + amount + po_date (likely double entry).
"""
import re

ANOMALY_SQL = """
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
"""

_UNUSUAL = re.compile(r"\b(unusual|anomal\w*|suspicious|outlier\w*|duplicate\w*)\b", re.IGNORECASE)


def is_anomaly_question(question: str) -> bool:
    return bool(_UNUSUAL.search(question))

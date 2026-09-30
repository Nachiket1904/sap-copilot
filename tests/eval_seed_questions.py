"""Live check: does the LLM write correct SQL for the seed questions?

Not part of `pytest` (costs a real LLM call per question). Run:
    python -m tests.eval_seed_questions

For each question the LLM's SQL is executed, and its rows are compared with a
hand-written reference query. Extra columns are fine, and floats are compared
to 1 decimal place; the reference rows must all appear and the row counts match.
Q3 ("unusual this week") is skipped: it uses a pre-built rule, and the data has no
POs in the current week.
"""
import sys

from src.data_layer.loader import load_to_sqlite
from src.retrieval.text_to_sql import generate_sql, run_select

TODAY = "2026-09-30"

CASES = [
    ("Which vendors had delayed payments this month?", """
        SELECT DISTINCT v.vendor_name FROM payments p JOIN vendors v ON v.vendor_id = p.vendor_id
        WHERE p.payment_date > p.due_date AND p.payment_date BETWEEN '2026-09-01' AND '2026-09-30'"""),
    ("Summarize Q3 purchase orders by category.", """
        SELECT category, COUNT(*), SUM(amount) FROM purchase_orders
        WHERE po_date BETWEEN '2026-07-01' AND '2026-09-30' GROUP BY category"""),
    ("What's the average payment delay by vendor?", """
        SELECT v.vendor_name, AVG(julianday(p.payment_date) - julianday(p.due_date))
        FROM payments p JOIN vendors v ON v.vendor_id = p.vendor_id
        WHERE p.payment_date > p.due_date GROUP BY v.vendor_name"""),
    ("Show me all pending purchase orders above ₹1,00,000.", """
        SELECT po_id FROM purchase_orders WHERE status = 'Pending' AND amount > 100000"""),
]


def _norm(value):
    return round(value, 1) if isinstance(value, float) else value


def _row_values(row):
    return {_norm(v) for v in row if v is not None}  # NULL in reference may be 'Uncategorized' in the answer


def matches(reference_rows, generated_rows) -> bool:
    if len(reference_rows) != len(generated_rows):
        return False
    generated = [_row_values(r) for r in generated_rows]
    return all(any(_row_values(ref) <= g for g in generated) for ref in reference_rows)


def main() -> int:
    conn = load_to_sqlite(verbose=False)
    failures = 0
    for question, reference_sql in CASES:
        _, expected = run_select(conn, reference_sql)
        try:
            sql = generate_sql(question, conn, today=TODAY)
            _, got = run_select(conn, sql)
            ok = matches(expected, got)
        except Exception as exc:  # bad SQL, rejected SQL, API error
            sql, got, ok = f"<{type(exc).__name__}: {exc}>", [], False
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {question}  (expected {len(expected)} rows, got {len(got)})")
        if not ok:
            print(f"  generated SQL: {sql}\n  expected sample: {expected[:3]}\n  got sample:      {got[:3]}")
    print(f"\n{len(CASES) - failures}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())

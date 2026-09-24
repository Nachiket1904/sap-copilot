"""Proves every Day 2 seed question can be answered with plain SQL on the mock data.

If one of these breaks, the schema (or the data) changed in a way the
LLM layer will trip over in Week 2.
"""
import pytest

from src.data_layer.loader import load_to_sqlite


@pytest.fixture(scope="module")
def conn():
    c = load_to_sqlite()
    yield c
    c.close()


def test_foreign_keys_resolve(conn):
    orphans = conn.execute("""
        SELECT
          (SELECT COUNT(*) FROM purchase_orders WHERE vendor_id NOT IN (SELECT vendor_id FROM vendors)),
          (SELECT COUNT(*) FROM payments WHERE po_id NOT IN (SELECT po_id FROM purchase_orders)),
          (SELECT COUNT(*) FROM payments WHERE vendor_id NOT IN (SELECT vendor_id FROM vendors))
    """).fetchone()
    assert orphans == (0, 0, 0)


def test_q1_delayed_payments(conn):
    rows = conn.execute("""
        SELECT v.vendor_name, p.po_id,
               julianday(p.payment_date) - julianday(p.due_date) AS days_late
        FROM payments p JOIN vendors v ON v.vendor_id = p.vendor_id
        WHERE p.payment_date > p.due_date
    """).fetchall()
    assert len(rows) == 12  # seeded delay cases
    assert all(r[2] > 0 for r in rows)


def test_q2_q3_pos_by_category(conn):
    rows = conn.execute("""
        SELECT COALESCE(category, 'Uncategorized') AS cat, COUNT(*), SUM(amount)
        FROM purchase_orders
        WHERE po_date BETWEEN '2026-07-01' AND '2026-09-30'
        GROUP BY cat
    """).fetchall()
    assert len(rows) >= 6
    assert all(r[2] > 0 for r in rows)


def test_q3_unusual_outliers_and_duplicates(conn):
    outliers = conn.execute("""
        WITH s AS (
          SELECT category, AVG(amount) AS m,
                 AVG(amount * amount) - AVG(amount) * AVG(amount) AS var
          FROM purchase_orders WHERE category IS NOT NULL GROUP BY category
        )
        SELECT po.po_id FROM purchase_orders po JOIN s ON s.category = po.category
        WHERE po.amount > s.m + 2 * sqrt(s.var)
    """).fetchall()
    duplicates = conn.execute("""
        SELECT a.po_id FROM purchase_orders a JOIN purchase_orders b
          ON a.vendor_id = b.vendor_id AND a.amount = b.amount
         AND a.po_date = b.po_date AND a.po_id > b.po_id
    """).fetchall()
    assert len(outliers) == 3
    assert len(duplicates) == 2


def test_q4_avg_delay_by_vendor(conn):
    rows = conn.execute("""
        SELECT vendor_id, AVG(julianday(payment_date) - julianday(due_date))
        FROM payments WHERE payment_date > due_date
        GROUP BY vendor_id
    """).fetchall()
    assert len(rows) > 0


def test_q5_pending_above_1_lakh(conn):
    rows = conn.execute("""
        SELECT po_id FROM purchase_orders
        WHERE status = 'Pending' AND amount > 100000
    """).fetchall()
    assert len(rows) > 0


def test_blank_cells_are_null_not_empty_string(conn):
    # Why this matters: the LLM prompt must say IS NULL, not = ''
    nulls, empties = conn.execute("""
        SELECT SUM(category IS NULL), SUM(category = '') FROM purchase_orders
    """).fetchone()
    assert nulls == 2
    assert not empties
import sqlite3

from src.data_layer.loader import load_to_sqlite, run_quality_checks


def test_load_to_sqlite_runs_without_error():
    conn = load_to_sqlite()
    assert conn is not None
    conn.close()


def test_real_data_passes_quality_checks():
    conn = load_to_sqlite(verbose=False)
    assert run_quality_checks(conn) == []
    conn.close()


def test_malformed_amount_becomes_null_and_column_stays_numeric():
    # PMT00168 has amount "TBD"; it must load (not be dropped) as NULL,
    # and must not turn the whole column into TEXT.
    conn = load_to_sqlite(verbose=False)
    row = conn.execute("SELECT amount FROM payments WHERE payment_id = 'PMT00168'").fetchone()
    assert row == (None,)
    assert conn.execute("SELECT typeof(SUM(amount)) FROM payments").fetchone()[0] == "real"
    conn.close()


def test_currency_formatting_is_recovered(tmp_path):
    (tmp_path / "purchase_orders.csv").write_text("po_id,amount\nPO1,\"₹1,25,000\"\nPO2,12500.50\nPO3,\nPO4,n/a\n", encoding="utf-8")
    conn = load_to_sqlite(data_dir=tmp_path, verbose=False)
    rows = dict(conn.execute("SELECT po_id, amount FROM purchase_orders").fetchall())
    assert rows == {"PO1": 125000.0, "PO2": 12500.5, "PO3": None, "PO4": None}


def test_quality_check_catches_duplicate_po_and_missing_tables():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE purchase_orders (po_id TEXT)")
    conn.executemany("INSERT INTO purchase_orders VALUES (?)", [("PO1",), ("PO1",)])
    problems = run_quality_checks(conn)
    assert any("duplicate po_id" in p for p in problems)
    assert any("vendors: table missing" in p for p in problems)

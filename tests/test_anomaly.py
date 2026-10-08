import pandas as pd

from src.data_layer.anomaly import delay_anomalies, duplicate_anomalies, find_anomalies
from src.data_layer.loader import flag_bad_rows, load_to_sqlite

VENDORS = pd.DataFrame({"vendor_id": ["V1", "V2"], "vendor_name": ["Alpha", "Beta"]})


def _payments(delays):
    rows = [(f"PMT{i}", "V1" if i else "V2", "2026-01-10", pd.Timestamp("2026-01-10") + pd.Timedelta(days=d))
            for i, d in enumerate(delays)]
    return pd.DataFrame(rows, columns=["payment_id", "vendor_id", "due_date", "payment_date"])


def test_delay_rule_flags_only_the_extreme_payment():
    delays = [0, 1, -1, 2, 0, 1, -2, 1, 0, 40]  # one payment 40 days late, rest near on time
    flagged = delay_anomalies(_payments(delays), VENDORS)
    assert flagged["record_id"].tolist() == ["PMT9"]
    assert flagged["value"].tolist() == [40.0]


def test_delay_rule_ignores_unpaid_rows():
    pay = _payments([0, 1, 0, 1, 0, 1, 30])
    pay.loc[6, "payment_date"] = pd.NaT  # scheduled, not paid yet
    assert delay_anomalies(pay, VENDORS).empty


def test_duplicate_rule_flags_the_later_po():
    pos = pd.DataFrame({
        "po_id": ["PO1", "PO2", "PO3"], "vendor_id": ["V1", "V1", "V2"],
        "amount": [500.0, 500.0, 500.0], "po_date": ["2026-05-01"] * 3,
    })
    flagged = duplicate_anomalies(pos, VENDORS)
    assert flagged["record_id"].tolist() == ["PO2"]
    assert "PO1" in flagged["detail"].iloc[0]


def test_real_data_finds_known_anomalies():
    found = set(find_anomalies(load_to_sqlite(verbose=False))["record_id"])
    assert {"PO00148", "PO00020", "PO00081", "PO00221", "PO00222"} <= found  # seeded PO anomalies
    assert {"PMT00028", "PMT00151"} <= found  # 35 and 33 days late


def test_validation_flags_bad_rows_without_dropping_them():
    conn = load_to_sqlite(verbose=False)
    conn.execute("INSERT INTO purchase_orders VALUES ('POX1', NULL, 'MRO', '2026-06-10', '2026-06-20', -50, 'Pending')")
    conn.execute("INSERT INTO payments VALUES ('PMTX1', 'POX1', 'V001', '2026-06-01', '2026-06-02', 10, 'Paid')")
    report = flag_bad_rows(conn, out_path=None)
    rules = set(zip(report["rule"], report["record_id"]))
    assert ("negative amount", "POX1") in rules
    assert ("missing vendor_id", "POX1") in rules
    assert ("payment date before PO date", "PMTX1") in rules
    assert conn.execute("SELECT COUNT(*) FROM purchase_orders WHERE po_id = 'POX1'").fetchone()[0] == 1  # kept

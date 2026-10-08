"""Deterministic anomaly rules over the loaded data (plain pandas, no LLM).

Rules (decision recorded in docs/architecture.md, Decision 4):
  1. payment delay: delay_days = payment_date - due_date. Flag a payment whose delay is more than
     K_DELAY standard deviations above the mean delay of ALL paid payments. Overall, not per vendor,
     because most vendors have only 1-2 payments, too few for a per-vendor mean to mean anything.
  2. amount outlier: PO amount > category mean + K_AMOUNT * stddev (population stddev).
  3. possible duplicate: two POs with the same vendor_id + amount + po_date.
"""
import pandas as pd

K_DELAY = 2.0
K_AMOUNT = 2.0

COLUMNS = ["rule", "record_id", "vendor_id", "vendor_name", "value", "detail"]


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNS)


def delay_anomalies(payments: pd.DataFrame, vendors: pd.DataFrame, k: float = K_DELAY) -> pd.DataFrame:
    """Payments paid unusually late. `payments` needs payment_id, vendor_id, due_date, payment_date."""
    df = payments.dropna(subset=["payment_date", "due_date"]).copy()
    if len(df) < 2:
        return _empty()
    df["delay_days"] = (pd.to_datetime(df["payment_date"]) - pd.to_datetime(df["due_date"])).dt.days
    mean, std = df["delay_days"].mean(), df["delay_days"].std(ddof=0)
    flagged = df[df["delay_days"] > mean + k * std].merge(vendors[["vendor_id", "vendor_name"]], on="vendor_id", how="left")
    return pd.DataFrame({
        "rule": "payment delay outlier",
        "record_id": flagged["payment_id"],
        "vendor_id": flagged["vendor_id"],
        "vendor_name": flagged["vendor_name"],
        "value": flagged["delay_days"].astype(float),
        "detail": [f"paid {int(d)} days after due date (mean {mean:.1f}, flag above {mean + k * std:.1f})"
                   for d in flagged["delay_days"]],
    })[COLUMNS]


def amount_anomalies(pos: pd.DataFrame, vendors: pd.DataFrame, k: float = K_AMOUNT) -> pd.DataFrame:
    """POs far above their category's normal size."""
    df = pos.dropna(subset=["amount", "category"]).copy()
    stats = df.groupby("category")["amount"].agg(mean="mean", std=lambda s: s.std(ddof=0))
    df = df.join(stats, on="category")
    flagged = df[df["amount"] > df["mean"] + k * df["std"]].merge(vendors[["vendor_id", "vendor_name"]], on="vendor_id", how="left")
    return pd.DataFrame({
        "rule": "amount outlier for category",
        "record_id": flagged["po_id"],
        "vendor_id": flagged["vendor_id"],
        "vendor_name": flagged["vendor_name"],
        "value": flagged["amount"].astype(float),
        "detail": [f"{r.category}: {r.amount:,.2f} vs category mean {r.mean:,.2f}" for r in flagged.itertuples()],
    })[COLUMNS]


def duplicate_anomalies(pos: pd.DataFrame, vendors: pd.DataFrame) -> pd.DataFrame:
    """The later PO of any pair sharing vendor + amount + date (likely double entry)."""
    df = pos.dropna(subset=["amount"]).sort_values("po_id")
    first = df.drop_duplicates(["vendor_id", "amount", "po_date"], keep="first").set_index(["vendor_id", "amount", "po_date"])["po_id"]
    dup = df[df.duplicated(["vendor_id", "amount", "po_date"], keep="first")].copy()
    dup["original"] = [first[(r.vendor_id, r.amount, r.po_date)] for r in dup.itertuples()]
    dup = dup.merge(vendors[["vendor_id", "vendor_name"]], on="vendor_id", how="left")
    return pd.DataFrame({
        "rule": "possible duplicate PO",
        "record_id": dup["po_id"],
        "vendor_id": dup["vendor_id"],
        "vendor_name": dup["vendor_name"],
        "value": dup["amount"].astype(float),
        "detail": [f"same vendor, amount and date as {o}" for o in dup["original"]],
    })[COLUMNS]


def find_anomalies(conn) -> pd.DataFrame:
    """Run every rule against a loaded SQLite connection; one row per flagged record."""
    payments = pd.read_sql("SELECT * FROM payments", conn)
    pos = pd.read_sql("SELECT * FROM purchase_orders", conn)
    vendors = pd.read_sql("SELECT vendor_id, vendor_name FROM vendors", conn)
    return pd.concat(
        [delay_anomalies(payments, vendors), amount_anomalies(pos, vendors), duplicate_anomalies(pos, vendors)],
        ignore_index=True,
    )

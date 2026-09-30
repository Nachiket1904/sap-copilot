"""Ground truth for the 5 seed questions, computed with pandas straight from the CSVs.

No SQL and no LLM, so it is an independent check of what src.app answers. Run:
    python -m tests.check_answers
Then compare each block below with the answer in docs/answer_review.md.
"""
import sys

import pandas as pd

from src.data_layer.loader import DATA_DIR

po = pd.read_csv(DATA_DIR / "purchase_orders.csv", parse_dates=["po_date", "delivery_date"])
pay = pd.read_csv(DATA_DIR / "payments.csv", parse_dates=["due_date", "payment_date"])
vendors = pd.read_csv(DATA_DIR / "vendors.csv")


def show(title, df):
    print(f"\n=== {title} ===")
    print(df.to_string(index=False) if len(df) else "(no rows)")


def main():
    pay["delay_days"] = (pay["payment_date"] - pay["due_date"]).dt.days
    delayed = pay[pay["delay_days"] > 0].merge(vendors[["vendor_id", "vendor_name"]], on="vendor_id")

    # Q1: delayed payments with payment_date in September 2026 ("this month" = 2026-09)
    sept = delayed[(delayed["payment_date"] >= "2026-09-01") & (delayed["payment_date"] <= "2026-09-30")]
    show("Q1 vendors with delayed payments in Sep 2026",
         sept[["vendor_id", "vendor_name", "payment_id", "due_date", "payment_date", "delay_days"]])

    # Q2: Q3 (Jul-Sep 2026) POs by category; missing category shown as (missing)
    q3 = po[(po["po_date"] >= "2026-07-01") & (po["po_date"] <= "2026-09-30")].copy()
    q3["category"] = q3["category"].fillna("(missing)")
    show("Q2 Q3 POs by category (count, total, average)",
         q3.groupby("category")["amount"].agg(orders="count", total="sum", average="mean").round(2).reset_index())

    # Q3: outlier (> category mean + 2 population std) or duplicate (same vendor+amount+date)
    stats = po.groupby("category")["amount"].agg(m="mean", sd=lambda x: x.std(ddof=0))
    j = po.join(stats, on="category")
    out = j[j["amount"] > j["m"] + 2 * j["sd"]][["po_id", "vendor_id", "category", "amount", "po_date"]]
    dup_mask = po.duplicated(["vendor_id", "amount", "po_date"], keep=False)
    show("Q3 outliers (expect PO00148, PO00020, PO00081)", out)
    show("Q3 duplicate groups (expect PO00221 and PO00222 each with a twin)",
         po[dup_mask].sort_values(["vendor_id", "po_date", "amount"])[["po_id", "vendor_id", "amount", "po_date"]])

    # Q4: average delay over delayed payments only, per vendor
    show("Q4 average delay days by vendor (delayed payments only)",
         delayed.groupby(["vendor_id", "vendor_name"])["delay_days"].agg(payments="count", avg_delay="mean")
         .round(2).reset_index())

    # Q5: Pending POs with amount > 1,00,000
    p5 = po[(po["status"] == "Pending") & (po["amount"] > 100000)]
    show(f"Q5 pending POs above 100000 ({len(p5)} expected)", p5[["po_id", "vendor_id", "amount", "po_date"]])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

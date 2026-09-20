"""Load mock SAP CSVs into a queryable SQLite database."""
import sqlite3
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "mock_sap"


def load_to_sqlite(db_path: str = ":memory:") -> sqlite3.Connection:
    """Load all CSVs in data/mock_sap into a SQLite DB, one table per file."""
    conn = sqlite3.connect(db_path)
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        print(f"No CSVs found in {DATA_DIR} yet — add mock data first (Day 3).")
    for csv_file in csv_files:
        table_name = csv_file.stem
        df = pd.read_csv(csv_file)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"Loaded {table_name} ({len(df)} rows)")
    return conn


if __name__ == "__main__":
    load_to_sqlite()

"""Load mock SAP CSVs into a queryable SQLite database.

Messy rows are kept, never dropped: blanks become NULL, and numeric columns
are cleaned (currency symbols / thousands separators stripped) so a stray
"TBD" can't turn a whole amount column into TEXT. Anything that could not be
parsed is reported, not hidden.
"""
import sqlite3
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "mock_sap"

# Columns that must be numeric in SQLite (so SUM/AVG/comparisons work), per table.
NUMERIC_COLUMNS = {
    "vendors": ["payment_terms_days"],
    "purchase_orders": ["amount"],
    "payments": ["amount"],
}

INTEGER_COLUMNS = {"payment_terms_days"}

# Primary key per table, used by the duplicate check.
PRIMARY_KEYS = {
    "vendors": "vendor_id",
    "purchase_orders": "po_id",
    "payments": "payment_id",
}


def _clean_numeric(series: pd.Series) -> tuple[pd.Series, list]:
    """Coerce a column to numbers; return (clean series, raw values that failed to parse).

    "₹1,25,000" and "12,500.00" are recovered. Truly unparseable values
    (e.g. "TBD") become NULL. Blank cells are already missing, not failures.
    """
    text = series.astype("string").str.replace(r"[₹,\s]", "", regex=True)
    cleaned = pd.to_numeric(text, errors="coerce")
    failed = series[cleaned.isna() & series.notna() & (series.astype("string").str.strip() != "")]
    return cleaned, failed.tolist()


def load_to_sqlite(db_path: str = ":memory:", data_dir: Path = DATA_DIR, verbose: bool = True) -> sqlite3.Connection:
    """Load all CSVs in data_dir into a SQLite DB, one table per file."""
    conn = sqlite3.connect(db_path)
    csv_files = sorted(Path(data_dir).glob("*.csv"))
    if not csv_files:
        print(f"No CSVs found in {data_dir} yet — add mock data first.")
    for csv_file in csv_files:
        table_name = csv_file.stem
        df = pd.read_csv(csv_file, dtype=str)  # read raw text first, then clean per column
        for col in NUMERIC_COLUMNS.get(table_name, []):
            if col in df.columns:
                df[col], failed = _clean_numeric(df[col])
                if col in INTEGER_COLUMNS:
                    df[col] = df[col].astype("Int64")
                if failed and verbose:
                    print(f"  warning: {table_name}.{col}: {len(failed)} unparseable value(s) stored as NULL: {failed}")
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        if verbose:
            print(f"Loaded {table_name} ({len(df)} rows)")
    return conn


def run_quality_checks(conn: sqlite3.Connection) -> list[str]:
    """Light sanity checks on a loaded DB. Returns a list of problems (empty = clean)."""
    problems = []
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table, pk in PRIMARY_KEYS.items():
        if table not in tables:
            problems.append(f"{table}: table missing")
            continue
        total, distinct = conn.execute(f"SELECT COUNT(*), COUNT(DISTINCT {pk}) FROM {table}").fetchone()
        if total == 0:
            problems.append(f"{table}: 0 rows")
        if total != distinct:
            problems.append(f"{table}: {total - distinct} duplicate {pk} value(s)")
        print(f"  {table}: {total} rows, {distinct} distinct {pk}")
    return problems


if __name__ == "__main__":
    connection = load_to_sqlite()
    issues = run_quality_checks(connection)
    if issues:
        raise SystemExit("Data quality problems:\n  " + "\n  ".join(issues))
    print("Data quality checks passed.")

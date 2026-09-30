"""Turn a natural-language question into SQL, run it safely, and phrase the answer.

Pipeline (max 2 LLM calls per question, see docs/architecture.md):
  question -> LLM #1 writes SQL -> validate (SELECT only) -> run read-only
           -> LLM #2 turns the rows into a plain-English answer

This module owns the prompts and the SQL safety checks. It only ever calls
`src.llm.client.ask()`, so it does not know which LLM provider is configured.
"""
import re
import sqlite3
from datetime import date

from src.llm.client import ask

MAX_ROWS = 200  # cap on rows handed to the answer-phrasing call

# Rules from docs/architecture.md ("Prompt rules the LLM must be given").
SQL_RULES = """\
- Today's date is {today}. Resolve "this month", "this week", "Q3" from it.
- Blank values are NULL: use IS NULL / COALESCE, never = ''.
- Dates are ISO YYYY-MM-DD text: use julianday() for date arithmetic.
- Currency is INR. 1,00,000 means 100000.
- Status values are exact. purchase_orders.status: Pending, Approved, Rejected, Closed.
  payments.status: Paid, Scheduled.
- "Category" means purchase_orders.category, NOT vendors.vendor_category.
- A payment is delayed when payment_date > due_date; delay days = julianday(payment_date) - julianday(due_date).
  "Average payment delay" averages delay days over delayed payments only (payment_date > due_date), per vendor.
- delivery_date is the scheduled delivery date, not proof the goods arrived.
- payments.vendor_id exists, so payments can join vendors directly.
- Output exactly ONE SQLite SELECT statement and nothing else. No explanation, no markdown."""

SQL_SYSTEM = "You are a careful SQLite analyst for a purchase-order database. You only write read-only SQL."

ANSWER_SYSTEM = (
    "You are an analyst answering a finance user's question about purchase orders. "
    "Use only the query results provided; never invent numbers. Be concise and name "
    "vendors, PO numbers, amounts (in INR) and delays where relevant. If a result is "
    "empty, say nothing matched. If amounts are missing (NULL), mention it."
)


def build_schema_description(conn) -> str:
    """Return a text description of all tables/columns for prompting the LLM."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables = [row[0] for row in cursor.fetchall()]
    lines = []
    for table in tables:
        cols = conn.execute(f"PRAGMA table_info({table});").fetchall()
        col_desc = ", ".join(f"{c[1]} ({c[2]})" for c in cols)
        lines.append(f"{table}: {col_desc}")
    return "\n".join(lines)


# --- Day 1: first manual LLM call (no SQL execution) -----------------------

def manual_answer(question: str, conn, today: str | None = None) -> str:
    """Proof the LLM call works end to end: schema + question in, plain English out.

    The model has no data here, so it can only describe how it would answer.
    """
    today = today or date.today().isoformat()
    prompt = (
        f"Database schema:\n{build_schema_description(conn)}\n\n"
        f"Today's date: {today}\n\n"
        f"Question: {question}\n\n"
        "You cannot see the data. In plain English, say which tables and columns "
        "you would use to answer this and how."
    )
    return ask(prompt, system=SQL_SYSTEM)


# --- Day 2: text-to-SQL ------------------------------------------------------

def build_sql_prompt(question: str, conn, today: str | None = None) -> str:
    today = today or date.today().isoformat()
    return (
        f"Schema (SQLite):\n{build_schema_description(conn)}\n\n"
        f"Rules:\n{SQL_RULES.format(today=today)}\n\n"
        f"Question: {question}\n\nSQL:"
    )


def extract_sql(llm_output: str) -> str:
    """Pull the SQL out of a reply that may be wrapped in ``` fences or trailing prose."""
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", llm_output, re.DOTALL | re.IGNORECASE)
    return (fenced.group(1) if fenced else llm_output).strip()


FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum|reindex)\b",
    re.IGNORECASE,
)


def validate_select(sql: str) -> str:
    """Return a cleaned single SELECT statement, or raise ValueError.

    Defence in depth: this text check rejects anything that is not one SELECT
    (or WITH ... SELECT); run_select() then executes on a query_only connection,
    so a validator miss still cannot write.
    """
    cleaned = sql.strip().rstrip(";").strip()
    without_strings = re.sub(r"'(?:[^']|'')*'", "''", cleaned)  # ignore keywords inside literals
    if ";" in without_strings:
        raise ValueError("Only a single SQL statement is allowed.")
    if not re.match(r"(select|with)\b", without_strings, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")
    bad = FORBIDDEN.search(without_strings)
    if bad:
        raise ValueError(f"Forbidden keyword in query: {bad.group(0)}")
    return cleaned


def run_select(conn: sqlite3.Connection, sql: str) -> tuple[list[str], list[tuple]]:
    """Validate then execute SQL read-only. Returns (column names, rows)."""
    safe_sql = validate_select(sql)
    conn.execute("PRAGMA query_only = ON")  # SQLite refuses any write on this connection
    try:
        cursor = conn.execute(safe_sql)
        columns = [d[0] for d in cursor.description]
        return columns, cursor.fetchall()
    finally:
        conn.execute("PRAGMA query_only = OFF")


def generate_sql(question: str, conn, today: str | None = None) -> str:
    """LLM call #1: question -> validated SELECT."""
    reply = ask(build_sql_prompt(question, conn, today), system=SQL_SYSTEM)
    return validate_select(extract_sql(reply))


def format_rows(columns: list[str], rows: list[tuple]) -> str:
    if not rows:
        return "(no rows)"
    shown = rows[:MAX_ROWS]
    lines = [" | ".join(columns)] + [" | ".join("NULL" if v is None else str(v) for v in r) for r in shown]
    if len(rows) > MAX_ROWS:
        lines.append(f"... {len(rows) - MAX_ROWS} more rows not shown (total {len(rows)})")
    return "\n".join(lines)


def answer_question(question: str, conn, today: str | None = None, verbose: bool = False) -> str:
    """Full pipeline: plain-English question in, plain-English answer out (2 LLM calls)."""
    sql = generate_sql(question, conn, today)
    columns, rows = run_select(conn, sql)
    if verbose:
        print(f"SQL:\n{sql}\n\nRows returned: {len(rows)}\n")
    prompt = (
        f"Question: {question}\n\nSQL that was run:\n{sql}\n\n"
        f"Query results ({len(rows)} rows):\n{format_rows(columns, rows)}\n\n"
        "Answer the question in plain English."
    )
    return ask(prompt, system=ANSWER_SYSTEM)


if __name__ == "__main__":
    import sys

    from src.data_layer.loader import load_to_sqlite

    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252 and choke on LLM punctuation
    args = sys.argv[1:]
    manual = "--manual" in args
    question = " ".join(a for a in args if a != "--manual") or "Which vendors had delayed payments this month?"
    connection = load_to_sqlite(verbose=False)
    print(f"Q: {question}\n")
    if manual:
        print(manual_answer(question, connection))
    else:
        print(answer_question(question, connection, verbose=True))

"""Turn a natural-language question into a SQL query the LLM layer can answer from.

Week 2 will fill this in: build a schema description from the SQLite DB,
prompt the LLM (Groq/Gemini) to write SQL, execute it safely (read-only), and pass the
result back to the LLM layer to phrase as an answer.
"""


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

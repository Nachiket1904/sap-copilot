"""Text-to-SQL tests. The LLM is stubbed, so these need no API key and cost nothing."""
import pytest

from src.data_layer.loader import load_to_sqlite
from src.retrieval import text_to_sql as t2s


@pytest.fixture(scope="module")
def conn():
    c = load_to_sqlite(verbose=False)
    yield c
    c.close()


@pytest.mark.parametrize("sql", [
    "SELECT * FROM vendors",
    "select vendor_id from vendors;",
    "WITH x AS (SELECT 1) SELECT * FROM x",
    "SELECT * FROM purchase_orders WHERE status = 'Delete me'",  # keyword inside a literal is fine
])
def test_validate_accepts_selects(sql):
    assert t2s.validate_select(sql)


@pytest.mark.parametrize("sql", [
    "DROP TABLE vendors",
    "DELETE FROM payments",
    "UPDATE vendors SET country = 'X'",
    "INSERT INTO vendors VALUES (1)",
    "SELECT 1; DROP TABLE vendors",
    "PRAGMA table_info(vendors)",
    "ATTACH DATABASE 'x.db' AS x",
    "SELECT * FROM vendors; SELECT 1",
])
def test_validate_rejects_non_selects(sql):
    with pytest.raises(ValueError):
        t2s.validate_select(sql)


def test_extract_sql_strips_code_fences():
    assert t2s.extract_sql("```sql\nSELECT 1;\n```") == "SELECT 1;"
    assert t2s.extract_sql("SELECT 2") == "SELECT 2"


def test_run_select_is_read_only_even_if_validator_is_bypassed(conn, monkeypatch):
    monkeypatch.setattr(t2s, "validate_select", lambda s: s)  # simulate a validator miss
    with pytest.raises(Exception):
        t2s.run_select(conn, "DELETE FROM vendors")
    assert conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0] == 30


def test_schema_description_mentions_all_tables(conn):
    schema = t2s.build_schema_description(conn)
    for table in ("vendors", "purchase_orders", "payments"):
        assert table in schema


def test_sql_prompt_carries_rules_and_date(conn):
    prompt = t2s.build_sql_prompt("q?", conn, today="2026-09-30")
    assert "2026-09-30" in prompt and "IS NULL" in prompt and "vendor_category" in prompt


def test_answer_question_runs_generated_sql_and_phrases_result(conn, monkeypatch):
    calls = []

    def fake_ask(prompt, system=None):
        calls.append(prompt)
        if len(calls) == 1:
            return ("```sql\nSELECT v.vendor_name, COUNT(*) AS late_payments FROM payments p "
                    "JOIN vendors v ON v.vendor_id = p.vendor_id "
                    "WHERE p.payment_date > p.due_date AND p.payment_date >= '2026-09-01' "
                    "GROUP BY v.vendor_name ORDER BY late_payments DESC\n```")
        return "Summit Consulting Services was paid late four times this month."

    monkeypatch.setattr(t2s, "ask", fake_ask)
    answer = t2s.answer_question("Which vendors had delayed payments this month?", conn, today="2026-09-30")
    assert len(calls) == 2  # architecture: max 2 LLM calls per question
    assert "Summit Consulting Services | 4" in calls[1]  # real rows reached the phrasing call
    assert answer.startswith("Summit")


def test_answer_question_refuses_destructive_sql(conn, monkeypatch):
    monkeypatch.setattr(t2s, "ask", lambda prompt, system=None: "DROP TABLE vendors")
    with pytest.raises(ValueError):
        t2s.answer_question("wipe it", conn)
    assert conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0] == 30

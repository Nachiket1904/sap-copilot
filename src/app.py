"""End-to-end copilot: question in, answer out.

    python -m src.app "Which vendors had delayed payments this month?"
    python -m src.app                # interactive prompt
    python -m src.app --seed         # run the 5 seed questions, write docs/answer_review.md
"""
import os
import sys
from pathlib import Path

from src.data_layer.loader import load_to_sqlite
from src.data_layer.anomaly import find_anomalies
from src.retrieval.anomalies import is_anomaly_question
from src.retrieval.text_to_sql import format_rows, generate_sql, phrase_answer, run_select

SEED_QUESTIONS = [
    "Which vendors had delayed payments this month?",
    "Summarize Q3 purchase orders by category.",
    "Flag any transactions that look unusual this week.",
    "What's the average payment delay by vendor?",
    "Show me all pending purchase orders above ₹1,00,000.",
]
# The mock data ends in Sep 2026, so "this month/week" is resolved against this fixed date, not the real clock.
AS_OF = os.environ.get("COPILOT_TODAY", "2026-09-30")
REVIEW_FILE = Path(__file__).resolve().parents[1] / "docs" / "answer_review.md"


def ask_copilot(question: str, conn, today: str | None = None) -> dict:
    """Route the question, run the SQL, phrase the answer. Never raises: errors come back in 'error'."""
    result = {"question": question, "sql": None, "columns": [], "rows": [], "answer": None, "error": None}
    try:
        if is_anomaly_question(question):
            found = find_anomalies(conn)  # deterministic pandas rules, no LLM-written SQL
            result["sql"] = "-- deterministic rules in src/data_layer/anomaly.py (no SQL)"
            result["columns"], result["rows"] = list(found.columns), list(found.itertuples(index=False, name=None))
        else:
            result["sql"] = generate_sql(question, conn, today)
            result["columns"], result["rows"] = run_select(conn, result["sql"])
        asked = question
        if is_anomaly_question(question):
            asked += "\n(Note for the answer: the rules scan ALL records, not just one week. Say so, and do not claim these happened this week.)"
        result["answer"] = phrase_answer(asked, result["sql"], result["columns"], result["rows"])
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def write_review(results: list[dict], today: str) -> None:
    """Dump everything a human needs to score each answer against the data."""
    lines = [f"# Answer review (run date {today})", "",
             "Check each answer against `python -m tests.check_answers` (independent pandas calculation), "
             "not against how plausible the text sounds.", "",
             "Three things can fail independently: SQL correct? Answer matches the data? Phrasing clear "
             "and free of invented numbers?", "",
             "| # | Question | SQL ok? | Answer ok? | Phrasing ok? | Overall (Right/Partial/Wrong) | Note |",
             "|---|---|---|---|---|---|---|"]
    lines += [f"| {i} | {r['question']} |  |  |  |  |  |" for i, r in enumerate(results, 1)]
    for i, r in enumerate(results, 1):
        lines += ["", f"## {i}. {r['question']}", "",
                  f"**Answer:**\n\n{r['answer'] or '(none)'}", ""]
        if r["error"]:
            lines += [f"**Error:** `{r['error']}`", ""]
        lines += ["**SQL:**", "```sql", (r["sql"] or "").strip(), "```", "",
                  f"**Rows ({len(r['rows'])}):**", "```", format_rows(r["columns"], r["rows"]), "```"]
    REVIEW_FILE.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    conn = load_to_sqlite(verbose=False)
    today = AS_OF
    if "--seed" in argv:
        results = [ask_copilot(q, conn, today) for q in SEED_QUESTIONS]
        for r in results:
            print(f"Q: {r['question']}\n{r['error'] or r['answer']}\n")
        write_review(results, today)
        print(f"Wrote {REVIEW_FILE}")
        return 0
    questions = [" ".join(argv)] if argv else None
    while True:
        q = questions.pop() if questions else input("Ask a question (blank to quit): ").strip()
        if not q:
            return 0
        r = ask_copilot(q, conn, today)
        print(f"\nSQL:\n{(r['sql'] or '').strip()}\n\n{r['error'] or r['answer']}\n")
        if argv:
            return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

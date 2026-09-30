"""End-to-end copilot: question in, answer out.

    python -m src.app "Which vendors had delayed payments this month?"
    python -m src.app                # interactive prompt
    python -m src.app --seed         # run the 5 seed questions, write docs/answer_review.md
"""
import sys
from datetime import date
from pathlib import Path

from src.data_layer.loader import load_to_sqlite
from src.retrieval.anomalies import ANOMALY_SQL, is_anomaly_question
from src.retrieval.text_to_sql import format_rows, generate_sql, phrase_answer, run_select

SEED_QUESTIONS = [
    "Which vendors had delayed payments this month?",
    "Summarize Q3 purchase orders by category.",
    "Flag any transactions that look unusual this week.",
    "What's the average payment delay by vendor?",
    "Show me all pending purchase orders above ₹1,00,000.",
]
REVIEW_FILE = Path(__file__).resolve().parents[1] / "docs" / "answer_review.md"


def ask_copilot(question: str, conn, today: str | None = None) -> dict:
    """Route the question, run the SQL, phrase the answer. Never raises: errors come back in 'error'."""
    result = {"question": question, "sql": None, "columns": [], "rows": [], "answer": None, "error": None}
    try:
        result["sql"] = ANOMALY_SQL if is_anomaly_question(question) else generate_sql(question, conn, today)
        result["columns"], result["rows"] = run_select(conn, result["sql"])
        result["answer"] = phrase_answer(question, result["sql"], result["columns"], result["rows"])
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
    today = date.today().isoformat()
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

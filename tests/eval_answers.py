"""End-to-end eval: run each question in tests/eval_cases.json through src.app and check the answer.

Costs real LLM calls, so it is not part of `pytest`. Run:
    python -m tests.eval_answers                 # all cases
    python -m tests.eval_answers q1 q5           # only ids starting with these prefixes
    python -m tests.eval_answers --runs 3        # repeat each case to expose flakiness

A case passes when every `must_contain` string appears in the answer and no `must_not_contain`
string does. Matching is case-insensitive and ignores thousands separators and the rupee sign,
so "2,232,098.64" and "₹2232098.64" both match "2232098.64". String match is deliberately
simple: exact correctness matters more than fuzzy matching at this stage.
"""
import json
import sys
from pathlib import Path

from src.app import AS_OF, ask_copilot
from src.data_layer.loader import load_to_sqlite

CASES_FILE = Path(__file__).with_name("eval_cases.json")


def normalize(text: str) -> str:
    return text.replace(",", "").replace("₹", "").lower()


def check(answer: str, case: dict) -> list[str]:
    """Return the list of failures (empty = pass)."""
    text = normalize(answer or "")
    failures = [f"missing: {s}" for s in case["must_contain"] if normalize(s) not in text]
    failures += [f"should not appear: {s}" for s in case.get("must_not_contain", []) if normalize(s) in text]
    return failures


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    runs = 1
    if "--runs" in argv:
        i = argv.index("--runs")
        runs = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    if argv:
        cases = [c for c in cases if any(c["id"].startswith(p) for p in argv)]
    conn = load_to_sqlite(verbose=False)
    passed = total = 0
    for case in cases:
        for _ in range(runs):
            result = ask_copilot(case["question"], conn, AS_OF)
            failures = [result["error"]] if result["error"] else check(result["answer"], case)
            total += 1
            passed += not failures
            print(f"{'PASS' if not failures else 'FAIL'}  {case['id']}")
            for f in failures:
                print(f"      {f}")
    print(f"\nPass rate: {passed}/{total} = {passed / total:.0%}" if total else "No cases selected.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

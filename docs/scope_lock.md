# Scope lock — v1 (DRAFT, not yet signed off)

Draft by Nachiket from the Week 3 state. Both people must review the lists below, move items between them,
and sign at the bottom. Anything not in "In v1" is **cut**, not "later".

## In v1

1. Natural-language Q&A over purchase orders, vendors and payments (text-to-SQL, 2 LLM calls max per question).
2. Anomaly flagging: payment delay outliers, amount outliers, duplicate POs (`src/data_layer/anomaly.py`).
3. Data-quality report: flagged (never dropped) bad rows in `data/mock_sap/flagged_rows.csv`.
4. Eval set + script with a recorded pass rate (`tests/eval_cases.json`, `tests/eval_answers.py`).
5. A simple UI (one page: question box, answer, the SQL that ran) — *proposal; see Open questions*.
6. README with setup, example questions, and a demo recording or screenshots.

## Explicitly out of v1

- Connecting to real SAP (OData/RFC) — mock CSVs only.
- Other SAP modules (finance, inventory, sales).
- Multi-turn conversation / follow-up questions; chat memory.
- Authentication, multiple users, role-based access.
- Fine-tuning or embeddings / RAG over documents.
- Per-vendor statistical models, forecasting, scheduled alerts or email notifications.
- Write-back actions (approving POs, editing data) — the copilot stays read-only.

## Open questions (decide on the call)

- [ ] Is a UI worth the time, or is a polished CLI + README enough for "portfolio-worthy"? (Streamlit is about half a day.)
- [ ] Do we apply a real "this week" date window to anomalies, or keep scanning all records?
- [ ] Which LLM provider do we show in the demo: Groq (current) or Gemini fallback?

## Where we are going into Week 4 (Polish & Ship)

- Clear: data layer, SQL pipeline, anomaly rules, eval harness.
- Fuzzy: UI choice, anomaly time window, how to show the LLM's SQL to a non-technical user.

## Sign-off

- [ ] Nachiket — date: ____
- [ ] Collaborator — date: ____

# Week 2 — Top 5 broken or missing (v0.1)

Candidates observed by Nachiket on Day 3–4. Her job: verify, edit, replace, then mark the 2–3 that matter most for Week 3.

| # | What breaks (specific) | Example | Why it matters for Week 3 | Week 3 priority? |
|---|---|---|---|---|
| 1 | "This week" has no data: the Q3 anomaly rule scans all POs, so the answer ignores the time window | "unusual this week" returns POs from May–Sep | Anomaly detection needs a real time window and recent seeded anomalies | |
| 2 | The LLM sometimes returns an empty or non-SELECT reply; only a retry (max 2) hides it | Seen on Q5 in one of several runs | Flaky output will look like false anomalies | |
| 3 | The LLM does arithmetic in the answer text; before the fix it gave Packaging average 1,047,600.02 instead of 104,760.02 | Q2 | Any computed figure must come from SQL, never from prose | |
| 4 | "Today" is a fixed date (`COPILOT_TODAY`), not the clock; relative questions are wrong if it isn't set to match the data | Q1 on a real October date returns nothing | Time-based anomalies depend on it | |
| 5 | Ambiguous columns: Scheduled payments with no `payment_date`, and past `delivery_date` on Pending POs ("scheduled", not "arrived") | Q5 phrasing / any lateness question | Delay anomalies need these defined | |

(Replace or reorder with what she found when scoring.)

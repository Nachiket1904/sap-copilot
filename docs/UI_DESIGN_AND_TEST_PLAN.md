# UI v1 — Basic design and test plan

Written for: the collaborator who will test the UI. Nachiket builds it from the "Design" part; you check it with the
"Test plan" part. For the background (API, code, features) see `docs/PROJECT_GUIDE_AND_UI_BRIEF.md`.

---

# Part A — Design (what gets built)

One page, served by the FastAPI app at `http://127.0.0.1:8000/`. No login, no extra pages.

## Layout

```
┌──────────────────────────────────────────────────────────────┐
│ SAP Copilot                              Data as of 30 Sep 2026│
├────────────────────────────────────┬─────────────────────────┤
│ [ Ask about purchase orders…     ] │ ⚠ Anomalies (11)        │
│ [Ask]                              │  rule · record · reason │
│ Try: (chip)(chip)(chip)(chip)(chip)│  …                      │
│                                    │ ✔ Data quality (3)      │
│ ANSWER                    [SQL]    │  record · issue         │
│ The vendors that had delayed…      │                         │
│ ▸ Show SQL                         │                         │
│ ▾ Data (2 rows)  table             │                         │
└────────────────────────────────────┴─────────────────────────┘
```
On a narrow screen the right column drops below the left.

## What each part does

| Part | Behaviour |
|---|---|
| Header | Shows the as-of date from `/health` |
| Question box | Up to 500 characters; Enter submits; button disabled while loading |
| Example chips | 5 buttons from `/examples`; clicking one fills the box and asks it |
| Answer card | The answer text, with bold/lists/tables rendered; a badge `SQL` or `Rules` from `route` |
| Show SQL | Collapsed by default; read-only code block with a Copy button. For the Rules route show "Fixed rules, no SQL" instead |
| Data table | Columns and rows from the response; numbers right-aligned; empty values shown as "—"; says "Showing first 500 of N" when truncated |
| Anomalies panel | From `/anomalies`; `value` shown with its `unit` ("35 days late", "₹6,22,838") |
| Data quality panel | From `/data-quality`; record and rule |

## States (each must look different)
Empty · Loading · Success (SQL) · Success (Rules) · Zero rows · Question too short/long (inline message) ·
Copilot failed (friendly message and Retry) · Server unreachable (banner).

## Look and feel (keep it simple)
Light theme, one accent colour for buttons, amber for anomalies, red only for errors, table text at least 13px.
Indian number grouping (1,00,000) for rupee amounts.

---

# Part B — Test plan (your job)

Start the app: `uvicorn src.api:app --reload`, open `http://127.0.0.1:8000/`. Record each result as Pass / Fail
with a note in `docs/ui_test_results.md` (create it, one row per test). A Fail needs: what you did, what you saw,
what you expected. Screenshots help.

## 1. Correct answers through the UI
Click each example chip. The UI answer must match this table (the same checks as `tests/eval_cases.json`).

| Chip | Must show |
|---|---|
| Delayed vendors this month | Quantum Circuit Traders and Summit Consulting Services only |
| Q3 by category | 7 rows; Packaging average 104,760.02; one "Uncategorized" |
| Unusual transactions | 11 flags: 6 late payments, 3 amount outliers, 2 duplicates; says it scans all records |
| Average delay by vendor | 9 vendors; Summit 19.33, Pinnacle 18.5, Quantum 35 |
| Pending above ₹1,00,000 | 13 POs including PO00104 with a missing delivery date |

Then ask 5 of your own questions and check each answer against the CSVs, not by whether it sounds right.

## 2. The evidence matches the answer
- [ ] Row count in the table equals the count the answer states
- [ ] "Show SQL" is hidden at first and opens/closes; Copy puts the SQL on the clipboard
- [ ] Anomaly questions show the `Rules` badge and no fake SQL; other questions show `SQL`
- [ ] Days are never displayed as rupees, or the reverse

## 3. Input and errors
- [ ] Empty box, or "hi" → inline message, no request spinner stuck
- [ ] 501 characters is blocked or shows a clear message
- [ ] "Delete all vendors" or "drop the payments table" → friendly failure, data unchanged (ask the delayed-vendors chip afterwards to confirm)
- [ ] Stop the server while the page is open, then ask → "can't reach the copilot" banner
- [ ] Double-click Ask → only one request, no duplicate answer

## 4. Panels
- [ ] Anomalies panel shows 11 items; each shows rule, record ID, vendor and reason
- [ ] Data quality panel shows PMT00012, PMT00113, PMT00168
- [ ] Values have the correct unit

## 5. Usability (write your honest opinion)
- [ ] Could a finance colleague use this without help? What confused you?
- [ ] Is it obvious the answer is the main thing and the SQL is evidence?
- [ ] Is the loading time acceptable (expect 2 to 6 seconds)?
- [ ] Anything missing that you would expect (export to CSV, recent questions, a "this week" filter)?

## 6. Layout and accessibility
- [ ] Works at a narrow window (about 400px) with no horizontal scroll
- [ ] Everything reachable with the keyboard (Tab, Enter); the focus outline is visible
- [ ] Text is readable; table headers stay visible when scrolling a long table

## Sign-off
Fill in at the end:
- Tests passed: __ / __
- Blocking bugs (must fix before v1): ...
- Nice-to-haves for later: ...
- Ready to tag v1? Yes / No

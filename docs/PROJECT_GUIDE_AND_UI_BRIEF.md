# SAP Copilot — How it works, and the UI brief

Written for: the collaborator who will design the UI. You do not need to read the Python. Part 1 explains what the
product does, Part 2 how the code is organised, Part 3 is the contract the UI talks to, Part 4 is the design brief.

---

# Part 1 — What the product is

A finance or procurement person types a question about purchase orders in plain English and gets a correct,
checkable answer. No SQL, no exports.

- **Data:** mock SAP data in 3 CSVs (`data/mock_sap/`): 228 purchase orders, 30 vendors, 168 payments. Amounts are INR.
  The data runs to September 2026, so the app treats "today" as **2026-09-30** (`COPILOT_TODAY` can override it).
- **Not in scope:** real SAP connection, multi-turn chat, logins, write actions. The copilot is read-only.

## Features

| # | Feature | What the user sees | How it works |
|---|---|---|---|
| 1 | **Ask a question** | A sentence answer plus a table of the rows behind it | The LLM writes one SQL query, the system checks it is a read-only SELECT, runs it, then the LLM words the result |
| 2 | **Show your working** | The exact SQL used, and the raw rows | Returned with every answer so the user can verify it |
| 3 | **Anomaly flagging** | A list of unusual records with the rule and the reason | Fixed pandas rules, no LLM: payments paid >2σ later than normal, POs far above their category's norm, duplicate POs |
| 4 | **Data-quality report** | Rows that look wrong (e.g. Paid with no amount) | Flagged, never deleted |
| 5 | **Example questions** | One-click starter questions | `GET /examples` |
| 6 | **Safety** | Questions that try to change data fail with a clear message | SELECT-only validation plus a read-only database connection |

## What the answers look like today (all verified against the data)

| Question | Answer in short |
|---|---|
| Which vendors had delayed payments this month? | Quantum Circuit Traders, Summit Consulting Services |
| Summarize Q3 purchase orders by category | 7 categories with count, total, average (one is "Uncategorized") |
| Flag any transactions that look unusual | 11 flags: 6 late payments, 3 amount outliers, 2 duplicate POs |
| What's the average payment delay by vendor? | 9 vendors, 11 to 35 days |
| Show pending purchase orders above ₹1,00,000 | 13 POs |

Quality is tracked by an eval set (`tests/eval_cases.json`): **10/10 pass** on the current build.

## Known limits the UI should be honest about
- "This week" is not applied to anomalies; the rules scan all records and the answer says so.
- The LLM's wording varies slightly between runs; the numbers should not.
- Each question costs one real LLM call pair, so it takes a few seconds (show a loading state).
- An answer can occasionally fail (HTTP 502); the UI needs a friendly retry message.

---

# Part 2 — How the code is organised

```
Browser UI
   │  POST /ask {"question": "..."}
   ▼
src/api.py            FastAPI web server (the only thing the UI talks to)
   ▼
src/app.py            ask_copilot(): decides the route
   ├── anomaly-type question ("unusual", "duplicate", "outlier"...)
   │      └─ src/data_layer/anomaly.py   fixed rules in pandas → rows
   └── everything else
          ├─ src/retrieval/text_to_sql.py  LLM #1 writes SQL → safety check → run read-only
          └─ LLM #2 turns the rows into a sentence answer
   ▼
src/data_layer/loader.py   CSV → in-memory SQLite (+ data-quality flags)
src/llm/client.py          one function ask(); Groq by default, Gemini as an option
```

| File | One-line purpose |
|---|---|
| `src/api.py` | HTTP endpoints for the UI |
| `src/app.py` | The question → answer flow; also `python -m src.app "question"` for the terminal |
| `src/retrieval/text_to_sql.py` | Prompts (schema + rules + worked examples), SELECT-only validation, retry on bad replies |
| `src/retrieval/anomalies.py` | Detects whether a question is about "unusual" things |
| `src/data_layer/anomaly.py` | The three anomaly rules |
| `src/data_layer/loader.py` | Loads CSVs, cleans numbers ("TBD" → empty), writes `flagged_rows.csv` |
| `src/llm/client.py` | Provider-neutral LLM wrapper |
| `tests/` | 43 automated tests (no API key needed) and `eval_answers.py` (live, scores answers) |
| `docs/` | Architecture, decisions, reviews, this guide |

**Why two paths?** SQL written by an LLM is flexible but varies run to run. "Unusual" must be explainable and repeatable,
so it uses fixed rules instead. The UI shows which route was used (`route: "sql"` or `"anomaly"`).

**Run it:** `pip install -r requirements.txt`, put `GROQ_API_KEY` in `.env`, then
`uvicorn src.api:app --reload`. Interactive API docs appear at `http://127.0.0.1:8000/docs`, which is the easiest way to
see real responses while designing.

---

# Part 3 — The contract the UI uses

Base URL: `http://127.0.0.1:8000`. All responses are JSON.

| Endpoint | Purpose |
|---|---|
| `GET /health` | `{"status":"ok","as_of":"2026-09-30"}` — show the as-of date in the UI |
| `GET /examples` | `{"questions":[5 strings]}` — example chips |
| `POST /ask` | Body `{"question": "..."}` (3 to 500 characters) |
| `GET /anomalies` | `{"count":11,"items":[...]}` |
| `GET /data-quality` | `{"count":3,"items":[...]}` |

**`POST /ask` response**
```json
{
  "question": "Which vendors had delayed payments this month?",
  "answer": "The vendors ... were Quantum Circuit Traders and Summit Consulting Services.",
  "route": "sql",
  "sql": "SELECT DISTINCT v.vendor_name FROM payments p JOIN ...",
  "columns": ["vendor_name"],
  "rows": [["Quantum Circuit Traders"], ["Summit Consulting Services"]],
  "row_count": 2,
  "truncated": false,
  "as_of": "2026-09-30"
}
```
- `rows` is capped at 500; `truncated` says if more existed.
- For `route: "anomaly"`, `sql` is a comment, not real SQL: show "Rules, not SQL" instead of a code block.
- The answer text may contain Markdown (bold, lists, tables). Render it.

**`/anomalies` item**
```json
{"rule":"payment delay outlier","record_id":"PMT00028","vendor_id":"V017",
 "vendor_name":"Quantum Circuit Traders","value":35.0,"unit":"days late",
 "detail":"paid 35 days after due date (mean -10.8, flag above 24.6)"}
```
`unit` is `"days late"` or `"INR"`, so format `value` accordingly (never show days under a ₹ heading).

**Errors:** `422` = question too short or too long (show the message). `502` = the copilot failed; `detail` has the reason
(show "Couldn't answer that, try rephrasing" and offer retry; keep the technical detail behind a "details" toggle).

---

# Part 4 — UI design brief

## Who uses it
A finance or procurement analyst. Comfortable with Excel, not with SQL. They need to **trust** the answer, so evidence
must always be one click away.

## Design principles
1. **Answer first, evidence second.** The sentence answer is the hero; SQL and rows sit below, collapsed by default.
2. **Always show how the answer was produced** (route badge, SQL, row count). Trust is the product.
3. **Be honest about limits** (as-of date, "scans all records", errors).
4. **One page, no navigation maze.** Single screen with three zones.

## Screen layout (desktop)

```
┌───────────────────────────────────────────────────────────────────────┐
│  SAP Copilot                                     Data as of 30 Sep 2026│
├───────────────────────────────────────┬───────────────────────────────┤
│  ASK                                  │  WATCHLIST                     │
│  ┌─────────────────────────────┐ [Ask]│  ⚠ Anomalies (11)             │
│  │ Ask about purchase orders…  │      │   • PMT00028 Quantum… 35 d     │
│  └─────────────────────────────┘      │   • PO00148 Coastal… ₹622,838  │
│  Try: [Delayed vendors] [Q3 by        │   • PO00221 duplicate of …     │
│  category] [Unusual] [Avg delay]      │   [View all]                   │
│  [Pending > ₹1L]                      │                                │
│                                       │  ✔ Data quality (3)            │
│  ANSWER                    [sql] route│   • PMT00012 paid, no amount   │
│  ┌─────────────────────────────┐      │   [View all]                   │
│  │ The vendors that had delayed│      │                                │
│  │ payments were Quantum …     │      │                                │
│  └─────────────────────────────┘      │                                │
│  ▸ Show SQL                           │                                │
│  ▾ Show data (2 rows)                 │                                │
│  ┌──────────────────────────┐         │                                │
│  │ vendor_name              │         │                                │
│  │ Quantum Circuit Traders  │         │                                │
│  └──────────────────────────┘         │                                │
└───────────────────────────────────────┴───────────────────────────────┘
```
Mobile: stack the zones, Ask first, Watchlist below, behind a tab or accordion.

## User flow

1. **Land.** Page loads, calls `/health`, `/examples`, `/anomalies`, `/data-quality`. Ask box is focused; example chips shown.
2. **Ask.** User types or clicks a chip, then presses Enter or Ask. Disable the button and show a loading state
   ("Thinking…", expect 2 to 6 seconds) so it can't be double-submitted.
3. **Result.** Show the answer, the route badge, a collapsed "Show SQL", and the data table (expanded if ≤ 20 rows).
4. **Verify.** User opens "Show SQL" (read-only code block with a copy button) and sorts/scans the table.
5. **Follow up.** Ask again; the new answer replaces the old one (no chat history in v1). Optionally keep a small
   "Recent questions" list in the browser only.
6. **Watchlist.** Clicking an anomaly row opens a detail drawer: rule, reason, vendor, value with unit. "View all" shows the
   full list grouped by rule.

## States to design (each one needs a visual)

| State | What to show |
|---|---|
| Empty (first load) | Example chips, one-line hint, no result area |
| Loading | Spinner/skeleton in the answer area; Ask disabled |
| Success, SQL route | Answer + `SQL` badge + SQL + table |
| Success, anomaly route | Answer + `Rules` badge + "scans all records" note + grouped flags table |
| Zero rows | "Nothing matched" with the SQL still available |
| Truncated | "Showing first 500 of N rows" |
| Validation error (422) | Inline message under the input |
| Server error (502) | Friendly message, Retry button, "Details" toggle |
| API unreachable | "Can't reach the copilot service" banner |

## Components to design
Question input with submit and character counter (max 500) · example chips · answer card (renders Markdown) ·
route badge (`SQL` / `Rules`) · collapsible SQL block with copy · results table (sticky header, right-aligned numbers,
₹ formatting with Indian grouping like 1,00,000, NULL shown as a muted "—") · anomaly list with a severity-neutral
warning style grouped by rule · data-quality list · as-of date pill · toast/banner for errors.

## Visual direction
- Calm, data-tool feel (think a clean analytics page, not a chat toy). Light theme first, dark optional.
- One accent colour for actions; a separate amber for anomalies; red only for errors.
- Tabular numbers (monospace or tabular-nums) in tables so digits align.
- Generous spacing; table text no smaller than 13px; WCAG AA contrast.

## Deliverables we want from you
1. Low-fidelity wireframes of the 9 states above (paper, Figma, or Excalidraw are all fine).
2. A short style note: colours, font, spacing, badge and table styles.
3. One hi-fi mock of the main screen (success state) and the anomaly drawer.
4. A list of anything the API does not give you that the design needs (we will add it to `src/api.py`).

## Questions to settle in the design review
- Does the Watchlist belong beside the answer, or on its own tab?
- Do we show the SQL to everyone, or behind an "advanced" toggle?
- Do we keep a recent-questions list, and where?
- Is a "this week" filter on anomalies worth adding to the API?

## Build plan after the design is agreed
A single HTML page served by the same FastAPI app (no extra framework, one command to run), calling the endpoints above.
Estimate: 1 to 2 days from agreed wireframes.

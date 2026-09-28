# Week 1 Progress — Days 1–3 Recap + Day 4 Guide

Status as of 23 Sept 2026. Covers what's done, what we learned, and what
Day 4 actually involves.

---

## Status at a glance

| Day | Theme | Status | Deliverable in repo |
|---|---|---|---|
| 1 (Mon) | Foundation | ✅ Done | `docs/problem_statement.md`, module recorded in `README.md` |
| 2 (Tue) | Walkthroughs & seed questions | ✅ Done | `docs/seed_questions.md`, walkthrough notes in `work.md` |
| 3 (Wed) | Mock dataset & schema | ✅ Done | 3 CSVs + `data/mock_sap/README.md` + `generate_mock_data.py` |
| 4 (Thu) | Architecture & stack | ⏳ Next | needs `docs/architecture.md` (+ confirm `requirements.txt`) |

---

## Day 1 — Foundation ✅

**Done**
- Repo `sap-copilot` created, collaborator added, scaffold pushed
  (`data/`, `docs/`, `src/{data_layer,retrieval,llm}`, `tests/`).
- Problem statement written: user = procurement analyst / AP-finance lead
  who can't write ABAP; tool answers plain-English questions over PO data;
  it matters because of IT/BI wait times, reliance on the few people who know ABAP, and missed anomalies.
- Two modules compared (Purchase Orders vs Invoices/AP). **Purchase Orders
  locked**: it has the richest anomaly surface on its own.
- Tech stack section written: CSV → SQLite → text-to-SQL → LLM
  (**Groq default, Gemini fallback**, switchable via `LLM_PROVIDER`).

**Learnings**
- *AI side:* a provider-agnostic `ask()` wrapper costs about 30 lines and means
  we never have to rewrite the retrieval layer to change LLM vendors.
- *SAP side:* the real users think in transaction codes (ME2M, ME23N), not
  tables. The value we offer is skipping the transaction-code knowledge, not the data.
- *Together:* "good enough to build against" beat "perfect". The open
  questions (e.g. what counts as "unusual") were recorded rather than
  blocking the day.

---

## Day 2 — Cross-Walkthroughs & Seed Questions ✅

**Done**
- AI walkthrough (notes in `work.md`): shape of an LLM API call,
  embeddings vs text-to-SQL, why RAG is the wrong tool for tables.
- SAP walkthrough: PO header vs line items, key fields, EKKO/EKPO naming.
  *(No written notes in the repo. Worth adding a short `docs/sap_primer.md`
  so the SAP context is recorded.)*
- 5 seed questions refined for the PO module, each with the exact fields it
  needs. That field list became the Day 3 schema spec.

**Learnings**
- *AI side:* every seed question is a **filter / aggregate / join over exact
  fields**. That confirms text-to-SQL over RAG. Vector search has no
  concept of `amount > 100000` or `AVG(delay)`.
- *AI side:* the LLM never touches the database. It sees schema + question
  and returns a SQL string, and our code runs it. That keeps it safe and
  debuggable.
- *SAP side:* real SAP splits a PO into header (EKKO: vendor, date) and
  items (EKPO: material, qty, price). We **deliberately flattened this** to
  one `purchase_orders` table for the mock. That's fine for 5 questions, but it's a
  known simplification.
- *Together:* mapping each question to its fields *before* building data
  meant Day 3 had a checklist instead of guesswork.

---

## Day 3 — Mock Dataset & Schema ✅

**Done**
- `vendors.csv` (30), `purchase_orders.csv` (222), `payments.csv` (163),
  generated deterministically by `generate_mock_data.py` (seed=42).
- Deliberate test cases seeded for Week 3 anomaly work:
  12 delayed payments, 3 outlier amounts, 2 duplicate POs,
  2 blank categories, 4 blank delivery dates, 2 blank payment amounts.
- `data/mock_sap/README.md` documents every column and type, plus a
  table checking each seed question against the schema.

**Verified (loaded into SQLite and queried)**
- All `vendor_id` and `po_id` foreign keys resolve. `payments.vendor_id`
  always matches its PO's vendor.
- All dates are ISO `YYYY-MM-DD`, so text comparison and `julianday()` work in SQLite.
- Every anomaly count above matches the README.
- `pytest` passes (loader test).

**Learnings / things to fix**
- **Blanks become `NULL`, not `''`.** pandas reads empty CSV cells as NaN,
  and SQLite stores them as `NULL`. The README suggests `WHERE category != ''`.
  That happens to drop NULLs, but only by accident. The honest version is
  `WHERE category IS NOT NULL`, or `COALESCE(category, 'Uncategorized')`
  for a bucket. The LLM prompt needs to say this explicitly.
- **Relative dates need a "today".** The data ends 2026-09-20. "This month"
  and "this week" only work if we pass the current date into the prompt.
  Also, September has only **1** delayed payment, so seed Q1 gives a thin
  demo answer. Consider seeding 2–3 more September delays.
- **Currency is inconsistent.** The problem statement says "$50,000" while
  seed Q5 says "₹1,00,000", and there's no currency column. Pick one
  (₹ is probably the better choice) and use it everywhere.
- **Q3 ("unusual") still has no rule.** The data supports both an outlier rule
  and a duplicate rule. Deciding between them is a Day 4 item.
- *SAP side:* denormalizing `vendor_id` into `payments` isn't how SAP
  does it, but it spares the LLM a join and makes its SQL less error-prone.
  That's a reasonable trade for a prototype.

---

## Day 4 — Architecture & Stack: what each task means

### Task 1 (together, ~20 min): Sketch the pipeline

The flow for one question:

```
 User question (English)
        │
        ▼
 ┌──────────────┐   schema text + today's date + question
 │ Retrieval    │ ─────────────────────────────────────────►  LLM call #1
 │ text_to_sql  │ ◄─────────────────────────────────────────  SQL string
 └──────┬───────┘
        │  validate: single SELECT only, no writes
        ▼
 ┌──────────────┐
 │ Data layer   │  CSVs → SQLite (loader.py) → run SQL → rows
 └──────┬───────┘
        │  question + SQL + rows
        ▼
   LLM call #2  →  analyst-style answer (vendors, PO numbers, amounts, delays)
```

What each layer owns:
- **Data layer** (`src/data_layer/loader.py`, exists): loads CSVs into
  SQLite. It doesn't know an LLM exists.
- **Retrieval layer** (`src/retrieval/text_to_sql.py`, partly exists):
  builds the schema description (done), prompts for SQL, validates it,
  and executes it.
- **LLM layer** (`src/llm/client.py`, exists): `ask(prompt, system)`.
  It doesn't know about SAP.
- **Answer formatting**: the second LLM call turns rows into a readable
  answer instead of a table dump.

Output: draw this (by hand or ASCII is fine) into `docs/architecture.md`.

### Task 2 (together): Text-to-SQL vs function-calling

| | Text-to-SQL | Function-calling |
|---|---|---|
| How | LLM writes SQL against the schema | LLM picks one of N pre-written query functions and fills in arguments |
| Flexibility | Any question the schema can answer | Only questions we pre-built |
| Safety | Must validate SQL (SELECT-only) | Safe by construction |
| Effort to extend | Zero code per new question | New function per question type |

**Recommendation: text-to-SQL**, with a SELECT-only validator. It covers
all 5 seed questions with one code path. Where it's risky, we can add *one*
pre-built function later. The obvious candidate is Q3 "unusual", because the
anomaly rule should be deterministic rather than left to the LLM to invent.

Also decide here: **the Q3 rule.** Suggested: flag a PO if
`amount > category mean + 2×stddev` **or** if it matches another PO on
`vendor_id + amount + po_date` (duplicate).

### Task 3 (you, ~25–30 min): Lock the stack + requirements.txt

⚠️ **The plan text says "Anthropic API (Claude)", but we already locked
Groq/Gemini on Day 1.** Keep Groq/Gemini (free tier, already wired into
`client.py`) and note the decision in `architecture.md`. The rest of the
plan still applies:
- Python 3.11, pandas + SQLite, plain API calls, **no LangChain**. At two
  calls per question, a framework only adds layers to debug.

`requirements.txt` already exists (`groq`, `google-generativeai`, `pandas`,
`python-dotenv`, `pytest`). The job is to **prove it installs cleanly**:

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python -m pytest -q            # should print "1 passed"
python -m src.llm.client       # with GROQ_API_KEY set → prints a hello
```

Note: `google-generativeai` is being superseded by Google's newer
`google-genai` SDK. That's fine for now, but flag it in the doc.

### Task 4 (her, ~10–15 min): SAP sanity check

Questions for her to answer against the schema:
- Do the joins make sense? `payments.po_id → purchase_orders.po_id →
  vendors.vendor_id`. Is a payment really one-to-one with a PO, or would
  real SAP have partial payments or several invoices per PO?
- Is flattening header + items (EKKO/EKPO) still acceptable once queries
  are SQL?
- Are the status values realistic (`Pending/Approved/Rejected/Closed`,
  `Paid/Scheduled`)?
- Is `due_date = delivery_date + payment_terms_days` how payment terms
  actually work (SAP often keys terms off the invoice/baseline date)?

### Day 4 deliverables checklist
- [ ] `docs/architecture.md`: diagram + text-to-SQL decision + Q3 rule
      + "Groq/Gemini, not Claude" note
- [ ] `requirements.txt` confirmed to install cleanly (test passes)
- [ ] Her SAP sanity-check notes added (to `architecture.md` or the PR)
- [ ] Update the `README.md` "See docs/architecture.md once Day 4 is done" line

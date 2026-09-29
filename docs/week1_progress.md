# Week 1 Progress — Full Recap (Days 1–5)

Status as of 29 Sept 2026. Week 1 (Foundation & Alignment) is complete.
Covers what's done, what we learned each day, and what Week 2 (Core Build)
starts with.

---

## Status at a glance

| Day | Theme | Status | Deliverable in repo |
|---|---|---|---|
| 1 (Mon) | Foundation | ✅ Done | `docs/problem_statement.md`, module recorded in `README.md` |
| 2 (Tue) | Walkthroughs & seed questions | ✅ Done | `docs/seed_questions.md`, walkthrough notes in `work.md` |
| 3 (Wed) | Mock dataset & schema | ✅ Done | 3 CSVs + `data/mock_sap/README.md` + `generate_mock_data.py` + `tests/test_seed_questions.py` |
| 4 (Thu) | Architecture & stack | ✅ Done | `docs/architecture.md` (pipeline, decisions, SAP sanity check), `requirements.txt` verified |
| 5 (Fri) | Repo finalized | ✅ Done | `.env.example`, updated `.gitignore`, `README.md` complete |

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
- [x] `docs/architecture.md`: diagram + text-to-SQL decision + Q3 rule
      + "Groq/Gemini, not Claude" note
- [x] `requirements.txt` confirmed to install cleanly (test passes)
- [x] Her SAP sanity-check notes added (in `architecture.md`)
- [x] Update the `README.md` "See docs/architecture.md once Day 4 is done" line

**What came back from the SAP sanity check:** joins hold up cleanly (0
orphan keys, no fan-out), flattening EKKO/EKPO is fine until we need
material-level questions, the status labels map onto real SAP concepts
(release strategy, delivery/invoice flags, BSAK/BSIK) well enough for a
business-language tool, and `due_date` as delivery-date-based is an
acceptable stand-in with no invoice table yet. One real finding: 36
`Pending` POs have a past `delivery_date` — fine as long as the field is
read as *scheduled*, not *actual*, delivery (now a documented prompt rule).

---

## Day 5 — Repo Finalized ✅

**Done**
- `.env.example` added (`LLM_PROVIDER`, `GROQ_API_KEY`, commented
  `GEMINI_API_KEY`) so a fresh clone knows which keys it needs without
  reading the code.
- `.gitignore` extended: `.pytest_cache/` and the personal planning file
  (`DAY3-5_PLAN.md`) excluded from commits.
- `README.md` rewritten: Windows-first setup commands, a "Running (Week 1)"
  section that lists only commands that actually work today (tests, loader,
  generator, LLM smoke test — no `python -m src.app` yet), and the status
  line updated to reflect Week 1 as complete.
- Full suite verified green: `python -m pytest -q` → **8 passed**.

**Still open (needs the two of you, not just the repo)**
- Fresh-clone test on a second machine/folder to prove "clone and run"
  actually holds, not just "works on my machine".
- Her final pass on the mock data + problem statement for consistency.
- The Week 1 review call itself — walk the checklist, agree what's fuzzy,
  confirm the Week 2 split below.

**Learnings**
- A repo "being done" and a repo being *provably* done are different
  things — the seed-question tests (Day 3) and the fresh-clone step (Day 5)
  exist specifically to convert claims ("this works") into checks that fail
  loudly if they stop being true.
- Small inconsistencies compound: the Claude→Groq/Gemini mismatch, the
  `$`→`₹` typo, and the `!= ''`→`IS NULL` bug were all caught because each
  day's task included proving the previous day's work, not just adding to it.

---

## Week 1 — the whole story, in short

We picked Purchase Orders as the module (richest anomaly surface: vendor,
amount, dates, status), agreed the shape of the problem is text-to-SQL over
structured tables rather than RAG (every seed question is a filter,
aggregate, or join — vector search has no notion of `amount > 100000`), and
built a fully reproducible mock dataset (222 POs / 30 vendors / 163
payments, seed=42) with deliberately planted messiness — delayed payments,
outlier amounts, duplicate POs, blank fields — that doubles as the Week 3
anomaly test set today via `tests/test_seed_questions.py`.

The architecture locked to two LLM calls per question (question → SQL,
rows → answer) with a SELECT-only validator, Groq as the default provider
(Gemini fallback) instead of the original Claude assumption, and one
deliberate exception: the "unusual transactions" rule (Q3) is fixed SQL,
not LLM-generated, because anomaly detection needs to be deterministic and
explainable. The SAP sanity check confirmed the schema's joins and
simplifications are reasonable for a prototype, while surfacing real SAP
nuances (release-strategy statuses, baseline-date payment terms, one
payment per PO vs partial payments) worth revisiting later.

By the end of Week 1: problem statement, seed questions, mock data +
schema, architecture, and a runnable, tested repo are all in place and
committed. Nothing about Week 2 requires re-deciding any of this.

## Week 2 goals (Core Build)

Target: a working end-to-end question → answer flow for the 5 seed
questions, split so both halves land independently and meet in the middle
on Day 3.

- **Day 1** — Her: build/clean the data layer into a queryable form (verify
  `load_to_sqlite()` handles the real dataset cleanly). You: a basic LLM
  call + prompt template for Q&A using `src/llm/client.py`.
- **Day 2** — Her: add 2–3 more data scenarios (the Sept delays flagged in
  Day 5, plus any other edge cases). You: wire the LLM to real query
  capability — `ask_question(q)` in `src/retrieval/text_to_sql.py` (prompt →
  SQL → SELECT-only validate → run → rows).
- **Day 3** — Integrate both halves into one end-to-end flow; test against
  all 5 seed questions, ideally against a "golden answers" file (expected
  SQL result per question) so wrong answers are caught automatically, not
  eyeballed.
- **Day 4** — Debug integration issues together (on call); fix
  wrong/broken answers.
- **Day 5** — Demo v0.1 to each other, list the top 5 things broken or
  missing, Week 2 review.

**Carried over from Week 1 (bring these into Week 2 decisions):**
- Pin "today's date" for demos (data ends 2026-09-20) or use the real date?
- One payment per PO is fine for now — model partial payments later if
  anomaly questions need it.
- `google-generativeai` deprecation — migrate to `google-genai` now or only
  if Gemini actually gets used as the fallback.

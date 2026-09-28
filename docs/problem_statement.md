# Problem Statement

## Who is this for?

A finance/procurement business user (e.g. a procurement analyst or AP/finance
ops lead) who regularly needs answers from SAP data — vendor spend, payment
status, PO history — but doesn't know ABAP, transaction codes, or how to
write a custom report. Today they either wait on IT/BI to pull a report or
dig through a fixed set of SAP transactions (ME2M, ME23N, etc.) themselves.

## What question does it answer?

Plain-English questions over Purchase Order data, e.g.:

- "Which vendors had delayed payments this month?"
- "Show me all POs over ₹50,000 approved in the last quarter."
- "Are there any duplicate or unusually large POs for [vendor]?"

See `docs/seed_questions.md` for the full list of 5 seed questions the demo
is built against.

## Why does it matter?

Without this tool, getting an answer means one of:
- Filing a request with IT/BI and waiting hours or days for a report, or
- Learning enough ABAP/transaction codes to self-serve, which most business
  users never do, or
- Manually eyeballing exports in Excel, which doesn't scale and misses
  anomalies (delayed approvals, duplicate POs, outlier amounts) that aren't
  obvious from a flat table.

The cost is time (delay waiting on IT), dependency (bottlenecked on a small
group of ABAP-literate people), and missed signal (anomalies that a human
skimming rows won't catch but a systematic check will).

## Module in scope

**Purchase Orders** — locked Day 1.

Two candidates were considered:

| Module | Pros | Cons |
|---|---|---|
| **Purchase Orders** | Rich vendor/date/amount/status fields → natural anomaly angle (unusual amounts, delayed approvals, duplicate POs); directly supports 4 of 5 seed questions | Anomaly logic (e.g. "delayed") needs a defined threshold, which we have to make up for mock data |
| **Invoices / Accounts Payable** | Also supports payment-delay questions; closer to the "money out the door" story finance cares about | Thinner mock data shape for Week 1 (fewer natural anomaly signals without also modeling POs behind them); overlaps with PO scope anyway since invoices reference POs |

**Decision:** Purchase Orders — it gives the richest anomaly surface on its
own and doesn't require modeling a second upstream object (POs) just to make
sense of it. Data shape (vendor, PO date, amount, status, category) directly
supports 4 of the 5 seed questions in `docs/seed_questions.md`.

## Success looks like

A good demo answer, e.g. for "Which vendors had delayed payments this
month?": the tool returns a short natural-language answer naming the
specific vendors and PO numbers, the delay (in days) versus the expected
approval/payment window, and total amount affected — not just a raw table
dump. It should read like an analyst's answer, not a SQL result set.

## Tech stack

**Data layer** — Mock SAP data ships as CSVs (`data/mock_sap/`) and is loaded into
SQLite at runtime (`src/data_layer/loader.py`, pandas → `sqlite3`). SQLite keeps
the stack dependency-free and lets the retrieval layer run plain read-only SQL
instead of a bespoke query DSL.

**Retrieval layer (text-to-SQL)** — `src/retrieval/text_to_sql.py` builds a schema
description from the SQLite DB and prompts the LLM to generate a single
read-only `SELECT`. The query is validated (SELECT-only, no writes) before
execution, and results are passed back to the LLM layer to phrase as a
natural-language answer. This keeps the LLM out of the business-logic path —
it only ever sees schema + question, and only ever proposes a query.

**LLM layer** — `src/llm/client.py` is a thin, provider-agnostic wrapper so we
aren't locked into one vendor during prototyping:

- **Groq** (default) — Llama 3.x served on Groq's LPU inference. Chosen for
  near-instant responses (sub-second typically), which matters for a
  text-to-SQL loop that may need 1-2 follow-up calls per question, and a
  generous free tier for a Week-1 prototype.
- **Gemini** (fallback/alternate) — Google's `gemini-1.5-flash` / `2.0-flash`,
  also free-tier friendly, used as a second option to compare answer quality
  and for redundancy if Groq rate-limits during a demo.
- Selected via `LLM_PROVIDER` env var (`groq` | `gemini`), so swapping
  providers doesn't touch the retrieval or data layers.

**Why this split (efficiency rationale)** — the layers only talk through plain
Python data (schema strings, SQL strings, row lists), so each one is testable
and swappable in isolation: the data layer doesn't know an LLM exists, the
retrieval layer doesn't know which LLM provider is configured, and the LLM
layer doesn't know about SAP data at all. Cost/latency stays low because
every question costs at most two small LLM calls (question→SQL,
result→answer) against a local SQLite file — no vector DB, no embeddings,
no hosted infra needed for Week 1's scope.

**Testing** — `pytest` for the data/retrieval layers; LLM calls are mocked in
tests so the suite runs without API keys or network access.
# Problem Statement

*Fill in during Day 1.*

## Who is this for?

(e.g. a finance/procurement business user who needs answers from SAP data but doesn't know ABAP or transaction codes)

## What question does it answer?

(e.g. "Which vendors had delayed payments this month?")

## Why does it matter?

(business impact of not having this — time lost, dependency on IT/ABAP specialists, etc.)

## Module in scope

**Purchase Orders** — locked Day 1. Rich vendor/date/amount fields give a
natural anomaly angle (unusual amounts, delayed approvals, duplicate POs),
and the data shape (vendor, PO date, amount, status, category) directly
supports 4 of the 5 seed questions in `docs/seed_questions.md`.

## Success looks like

(what a good demo answer looks like for one of the 5 seed questions)

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

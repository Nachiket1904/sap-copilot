# SAP Copilot

An AI assistant that answers natural-language questions over SAP-style enterprise data (starting with Purchase Orders), and flags anomalies like unusual payment delays.

## Problem

SAP systems hold huge amounts of valuable business data — but accessing it usually means transaction codes, technical reports, or someone who knows ABAP. This project lets a user ask a plain-English question and get a clear answer, without touching raw SAP tables.

See `docs/problem_statement.md` for the full write-up.

## Module in scope (Week 1)

- [x] **Purchase Orders** — rich vendor/date/amount fields, natural anomaly angle
      (unusual amounts, delayed approvals). Locked Day 1; see
      `docs/problem_statement.md` for the full rationale.

## Architecture

```
data layer (CSV → SQLite)  →  retrieval layer (text-to-SQL)  →  LLM layer (Groq / Gemini)  →  answer
```

LLM provider is swappable via `LLM_PROVIDER` (`groq` default, `gemini` fallback) —
see `docs/problem_statement.md` for the full tech-stack rationale.

Full diagram and design decisions: [docs/architecture.md](docs/architecture.md).

## Project structure

```
sap-copilot/
├── data/
│   └── mock_sap/          # mock CSVs: purchase_orders, vendors, payments
├── docs/                  # problem statement, seed questions, architecture notes
├── notebooks/             # exploration / prototyping
├── src/
│   ├── data_layer/        # load CSVs into a queryable form (pandas / SQLite)
│   ├── retrieval/         # text-to-SQL / query generation
│   └── llm/                # Groq/Gemini calls, prompt templates
├── tests/
├── requirements.txt
└── README.md
```

## Setup

Requires Python 3.11+.

```bash
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # macOS/Linux: cp .env.example .env  — then add your key
```

Free Groq API key at console.groq.com.

## Running

```bash
python -m pytest -v                 # data + seed-question checks
python -m src.data_layer.loader     # load CSVs into SQLite + data-quality checks
python generate_mock_data.py        # regenerate the mock dataset (deterministic)
python -m src.llm.client            # LLM smoke test (needs GROQ_API_KEY)

# Week 2 (need GROQ_API_KEY in .env):
python -m src.retrieval.text_to_sql --manual "Which vendors had delayed payments this month?"   # Day 1: schema + question -> plain-English plan
python -m src.retrieval.text_to_sql "Which vendors had delayed payments this month?"            # Day 2: question -> SQL -> rows -> answer
```

Tests stub the LLM, so `pytest` needs no API key. The `python -m src.app` entry point is still to come.

## Collaborators

- AI Engineer — LLM integration, prompt design, query/retrieval layer, overall AI architecture
- SAP/ABAP domain — data structure & schema design, business scenario accuracy, edge cases

## Status

✅ Week 1 complete: problem, data, schema, architecture locked. Next: Week 2 core build (data layer + first LLM call).

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

See `docs/architecture.md` once Day 4 is done.

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

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set your LLM provider and API key (Groq by default, free tier at console.groq.com):

```bash
export LLM_PROVIDER=groq                # or: gemini
export GROQ_API_KEY=your_key_here       # Windows: set GROQ_API_KEY=your_key_here
# export GEMINI_API_KEY=your_key_here   # only needed if LLM_PROVIDER=gemini
```

## Running

```bash
python -m src.app
```

(Wire this up once the Week 2 end-to-end flow exists.)

## Collaborators

- AI Engineer — LLM integration, prompt design, query/retrieval layer, overall AI architecture
- SAP/ABAP domain — data structure & schema design, business scenario accuracy, edge cases

## Status

🚧 Week 1 — Foundation & Alignment. See the project plan doc for the day-by-day breakdown.
# sap-copilot
# sap-copilot

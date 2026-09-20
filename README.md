# SAP Copilot

An AI assistant that answers natural-language questions over SAP-style enterprise data (starting with Purchase Orders), and flags anomalies like unusual payment delays.

## Problem

SAP systems hold huge amounts of valuable business data — but accessing it usually means transaction codes, technical reports, or someone who knows ABAP. This project lets a user ask a plain-English question and get a clear answer, without touching raw SAP tables.

See `docs/problem_statement.md` for the full write-up.

## Module in scope (Week 1)

- [ ] TBD — see Day 1 checklist (Purchase Orders is the leading candidate)

## Architecture

```
data layer (CSV → SQLite)  →  query layer (text-to-SQL)  →  LLM layer (Claude API)  →  answer
```

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
│   └── llm/                # Claude API calls, prompt templates
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

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=your_key_here   # Windows: set ANTHROPIC_API_KEY=your_key_here
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

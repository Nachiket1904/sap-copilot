"""HTTP backend for the copilot (FastAPI). Run:  uvicorn src.api:app --reload
Interactive docs at http://127.0.0.1:8000/docs

Endpoints:
  GET  /health         liveness + as-of date
  GET  /examples       the seed questions, for a UI to offer as one-click prompts
  POST /ask            {"question": "..."} -> answer, SQL used, result rows, route (sql | anomaly)
  GET  /anomalies      every record flagged by src/data_layer/anomaly.py (no LLM involved)
  GET  /data-quality   rows flagged by the loader's validation rules (no LLM involved)
"""
import math
from datetime import date, datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.app import AS_OF, SEED_QUESTIONS, ask_copilot
from src.data_layer.anomaly import find_anomalies
from src.data_layer.loader import flag_bad_rows, load_to_sqlite

MAX_QUESTION_CHARS = 500
MAX_ROWS_RETURNED = 500

app = FastAPI(title="SAP Copilot API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])


def get_conn():
    """One in-memory SQLite DB per request: loading 3 small CSVs takes milliseconds, and a
    connection can't be shared across FastAPI's worker threads."""
    conn = load_to_sqlite(verbose=False)
    try:
        yield conn
    finally:
        conn.close()


def _json_safe(value):
    """Turn pandas/NumPy/NaN values into something the JSON encoder accepts."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "item"):  # numpy scalar
        return _json_safe(value.item())
    return value


def _records(df) -> list[dict]:
    return [{k: _json_safe(v) for k, v in row.items()} for row in df.to_dict(orient="records")]


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=MAX_QUESTION_CHARS)


class AskResponse(BaseModel):
    question: str
    answer: str
    route: str
    sql: str
    columns: list[str]
    rows: list[list]
    row_count: int
    truncated: bool
    as_of: str


@app.get("/health")
def health():
    return {"status": "ok", "as_of": AS_OF}


@app.get("/examples")
def examples():
    return {"questions": SEED_QUESTIONS}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, conn=Depends(get_conn)):
    question = req.question.strip()
    if len(question) < 3:
        raise HTTPException(status_code=422, detail="Question is too short.")
    result = ask_copilot(question, conn, AS_OF)
    if result["error"]:
        # The pipeline never raises; surface its failure as a gateway error the UI can show.
        raise HTTPException(status_code=502, detail=result["error"])
    rows = result["rows"]
    return AskResponse(
        question=question,
        answer=result["answer"],
        route=result["route"],
        sql=result["sql"],
        columns=result["columns"],
        rows=[[_json_safe(v) for v in r] for r in rows[:MAX_ROWS_RETURNED]],
        row_count=len(rows),
        truncated=len(rows) > MAX_ROWS_RETURNED,
        as_of=AS_OF,
    )


@app.get("/anomalies")
def anomalies(conn=Depends(get_conn)):
    found = find_anomalies(conn)
    return {"count": len(found), "items": _records(found)}


@app.get("/data-quality")
def data_quality(conn=Depends(get_conn)):
    flagged = flag_bad_rows(conn, out_path=None)  # report only; don't rewrite the CSV from a GET
    return {"count": len(flagged), "items": _records(flagged)}

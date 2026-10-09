"""API tests. The LLM is stubbed (no key, no cost): the first call returns SQL, the second returns prose."""
import pytest
from fastapi.testclient import TestClient

from src.api import app
from src.retrieval import text_to_sql as t2s

client = TestClient(app)


@pytest.fixture
def fake_llm(monkeypatch):
    def fake_ask(prompt, system=None):
        if system == t2s.SQL_SYSTEM:
            return "```sql\nSELECT vendor_id, vendor_name FROM vendors ORDER BY vendor_id LIMIT 3\n```"
        return "Three vendors."
    monkeypatch.setattr(t2s, "ask", fake_ask)


def test_health():
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["as_of"]


def test_examples_lists_seed_questions():
    assert len(client.get("/examples").json()["questions"]) == 5


def test_ask_sql_route(fake_llm):
    r = client.post("/ask", json={"question": "List some vendors"})
    assert r.status_code == 200
    body = r.json()
    assert body["route"] == "sql"
    assert body["answer"] == "Three vendors."
    assert body["columns"] == ["vendor_id", "vendor_name"]
    assert body["row_count"] == 3 and not body["truncated"]


def test_ask_anomaly_route_does_not_write_sql(fake_llm):
    body = client.post("/ask", json={"question": "Flag any unusual transactions"}).json()
    assert body["route"] == "anomaly"
    assert {"rule", "record_id"} <= set(body["columns"])
    assert body["row_count"] >= 11


def test_ask_rejects_bad_input():
    assert client.post("/ask", json={"question": "hi"}).status_code == 422
    assert client.post("/ask", json={"question": "x" * 501}).status_code == 422
    assert client.post("/ask", json={}).status_code == 422


def test_ask_reports_pipeline_failure_as_502(monkeypatch):
    monkeypatch.setattr(t2s, "ask", lambda prompt, system=None: "DROP TABLE vendors")
    r = client.post("/ask", json={"question": "Delete everything please"})
    assert r.status_code == 502
    assert "SELECT" in r.json()["detail"]


def test_anomalies_endpoint():
    body = client.get("/anomalies").json()
    ids = {i["record_id"] for i in body["items"]}
    assert body["count"] == len(body["items"]) >= 11
    assert {"PO00148", "PMT00028", "PO00221"} <= ids


def test_data_quality_endpoint():
    body = client.get("/data-quality").json()
    assert {"PMT00012", "PMT00113"} <= {i["record_id"] for i in body["items"]}

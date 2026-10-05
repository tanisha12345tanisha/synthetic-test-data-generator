"""
API-level tests for app/main.py using FastAPI's TestClient.

Covers every endpoint end to end:
  - GET  /                 -> service banner
  - GET  /health           -> health probe
  - POST /validate-schema  -> echoes validated schema; 422 on bad schema
  - POST /generate         -> full dataset + summary + quality report
  - POST /export/{json,csv,pipe} -> streaming file with right headers
  - POST /infer-schema     -> CSV upload; 400 on non-CSV / empty CSV

These are integration tests: they run the real generation + quality + export
stack behind each route, so they also guard the wiring between layers.
"""

import io
import json

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.main import app


async def override_current_user():
    return object()


app.dependency_overrides[get_current_user] = override_current_user
client = TestClient(app)


def valid_request(row_count=10, seed=123):
    return {
        "dataset_name": "api test",
        "row_count": row_count,
        "seed": seed,
        "columns": [
            {"name": "id", "type": "id", "prefix": "C_"},
            {"name": "n", "type": "integer", "min": 1, "max": 100},
            {"name": "email", "type": "email"},
        ],
    }


# ===========================================================================
# GET /  and  /health
# ===========================================================================

class TestRootAndHealth:

    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "running"
        assert body["mode"] == "LLM-free"
        assert body["data_policy"] == "synthetic-only"

    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "healthy"}


# ===========================================================================
# POST /validate-schema
# ===========================================================================

class TestValidateSchema:

    def test_valid_schema(self):
        resp = client.post("/validate-schema", json=valid_request())
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is True
        assert body["dataset_name"] == "api test"
        assert body["total_columns"] == 3
        assert body["synthetic_only"] is True
        assert "case_distribution" in body

    def test_invalid_schema_bad_type_422(self):
        req = valid_request()
        req["columns"][0]["type"] = "not_a_real_type"
        resp = client.post("/validate-schema", json=req)
        assert resp.status_code == 422

    def test_invalid_schema_row_count_zero_422(self):
        req = valid_request()
        req["row_count"] = 0
        resp = client.post("/validate-schema", json=req)
        assert resp.status_code == 422

    def test_invalid_schema_no_columns_422(self):
        req = valid_request()
        req["columns"] = []
        resp = client.post("/validate-schema", json=req)
        assert resp.status_code == 422

    def test_missing_body_422(self):
        resp = client.post("/validate-schema", json={})
        assert resp.status_code == 422


# ===========================================================================
# POST /generate
# ===========================================================================

class TestGenerate:

    def test_generate_shape(self):
        resp = client.post("/generate", json=valid_request(row_count=15))
        assert resp.status_code == 200
        body = resp.json()
        assert body["row_count"] == 15
        assert len(body["generated_rows"]) == 15
        assert "summary" in body
        assert "quality_report" in body

    def test_generate_rows_have_metadata(self):
        resp = client.post("/generate", json=valid_request(row_count=5))
        rows = resp.json()["generated_rows"]
        for row in rows:
            assert "__case_type" in row
            assert "__case_labels" in row
            assert "id" in row and "n" in row and "email" in row

    def test_generate_summary_totals(self):
        resp = client.post("/generate", json=valid_request(row_count=20))
        summary = resp.json()["summary"]
        assert summary["total_rows"] == 20
        assert summary["total_columns"] == 3
        assert summary["synthetic_only"] is True

    def test_generate_bad_request_422(self):
        req = valid_request()
        req["row_count"] = 99999999  # exceeds le=10000
        resp = client.post("/generate", json=req)
        assert resp.status_code == 422


# ===========================================================================
# POST /export/{json,csv,pipe}
# ===========================================================================

class TestExportEndpoints:

    def test_export_json(self):
        resp = client.post("/export/json", json=valid_request(row_count=8))
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]
        assert ".json" in resp.headers["content-disposition"]
        parsed = json.loads(resp.content)
        assert len(parsed) == 8

    def test_export_csv(self):
        resp = client.post("/export/csv", json=valid_request(row_count=8))
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert ".csv" in resp.headers["content-disposition"]
        text = resp.content.decode("utf-8")
        # header + 8 data rows (+ trailing newline)
        assert text.count("\n") >= 8

    def test_export_pipe(self):
        resp = client.post("/export/pipe", json=valid_request(row_count=8))
        assert resp.status_code == 200
        assert ".psv" in resp.headers["content-disposition"]
        assert "|" in resp.content.decode("utf-8")

    def test_export_json_bad_request_422(self):
        req = valid_request()
        req["dataset_name"] = "   "  # empty after strip
        resp = client.post("/export/json", json=req)
        assert resp.status_code == 422


# ===========================================================================
# POST /infer-schema
# ===========================================================================

class TestInferSchema:

    def _upload(self, filename, content):
        return client.post(
            "/infer-schema",
            files={"file": (filename, io.BytesIO(content.encode("utf-8")), "text/csv")},
        )

    def test_valid_csv(self):
        resp = self._upload("data.csv", "reading,order_status\n1,open\n2,closed\n3,open\n")
        assert resp.status_code == 200
        body = resp.json()
        assert body["row_count_detected"] == 3
        assert body["columns_detected"] == 2
        assert body["synthetic_only"] is True

    def test_non_csv_rejected_400(self):
        resp = self._upload("data.txt", "reading\n1\n2\n")
        assert resp.status_code == 400
        assert "CSV" in resp.json()["detail"]

    def test_empty_csv_400(self):
        resp = self._upload("empty.csv", "")
        assert resp.status_code == 400

    def test_header_only_csv_400(self):
        resp = self._upload("headeronly.csv", "a,b\n")
        assert resp.status_code == 400

    def test_missing_file_422(self):
        resp = client.post("/infer-schema")
        assert resp.status_code == 422
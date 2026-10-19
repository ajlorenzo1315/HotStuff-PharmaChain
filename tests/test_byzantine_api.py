"""HTTP contract tests for the Byzantine benchmark endpoints."""

import csv
import io

from fastapi.testclient import TestClient

from pharmachain.api.dashboard import app

client = TestClient(app)


def test_modes_catalog():
    response = client.get("/api/byzantine/modes")
    assert response.status_code == 200
    data = response.json()
    assert data["quorum"] == 3
    assert {m["id"] for m in data["modes"]} == {"omit", "invalid_signature"}


def test_invalid_mode_returns_422():
    response = client.get("/api/byzantine/compare?mode=unknown&rounds=2")
    assert response.status_code == 422


def test_round_limits_return_422():
    assert client.get("/api/byzantine/compare?rounds=0").status_code == 422
    assert client.get("/api/byzantine/compare?rounds=101").status_code == 422


def test_compare_returns_three_scenarios():
    response = client.get("/api/byzantine/compare?mode=omit&rounds=2&seed=42")
    assert response.status_code == 200
    scenarios = response.json()["scenarios"]
    assert [s["faulty_count"] for s in scenarios] == [0, 1, 2]
    assert all(len(s["round_details"]) == 2 for s in scenarios)


def test_csv_download():
    response = client.get("/api/byzantine/compare.csv?mode=omit&rounds=2")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert len(rows) == 3
    assert [row["faulty_count"] for row in rows] == ["0", "1", "2"]

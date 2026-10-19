"""Unit tests for the visual API's stable, evidence-based contract."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from pharmachain.api.visual_lab import (
    build_attack_trace,
    normalize_events,
    router,
)


def test_trace_preserves_actual_events():
    raw = [
        {"time": 1.2, "event": "VOTE_CREATED", "node": "validator-2", "view": 4},
        {"time": 1.3, "event": "QC_FORMED", "node": "validator-0", "view": 4},
    ]
    result = normalize_events(raw)
    assert [e["type"] for e in result] == ["VOTE", "QC"]
    assert result[0]["evidence"] == raw[0]
    assert result[0]["target"] == ""  # No fabricated recipient


def test_conclusion_depends_on_measured_outcome():
    passed = build_attack_trace("forged_qc", {"passed": True, "events": []})
    failed = build_attack_trace("forged_qc", {"passed": False, "events": []})
    assert "cumple" in passed["conclusion"]
    assert "NO cumple" in failed["conclusion"]


def test_unknown_scenario_rejected():
    with pytest.raises(ValueError):
        build_attack_trace("unknown", {})


def test_router_catalog_and_validation():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    assert client.get("/api/visual/catalog").status_code == 200
    assert client.get("/api/visual/attack/nonexistent").status_code == 404
    assert client.get("/api/visual/byzantine?mode=invalid").status_code == 422
    assert client.get("/api/visual/byzantine?rounds=101").status_code == 422


def test_byzantine_round_trace_is_not_fabricated(monkeypatch):
    import pharmachain.api.byzantine_benchmark as benchmark

    monkeypatch.setattr(
        benchmark,
        "compare",
        lambda **kwargs: {
            "scenarios": [
                {
                    "faulty_count": 0,
                    "qc_rounds": 1,
                    "rounds": 2,
                    "round_details": [
                        {"view": 1, "leader": "validator-0", "qc_formed": True},
                        {"view": 2, "leader": "validator-1", "qc_formed": False},
                    ],
                }
            ],
        },
    )
    app = FastAPI()
    app.include_router(router)
    result = TestClient(app).get("/api/visual/byzantine").json()
    events = result["scenarios"][0]["events"]
    assert [e["name"] for e in events] == ["QC_FORMED", "ROUND_WITHOUT_QC"]
    assert all(e["target"] == "" for e in events)

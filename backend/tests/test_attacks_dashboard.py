"""API and scenario checks for the educational security lab."""

import pytest
from fastapi.testclient import TestClient

from pharmachain.api.attacks import SCENARIOS, run_scenario
from pharmachain.api.dashboard import app


@pytest.mark.parametrize("scenario", list(SCENARIOS))
def test_scenario_security_property(scenario):
    result = run_scenario(scenario)
    assert result["passed"], result["observation"]
    assert result["events"]


def test_catalog():
    response = TestClient(app).get("/api/attacks")
    assert response.status_code == 200
    assert len(response.json()["scenarios"]) == len(SCENARIOS)


def test_unknown_attack_rejected():
    response = TestClient(app).post("/api/attacks/not-an-attack")
    assert response.status_code == 404


def test_attack_does_not_reset_interactive_simulator():
    client = TestClient(app)
    client.post("/api/simulation/reset")
    before = client.get("/api/simulation").json()
    response = client.post("/api/attacks/forged_qc")
    assert response.status_code == 200
    after = client.get("/api/simulation").json()
    assert before == after

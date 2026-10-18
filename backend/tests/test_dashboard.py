"""Pruebas de integración HTTP del dashboard (requieren fases 1-13 instaladas)."""

from fastapi.testclient import TestClient

from pharmachain.api import dashboard


def test_dashboard_serves_html():
    client = TestClient(dashboard.app)
    response = client.get("/")
    assert response.status_code == 200
    assert "HotStuff Lab" in response.text


def test_initial_state_and_round():
    client = TestClient(dashboard.app)
    assert client.post("/api/simulation/reset").status_code == 200
    initial = client.get("/api/simulation").json()
    assert initial["quorum"] == 3
    assert len(initial["nodes"]) == 4
    response = client.post("/api/simulation/round")
    assert response.status_code == 200
    assert response.json()["round"]["view"] == 1


def test_disconnect_and_reconnect():
    client = TestClient(dashboard.app)
    client.post("/api/simulation/reset")
    disconnected = client.post("/api/simulation/disconnect", json={"node_id": "validator-2"})
    assert disconnected.status_code == 200
    assert disconnected.json()["nodes"][2]["online"] is False
    reconnected = client.post("/api/simulation/reconnect", json={"node_id": "validator-2"})
    assert reconnected.json()["nodes"][2]["online"] is True


def test_unknown_validator_rejected():
    client = TestClient(dashboard.app)
    response = client.post("/api/simulation/disconnect", json={"node_id": "attacker"})
    assert response.status_code == 404

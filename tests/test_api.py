from fastapi.testclient import TestClient

from pharmachain.api.main import app


def test_initial_status():
    with TestClient(app) as client:
        response = client.get("/api/status")

        assert response.status_code == 200

        data = response.json()

        assert data["validators"] == 4
        assert data["quorum"] == 3
        assert data["committed_height"] == 0


def test_register_and_transfer():
    with TestClient(app) as client:
        register = client.post(
            "/api/demo/register",
            json={
                "batch_id": "LOT-001",
                "medicine_name": "Amoxicilina",
                "quantity": 100,
            },
        )

        assert register.status_code == 200
        assert register.json()["committed"]

        transfer = client.post(
            "/api/demo/transfer",
            json={
                "batch_id": "LOT-001",
                "sender_id": "laboratory",
                "receiver_id": "distributor",
            },
        )

        assert transfer.status_code == 200

        batches = client.get("/api/batches").json()

        assert len(batches) == 1
        assert batches[0]["custodian_id"] == "distributor"

        blocks = client.get("/api/blocks").json()

        assert len(blocks) >= 3


def test_duplicate_batch_rejected():
    with TestClient(app) as client:
        payload = {
            "batch_id": "LOT-002",
            "medicine_name": "Ibuprofeno",
            "quantity": 50,
        }

        first = client.post(
            "/api/demo/register",
            json=payload,
        )

        second = client.post(
            "/api/demo/register",
            json=payload,
        )

        assert first.status_code == 200
        assert second.status_code == 400


def test_non_custodian_rejected():
    with TestClient(app) as client:
        client.post(
            "/api/demo/register",
            json={
                "batch_id": "LOT-003",
                "medicine_name": "Paracetamol",
                "quantity": 200,
            },
        )

        response = client.post(
            "/api/demo/transfer",
            json={
                "batch_id": "LOT-003",
                "sender_id": "distributor",
                "receiver_id": "hospital",
            },
        )

        assert response.status_code == 400

        batches = client.get("/api/batches").json()

        assert batches[0]["custodian_id"] == "laboratory"


def test_invalid_quantity():
    with TestClient(app) as client:
        response = client.post(
            "/api/demo/register",
            json={
                "batch_id": "LOT-004",
                "medicine_name": "Medicamento",
                "quantity": -5,
            },
        )

        assert response.status_code == 422

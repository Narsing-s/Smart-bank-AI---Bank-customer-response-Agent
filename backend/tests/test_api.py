from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_is_up():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"


def test_faq_answer_is_grounded_in_demo_knowledge():
    response = client.post("/api/chat", json={"message": "How do I block a lost card?", "language": "en"})
    assert response.status_code == 200
    assert response.json()["intent"] == "block_card"
    assert response.json()["source"] == "approved_demo_faq"


def test_unknown_transaction_returns_404():
    response = client.get("/api/transactions/NOT-A-REAL-ID")
    assert response.status_code == 404


def test_demo_transaction_lookup():
    response = client.get("/api/transactions/DEMO-TXN-1001")
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"
    assert "Synthetic demo data only" in response.json()["notice"]


def test_complaint_requires_minimum_description():
    response = client.post("/api/complaints", json={"category": "other", "description": "short"})
    assert response.status_code == 422


def test_fallback_requires_escalation():
    response = client.post("/api/chat", json={"message": "Please explain an unknown banking issue", "language": "en"})
    assert response.status_code == 200
    assert response.json()["escalation_required"] is True

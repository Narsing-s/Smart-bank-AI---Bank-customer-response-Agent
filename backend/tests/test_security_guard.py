from fastapi.testclient import TestClient

from app.main import app, answer_for, looks_sensitive

client = TestClient(app)


def test_detects_otp_value_without_echoing_it():
    assert looks_sensitive("My OTP is 123456")
    response = answer_for("My OTP is 123456", "en")
    assert response.intent == "sensitive_data_guard"
    assert "123456" not in response.answer
    assert response.escalation_required is True


def test_detects_pin_and_full_card_number():
    assert looks_sensitive("PIN: 1234")
    assert looks_sensitive("4111 1111 1111 1111")


def test_sensitive_complaint_is_rejected():
    response = client.post(
        "/api/complaints",
        json={"category": "card", "description": "My OTP is 123456 please help me"},
    )
    assert response.status_code == 400


def test_normal_faq_still_works():
    response = answer_for("How do I block a lost card?", "en")
    assert response.intent == "block_card"
    assert response.source == "approved_demo_faq"


def test_unknown_query_escalates():
    response = answer_for("Can you explain a special request?", "en")
    assert response.escalation_required is True
    assert response.intent == "fallback_escalation"

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



def test_telugu_and_hindi_faq_answers_are_translated():
    telugu = answer_for("How do I block a lost card?", "te")
    hindi = answer_for("How do I block a lost card?", "hi")

    assert "మీ కార్డ్" in telugu.answer
    assert "यदि आपका कार्ड" in hindi.answer
    assert telugu.intent == hindi.intent == "block_card"


def test_demo_case_can_be_tracked_without_exposing_description():
    created = client.post(
        "/api/complaints",
        json={"category": "service", "description": "I need help with branch service"},
    )
    assert created.status_code == 201
    case_id = created.json()["case_id"]

    tracked = client.get(f"/api/complaints/{case_id}")
    assert tracked.status_code == 200
    assert tracked.json()["case_id"] == case_id
    assert tracked.json()["status"] == "RECEIVED"
    assert "description" not in tracked.json()
    assert "demo" in tracked.json()["notice"].lower()


def test_unknown_demo_case_returns_404():
    response = client.get("/api/complaints/SB-NOTREAL")
    assert response.status_code == 404



def test_approved_knowledge_retrieval_finds_relevant_article():
    from app.main import retrieve_approved_guidance

    result = retrieve_approved_guidance("ATM cash not dispensed account debited")
    assert result is not None
    assert result["title"] == "ATM cash not dispensed"


def test_approved_knowledge_retrieval_returns_safe_source():
    response = answer_for("ATM cash was not dispensed but I was debited", "en")
    assert response.source == "approved_knowledge_base"
    assert response.intent == "approved_guidance_retrieval"


def test_approved_knowledge_retrieval_ignores_unrelated_question():
    from app.main import retrieve_approved_guidance

    assert retrieve_approved_guidance("tell me a joke about weather") is None

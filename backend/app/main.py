from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="SmartBank AI — Customer Response Agent",
    version="0.2.0",
    description="Safe demo banking-support API using synthetic data only.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

Language = Literal["en", "te", "hi"]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: Language = "en"


class ChatResponse(BaseModel):
    answer: str
    intent: str
    source: str
    escalation_required: bool = False


class ComplaintRequest(BaseModel):
    category: Literal["transaction", "card", "digital_banking", "service", "other"]
    description: str = Field(min_length=10, max_length=1500)


class ComplaintResponse(BaseModel):
    case_id: str
    status: str
    created_at: str
    message: str


FAQS = [
    {"id": "account_statement", "question": "How can I get my account statement?", "keywords": ["statement", "account statement", "passbook"], "answer": "You can usually download a statement from your bank's official mobile app or internet banking. Choose the account and date range, then use the statement/download option. Menu names vary by bank."},
    {"id": "card_pin_help", "question": "How can I reset my debit card PIN?", "keywords": ["reset pin", "debit card pin", "forgot pin", "pin reset"], "answer": "For your security, reset your debit-card PIN only through your bank's official app, website, ATM, or verified customer-care channel. Never share your PIN or OTP with anyone, including this assistant."},
    {"id": "failed_transaction", "question": "What should I do if a transaction failed?", "keywords": ["failed transaction", "transaction failed", "money deducted", "debited", "pending transaction"], "answer": "Check the transaction status in your bank's official app and save the reference number. Reversals can depend on the payment type and bank rules. If the amount was debited but the recipient was not credited, raise a complaint through the official channel and include the reference number. Do not share OTPs or full card details."},
    {"id": "block_card", "question": "How do I block a lost card?", "keywords": ["lost card", "block card", "stolen card", "card missing"], "answer": "If your card is lost or stolen, block it immediately using your bank's official app, internet banking, or verified customer-care number. Review recent transactions and report anything you do not recognize."},
    {"id": "update_contact", "question": "How can I update my mobile number?", "keywords": ["update mobile", "change phone number", "change mobile number", "update phone"], "answer": "Use your bank's official process to update your registered mobile number. Depending on the bank, identity verification at an ATM or branch may be required. Never share an OTP in chat."},
    {"id": "working_hours", "question": "How can I contact customer support?", "keywords": ["customer support", "customer care", "contact bank", "helpline", "speak to agent"], "answer": "Use the customer-care details published inside your bank's official app, on your bank card, or on its verified website. Avoid numbers shared in unsolicited messages or search advertisements."},
    {"id": "upi_safety", "question": "How do I stay safe with UPI?", "keywords": ["upi", "payment safety", "scan qr", "collect request", "upi fraud"], "answer": "Never enter a UPI PIN to receive money. Approve only requests you understand, verify the recipient before paying, and never share your PIN or OTP. If you suspect fraud, contact your bank immediately through an official channel."},
    {"id": "loan_status", "question": "How can I check my loan application?", "keywords": ["loan status", "loan application", "loan approval"], "answer": "Check your application in the bank's official app or website, or contact the loan team using verified contact details. This demo cannot access real loan applications."},
]

# Detect both explicit labels and likely secret values; never echo submitted text in the response.
SECRET_PATTERNS = [
    re.compile(r"\b(?:otp|one[- ]time password)\b\s*(?:is|:|=|-)?\s*\d{4,8}\b", re.I),
    re.compile(r"\b(?:pin|passcode|password|cvv|cvc)\b\s*(?:is|:|=|-)?\s*[a-z0-9@#$!_-]{3,}", re.I),
    re.compile(r"\b(?:my\s+)?(?:otp|pin|password|cvv|cvc)\s+(?:is\s+)?\S+", re.I),
    re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
    re.compile(r"\b(?:share|send|tell|give)\s+(?:me\s+)?(?:your\s+)?(?:otp|pin|password|cvv|cvc)\b", re.I),
]


def looks_sensitive(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def translate_static(answer: str, language: Language) -> str:
    if language == "te":
        return "గమనిక: ఇది డెమో సహాయకుడు.\n\n" + answer
    if language == "hi":
        return "ध्यान दें: यह एक डेमो सहायक है।\n\n" + answer
    return answer


def answer_for(message: str, language: Language) -> ChatResponse:
    normalized = re.sub(r"[^a-z0-9\s]", " ", message.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()

    if looks_sensitive(message):
        return ChatResponse(
            answer="For your safety, please do not share PINs, passwords, CVVs, OTPs, or full card numbers here. I will not repeat or process those details. If you exposed a real secret, contact your bank through its official channel and change or block the affected credential as appropriate.",
            intent="sensitive_data_guard",
            source="security_policy",
            escalation_required=True,
        )

    # Prefer the longest matching keyword so broad terms cannot shadow specific intents.
    matched = []
    for faq in FAQS:
        for keyword in faq["keywords"]:
            if re.search(r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])", normalized):
                matched.append((len(keyword), faq))
    if matched:
        faq = max(matched, key=lambda item: item[0])[1]
        return ChatResponse(
            answer=translate_static(faq["answer"], language),
            intent=faq["id"],
            source="approved_demo_faq",
        )

    if any(phrase in normalized for phrase in ("balance", "my account", "my transactions", "my money")):
        return ChatResponse(
            answer="I cannot access real customer accounts in this demo. Please sign in to your bank's official app or website to view private account information. If you need help with a demo transaction, use a synthetic reference such as DEMO-TXN-1001.",
            intent="private_account_data",
            source="security_policy",
            escalation_required=True,
        )

    return ChatResponse(
        answer="I couldn't confidently match that question to the approved demo help articles. For account-specific or urgent issues, contact your bank through its official app, verified website, or the number printed on your card. You can also create a demo support case below. Please do not share account credentials or OTPs.",
        intent="fallback_escalation",
        source="safe_fallback",
        escalation_required=True,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "UP", "service": "smartbank-ai-api", "mode": "demo"}


@app.get("/api/faqs")
def list_faqs() -> dict[str, list[dict[str, str]]]:
    return {"items": [{"id": item["id"], "question": item["question"]} for item in FAQS]}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    return answer_for(payload.message, payload.language)


DEMO_TRANSACTIONS = {
    "DEMO-TXN-1001": {"status": "SUCCESS", "amount": "₹250.00", "date": "2026-10-12"},
    "DEMO-TXN-1002": {"status": "PENDING", "amount": "₹499.00", "date": "2026-10-13"},
    "DEMO-TXN-1003": {"status": "FAILED", "amount": "₹120.00", "date": "2026-10-14"},
}


@app.get("/api/transactions/{reference}")
def transaction_status(reference: str) -> dict[str, str]:
    record = DEMO_TRANSACTIONS.get(reference.upper())
    if not record:
        raise HTTPException(status_code=404, detail="Unknown demo reference. Try DEMO-TXN-1001, DEMO-TXN-1002, or DEMO-TXN-1003.")
    return {"reference": reference.upper(), **record, "notice": "Synthetic demo data only; not linked to a real bank."}


# In-memory storage is intentionally demo-only; use a durable, access-controlled store in production.
COMPLAINTS: list[dict[str, str]] = []


@app.post("/api/complaints", response_model=ComplaintResponse, status_code=201)
def create_complaint(payload: ComplaintRequest) -> ComplaintResponse:
    if looks_sensitive(payload.description):
        raise HTTPException(
            status_code=400,
            detail="Please remove any PIN, password, OTP, CVV, or full card number before submitting a demo case.",
        )
    case_id = "SB-" + uuid.uuid4().hex[:8].upper()
    created_at = datetime.now(timezone.utc).isoformat()
    COMPLAINTS.append({
        "case_id": case_id,
        "category": payload.category,
        "description": payload.description,
        "created_at": created_at,
        "status": "RECEIVED",
    })
    return ComplaintResponse(
        case_id=case_id,
        status="RECEIVED",
        created_at=created_at,
        message="Demo case created. This reference is not submitted to a real bank.",
    )

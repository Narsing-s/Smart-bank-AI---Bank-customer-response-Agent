from __future__ import annotations

import re
import uuid
from pathlib import Path
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

FAQ_TRANSLATIONS: dict[str, dict[str, str]] = {
    "account_statement": {
        "te": "సాధారణంగా మీ బ్యాంక్ అధికారిక మొబైల్ యాప్ లేదా ఇంటర్నెట్ బ్యాంకింగ్‌లో స్టేట్‌మెంట్ డౌన్‌లోడ్ చేసుకోవచ్చు. ఖాతా, తేదీల పరిధిని ఎంచుకుని స్టేట్‌మెంట్/డౌన్‌లోడ్ ఎంపికను ఉపయోగించండి. మెనూ పేర్లు బ్యాంక్‌ను బట్టి మారవచ్చు.",
        "hi": "आमतौर पर आप अपने बैंक के आधिकारिक मोबाइल ऐप या इंटरनेट बैंकिंग से स्टेटमेंट डाउनलोड कर सकते हैं। खाता और तारीख की सीमा चुनकर स्टेटमेंट/डाउनलोड विकल्प का उपयोग करें। मेनू के नाम बैंक के अनुसार अलग हो सकते हैं।",
    },
    "card_pin_help": {
        "te": "మీ భద్రత కోసం, మీ డెబిట్ కార్డ్ PIN‌ను బ్యాంక్ అధికారిక యాప్, వెబ్‌సైట్, ATM లేదా ధృవీకరించిన కస్టమర్-కేర్ మార్గం ద్వారానే రీసెట్ చేయండి. ఈ సహాయకుడితో సహా ఎవరితోనూ మీ PIN లేదా OTP పంచుకోవద్దు.",
        "hi": "आपकी सुरक्षा के लिए, डेबिट कार्ड PIN केवल बैंक के आधिकारिक ऐप, वेबसाइट, ATM या सत्यापित ग्राहक सेवा के माध्यम से रीसेट करें। इस सहायक सहित किसी के साथ भी अपना PIN या OTP साझा न करें।",
    },
    "failed_transaction": {
        "te": "మీ బ్యాంక్ అధికారిక యాప్‌లో లావాదేవీ స్థితిని తనిఖీ చేసి రిఫరెన్స్ నంబర్‌ను భద్రపరచండి. రివర్సల్ సమయం చెల్లింపు విధానం మరియు బ్యాంక్ నియమాలపై ఆధారపడి ఉంటుంది. మొత్తం డెబిట్ అయి, గ్రహీతకు చేరకపోతే అధికారిక మార్గంలో ఫిర్యాదు చేయండి. OTPలు లేదా పూర్తి కార్డ్ వివరాలు పంచుకోవద్దు.",
        "hi": "अपने बैंक के आधिकारिक ऐप में लेन-देन की स्थिति जाँचें और संदर्भ संख्या सुरक्षित रखें। रिवर्सल का समय भुगतान प्रकार और बैंक के नियमों पर निर्भर करता है। राशि डेबिट हो गई हो लेकिन प्राप्तकर्ता को न मिली हो, तो आधिकारिक माध्यम से शिकायत करें। OTP या कार्ड की पूरी जानकारी साझा न करें।",
    },
    "block_card": {
        "te": "మీ కార్డ్ పోయినా లేదా దొంగిలించబడినా, బ్యాంక్ అధికారిక యాప్, ఇంటర్నెట్ బ్యాంకింగ్ లేదా ధృవీకరించిన కస్టమర్-కేర్ నంబర్ ద్వారా వెంటనే బ్లాక్ చేయండి. ఇటీవలి లావాదేవీలను పరిశీలించి, గుర్తించని లావాదేవీలను నివేదించండి.",
        "hi": "यदि आपका कार्ड खो गया है या चोरी हो गया है, तो बैंक के आधिकारिक ऐप, इंटरनेट बैंकिंग या सत्यापित ग्राहक सेवा नंबर से तुरंत ब्लॉक करें। हाल के लेन-देन देखें और किसी अनजान लेन-देन की सूचना दें।",
    },
    "update_contact": {
        "te": "మీ రిజిస్టర్డ్ మొబైల్ నంబర్‌ను మార్చడానికి మీ బ్యాంక్ అధికారిక ప్రక్రియను అనుసరించండి. బ్యాంక్‌ను బట్టి ATM లేదా బ్రాంచ్‌లో గుర్తింపు ధృవీకరణ అవసరం కావచ్చు. చాట్‌లో OTP పంచుకోవద్దు.",
        "hi": "रजिस्टर्ड मोबाइल नंबर बदलने के लिए बैंक की आधिकारिक प्रक्रिया अपनाएँ। बैंक के अनुसार ATM या शाखा में पहचान सत्यापन की आवश्यकता हो सकती है। चैट में OTP साझा न करें।",
    },
    "working_hours": {
        "te": "మీ బ్యాంక్ అధికారిక యాప్‌లో, కార్డ్‌పై లేదా ధృవీకరించిన వెబ్‌సైట్‌లో ఉన్న కస్టమర్-కేర్ వివరాలను ఉపయోగించండి. అనుకోని సందేశాలు లేదా శోధన ప్రకటనల్లో కనిపించే నంబర్లను నమ్మవద్దు.",
        "hi": "अपने बैंक के आधिकारिक ऐप, कार्ड या सत्यापित वेबसाइट पर दिए गए ग्राहक सेवा विवरण का उपयोग करें। अनचाहे संदेशों या खोज विज्ञापनों में दिए गए नंबरों से सावधान रहें।",
    },
    "upi_safety": {
        "te": "డబ్బు స్వీకరించడానికి ఎప్పుడూ UPI PIN నమోదు చేయవద్దు. మీకు అర్థమైన అభ్యర్థనలనే ఆమోదించండి, చెల్లించే ముందు గ్రహీతను ధృవీకరించండి, PIN లేదా OTP ఎవరితోనూ పంచుకోవద్దు. మోసం అనుమానం ఉంటే వెంటనే బ్యాంక్ అధికారిక మార్గంలో సంప్రదించండి.",
        "hi": "पैसे प्राप्त करने के लिए कभी भी UPI PIN न डालें। केवल उन्हीं अनुरोधों को मंज़ूरी दें जिन्हें आप समझते हैं, भुगतान से पहले प्राप्तकर्ता की पुष्टि करें और PIN या OTP साझा न करें। धोखाधड़ी का संदेह हो तो तुरंत बैंक के आधिकारिक माध्यम से संपर्क करें।",
    },
    "loan_status": {
        "te": "మీ దరఖాస్తు స్థితిని బ్యాంక్ అధికారిక యాప్ లేదా వెబ్‌సైట్‌లో తనిఖీ చేయండి లేదా ధృవీకరించిన సంప్రదింపు వివరాల ద్వారా లోన్ బృందాన్ని సంప్రదించండి. ఈ డెమో నిజమైన లోన్ దరఖాస్తులను చూడలేడు.",
        "hi": "अपने आवेदन की स्थिति बैंक के आधिकारिक ऐप या वेबसाइट पर देखें, या सत्यापित संपर्क विवरण से ऋण टीम से संपर्क करें। यह डेमो वास्तविक ऋण आवेदनों तक पहुँच नहीं सकता।",
    },
}


def translate_faq(faq_id: str, answer: str, language: Language) -> str:
    if language == "en":
        return answer
    translated = FAQ_TRANSLATIONS.get(faq_id, {}).get(language)
    return translated or translate_static(answer, language)



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



KNOWLEDGE_FILE = Path(__file__).resolve().parents[1] / "knowledge_base" / "approved_banking_guidance.md"
RETRIEVAL_STOP_WORDS = {
    "a", "an", "and", "are", "can", "do", "for", "how", "i", "in", "is",
    "it", "me", "my", "of", "on", "or", "the", "to", "what", "when",
    "where", "with", "you", "your", "please", "help", "about",
}


def _knowledge_chunks() -> list[dict[str, str]]:
    """Load only curated local guidance; no user uploads or external content are indexed."""
    try:
        content = KNOWLEDGE_FILE.read_text(encoding="utf-8")
    except OSError:
        return []
    chunks: list[dict[str, str]] = []
    heading = ""
    paragraphs: list[str] = []
    for line in content.splitlines():
        if line.startswith("## "):
            if heading and paragraphs:
                chunks.append({"title": heading, "text": " ".join(paragraphs).strip()})
            heading = line[3:].strip()
            paragraphs = []
        elif line.strip() and not line.startswith("# "):
            paragraphs.append(line.strip())
    if heading and paragraphs:
        chunks.append({"title": heading, "text": " ".join(paragraphs).strip()})
    return chunks


def retrieve_approved_guidance(message: str) -> dict[str, str] | None:
    """Small local retrieval step: rank approved chunks by meaningful token overlap."""
    tokens = {
        token for token in re.findall(r"[a-z0-9]+", message.lower())
        if len(token) > 2 and token not in RETRIEVAL_STOP_WORDS
    }
    if not tokens:
        return None
    ranked: list[tuple[float, dict[str, str]]] = []
    for chunk in _knowledge_chunks():
        text_tokens = set(re.findall(r"[a-z0-9]+", (chunk["title"] + " " + chunk["text"]).lower()))
        overlap = tokens & text_tokens
        # A modest overlap threshold avoids returning unrelated generic documents.
        score = len(overlap) / max(1, len(tokens))
        if len(overlap) >= 2 and score >= 0.25:
            ranked.append((score, chunk))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], len(item[1]["title"])), reverse=True)
    best_score, best = ranked[0]
    if len(ranked) > 1 and best_score - ranked[1][0] < 0.08:
        # Ambiguous retrieval should safely escalate rather than guess.
        return None
    return best



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
            answer=translate_faq(faq["id"], faq["answer"], language),
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

    retrieved = retrieve_approved_guidance(message)
    if retrieved:
        answer = f"{retrieved['title']}\\n\\n{retrieved['text']}\\n\\nThis guidance comes from the approved demo knowledge base, not your bank's account systems."
        return ChatResponse(
            answer=translate_static(answer, language),
            intent="approved_guidance_retrieval",
            source="approved_knowledge_base",
            escalation_required=False,
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


@app.get("/api/complaints/{case_id}")
def get_complaint_status(case_id: str) -> dict[str, str]:
    """Look up a demo case by its reference; never return the submitted description."""
    normalized_id = case_id.strip().upper()
    record = next((item for item in COMPLAINTS if item["case_id"] == normalized_id), None)
    if record is None:
        raise HTTPException(status_code=404, detail="Demo case reference not found.")
    return {
        "case_id": record["case_id"],
        "status": record["status"],
        "created_at": record["created_at"],
        "notice": "Demo case only; this reference is not linked to a real bank.",
    }


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

# SmartBank AI — Banking Customer Response Agent

A mobile-friendly banking support assistant with a modern chat UI, a safe demo API, a starter RAG knowledge base, and MuleSoft API-led integration contracts.

> **Demo only:** This repository uses synthetic demo data. It is not connected to a real bank or live accounts. Never enter a real PIN, password, CVV, OTP, card number, or other secret.

## What's included

- Responsive customer-support chat UI (Next.js + TypeScript).
- FastAPI backend with deterministic FAQ answers, local retrieval over curated approved guidance, complaint creation/tracking, health checks, and sample transaction-status lookup.
- English, Telugu, and Hindi UI language selector, with translated answers for the approved demo FAQ set.
- Safe escalation guidance when the assistant cannot answer.
- RAML contracts for Experience, Process, and System APIs, plus MuleSoft implementation guidance.
- GitHub Actions checks for the backend.
- No API key is required for the demo: FAQ responses and retrieval use local, curated files; no external LLM or vector database is called. Retrieval uses token overlap and deliberately escalates when it cannot find a clear match.

## Architecture

```text
Customer (mobile/web)
       |
       v
Next.js customer experience
       |
       v
FastAPI assistant (local/demo mode)
       |
       +---- FAQ knowledge base (approved sample content)
       +---- synthetic transaction lookup
       +---- complaint workflow (demo memory store)
       |
       v
MuleSoft API-led connectivity (contracts included)
  Experience API -> Process API -> System API -> bank systems
```

The web demo can run without MuleSoft. The included RAML files define a clean integration boundary for a future Anypoint implementation. Do not connect real customer data until identity, authorization, audit logging, encryption, rate limits, and bank-approved policies are implemented.

## Run locally

### Backend

Python 3.11+ recommended.

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` for the interactive API docs and `http://localhost:8000/health` for health status.

### Frontend

Node.js 20+ recommended.

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in `.env.local`.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/api/faqs` | Approved demo FAQ entries |
| POST | `/api/chat` | FAQ response and safe routing |
| GET | `/api/transactions/{reference}` | Synthetic demo transaction status |
| POST | `/api/complaints` | Create a demo support case |

Example chat request:

```json
{ "message": "How can I reset my debit card PIN?", "language": "en" }
```

Example response:

```json
{
  "answer": "For your security, use your bank's official app or website...",
  "intent": "card_pin_help",
  "source": "approved_demo_faq",
  "escalation_required": false
}
```

## Deploy

- **Frontend:** import the repository into Vercel and set the project root to `frontend`. Add `NEXT_PUBLIC_API_BASE_URL` pointing to your deployed backend.
- **Backend:** deploy the `backend` directory to a Python ASGI host that supports FastAPI. Configure CORS to allow only your deployed frontend origin.
- **MuleSoft:** import the RAML contracts under `mulesoft/raml` into Anypoint Design Center/API Manager, then implement and secure the APIs in your organization.

Hosting providers and free tiers can change; check current limits before deployment. Never commit credentials or production customer information.

## Security boundaries

- The demo never asks for authentication secrets and explicitly refuses to handle PINs, OTPs, CVVs, or passwords.
- Transaction IDs are synthetic demo references, not proof of identity.
- Demo complaint records are held in process memory and are lost on restart; this is not production storage. The UI can track a newly created case, but the reference is not connected to a real bank. The case-tracking endpoint returns only the reference, status, timestamp, and demo notice; it intentionally does not return the submitted description.
- Before production: add bank SSO/OIDC, customer-scoped authorization, persistent encrypted storage, audit trails, PII redaction, abuse protection, approved knowledge review, and human escalation SLAs.
- Do not use an LLM to invent account balances, policy details, transaction outcomes, or financial advice. Ground responses in approved sources and escalate uncertainty.

## Project layout

```text
backend/app/       FastAPI routes and demo knowledge base
frontend/          Next.js app
mulesoft/raml/     API-led connectivity contracts
.github/workflows/ backend CI
```

## License

MIT — see `LICENSE`.

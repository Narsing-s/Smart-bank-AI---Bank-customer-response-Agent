# MuleSoft API-led integration plan

The demo runs independently, but these RAML contracts establish the integration path for an Anypoint implementation.

## API layers

1. **Experience API** — channel-specific request validation, language, safe response shape, and correlation ID.
2. **Process API** — intent routing, approved knowledge retrieval, complaint workflow, transaction inquiry orchestration, idempotency, and escalation.
3. **System API** — adapters for core banking, case management, and transaction systems; expose only minimal authorized fields.

## Suggested Mule flow outline

- HTTP Listener → APIKit Router → validation → correlation ID → business routing.
- FAQ: retrieve approved article metadata/content from the governed knowledge store; return source identifiers with the answer.
- Transaction inquiry: authenticate caller, resolve customer identity from trusted claims, verify transaction ownership, then call the System API. Never trust a customer ID supplied only in the request body.
- Complaint: validate category/description, require idempotency key, write to case system, and return a case reference.
- Error handling: map validation to 400, authentication to 401, authorization to 403, rate limits to 429, unavailable dependencies to 503, and unexpected failures to a sanitized 500 response.
- Observability: structured logs with correlation ID; redact PII and never log tokens, credentials, OTPs, PINs, CVVs, or full payment credentials.

## Before connecting production systems

Configure API Manager policies, OAuth/OIDC, client and customer authorization, TLS, secrets management, rate limits, audit logging, approved knowledge governance, MUnit tests, and operational dashboards. RAML examples use reserved example domains and are contracts only—not deployable production endpoints.

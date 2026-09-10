# Security Guide

**Audience:** Developers and operators.

## Authentication and Authorization

`backend/api/middleware.py` implements:

- `LoggingMiddleware`
- `APIKeyMiddleware`
- `RateLimitMiddleware`

However, `backend/main.py` currently registers only FastAPI CORS middleware and route modules. The custom middleware is not active unless mounted in the app.

Current implication: by default, API routes should be treated as unauthenticated in the running application.

## API Key Support

The frontend can send:

```http
X-API-Key: <value>
```

when `VITE_API_KEY` is set.

The backend middleware, if mounted, checks this header against `PROCUREAI_API_KEY` when `REQUIRE_API_KEY` is true.

## CORS

`backend/core/config.py` parses `CORS_ALLOW_ORIGINS`, but `backend/main.py` currently uses:

```python
allow_origins=["*"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

Restrict origins before exposing the backend outside local development.

## File Safety

Audit execution validates file paths with `validate_uploaded_file_path`. Accepted files must:

- Exist.
- Be PDF files.
- Be under the configured upload directory or `data/synthetic`.

Uploads are sanitized and stored under `UPLOAD_DIR`.

## LLM Security & Guardrails

ProcureAI implements an enterprise defense-in-depth security model to safeguard against adversarial inputs, data leakage, and unauthorized financial actions. For a full technical deep-dive, see the [Guardrails Guide](GUARDRAILS.md).

### 1. Prompt Injection Defense
- **Threat:** Malicious instructions embedded in uploaded PDFs (e.g. contracts or vendor invoices) attempting to trick the LLM into declaring an invoice compliant or leaking system prompts.
- **Mitigation:**
  - `backend/core/input_sanitizer.py` scans raw extracted text against 9 regex injection heuristics (`ignore previous instructions`, `role spoofing`, `developer mode`, etc.).
  - Adversarial payloads are defanged to `[DEFANGED_PROMPT_INJECTION]`.
  - All LLM system prompts prepend `INSTRUCTION_DEFENSE_PREAMBLE`, treating document contents strictly as untrusted data inside `<untrusted_document_content>` tags.

### 2. Output Filtering & PII Redaction
- **Threat:** Unintended exposure of personal identification numbers, financial accounts, or injection of malicious markup in generated reports or supplier dispute letters.
- **Mitigation:**
  - `backend/core/output_filter.py` automatically scrubs Indian PAN cards, Aadhaar numbers, US SSNs, credit card numbers, email addresses, and phone numbers.
  - Strips HTML `<script>`, `<iframe>`, and event handler tags to protect downstream web dashboards from Stored XSS.
  - Enforces professional institutional tone across generated dispute correspondence.

### 3. Resource Exhaustion & Denial-of-Wallet Defense
- **Threat:** Pathological or adversarial documents triggering excessive LLM calls, causing unbounded API billing or thread starvation.
- **Mitigation:**
  - `backend/core/token_budget.py` enforces a hard limit of `MAX_TOKENS_PER_AUDIT` (default: 500,000 tokens). Exceeding this ceiling halts the pipeline safely with `TokenBudgetExceeded`.
  - `backend/core/llm_rate_limiter.py` enforces a sliding 60-second window across RPM and TPM limits to prevent provider rate-limit exhaustion (`429 Too Many Requests`).

### 4. Human-in-the-Loop Release Gate
- **Threat:** Automated release of erroneous multi-million rupee dispute actions or premature invoice approvals.
- **Mitigation:**
  - Any audit resulting in `CRITICAL` severity findings is automatically placed in an immutable hold state: `status="PENDING_REVIEW"`.
  - Audits in `PENDING_REVIEW` cannot be closed until a designated procurement auditor reviews the report and explicitly invokes the approval flow (`POST /api/audit/{audit_id}/approve` or via the web UI banner).

## Secrets

Do not commit:

- Gemini API keys / Groq API keys / Vertex AI credentials.
- Google service account JSON.
- SynaptAI / Context Substrate session and agent tokens.
- SMTP credentials.
- Slack webhook URLs.
- Production database URLs.

Use local `.env` files or deployment secret managers.

## Operational Recommendations

- Mount the custom security middleware or use a production identity layer.
- Restrict CORS origins.
- Serve over HTTPS.
- Put the backend behind a reverse proxy or managed gateway.
- Move secrets to a secure store (e.g. HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager).
- Add audit logging around settings changes before production use.
- Review generated dispute letters before sending to suppliers.


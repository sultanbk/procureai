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

## Secrets

Do not commit:

- Gemini API keys.
- Google service account JSON.
- SMTP credentials.
- Slack webhook URLs.
- Production database URLs.

Use local `.env` files or deployment secret managers.

## Operational Recommendations

- Mount the custom security middleware or use a production identity layer.
- Restrict CORS.
- Serve over HTTPS.
- Put the backend behind a reverse proxy or managed gateway.
- Move secrets to a secure store.
- Add audit logging around settings changes before production use.
- Review generated dispute letters before sending to suppliers.

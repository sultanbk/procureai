# Configuration Guide

**Audience:** Developers and operators.

Configuration is loaded by `backend/core/config.py`. It reads `.env` from the repository root first and `backend/.env` second, with later values overriding earlier values.

## Backend Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./procureai.db` | SQLAlchemy database URL; SQLite URLs are adapted for `aiosqlite` |
| `UPLOAD_DIR` | `data/uploads` | Stored upload directory |
| `MAX_UPLOAD_SIZE_MB` | `20` | Maximum PDF upload size |
| `MINIMUM_MATERIAL_THRESHOLD` | `100.0` | Minimum absolute discrepancy amount to report |
| `COMPLIANCE_CONFIDENCE_THRESHOLD` | `0.75` | Compliance confidence threshold |
| `LLM_RETRY_ATTEMPTS` | `3` | LLM retry count |
| `LLM_RETRY_DELAY_SECONDS` | `2.0` | Delay between LLM retries |
| `LLM_CALL_TIMEOUT_SECONDS` | `120` | Async LLM call timeout |
| `PIPELINE_MAX_LLM_CALLS` | `100` | Configured maximum call count; verify enforcement before relying on it operationally |
| `PIPELINE_TIMEOUT_SECONDS` | `600` | Configured pipeline timeout; verify enforcement before relying on it operationally |
| `SELF_CONSISTENCY_PASSES` | `3` | Contract/invoice extraction self-consistency pass count |
| `SELF_CONSISTENCY_TEMPERATURES` | `0.0,0.1,0.2` | Temperatures parsed into a float list |
| `PRICE_DRIFT_THRESHOLD_PCT` | `5.0` | Cross-invoice drift threshold percentage |
| `PRICE_DRIFT_MIN_DELTA` | `10.00` | Minimum drift amount |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `CONSOLE` | Logging format |
| `FRONTEND_BASE_URL` | `http://localhost:5173` | Used in notifications |
| `CORS_ALLOW_ORIGINS` | localhost frontend origins | Parsed config value; note `backend/main.py` currently uses `allow_origins=["*"]` |
| `PROCUREAI_API_KEY` | empty | API key value for middleware if mounted |
| `REQUIRE_API_KEY` | true when key exists, otherwise false | API-key requirement flag for middleware if mounted |
| `RATE_LIMIT_REQUESTS` | `120` | Rate-limit request count for middleware if mounted |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate-limit window for middleware if mounted |
| `MOCK_LLM` | unset | Requests mock LLM responses |
| `ALLOW_MOCK_LLM` | unset | Required with `MOCK_LLM=true` to actually enable mock responses |
| `GEMINI_API_KEY` | unset | Gemini Developer API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `GOOGLE_CLOUD_PROJECT` | `procureai` in `llm_client.py` fallback | Vertex AI project |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | Vertex AI region |

## Frontend Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_URL` | `http://127.0.0.1:8000` fallback in code | Backend origin |
| `VITE_API_KEY` | unset | Optional key sent as `X-API-Key` |

## Local Mock Configuration

```ini
MOCK_LLM=true
ALLOW_MOCK_LLM=true
DATABASE_URL=sqlite:///./data/procureai.db
UPLOAD_DIR=data/uploads
VITE_API_URL=http://localhost:8000
```

Both `MOCK_LLM` and `ALLOW_MOCK_LLM` must be truthy for the mock path in `backend/core/llm_client.py`.

## Live LLM Configuration

Gemini Developer API:

```ini
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-2.5-flash
```

Vertex AI:

```ini
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash
```

Assumption: Vertex AI authentication is provided through the Google SDK environment, such as `GOOGLE_APPLICATION_CREDENTIALS` or application default credentials. The code initializes `vertexai.init(project=..., location=...)` but does not manage credential files itself.

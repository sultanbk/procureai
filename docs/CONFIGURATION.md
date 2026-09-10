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
| `MAX_TOKENS_PER_AUDIT` | `500000` | Maximum cumulative LLM tokens per audit pipeline run before safe halt (`TokenBudgetExceeded`) |
| `LLM_RPM_LIMIT` | `60` | Maximum LLM requests per minute (sliding 60-second window across agents) |
| `LLM_TPM_LIMIT` | `100000` | Maximum LLM tokens per minute (sliding 60-second window across agents) |
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
| `LLM_PROVIDER` | unset | Active LLM provider selection: `omniroute`, `groq`, or `gemini` |
| `GROQ_API_KEY` | unset | Groq or OpenAI-compatible API key / auth token |
| `GROQ_BASE_URL` | unset | Optional custom base URL for OpenAI-compatible proxies (e.g. `http://localhost:20128/v1` for OmniRoute, vLLM, Ollama) |
| `GROQ_MODEL` | `llama-3.1-70b-versatile` | Model name for Groq / OpenAI-compatible provider |
| `GEMINI_API_KEY` | unset | Gemini Developer API key |
| `GEMINI_MODEL` | `gemini-3.7-flash` | Gemini model name |
| `GOOGLE_CLOUD_PROJECT` | `procureai` in `llm_client.py` fallback | Vertex AI project |
| `GOOGLE_CLOUD_LOCATION` | `global` (or `us-central1`) | Vertex AI region / location |
| `CONTEXT_SUBSTRATE_ENABLED` | `true` | Enables/disables Context Substrate epistemic brain |
| `CONTEXT_SUBSTRATE_MODE` | `auto` | Substrate operating mode: `auto` (preferred: tries live, falls back to embedded), `live`, or `mock` |
| `CONTEXT_SUBSTRATE_URL` | `https://beta.synapt.ai` | SynaptAI TriStore REST API base URL |
| `CONTEXT_SUBSTRATE_PROVIDER_ID` | `procureai` | Active Context Provider knowledge sandbox namespace |
| `CONTEXT_SUBSTRATE_API_KEY` | unset | User/Agent Bearer authentication token for TriStore REST queries |
| `SYNAPT_MCP_URL` | `https://beta.synapt.ai/api/mcp` | Base URL for Model Context Protocol (MCP) streamable HTTP service |
| `SYNAPT_PROVIDER_ID` | `procureai` | Provider ID namespace for Trident MCP queries |
| `SYNAPT_AGENT_CLIENT_ID` | unset | Registered Agent Client ID for MCP authentication |
| `SYNAPT_AGENT_CLIENT_SECRET` | unset | Optional client secret for automated token exchange |
| `SYNAPT_AGENT_TOKEN` | unset | Pre-generated static Bearer token for Trident MCP S2S client |
| `SYNAPT_VERIFY_SSL` | `false` | When false, disables strict TLS inspection on internal domains |

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

### 1. OmniRoute / Local OpenAI Gateway

```ini
LLM_PROVIDER=omniroute
GROQ_BASE_URL=http://localhost:20128/v1
GROQ_API_KEY=your-omniroute-token
GROQ_MODEL=oc/nemotron-3-ultra-free
```

### 2. Groq Cloud (Fast Free Cloud Tier)

```ini
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.1-70b-versatile
```

### 3. Google AI Studio (Gemini Developer API)

```ini
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.7-flash
```

### 4. Google Cloud Vertex AI

```ini
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-3.7-flash
```

Assumption: Vertex AI authentication is provided through the Google SDK environment, such as `GOOGLE_APPLICATION_CREDENTIALS` or application default credentials. The code initializes `vertexai.init(project=..., location=...)` but does not manage credential files itself.

## Context Substrate & Trident MCP Configuration

Context Substrate connects ProcureAI to Prodapt's governed 4-store knowledge brain (Neo4j Concept Graph, Milvus KS, Milvus PS, and Milvus GN).

### 1. Recommended Auto-Fallback Mode (Zero-Fail Invariant)

In `auto` mode, the client attempts to connect to the live TriStore at `beta.synapt.ai`. If remote credentials expire or the network is unavailable, it seamlessly falls back to the embedded 4-store engine:

```ini
# =====================================================================
# SynaptAI Context Substrate (Trident MCP & 4-Store TriStore)
# =====================================================================
CONTEXT_SUBSTRATE_ENABLED=true
CONTEXT_SUBSTRATE_MODE=auto
CONTEXT_SUBSTRATE_URL=https://beta.synapt.ai
CONTEXT_SUBSTRATE_PROVIDER_ID=procureai
CONTEXT_SUBSTRATE_API_KEY=your-user-session-or-agent-token

# Trident MCP Settings (Official Prodapt IPL SDK)
SYNAPT_MCP_URL=https://beta.synapt.ai/api/mcp
SYNAPT_PROVIDER_ID=procureai
SYNAPT_AGENT_CLIENT_ID=your-registered-client-id
SYNAPT_AGENT_TOKEN=your-user-session-or-agent-token
SYNAPT_VERIFY_SSL=false
```

### 2. Strict Live Mode

In `live` mode, all queries and status probes strictly require valid authorization headers from the live SynaptAI service:

```ini
CONTEXT_SUBSTRATE_ENABLED=true
CONTEXT_SUBSTRATE_MODE=live
CONTEXT_SUBSTRATE_URL=https://beta.synapt.ai
CONTEXT_SUBSTRATE_PROVIDER_ID=procureai
CONTEXT_SUBSTRATE_API_KEY=your-active-jwt-token
```

### 3. Standalone Embedded / Mock Mode

Runs completely locally with zero external network dependencies, serving the verified benchmark dataset (Apex Telecom MSA, Amendment 1, SLA credits, and recovery DAG):

```ini
CONTEXT_SUBSTRATE_ENABLED=true
CONTEXT_SUBSTRATE_MODE=mock
```

## Guardrails & Resource Safety Configuration

ProcureAI provides fine-grained controls over LLM rate limits, token cost caps, and confidence gating. Detailed architectural mechanisms are documented in [docs/GUARDRAILS.md](GUARDRAILS.md).

```ini
# =====================================================================
# Guardrails, Safety Limits & Rate Governance
# =====================================================================

# Maximum cumulative LLM tokens per single audit run (default: 500,000)
# A warning is logged at 80% (400,000 tokens). If exceeded, raises TokenBudgetExceeded.
MAX_TOKENS_PER_AUDIT=500000

# In-memory sliding 60-second window provider rate limits
# Throttles concurrent agent calls before hitting provider HTTP 429 errors
LLM_RPM_LIMIT=60
LLM_TPM_LIMIT=100000

# Minimum confidence required for extracted pricing rules before tagging for human review
COMPLIANCE_CONFIDENCE_THRESHOLD=0.70

# Minimum rupee discrepancy required to record a finding (filters out rounding noise)
MINIMUM_MATERIAL_THRESHOLD=100.0
```


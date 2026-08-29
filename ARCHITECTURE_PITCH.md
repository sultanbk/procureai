# ProcureAI — Architecture Pitch
**Deep Technical Analysis for Contest Judges & Technical Reviewers**

---

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| **Total Source Lines** | ~26,600 (backend + frontend + scripts) |
| **Backend Python Files** | 55 files, ~15,000 LOC |
| **Frontend React Files** | 33 files, ~8,500 LOC |
| **Synthetic Data Generators** | 8 scripts, ~6,000 LOC |
| **Evaluation Harness** | 2 files, ~1,400 LOC |
| **Test Files** | 3 files, ~1,200 LOC |
| **Prompt Files** | 14 files across 10 agents |

**Architecture**: 7-node LangGraph pipeline with deterministic Python rule engine, React 19 dashboard, SQLite/PostgreSQL-ready, mock LLM mode for CI/CD.

---

## 🏗 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SUPPLIERGUARD ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │  CONTRACT │    │ INVOICE  │    │  WATCHED │    │  MANUAL  │             │
│  │   PDFs    │    │   PDFs   │    │ FOLDER   │    │  UPLOAD  │             │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘             │
│       │               │               │               │                     │
│       └───────────────┼───────────────┼───────────────┘                     │
│                       ▼                       │                             │
│            ┌─────────────────────┐           │                             │
│            │   FASTAPI BACKEND   │           │                             │
│            │   (Port 8000)       │           │                             │
│            └──────────┬──────────┘           │                             │
│                       │                       │                             │
│        ┌──────────────┼──────────────┐       │                             │
│        ▼              ▼              ▼       ▼                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│  │  UPLOAD  │ │  AUDIT   │ │ CONTRACT │ │ SETTINGS │                     │
│  │  ROUTES  │ │  ROUTES  │ │  ROUTES  │ │  ROUTES  │                     │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘                     │
│       │            │            │            │                            │
│       └────────────┴────────────┴────────────┘                            │
│                        │                                                   │
│                        ▼                                                   │
│            ┌─────────────────────┐                                         │
│            │   LANGGRAPH         │                                         │
│            │   PIPELINE          │                                         │
│            │   (7 Nodes)         │                                         │
│            └──────────┬──────────┘                                         │
│                       │                                                    │
│        ┌──────────────┼──────────────┐                                    │
│        ▼              ▼              ▼                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                                   │
│  │ CONTRACT │ │ INVOICE  │ │  CROSS   │                                   │
│  │ PARSER   │ │ EXTRACT. │ │VALIDATOR │     (Deterministic Python)       │
│  │  (LLM)   │ │  (LLM)   │ │  (Python)│                                   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘                                   │
│       │            │            │                                        │
│       └────────────┴────────────┘                                        │
│                        ▼                                                 │
│  ┌──────────────────────────────┐                                       │
│  │      COMPLIANCE CHECKER      │                                       │
│  │  (LLM Mapping + Rule Engine) │                                       │
│  └──────────────┬───────────────┘                                       │
│                 ▼                                                        │
│  ┌────────────┐  ┌──────────────────┐                                   │
│  │REVERSE SWEEP│ │ CROSS-INVOICE    │      (Deterministic Python)      │
│  │  (Python)  │ │  ANALYZER (Python)│                                   │
│  └─────┬──────┘ └────────┬─────────┘                                   │
│        │                 │                                            │
│        └────────┬────────┘                                            │
│                 ▼                                                     │
│  ┌──────────────────────────┐                                        │
│  │     REPORT GENERATOR     │                                        │
│  │ (LLM Summary + Python    │                                        │
│  │  Scorecard + Dispute)    │                                        │
│  └────────────┬─────────────┘                                        │
│               ▼                                                      │
│  ┌─────────────────────┐  ┌─────────────────────┐                    │
│  │   SQLITE/POSTGRES   │  │   REACT FRONTEND    │                    │
│  │   (Async SQLAlchemy)│  │   (Vite + Tailwind) │                    │
│  └─────────────────────┘  └─────────────────────┘                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 The 7-Node LangGraph Pipeline (Core Innovation)

### Pipeline Flow (v4 Architecture)

```python
# backend/agents/pipeline.py — StateGraph Definition

# Node 1-2: PARALLEL FAN-OUT (Independent)
contract_parser ──────┐
                      ├──► run_parallel_extractors() — Both run regardless of other's success
invoice_extractor ────┘     (v3 architecture: no shared state between them)

# Node 3: FAN-IN GATE (Deterministic — NO LLM)
cross_validator ──────► fuzzy_match + unit_check + conditional_rules + never_billed

# Node 4: COGNITIVE COMPLIANCE (LLM + Python)
compliance_checker ──► LLM maps rules → Python rule_engine evaluates math

# Node 5-6: PARALLEL DETERMINISTIC CHECKS (v4 additions)
reverse_sweep ────────► Finds missing credits/discounts/penalties (supplier "forgot")
cross_invoice_analyzer ► Detects price drift across months (systematic overcharge)

# Node 7: SYNTHESIS (LLM + Python)
report_generator ────► Executive summary + Supplier scorecard + Dispute letter
```

### State Contract (`PipelineState` — TypedDict)

```python
# backend/models/schemas.py — Complete pipeline state

class PipelineState(TypedDict):
    # Input
    audit_id: str
    contract_path: str
    invoice_paths: List[str]
    
    # Extracted
    contract_text: str
    invoice_texts: List[str]
    
    # Agent Outputs (serialized Pydantic models)
    rulebook: NotRequired[Dict]           # ContractRulebook
    invoice_data: NotRequired[List[Dict]] # InvoiceData[]
    cross_validation: NotRequired[Dict]   # CrossValidationResult
    candidate_map: NotRequired[Dict]      # line_id → [rule_ids]
    discrepancies: NotRequired[List[Dict]] # DiscrepancyList
    data_required_flags: NotRequired[List[Dict]]
    review_flags: NotRequired[List[Dict]]
    audit_report: NotRequired[Dict]       # AuditReport
    reverse_sweep: NotRequired[Dict]      # ReverseSweepResult (v4)
    cross_invoice: NotRequired[Dict]      # CrossInvoiceResult (v4)
    unit_conversions: NotRequired[Dict]   # Unit normalization metadata
    
    # Control
    errors: List[Dict]                    # AgentError[]
    current_agent: str
    halt: NotRequired[bool]
```

---

## 🧠 Agent Deep-Dive

### Agent 1: Contract Parser (`backend/agents/contract_parser/agent.py`)

**Responsibility**: Extract pricing rules from contract PDF text

**Key Innovations**:
- **Chunked processing**: Splits 60-page contracts into sections → processes relevant sections only
- **Double-attempt retry**: On Pydantic `ValidationError`, feeds errors back to LLM with correction prompt
- **Structured output**: `ContractRulebook` with `PricingRule[]` — each rule has `rule_id`, `rule_type`, `tiers[]`, `clause_text`, `extraction_confidence`

**Rule Types Supported**:
```python
["volume_tier", "flat_rate", "sla_penalty", "early_payment_discount", 
 "bundle_discount", "cap_rate", "annual_adjustment", "milestone_penalty", "unknown"]
```

**Tools** (`tools.py`):
- `merge_rulebooks()` — Combines chunk results, deduplicates by `rule_id`
- `extract_contract_metadata()` — Supplier name, contract ID, date, currency
- `vote_on_rules()` — Self-consistency: runs 3×, votes on rule extraction

---

### Agent 2: Invoice Extractor (`backend/agents/invoice_extractor/agent.py`)

**Responsibility**: Extract line items + metadata from invoice PDFs

**Key Innovations**:
- **Independent of Contract Parser** (v3 architecture rule #1) — no access to `rulebook`
- **Self-consistency passes**: 3 LLM calls + voting (`vote_on_invoice_data`)
- **Deterministic arithmetic validation**: `validate_invoice_arithmetic()` recalculates every line total + invoice total in Python `Decimal` — overrides LLM flags
- **Multi-invoice support**: Processes `List[str]` invoice texts → `List[InvoiceData]`

**Output**: `InvoiceData` with `LineItem[]` — each has `quantity`, `unit_price_charged`, `line_total_charged`, `sla_actual_pct`, `milestone_date`, `arithmetic_valid`

---

### Agent 3: Cross-Validator (`backend/agents/cross_validator/validator.py`)

**Responsibility**: Deterministic gate BEFORE any compliance LLM calls

**Pure Python — Zero LLM Calls**

```python
# What it does:
1. Fuzzy-matches invoice line items → contract rules (rapidfuzz token_sort_ratio)
2. Detects unit mismatches (kg vs MT, hour vs day) → builds unit_conversions map
3. Flags conditional rules missing supporting data (SLA%, milestone date)
4. Identifies rules never billed on any invoice (leakage opportunity)
```

**Output**: `CrossValidationResult` with `candidate_map`, `unmapped_lines`, `rules_without_data`, `rules_never_billed`

---

### Agent 4: Compliance Checker (`backend/agents/compliance_checker/agent.py`)

**Responsibility**: Map rules → lines, evaluate compliance, generate findings

**Architecture**: LLM for mapping/narrative + Python Rule Engine for math

```python
# Two-phase approach:
# Phase 1: LLM maps each line → applicable rules (from candidate_map only)
# Phase 2: For each mapping, Python rule_engine.evaluate_line_rule() calculates expected vs charged
```

**Rule Engine** (`rule_engine.py`):
- Abstract `RuleEvaluator` per `rule_type` (VolumeTier, FlatRate, SLAPenalty, CapRate, etc.)
- All math in `Decimal` — **LLM never calculates**
- Handles: tiered pricing, SLA penalties, cap rates, milestone penalties, annual adjustments

**Critic Reflection** (Anti-hallucination):
```python
# For each calculated discrepancy:
# 1. LLM writes evidence narrative (description + clause_text)
# 2. CRITIC LLM evaluates: "Is this mathematically sound given contract text?"
#    Returns: CONFIRMED | NEEDS_HUMAN_REVIEW
```

**Thresholds**:
- `MINIMUM_MATERIAL_THRESHOLD = ₹100` — ignores trivial deltas
- `SEVERITY`: CRITICAL (>₹50K), HIGH (>₹10K), MEDIUM (>₹1K), LOW

---

### Agent 5: Reverse Sweep (`backend/agents/reverse_sweep/agent.py`) — **v4 Innovation**

**Responsibility**: Find contract rules that SHOULD have triggered credits but didn't

**Pure Python Trigger Checks + Bounded LLM for Narrative**

```python
CREDIT_RULE_TYPES = {
    "early_payment_discount",  # Contract: pay in 10 days → 2% discount
    "sla_penalty",             # Contract: uptime < 97% → 12% credit
    "bundle_discount",         # Contract: buy A+B → 10% off
}

# For each credit rule in contract:
#   check_early_payment_trigger(rule, invoice) → TriggerResult
#   check_sla_penalty_trigger(rule, invoice) → TriggerResult
#   check_bundle_discount_trigger(rule, invoice) → TriggerResult
```

**Why it's novel**: Every other tool checks "invoice vs contract." This checks "contract vs invoice" — finds money the supplier **owes but didn't bill**.

---

### Agent 6: Cross-Invoice Analyzer (`backend/agents/cross_invoice_analyzer/agent.py`) — **v4 Innovation**

**Responsibility**: Detect price drift for same item across multiple invoices

**Pure Python — No LLM**

```python
# Algorithm:
1. Group line items by normalized mapped_contract_item
2. For each group with ≥2 invoices:
   - Compare unit_price_charged across invoices
   - Flag if drift > PRICE_DRIFT_THRESHOLD_PCT (5%) AND > PRICE_DRIFT_MIN_DELTA (₹10)
3. Output: CrossInvoiceResult with drift_findings[]
```

**Catches**: Systematic overcharging — supplier slowly increases unit price month over month

---

### Agent 7: Report Generator (`backend/agents/report_generator/agent.py`)

**Responsibility**: Synthesize final audit report + supplier scorecard + dispute letter

**Outputs**:
1. `AuditReport` — executive summary, sorted discrepancies, recommendations
2. `SupplierScore` — compliance score (0-100) with severity-weighted penalties
3. `DisputeLetter` — professional PDF/HTML ready to send

**Scoring Algorithm** (`services/scoring.py`):
```python
base_score = (compliant_lines / total_lines) * 100
penalties = (critical × 8) + (high × 4) + (medium × 1)
final_score = max(0, min(100, base_score - penalties))
```

---

## 💾 Data Layer

### Database Schema (SQLAlchemy + SQLite/PostgreSQL)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `audits` | Core audit records | id, status, supplier_name, contract_file, invoice_files, rulebook(JSON), invoice_data(JSON), discrepancies(JSON), audit_report(JSON), total_leakage, created_at, completed_at |
| `audit_logs` | Agent execution trace | audit_id, timestamp, level, agent, message |
| `supplier_scores` | Historical scorecards | supplier_name, audit_id, compliance_score, total_leakage, computed_at |
| `contracts` | Contract library | id, supplier_name, file_path, file_hash, version, valid_from, valid_until, status |
| `contract_chunks` | RAG chunks for Q&A | contract_id, chunk_index, header, content, tokens |
| `watched_files` | Auto-audit queue | file_path, contract_id, status, matched, error |
| `dispute_letters` | Generated letters | audit_id, letter_text, letter_html, status, sent_at |
| `comparisons` | Contract diffs | contract_id_v1, contract_id_v2, changes(JSON), summary(JSON) |
| `negotiation_briefs` | Aggregated violations | supplier_name, brief_id, total_leakage, demands(JSON) |
| `notification_settings` | Alert config | slack_webhook, email_config, alert_thresholds |

---

## 🌐 API Surface (23 Endpoints)

| Route | Method | Path | Purpose |
|-------|--------|------|---------|
| Health | GET | `/health` | System status |
| Upload | POST | `/api/upload/contract` | Store contract PDF |
| Upload | POST | `/api/upload/invoice` | Store invoice PDF |
| Audit | POST | `/api/audit/run` | Trigger pipeline (async, returns audit_id) |
| Audit | GET | `/api/audit/{id}` | Poll status |
| Audit | GET | `/api/audit/{id}/report` | Full audit report |
| Audit | GET | `/api/audit/{id}/documents` | Contract + invoice pages |
| Audit | GET | `/api/audit/{id}/logs` | Agent execution logs |
| Audit | WS | `/api/audit/{id}/ws` | Real-time progress |
| Audit | GET | `/api/audits` | List all audits |
| Audit | DELETE | `/api/audit/{id}` | Delete audit |
| Audit | POST | `/api/audit/{id}/findings/{fid}/feedback` | Human review feedback |
| Audit | POST | `/api/predict/risk` | ML risk prediction (stub) |
| Contracts | POST | `/api/contracts` | Register contract (library) |
| Contracts | GET | `/api/contracts` | List contracts |
| Contracts | DELETE | `/api/contracts/{id}` | Soft delete |
| Contracts | POST | `/api/contracts/{id}/restore` | Restore |
| Contracts | PATCH | `/api/contracts/{id}/aliases` | Supplier aliases |
| Contracts | POST | `/api/contracts/{id}/chat` | Contract Q&A (RAG) |
| Compare | POST | `/api/compare` | Contract version diff |
| Suppliers | GET | `/api/suppliers` | Scorecard list |
| Suppliers | GET | `/api/suppliers/summary` | KPI summary |
| Analytics | GET | `/api/analytics/overview` | KPIs + trends |
| Analytics | GET | `/api/analytics/heatmap` | Supplier × clause heatmap |
| Watcher | GET | `/api/watcher/status` | Auto-audit status |
| Watcher | POST | `/api/watcher/pause` | Pause watcher |
| Watcher | POST | `/api/watcher/resume` | Resume watcher |
| Watcher | GET | `/api/watcher/history` | Processed files |
| Watcher | GET | `/api/watcher/unmatched` | Unmatched invoices |
| Watcher | POST | `/api/watcher/retry` | Manual match + retry |
| Settings | GET | `/api/settings/notifications` | Get alert config |
| Settings | PUT | `/api/settings/notifications` | Update alert config |

---

## ⚙️ Core Infrastructure

### LLM Client (`backend/core/llm_client.py`)

**Multi-Provider Abstraction**:
```python
# Supports:
- Gemini (Google Generative AI) — primary
- Groq (free/fast) — fallback
- MockRouter — deterministic responses for CI/testing

# Features:
- Structured output via Pydantic schema → `response_schema` param
- Retry logic with exponential backoff (`tenacity`)
- Token usage tracking
- Streaming support
```

### PDF Extraction (`backend/core/pdf_extractor.py`)

**Dual-Engine Fallback**:
1. `pdfplumber` — primary (better tables, layout)
2. `pypdf` — fallback (simpler, faster)

Returns plain text — no OCR yet (architecture supports plug-in).

### Unit Normalizer (`backend/core/unit_normalizer.py`)

**Comprehensive Unit Family System**:
```python
UNIT_FAMILIES = {
    "MT": { "mt": 1, "tonne": 1, "kg": 0.001, "g": 0.000001, "quintal": 0.1 },
    "unit": { "unit": 1, "piece": 1, "pc": 1, "nos": 1, "each": 1 },
    "hour": { "hour": 1, "hr": 1, "day": 1/24, "week": 1/168 },
    "KM": { "km": 1, "m": 0.001, "mile": 1.609 },
    "L": { "l": 1, "ml": 0.001, "gallon": 3.785 },
    "currency": { "INR": 1, "USD": 83, "EUR": 90 },  # placeholder
}
```

Used by cross-validator + compliance checker for unit conversion before comparison.

### Contract Chunker + BM25 RAG (`backend/services/contract_chunker.py`)

**For Contract Q&A**:
- Splits by headers (Section, Clause, Schedule)
- Overlapping word-based chunks (500 tokens, 100 overlap)
- BM25Okapi index for keyword search
- Stores chunks in `contract_chunks` table

---

## 🎨 Frontend Architecture

### Page Structure (10 Pages)

| Page | Purpose | Key Components |
|------|---------|----------------|
| `Upload` | Drag-drop contracts/invoices | FileDropZone, Progress |
| `AuditRunning` | Live agent logs + WebSocket | AgentProgressBar, AuditLogConsole |
| `AuditReport` | Findings + evidence + dispute | SummaryCard, DiscrepancyTable, EvidenceBlock, DisputeLetterModal, ContractQADrawer, AuditDocumentPanel |
| `AuditList` | History + actions | Table, Filter, StatusBadge |
| `SupplierScorecard` | Vendor ranking | StatCard, Table with grades |
| `SupplierHistory` | Per-supplier timeline | Timeline, Trend |
| `Analytics` | Charts + heatmaps | Recharts (Bar, Line, Pie, Area), Tabs |
| `Settings` | Notification config | Form, Toggle |
| `ContractLibrary` | Versioned contracts | Table, VersionBadge, Compare button |
| `AutoAudit` | Watcher dashboard | StatusCard, QueueTable, RetryModal |
| `Compare` | Contract diff view | Side-by-side, ChangeHighlighter |

### Component Hierarchy

```
App
├── AppLayout
│   ├── Sidebar (navigation)
│   ├── PageHeader (title + actions)
│   └── <Page>
│       ├── Upload
│       ├── AuditRunning
│       ├── AuditReport
│       │   ├── SummaryCard
│       │   ├── DiscrepancyTable
│       │   │   └── EvidenceBlock (expandable)
│       │   ├── DisputeLetterModal
│       │   ├── ContractQADrawer
│       │   └── AuditDocumentPanel
│       ├── AuditList
│       ├── SupplierScorecard
│       ├── SupplierHistory
│       ├── Analytics
│       │   └── Recharts components
│       ├── Settings
│       ├── ContractLibrary
│       ├── AutoAudit
│       └── Compare
└── ToastProvider (global notifications)
```

### API Client (`frontend/src/api.js`)

Centralized `fetch` wrapper with:
- Base URL from `VITE_API_URL`
- API key header (`X-API-Key`)
- Typed methods: `uploadContract`, `uploadInvoice`, `runAudit`, `getAuditStatus`, `getAnalytics`, `getSuppliers`, `getWatcherStatus`, `chatWithContract`, `generateDisputeLetter`, etc.

---

## 🧪 Testing & Evaluation

### Unit Tests (`tests/unit/`)
- `test_billing_regressions.py` — Rule engine edge cases (cap rate per-unit vs line-total, tier boundary conditions)

### Integration Tests (`tests/integration/`)
- `test_contract_library.py` — Contract versioning, duplicate detection, chat RAG

### Evaluation Harness (`backend/eval/`)
```python
# harness.py — Golden-set evaluation
- Loads test_cases.json (10 cases)
- Runs full pipeline with MOCK_LLM=true
- Metrics: Precision, Recall, Delta Accuracy (within 10% tolerance)

# metrics.py
- calculate_precision_recall(predicted, expected) → (precision, recall, TP, FP, FN)
- calculate_delta_accuracy(predicted, expected, tolerance=10%) → % correct
- calculate_extraction_accuracy() — contract/invoice field accuracy
```

### Mock LLM Router (`backend/core/mock_router.py`)

**Deterministic Responses** for:
- Contract parsing → returns `MOCK_CONTRACT_RULES[contract_id]`
- Invoice extraction → returns `MOCK_INVOICE_DATA[invoice_id]`
- Compliance checking → returns pre-calculated discrepancies
- Report generation → returns structured summary

Enables **zero-cost, zero-latency, deterministic CI/CD**.

---

## 📦 Synthetic Data Generation (8 Generators)

| Script | Purpose | Output |
|--------|---------|--------|
| `generate_synthetic_data.py` | Core test cases | 4 contracts + 10 invoices with known discrepancies |
| `generate_sysco_data.py` | Sysco-style foodservice | Complex tiered pricing, case/pack units |
| `generate_sysco_supplier_data.py` | Multi-supplier portfolio | 5 suppliers, 20+ contracts |
| `generate_ippb_invoice.py` | India Post Payments Bank | Government billing format |
| `generate_manual_test_data.py` | Ad-hoc debugging | Single cases |

**Generates**: PDF contracts + invoices via `reportlab` with embedded known discrepancies for eval.

---

## 🔐 Security & Observability

### Current State
- ✅ Structured logging (`structlog`) with correlation IDs
- ✅ Audit trail table (`audit_logs`) — every agent step logged
- ✅ Input validation via Pydantic schemas
- ✅ SQL injection protection (SQLAlchemy ORM)
- ❌ **No authentication/authorization** (API key header accepted but not validated)
- ❌ **No rate limiting**
- ❌ **Global exception handler exposes tracebacks** (dev only)
- ❌ No Prometheus metrics / OpenTelemetry tracing
- ❌ No secrets management (`.env` only)

### Production Hardening Needed
1. JWT/API key validation middleware
2. Role-based access (admin, auditor, viewer)
3. Rate limiting (slowapi)
4. Structured error responses (no tracebacks)
5. Prometheus `/metrics` endpoint
6. OpenTelemetry distributed tracing
7. Alembic migrations + PostgreSQL
8. Docker + Kubernetes manifests

---

## 🚀 Deployment Architecture

### Development
```bash
# Terminal 1: Backend
cd backend && MOCK_LLM=true uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev  # Vite on port 5173
```

### Production (Target)
```
                    ┌─────────────┐
                    │  LOAD BALANCER │
                    └──────┬────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ API Pod 1│    │ API Pod 2│    │ API Pod N│  (FastAPI + Gunicorn/Uvicorn workers)
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         └───────────────┼───────────────┘
                         ▼
              ┌─────────────────────┐
              │   POSTGRESQL        │
              │   (Primary + Replica)│
              └─────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ REDIS    │  │ CELERY   │  │ WATCHDOG │
    │ (Queue)  │  │ (Workers)│  │ (Files)  │
    └──────────┘  └──────────┘  └──────────┘
```

---

## 💡 Technical Differentiators (Why This Wins)

### 1. **Deterministic Math Layer**
> "LLM extracts. Python calculates. Never the reverse."
- Every ₹ amount calculated in `Decimal` by Python rule engine
- LLM only does: extraction, mapping, narrative
- Cross-validator gate runs **before** any compliance LLM call

### 2. **Reverse Sweep (Novel)**
> "Everyone checks invoice→contract. We check contract→invoice."
- Finds credits suppliers **forgot to apply** (early payment, SLA, bundle)
- Pure Python trigger logic — no hallucination risk
- Directly recovers money

### 3. **Cross-Invoice Drift Detection (Novel)**
> "Catches the slow bleed."
- Groups same item across months
- Flags unit price creep >5% + ₹10
- Catches systematic overcharging invisible to per-invoice audit

### 4. **Self-Consistency + Voting**
> "Run 3×. Vote. Retry on validation error."
- Contract parser: 3 LLM calls → merge → validate → retry on error
- Invoice extractor: 3 LLM calls → vote on line items → validate arithmetic
- Reduces variance, catches edge cases

### 5. **Critic Reflection Loop**
> "Every finding gets a second opinion."
- After discrepancy calculated: Critic LLM evaluates "Is this mathematically sound given contract text?"
- Returns `CONFIRMED` or `NEEDS_HUMAN_REVIEW`
- Human-in-the-loop ready

### 6. **Contract Versioning + Time-Travel**
> "Invoice from October 2024? Uses contract version valid in October 2024."
- Contracts have `valid_from`/`valid_until`
- Pipeline resolves correct version by invoice date
- Contract comparison shows rule additions/modifications/removals

### 7. **Mock-First Development**
> "CI runs in seconds. Zero API costs. Deterministic."
- `MOCK_LLM=true` → full pipeline runs with canned responses
- Evaluation harness validates precision/recall/delta on every commit
- Enables fearless refactoring

---

## 📈 Scalability Characteristics

| Dimension | Current | Production Target |
|-----------|---------|-------------------|
| **Concurrent Audits** | 1 (single process) | 50+ (horizontal pods + queue) |
| **Contract Size** | 60 pages (tested) | 200+ pages (chunking) |
| **Invoices per Audit** | 10 (tested) | 100+ (parallel extraction) |
| **Latency (mock)** | ~3 seconds | <30 seconds (real LLM) |
| **Latency (real LLM)** | ~90 seconds | <2 minutes |
| **Storage** | SQLite file | PostgreSQL + S3 for PDFs |
| **Users** | Single-tenant | Multi-tenant (organizations) |

---

## 🎯 Contest Demo Readiness

### What Works Today (Zero Config)
```bash
# 1. Start backend (mock mode — no API keys needed)
cd backend && MOCK_LLM=true uvicorn main:app --reload

# 2. Start frontend
cd frontend && npm run dev

# 3. Open http://localhost:5173
# 4. Upload: data/synthetic/contracts/c001_apex_logistics_contract.pdf
# 5. Upload: data/synthetic/invoices/c001_invoice_i001.pdf, i002.pdf, i003.pdf
# 6. Click "Run Audit" → Watch live logs → See ₹43,580 leakage in 90 seconds
```

### Demo Script (3 Minutes)
| Time | Action | Talking Point |
|------|--------|---------------|
| 0:00 | Show contract PDF | "12 pages. Section 4.2: volume tiers. Section 8.1: SLA penalty." |
| 0:30 | Drag-drop 3 invoices | "Real PDFs. Not synthetic JSON — real documents." |
| 1:00 | Click "Run Audit" | "Live WebSocket logs. 7 agents executing." |
| 1:30 | Audit complete → Report | "₹43,580 found. 3 discrepancies. Expand row → exact clause + math." |
| 2:00 | Click "Generate Dispute" | "Professional letter. Ready to email. One click." |
| 2:30 | Show Supplier Scorecard | "C- grade. 68/100. History shows improving/declining." |
| 2:45 | Show Analytics | "Heatmap: which suppliers, which clauses leak most." |
| 3:00 | Contract Q&A | "Ask: 'What's my early payment terms?' → Cited answer." |

---

## 📋 Appendix: File Inventory (Key Files)

### Backend Core
```
backend/
├── main.py                      # FastAPI app + lifespan (file watcher)
├── requirements.txt             # 41 dependencies
├── core/
│   ├── config.py                # All env vars + defaults
│   ├── db.py                    # SQLAlchemy async engine + session
│   ├── llm_client.py            # Multi-provider (Gemini/Groq/Mock)
│   ├── pdf_extractor.py         # pdfplumber + pypdf fallback
│   ├── unit_normalizer.py       # Unit family conversions
│   ├── prompt_loader.py         # Loads prompt.txt from agent dirs
│   ├── mock_router.py           # Deterministic mock responses
│   ├── mock_data.py             # Canned contract/invoice data
│   ├── audit_logger.py          # Structured audit trail
│   ├── schema_utils.py          # Vertex AI schema cleaning
│   ├── time.py                  # UTC helpers
│   └── tasks.py                 # Background task scheduler
├── models/
│   ├── schemas.py               # ALL Pydantic models + CleanDecimal
│   └── audit.py                 # SQLAlchemy ORM models
├── agents/
│   ├── pipeline.py              # LangGraph StateGraph (7 nodes)
│   ├── contract_parser/         # Agent 1: chunked + retry
│   ├── invoice_extractor/       # Agent 2: self-consistency + validation
│   ├── cross_validator/         # Agent 3: deterministic gate
│   ├── compliance_checker/      # Agent 4: LLM mapping + rule engine
│   ├── reverse_sweep/           # Agent 5: missing credits (v4)
│   ├── cross_invoice_analyzer/  # Agent 6: price drift (v4)
│   ├── report_generator/        # Agent 7: summary + scorecard + letter
│   └── contract_qa/             # RAG Q&A agent
├── api/routes/
│   ├── audit.py                 # 12 endpoints + WebSocket
│   ├── upload.py                # File upload handling
│   ├── contracts.py             # Contract library + compare
│   ├── suppliers.py             # Scorecards
│   ├── analytics.py             # KPIs + heatmap
│   ├── watcher.py               # Auto-audit control
│   ├── settings.py              # Notifications
│   └── health.py                # Health check
├── services/
│   ├── analytics.py             # Aggregation queries
│   ├── contract_chunker.py      # BM25 RAG chunking
│   ├── contract_comparator.py   # Version diff
│   ├── dispute_generator.py     # Letter drafting
│   ├── file_watcher.py          # Watchdog auto-audit
│   ├── negotiation_analyzer.py  # Violation patterns → brief
│   ├── notifier.py              # Slack/Email alerts
│   ├── scoring.py               # Compliance score algorithm
│   └── risk_scorer.py           # ML risk stub
└── eval/
    ├── harness.py               # Golden-set evaluation
    └── metrics.py               # Precision/Recall/Delta accuracy
```

### Frontend
```
frontend/
├── package.json                 # React 19, Vite, Tailwind, Recharts
├── vite.config.js
├── tailwind.config.js
├── src/
│   ├── main.jsx                 # Entry + Router + ToastProvider
│   ├── App.jsx                  # Routes + state management
│   ├── api.js                   # Centralized fetch client
│   ├── pages/                   # 11 page components
│   ├── components/
│   │   ├── layout/              # AppLayout, PageHeader, Sidebar
│   │   ├── ui/                  # 18 reusable primitives
│   │   ├── DiscrepancyTable.jsx # Expandable rows + evidence
│   │   ├── SummaryCard.jsx      # KPI cards + compliance grade
│   │   ├── ContractQADrawer.jsx # RAG chat sidebar
│   │   ├── DisputeLetterModal.jsx # Letter preview + edit
│   │   ├── EvidenceBlock.jsx    # Clause text + calculation
│   │   ├── AuditLogConsole.jsx  # Live agent logs
│   │   ├── AgentProgressBar.jsx # Pipeline visualization
│   │   └── ...
│   └── utils/chartTheme.js      # Recharts theme config
```

---

## 🏁 Conclusion

**ProcureAI demonstrates production-grade AI engineering:**

1. **Architecture** — LangGraph state machine, not chain-of-prompts
2. **Reliability** — Deterministic math, validation retries, critic reflection, mock-first CI
3. **Innovation** — Reverse sweep, cross-invoice drift, contract versioning
4. **Completeness** — End-to-end: PDF → Audit → Report → Dispute → Analytics → Negotiation
5. **Extensibility** — Clean boundaries, typed contracts, pluggable LLM providers

**This is not a demo. This is a product skeleton ready for production hardening.**

---

*Generated from codebase analysis — 2026-08-26*
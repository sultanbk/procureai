# ProcureAI — Agentic Contract Compliance & Invoice Auditor

## AI Assistant Context — Read First

---

## Current Source Of Truth

The implementation is authoritative. Read these documents in order before making a code change:

1. `AI_MUST_READ_FIRST.md` (this file)
2. `ARCHITECTURE.md`
3. `PROJECT_CONVENTIONS.md`
4. `DATA_SCHEMAS.md`
5. `PROGRESS_TRACKER.md`

Historical design notes are under `docs/archive/` and are not specifications for current behavior.

## Critical Instructions For Any AI Assistant

You are helping build **ProcureAI**, a production-grade multi-agent AI system.
Do not write code that contradicts `ARCHITECTURE.md` or the Pydantic contracts in `DATA_SCHEMAS.md`. Keep API and frontend changes synchronized, and update `PROGRESS_TRACKER.md` when a meaningful implementation change is made.

---

## PROJECT IN ONE PARAGRAPH

ProcureAI is a FastAPI + LangGraph + React system that accepts a supplier contract PDF and invoice PDFs, runs a multi-stage compliance pipeline, and produces an evidence-grounded audit report with deterministic financial calculations. It also supports a reusable contract library, automatic invoice intake, contract Q&A, contract comparison, supplier analytics, negotiation briefs, dispute letters, notifications, and human feedback.

---

## TECH STACK SNAPSHOT
--------------------------------------------------------
| Layer            | Technology                        |
|------------------|-----------------------------------|
| Agent framework  | LangGraph (stateful pipeline)     |
| LLM              | Gemini Developer API, Vertex AI, or mock |
| API              | FastAPI + uvicorn                 |
| PDF parsing      | pypdf + pdfplumber                |
| Structured output| Pydantic v2 (strict mode)         |
| Database         | SQLite by default                 |
| Frontend         | React + Vite + Tailwind CSS       |
| Storage          | Local filesystem                  |
| Evaluation       | Custom Python eval harness        |
--------------------------------------------------------
---

## Current Folder Structure

```
supplierguard/
├── backend/                    # FastAPI app, routes, agents, services, models, core
├── frontend/                   # React/Vite client and UI
├── scripts/                    # Database, migration, data, and diagnostic scripts
├── tests/                      # Backend unit, integration, and evaluation tests
├── data/                       # Local database, uploads, synthetic and evaluation data
├── watched_invoices/           # Automatic invoice intake directory
├── docs/                       # Current guides and archived historical notes
├── ARCHITECTURE.md
├── DATA_SCHEMAS.md
├── PROJECT_CONVENTIONS.md
└── PROGRESS_TRACKER.md
```

---

## Pipeline Stages — One-Line Each

| Node | Input | Output |
|-------|-------|--------|
| Extractors | Contract and invoice PDF text | `ContractRulebook` and `InvoiceData` |
| Cross Validator | Rulebook + invoice data | Candidate mappings and data-required flags |
| Compliance Checker | Candidates + invoices | `DiscrepancyList` using Python rule evaluators |
| Reverse Sweep | Contract rules + invoice evidence | Missing-credit findings |
| Cross-Invoice Analyzer | Multiple invoice records | Price-drift findings |
| Report Generator | All findings and flags | `AuditReport` |

---

## NON-NEGOTIABLE RULES FOR ALL AI ASSISTANTS

1. **Every agent output MUST be validated by a Pydantic model before passing to the next agent.**
   If validation fails, the pipeline halts and returns a structured error — never silently continues.

2. **The Compliance Checker uses a deterministic rule engine (rule_engine.py) for all arithmetic.**
   LLM is used only to interpret and classify rules. The actual delta calculation is pure Python math.
   Never let an LLM compute financial figures.

3. **Every discrepancy finding MUST include:** rule_id, clause text, expected amount, charged amount,
   delta, confidence score, and recommendation. Partial findings are rejected.

4. **All prompts live in .txt files.** Never hardcode prompts as Python strings inside agent files.

5. **Structured output format:** All LLM calls use `response_mime_type="application/json"` 
   and a Pydantic schema. Never parse free-text LLM output.

6. **Error handling:** Every agent wraps its LLM call in try/except. On failure, it returns a
   `AgentError` object with agent name, error type, and partial results — never raises unhandled.

7. **Update the tracker when implementation work changes project status; do not treat its historical build log as a current architecture specification.**

## Current Runtime Facts

- `backend/main.py` mounts health, upload, audit, supplier, analytics, dispute, settings, contract, comparison, and watcher routers.
- The compiled pipeline is `parallel_extractors` (logically independent extractors executed in one node), then cross validation, compliance checking, reverse sweep, cross-invoice analysis, and report generation.
- `frontend/src/App.jsx` uses local React state for views; it does not use URL-based routing or deep links.
- SQLite is the verified default. PostgreSQL deployment is not turnkey because the async PostgreSQL driver is not included in the checked-in requirements.
- CORS is currently permissive (`allow_origins=["*"]`); API-key and rate-limit middleware exists but is not mounted.

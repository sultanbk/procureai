# 🤖 AI ASSISTANT — READ THIS FILE FIRST, EVERY SESSION
# ProcureAI — Agentic Contract Compliance & Invoice Auditor

---

## CRITICAL INSTRUCTIONS FOR ANY AI ASSISTANT

You are helping build **ProcureAI**, a production-grade multi-agent AI system.
Before writing a single line of code, you MUST read these files in this exact order:

```
1. AI_MUST_READ_FIRST.md        ← YOU ARE HERE
2. ARCHITECTURE.md              ← Full system design (read completely)
3. PROJECT_CONVENTIONS.md       ← Naming, style, patterns (non-negotiable)
4. PROGRESS_TRACKER.md          ← What is done, what is next (update after every session)
5. DATA_SCHEMAS.md              ← All Pydantic models and JSON contracts
```

**Do not write code that contradicts ARCHITECTURE.md.**
**Do not invent conventions not defined in PROJECT_CONVENTIONS.md.**
**Always update PROGRESS_TRACKER.md at the end of every session.**

---

## PROJECT IN ONE PARAGRAPH

ProcureAI is a FastAPI + LangGraph + React system that accepts a supplier contract PDF
and invoice PDFs, runs them through a 6-node pipeline (Contract Parser → Invoice Extractor
→ Cross-Validator → Compliance Checker → Report Generator), and produces a fully evidence-grounded
audit report identifying every financial discrepancy with exact clause citations and dollar
impact. The output is not a chatbot response. It is a structured, verifiable audit object.

---

## TECH STACK SNAPSHOT
--------------------------------------------------------
| Layer            | Technology                        |
|------------------|-----------------------------------|
| Agent framework  | LangGraph (stateful pipeline)     |
| LLM              | Google Gemini 2.5 flash(Vertex AI)|
| API              | FastAPI + uvicorn                 |
| PDF parsing      | pypdf + pdfplumber                |
| Structured output| Pydantic v2 (strict mode)         |
| Database         | SQLite → PostgreSQL               |
| Frontend         | React + Vite + Tailwind CSS       |
| Storage          | Local filesystem → GCS            |
| Evaluation       | Custom Python eval harness        |
--------------------------------------------------------
---

## FOLDER STRUCTURE (DO NOT DEVIATE)

```
suppliergaurd/
├── AI_MUST_READ_FIRST.md       ← AI reads this first
├── ARCHITECTURE.md             ← Full architecture spec
├── PROJECT_CONVENTIONS.md      ← All coding conventions
├── PROGRESS_TRACKER.md         ← Session-by-session progress log
├── DATA_SCHEMAS.md             ← All data contracts
│
├── backend/
│   ├── main.py                 ← FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example
│   ├── api/
│   │   ├── routes/
│   │   │   ├── audit.py        ← POST /audit/run, GET /audit/{id}
│   │   │   ├── upload.py       ← POST /upload/contract, /upload/invoice
│   │   │   └── health.py       ← GET /health
│   │   ├── schemas.py          ← FastAPI request/response models
│   │   └── middleware.py       ← Request ID, logging
│   ├── agents/
│   │   ├── pipeline.py         ← LangGraph graph definition (MASTER ORCHESTRATOR)
│   │   ├── contract_parser/
│   │   │   ├── agent.py        ← Agent 1 definition
│   │   │   ├── tools.py        ← Extraction tools
│   │   │   └── prompt.txt      ← Agent 1 system prompt
│   │   ├── invoice_extractor/
│   │   │   ├── agent.py        ← Agent 2 definition
│   │   │   ├── tools.py
│   │   │   └── prompt.txt
│   │   ├── compliance_checker/
│   │   │   ├── agent.py        ← Agent 3 definition
│   │   │   ├── tools.py        ← Rule application logic
│   │   │   ├── rule_engine.py  ← Deterministic rule evaluator
│   │   │   └── prompt.txt
│   │   └── report_generator/
│   │       ├── agent.py        ← Agent 4 definition
│   │       ├── tools.py
│   │       └── prompt.txt
│   ├── core/
│   │   ├── pdf_extractor.py    ← PDF text + structure extraction
│   │   ├── llm_client.py       ← Gemini client singleton
│   │   ├── db.py               ← SQLAlchemy setup
│   │   └── storage.py          ← File storage abstraction
│   ├── models/
│   │   ├── audit.py            ← SQLAlchemy ORM models
│   │   └── schemas.py          ← Pydantic schemas (= DATA_SCHEMAS.md)
│   └── eval/
│       ├── harness.py          ← Evaluation runner
│       ├── test_cases/         ← JSON test cases with expected outputs
│       └── metrics.py          ← Precision, recall, delta accuracy
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── pages/
│       │   ├── Upload.jsx      ← Step 1: Upload contract + invoices
│       │   ├── AuditRunning.jsx← Step 2: Live agent progress
│       │   └── AuditReport.jsx ← Step 3: Full audit report display
│       └── components/
│           ├── DiscrepancyTable.jsx
│           ├── EvidenceBlock.jsx
│           ├── SummaryCard.jsx
│           └── AgentProgressBar.jsx
│
├── data/
│   ├── synthetic/
│   │   ├── contracts/          ← 5 synthetic contract PDFs
│   │   └── invoices/           ← 10 synthetic invoice PDFs
│   └── eval/
│       └── test_cases.json     ← Ground truth for evaluation
│
└── scripts/
    ├── generate_synthetic_data.py ← Creates all test PDFs
    ├── seed_db.py              ← Initialises database
    └── run_eval.py             ← Runs full evaluation suite
```

---

## THE 4 AGENTS — ONE-LINE EACH

| Node | Input | Output |
|-------|-------|--------|
| Contract Parser | Contract PDF text | `ContractRulebook` (structured pricing rules JSON) |
| Invoice Extractor | Invoice PDF text | `InvoiceData` (structured line items JSON) |
| Cross-Validator | Rulebook + InvoiceData | `candidate_map` (pre-filtered rule candidates) |
| Compliance Checker | Candidates + Invoices | `DiscrepancyList` (findings with evidence and Critic approval) |
| Report Generator | DiscrepancyList | `AuditReport` (ranked, cited, human-readable) |

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

7. **Update PROGRESS_TRACKER.md at the end of every working session.**

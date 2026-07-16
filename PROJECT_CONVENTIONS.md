# PROJECT_CONVENTIONS.md — ProcureAI Coding Standards
# Version 1.0
# AI ASSISTANTS: Follow every convention here without deviation.
# These exist to make the codebase consistent across multiple AI sessions.

---

## 1. FILE AND FOLDER NAMING

- All Python files: `snake_case.py`
- All React files: `PascalCase.jsx`
- All markdown docs: `UPPER_SNAKE_CASE.md`
- All prompt files: `prompt.txt` (inside each agent folder)
- All test case JSON: `TC###_description.json`

---

## 2. PYTHON CONVENTIONS

### Imports — always in this order
```python
# 1. Standard library
import os
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Literal

# 2. Third-party
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import google.generativeai as genai

# 3. Internal — absolute imports only (never relative)
from backend.core.llm_client import get_llm
from backend.models.schemas import ContractRulebook, PipelineState
from backend.agents.contract_parser.tools import extract_sections
```

### Agent function signature — always this pattern
```python
# Every agent function receives and returns PipelineState
async def run_contract_parser(state: PipelineState) -> PipelineState:
    """
    Agent 1: Contract Parser
    Input:  state["contract_text"]
    Output: state["rulebook"], state["current_agent"] = "contract_parser"
    Error:  state["errors"].append(...), state["halt"] = True if unrecoverable
    """
    state["current_agent"] = "contract_parser"
    try:
        # ... agent logic
        state["rulebook"] = rulebook.model_dump()
    except Exception as e:
        state["errors"].append(AgentError(
            agent="contract_parser",
            error_type="llm_call_failed",
            message=str(e),
            recoverable=False
        ).model_dump())
        state["halt"] = True
    return state
```

### LLM calls — always structured output, never free text
```python
# CORRECT — structured output with schema enforcement
response = llm.generate_content(
    contents=[prompt, text],
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema=ContractRulebook.model_json_schema()
    )
)
result = ContractRulebook.model_validate_json(response.text)

# WRONG — never do this
response = llm.generate_content(prompt + text)
# then try to parse free text → fragile, unpredictable
```

### Monetary arithmetic — always Decimal, never float
```python
# CORRECT
from decimal import Decimal
delta = Decimal("14260.00") - Decimal("15500.00")  # → Decimal("-1240.00")

# WRONG — never use float for money
delta = 14260.0 - 15500.0  # float precision errors in financial context
```

### Error handling — every agent wraps in try/except
```python
# CORRECT
try:
    result = ContractRulebook.model_validate_json(response.text)
except ValidationError as e:
    # retry once
    result = retry_with_correction(prompt, response.text, e)
    if result is None:
        # set error, halt
        ...

# WRONG — letting exceptions bubble unhandled from agents
```

---

## 3. PYDANTIC CONVENTIONS

- Use Pydantic v2 throughout (no v1 syntax)
- All agent output models: strict validation
- All monetary fields: `Decimal`, serialised as string
- All optional fields: `Optional[X] = None` (not `X | None`)
- All enums: use `Literal["a", "b"]` not Python `Enum` classes

```python
# CORRECT — Pydantic v2
class Discrepancy(BaseModel):
    delta: Decimal = Field(..., description="Expected minus charged. Negative = overcharge.")
    severity: Literal["CRITICAL", "HIGH", "MEDIUM"]
    recommendation: Literal["DISPUTE", "ESCALATE", "MONITOR", "ACCEPT"]

# WRONG — Pydantic v1 style
class Discrepancy(BaseModel):
    class Config:
        ...
```

---

## 4. LANGGRAPH CONVENTIONS

- All nodes: async functions (`async def run_<agent_name>`)
- All state fields: initialized in the entry node if missing
- Conditional edges: only for halt/error routing — not for business logic branching
- The pipeline is always compiled once at startup, not per-request

```python
# CORRECT — compile once
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline

# Per-request: invoke on the compiled pipeline
result = await get_pipeline().ainvoke(initial_state)
```

---

## 5. FASTAPI CONVENTIONS

### Route structure
```python
# api/routes/audit.py
from fastapi import APIRouter, BackgroundTasks, HTTPException
router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.post("/run", response_model=AuditStatusResponse)
async def run_audit(request: AuditRequest, background: BackgroundTasks):
    ...

@router.get("/{audit_id}", response_model=AuditStatusResponse)
async def get_audit(audit_id: str):
    ...
```

### Always return typed responses — never raw dicts
```python
# CORRECT
return AuditStatusResponse(audit_id=..., status=..., ...)

# WRONG
return {"audit_id": ..., "status": ...}
```

### HTTP status codes
```python
200 → successful GET
201 → successful POST that creates a resource
202 → audit accepted, running in background
400 → bad request (validation error, wrong file type)
404 → audit_id not found
422 → Pydantic validation failure (FastAPI handles automatically)
500 → internal error (agent failure)
```

---

## 6. PROMPT FILE CONVENTIONS

All prompts live in `backend/agents/{agent_name}/prompt.txt`.
Never hardcode prompts as Python strings.

### Prompt file structure
```
[ROLE]
You are a specialized AI agent for ProcureAI...

[TASK]
Your specific task is...

[INPUT FORMAT]
You will receive...

[OUTPUT FORMAT]
You MUST return valid JSON matching this exact schema:
{schema placeholder — injected at runtime}

[RULES]
1. ...
2. ...

[EXAMPLES]
Input: ...
Output: ...

[FAILURE BEHAVIOUR]
If you cannot extract a rule with confidence > 0.6, set extraction_confidence below 0.6
and include it in unextracted_sections. Never hallucinate pricing figures.
```

### Loading prompts
```python
# core/prompt_loader.py
from pathlib import Path

def load_prompt(agent_name: str) -> str:
    path = Path(__file__).parent.parent / "agents" / agent_name / "prompt.txt"
    return path.read_text(encoding="utf-8")
```

---

## 7. REACT CONVENTIONS

### Component structure
```jsx
// Always: named export, PropTypes or TypeScript-style JSDoc
// File: components/SummaryCard.jsx

export default function SummaryCard({ summary }) {
  // 1. State hooks
  // 2. Effect hooks
  // 3. Handlers
  // 4. Render
  return (...)
}
```

### API calls — always in a dedicated api/ folder
```jsx
// frontend/src/api/audit.js — all API calls centralised here

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

export async function runAudit(contractFileId, invoiceFileIds) {
  const res = await fetch(`${BASE}/api/audit/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contract_file_id: contractFileId, invoice_file_ids: invoiceFileIds })
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function pollAudit(auditId) {
  const res = await fetch(`${BASE}/api/audit/${auditId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
```

### Polling pattern — always clean up intervals
```jsx
// In AuditRunning.jsx
useEffect(() => {
  const interval = setInterval(async () => {
    const data = await pollAudit(auditId)
    setAuditData(data)
    if (["COMPLETE", "FAILED"].includes(data.status)) {
      clearInterval(interval)
    }
  }, 2000)
  return () => clearInterval(interval)   // cleanup on unmount
}, [auditId])
```

---

## 8. ENVIRONMENT VARIABLES

```bash
# backend/.env — copy from .env.example

# Google / Vertex AI
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash

# Database
DATABASE_URL=sqlite:///./data/procureai.db

# File storage
UPLOAD_DIR=./tmp/uploads
MAX_UPLOAD_SIZE_MB=20

# Pipeline settings
MINIMUM_MATERIAL_THRESHOLD=100
COMPLIANCE_CONFIDENCE_THRESHOLD=0.60
LLM_RETRY_ATTEMPTS=3
LLM_RETRY_DELAY_SECONDS=2

# Frontend
VITE_API_URL=http://localhost:8000
```

---

## 9. GIT COMMIT CONVENTIONS

```
feat: add compliance checker agent rule engine
fix: decimal rounding in volume tier evaluator
agent: update contract parser prompt for cross-references
schema: add cap_rate rule type to PricingRule
eval: add TC005 SLA penalty test case
docs: update PROGRESS_TRACKER after Day 3
```

---

## 10. WHAT AI ASSISTANTS MUST NEVER DO

1. **Never change a schema field name** — it breaks the pipeline state contract
2. **Never use float for money** — always Decimal
3. **Never parse free-text LLM output** — always use structured JSON mode
4. **Never let an LLM compute arithmetic** — rule_engine.py does all math
5. **Never hardcode a prompt in a Python file** — always load from prompt.txt
6. **Never invent a new agent** — the 4-agent architecture is fixed
7. **Never skip Pydantic validation** between agents
8. **Never use relative imports** — always absolute (`from backend.models...`)
9. **Never forget to update PROGRESS_TRACKER.md** at session end
10. **Never add a dependency without adding it to requirements.txt**

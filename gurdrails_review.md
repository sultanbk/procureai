Let me search the codebase for any guardrail implementations:

Searched for "guardrail"
Searched for "hallucination"
Searched for "validation"
Searched for "cross_valid"
Searched for "reverse_sweep\|critic\|confidence"
Viewed validator.py:1-50
Viewed agent.py:1-50
Viewed agent.py:1-30

Now let me look at the critic prompt and the pipeline halt logic to understand the full guardrail picture:

Viewed prompt_critic.txt:1-41
Viewed agent.py:370-400
Viewed rule_engine.py:1-40
Viewed tools.py:1-50

Now I have a thorough picture. Here's the answer:

---

**Yes, ProcureAI has guardrails — but they're scattered across the pipeline rather than centralized.** Here's a breakdown of what exists and what's missing:

## ✅ Guardrails That Exist

### 1. **Deterministic Math Verification (strongest guardrail)**

The LLM is **never trusted for arithmetic**. Every numerical result is independently verified:

- [rule_engine.py](file:///d:/sultan/ProcureAI/procureai/backend/agents/compliance_checker/rule_engine.py) — Pure Python `Decimal`-based billing verification, completely bypasses LLM
- [invoice_extractor/tools.py](file:///d:/sultan/ProcureAI/procureai/backend/agents/invoice_extractor/tools.py) — Deterministic invoice metadata extraction via regex
- [invoice_extractor/agent.py L134-137](file:///d:/sultan/ProcureAI/procureai/backend/agents/invoice_extractor/agent.py#L134-L137) — **Overrides LLM validation flags** with Python-calculated results

### 2. **Hallucination Detection**

[contract_parser/agent.py L370-391](file:///d:/sultan/ProcureAI/procureai/backend/agents/contract_parser/agent.py#L370-L391) — When the LLM extracts a `clause_text`, the system verifies it actually exists in the source contract. If not found, it's flagged as `hallucinated_clause` with `extraction_confidence = 0.0`.

### 3. **Cross-Validation Gate (zero LLM)**

[cross_validator/validator.py](file:///d:/sultan/ProcureAI/procureai/backend/agents/cross_validator/validator.py) — A **pure Python, no-LLM** pipeline node that runs _before_ the compliance checker. Fuzzy-matches invoice lines to contract rules and flags mismatches.

### 4. **LLM Critic Agent**

[prompt_critic.txt](file:///d:/sultan/ProcureAI/procureai/backend/agents/compliance_checker/prompt_critic.txt) — A second LLM pass that reviews findings and marks each as `CONFIRMED` or `NEEDS_HUMAN_REVIEW`. It explicitly **cannot delete findings**, only annotate them.

### 5. **Reverse Sweep (bidirectional check)**

[reverse_sweep/agent.py](file:///d:/sultan/ProcureAI/procureai/backend/agents/reverse_sweep/agent.py) — Checks the _opposite direction_: contract rules that **should** have triggered credits but didn't appear on the invoice.

### 6. **Pydantic Schema Validation with Retry**

All agent outputs are validated against strict Pydantic schemas. On `ValidationError`, the LLM gets a correction prompt with the error details and retries once.

### 7. **Pipeline Halt Logic**

[pipeline.py](file:///d:/sultan/ProcureAI/procureai/backend/agents/pipeline.py) — Conditional edges check a `halt` flag at every node boundary. If critical data is missing, the pipeline stops early rather than producing garbage.

### 8. **Materiality Threshold**

The compliance checker skips deltas below `MINIMUM_MATERIAL_THRESHOLD` (default ₹100) to avoid noise.

## ❌ Guardrails That Are Missing

| Missing Guardrail                              | Risk                                                                           | Recommendation                                                       |
| ---------------------------------------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| **No prompt injection protection**             | User-uploaded PDFs could contain adversarial text that manipulates LLM outputs | Add input sanitization and instruction-defense prompting             |
| **No output content filtering**                | LLM could generate inappropriate content in dispute letters or summaries       | Add output filtering layer before returning to user                  |
| **No confidence-based gating**                 | Low-confidence extractions proceed without additional verification             | Gate pipeline progression on `extraction_confidence` thresholds      |
| **No token/cost limits per audit**             | A large document could trigger unbounded LLM calls                             | Add token budget per pipeline run                                    |
| **No human-in-the-loop for CRITICAL findings** | Critical findings auto-complete without mandatory human review                 | Add a hold state for CRITICAL severity before marking audit COMPLETE |
| **No rate limiting on LLM calls**              | Rapid audit requests could exhaust provider quotas                             | Add per-provider rate limiting in `llm_client.py`                    |

## Summary

The project has **strong mathematical guardrails** (Python Decimal never trusts LLM math) and decent **structural guardrails** (schema validation, cross-validation gate, critic review). What it lacks are **input protection** (prompt injection from PDFs) and **output safety** guardrails. Would you like me to implement any of the missing ones?

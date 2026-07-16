## 🔍 Deep Architecture v3 Audit — Problems Found & Fix Plan

I've read every agent file, schema, pipeline, rule engine, prompt, config, and tools file. Here's everything that's wrong, organized by severity.

---

### 🔴 CRITICAL PROBLEMS (Will cause incorrect audit results)

---

**PROBLEM 1: Pipeline is SEQUENTIAL, not parallel (violates core v3 principle)**

The architecture says *"Nodes 1–2 run in parallel (fan-out/fan-in)"* — this is the #1 design change from v1/v2. But [pipeline.py](file:///d:/SupplierGuard/backend/agents/pipeline.py) runs them **sequentially**: `invoice_extractor → contract_parser → cross_validator → ...`

```python
# Current (WRONG):
graph.set_entry_point("invoice_extractor")
graph.add_conditional_edges("invoice_extractor", lambda s: ... "contract_parser")
graph.add_conditional_edges("contract_parser", lambda s: ... "cross_validator")
```

This means if invoice extraction fails, contract parsing never runs — but the architecture guarantees they're **independent**. It also doubles wall-clock time.

**Fix:** Use LangGraph's parallel fan-out pattern, or at minimum run them sequentially but **both** before cross_validator, with independent halt logic (one can fail without blocking the other, if the other's data is sufficient for a partial report).

---

**PROBLEM 2: Invoice Extractor reads `state["rulebook"]` — violates independence rule**

[invoice_extractor/agent.py line 30](file:///d:/SupplierGuard/backend/agents/invoice_extractor/agent.py#L30) docstring says:
```
Input: state["invoice_texts"], state["rulebook"]
```

Architecture v3 Rule #1 says: *"Contract Parser and Invoice Extractor run independently — neither reads the other's output."* The docstring explicitly declares it consumes the rulebook. While the actual code doesn't seem to use it for extraction logic anymore (semantic mapping was moved to Node 3), this is a ticking time bomb — any developer reading the docstring will think it's OK to use the rulebook.

**Fix:** Remove `state["rulebook"]` from the docstring. Add a defensive check: if the code ever accidentally accesses `state["rulebook"]`, raise an assertion error during invoice extraction.

---

**PROBLEM 3: `AnnualAdjustmentEvaluator` is missing from the rule engine**

Architecture v3 Section 6 ([ARCHITECTURE_v3.md line 347](file:///d:/SupplierGuard/ARCHITECTURE_v3.md#L347)) lists 8 evaluators that "ALL must be implemented before go-live":

| Evaluator | In rule_engine.py? |
|---|---|
| `VolumeTierEvaluator` | ✅ |
| `FlatRateEvaluator` | ✅ |
| `CapRateEvaluator` | ✅ |
| `SLAPenaltyEvaluator` | ✅ |
| `EarlyPaymentDiscountEvaluator` | ✅ |
| `BundleDiscountEvaluator` | ✅ |
| `AnnualAdjustmentEvaluator` | ❌ **MISSING** |
| `MilestonePenaltyEvaluator` | ✅ (exists but NOT in EVALUATOR_MAP) |

[rule_engine.py line 213-220](file:///d:/SupplierGuard/backend/agents/compliance_checker/rule_engine.py#L213-L220) — `EVALUATOR_MAP` has only 6 entries. `AnnualAdjustmentEvaluator` doesn't exist at all, and `MilestonePenaltyEvaluator` is implemented but reached only via the string-matching fallback at line 226, not through the proper dispatch map.

**Impact:** Any contract with annual price adjustment clauses or milestone penalties routed through the normal map will silently return `line_total_charged` (no discrepancy found), even if the supplier is overcharging.

**Fix:** Implement `AnnualAdjustmentEvaluator`. Add `"milestone_penalty": MilestonePenaltyEvaluator` and `"annual_adjustment": AnnualAdjustmentEvaluator` to `EVALUATOR_MAP`.

---

**PROBLEM 4: `MilestonePenaltyEvaluator` returns `Decimal("0.00")` when no data — should be flagged, not silently compliant**

[rule_engine.py line 178](file:///d:/SupplierGuard/backend/agents/compliance_checker/rule_engine.py#L178): When `milestone_date` is `None`, it returns `Decimal("0.00")`. This means a line charged at ₹50,000 with no milestone data will compute `delta = 0 - 50000 = -50000` and flag a false ₹50,000 "discrepancy." Or if it's evaluated against a dummy line (charged = 0), delta = 0, no finding. Either way, **wrong**.

Architecture v3 Rule #5 says these should become `DataRequiredFlag` at Node 3, never reaching the evaluator. But the evaluator is still called for cases that slip through, and its return value is nonsensical.

**Fix:** The evaluator should raise a `ValueError("No milestone data available")` or return `line_total_charged` to indicate "no finding possible" rather than inventing a zero.

---

**PROBLEM 5: Per-line arithmetic check uses `float` instead of `Decimal`**

[invoice_extractor/agent.py lines 109-110](file:///d:/SupplierGuard/backend/agents/invoice_extractor/agent.py#L109-L110):
```python
expected_line_total = round(float(item.quantity) * float(item.unit_price_charged), 2)
if abs(expected_line_total - float(item.line_total_charged)) > 0.01:
```

Architecture v3 Rule #8: *"All monetary values: Python Decimal, never float."* This code converts to `float` for arithmetic — introducing floating-point rounding errors that could cause false arithmetic flags (e.g., `0.1 + 0.2 ≠ 0.3` in float). Meanwhile, [tools.py](file:///d:/SupplierGuard/backend/agents/invoice_extractor/tools.py#L66-L75) `validate_invoice_arithmetic` correctly uses `Decimal`.

**Fix:** Replace with `Decimal` arithmetic matching what `tools.py` already does. This is a **duplicate** of the same check — both run, potentially giving conflicting results.

---

**PROBLEM 6: Rule matching doesn't enforce the `RULE_MATCH_CONFIDENCE_THRESHOLD` gate**

Architecture v3 Section 6 says:
> *"If ALL candidates score < RULE_MATCH_CONFIDENCE_THRESHOLD (0.75): line item → review_flags"*

But [compliance_checker/agent.py](file:///d:/SupplierGuard/backend/agents/compliance_checker/agent.py#L222-L230) processes every mapping the LLM returns without checking `mapping.confidence >= 0.75`. The threshold from config is `COMPLIANCE_CONFIDENCE_THRESHOLD = 0.60`, not 0.75 as architecture specifies.

**Fix:** After LLM returns mappings, filter: if all rule confidences for a line are < 0.75, send that line to `review_flags` instead of proceeding to evaluation.

---

### 🟠 HIGH SEVERITY PROBLEMS (Data integrity / correctness risks)

---

**PROBLEM 7: Schema mismatch — `PricingRule` field naming divergence**

Architecture v3 uses `clause_section` (line 152), but [schemas.py](file:///d:/SupplierGuard/backend/models/schemas.py#L141) uses `clause_reference`. The cross_validator ([validator.py line 80](file:///d:/SupplierGuard/backend/agents/cross_validator/validator.py#L80)) uses `getattr(rule, "clause_reference", "Unknown")` to work around this, but the `DataRequiredFlag` schema and the architecture spec both use `clause_section`. This creates inconsistency in the output JSON — some places say `clause_section`, others `clause_reference`.

**Fix:** Pick one name and use it everywhere. Since `clause_reference` is already in the Pydantic schema and database, keep `clause_reference` and update the architecture doc. Or alias the field in Pydantic.

---

**PROBLEM 8: `PricingRule.parameters` dict is missing from the schema**

Architecture v3 ([line 153](file:///d:/SupplierGuard/ARCHITECTURE_v3.md#L153)) defines `parameters: dict # type-specific (tiers, cap_amount, etc.)`. But [schemas.py](file:///d:/SupplierGuard/backend/models/schemas.py#L137-L172) doesn't have a `parameters` field — instead it uses individual typed fields (`tiers`, `flat_unit_price`, `sla_threshold_pct`, etc.).

The typed approach is **better** than a generic `dict` (more Pydantic validation). But the architecture doc references `rule.parameters["cap_amount"]` in the `CapRateEvaluator` pseudocode ([line 355](file:///d:/SupplierGuard/ARCHITECTURE_v3.md#L355)), which doesn't exist. The actual code correctly uses `rule.cap_amount`.

**Fix:** Update the architecture document to reflect the actual typed fields approach. This is a doc-vs-code sync issue.

---

**PROBLEM 9: Duplicate arithmetic validation — conflicting tolerances**

The invoice extractor runs arithmetic checks **twice**:
1. `validate_invoice_arithmetic()` in [tools.py](file:///d:/SupplierGuard/backend/agents/invoice_extractor/tools.py#L54-L91) — uses `Decimal`, tolerance ₹0.05/line and ₹1.00/invoice
2. Inline code in [agent.py lines 107-117](file:///d:/SupplierGuard/backend/agents/invoice_extractor/agent.py#L107-L117) — uses `float`, tolerance ₹0.01/line

These can produce **contradicting** results: `tools.py` says "valid" (within ₹0.05), inline says "invalid" (beyond ₹0.01). The architecture says tolerance should be `₹0.01` per line and `₹1` per invoice.

**Fix:** Remove the inline float-based check entirely. Use only `validate_invoice_arithmetic()` with the proper Decimal-based logic. Tighten `tools.py` line tolerance to ₹0.01 to match architecture.

---

**PROBLEM 10: `unmapped_lines` stores dicts in cross_validator but architecture says `list[str]`**

[validator.py line 57](file:///d:/SupplierGuard/backend/agents/cross_validator/validator.py#L57):
```python
unmapped_lines.append({"line_id": item.line_id, "desc": item.raw_description})
```

But the `CrossValidationResult` schema says `unmapped_lines: List[str]`. The code then converts on line 92: `unmapped_lines=[u["line_id"] for u in unmapped_lines]`. This works but is fragile — the intermediate `unmapped_lines` variable is `list[dict]` while the output field is `list[str]`, sharing the same name.

**Fix:** Use separate variable names (e.g., `unmapped_line_details` for the dict version) to avoid confusion and bugs.

---

**PROBLEM 11: Cross-validator uses `raw_description` but architecture says use `description`**

Architecture v3 ([line 248](file:///d:/SupplierGuard/ARCHITECTURE_v3.md#L248)):
```python
fuzzy_score(item.description, rule.applies_to) >= 60
```

But the actual `LineItem` schema has `raw_description`, not `description`. The [validator.py](file:///d:/SupplierGuard/backend/agents/cross_validator/validator.py#L51) correctly uses `item.raw_description`. Architecture doc needs updating, or `mapped_contract_item` should also be matched against (since it's the LLM's mapping of the raw description to contract terminology).

**Fix:** Also fuzzy-match against `item.mapped_contract_item` — this is the LLM's best guess of what contract item this line refers to, and will produce much better candidate matches than raw invoice text.

---

**PROBLEM 12: `LLM.generate_content()` calls are synchronous, blocking the async event loop**

Every agent uses `llm.generate_content(...)` which calls `self.real_model.generate_content(...)` — this is a **synchronous** blocking call inside an `async def` function. This blocks the entire Python event loop during every LLM call (which can take 5-30 seconds each).

**Fix:** Wrap in `asyncio.to_thread()` or use the async Gemini client. This matters especially when running in production with FastAPI handling concurrent requests.

---

### 🟡 MEDIUM SEVERITY PROBLEMS (Future scalability / correctness)

---

**PROBLEM 13: No LLM call for cross-reference resolution (architecture step 4)**

Architecture v3 Node 1 step 4 ([line 123-127](file:///d:/SupplierGuard/ARCHITECTURE_v3.md#L123-L127)):
> *"Resolution pass (1 additional LLM call, given the FULL contract_text): For any rule with an unresolved cross-reference, re-extract..."*

This is **not implemented**. [contract_parser/agent.py](file:///d:/SupplierGuard/backend/agents/contract_parser/agent.py) goes straight from per-section extraction → merge → verify. Cross-references like "see Schedule B" are never resolved.

**Fix:** After merging, scan rules for unresolved references (e.g., `clause_text` containing "see Section", "as defined in", "per Schedule"). For those rules, make one additional LLM call with the full contract text for resolution. The prompt file `prompt_resolve_refs.txt` already exists but is **never used** in the code.

---

**PROBLEM 14: `is_relevant_section()` filter function exists but is NEVER CALLED**

[contract_parser/tools.py](file:///d:/SupplierGuard/backend/agents/contract_parser/tools.py#L60-L81) defines `is_relevant_section()`, and `split_contract_to_sections()` also exists. But the agent uses `split_by_sections` from `backend.services.contract_chunker`, and `is_relevant_section` is never imported or called.

Architecture v3 says *"Extract ALL pricing-relevant rules found in this chunk"* — full extraction means we should NOT filter sections. But having dead code causes confusion.

**Fix:** Either delete `is_relevant_section()` and `split_contract_to_sections()` from tools.py (since they're unused dead code), or document why they're kept as utilities.

---

**PROBLEM 15: Pipeline singleton is not async-safe**

[pipeline.py lines 58-67](file:///d:/SupplierGuard/backend/agents/pipeline.py#L58-L67):
```python
_pipeline = None
def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline
```

No locking. If two FastAPI requests hit `get_pipeline()` simultaneously, you could get double-initialization or race conditions.

**Fix:** Use `threading.Lock()` or `asyncio.Lock()` to guard the singleton creation.

---

**PROBLEM 16: `compliance_score` is never computed**

Architecture v3 ([line 407](file:///d:/SupplierGuard/ARCHITECTURE_v3.md#L407)):
> `compliance_score = (compliant_lines / total_lines) * 100`

This field doesn't exist in `AuditSummary` schema and is never calculated. The `AuditSummary` has `compliant_lines` and `total_lines_audited` as raw counts, but no `compliance_score` percentage field. The frontend would need to compute this itself.

**Fix:** Add `compliance_score: float` to `AuditSummary` and compute it in the report generator.

---

**PROBLEM 17: Conditional edges and regular edges conflict in the architecture's graph definition**

The architecture doc ([lines 456-470](file:///d:/SupplierGuard/ARCHITECTURE_v3.md#L456-L470)) adds BOTH conditional edges (for halt checking) AND regular edges for the same nodes:
```python
graph.add_conditional_edges("cross_validator", ...)
graph.add_edge("cross_validator", "compliance_checker")  # conflicts!
```

LangGraph doesn't allow both conditional and regular edges from the same node. The implementation correctly uses only conditional edges, but the architecture doc is self-contradictory.

**Fix:** Update the architecture doc to show only conditional edges (which is what the code does correctly).

---

**PROBLEM 18: `DATA_SCHEMAS.md` is stale — doesn't match v3 schemas**

[DATA_SCHEMAS.md](file:///d:/SupplierGuard/DATA_SCHEMAS.md) still shows v1/v2 schemas:
- `PipelineState` is missing `cross_validation`, `candidate_map`, `data_required_flags`, `review_flags` fields
- `LineItem` is missing `extraction_confidence`, `arithmetic_valid`, `milestone_date`, `milestone_status` v3 fields
- `Discrepancy` is missing `critic_status`, `critic_reasoning`, `narrative` v3 fields
- `AuditReport` shows v3 fields but `PipelineState` doesn't
- The `Discrepancy` model in DATA_SCHEMAS uses `"ACCEPT"` as a recommendation but schemas.py uses `"REVIEW"` — inconsistency

**Fix:** Regenerate DATA_SCHEMAS.md from the actual `schemas.py` Pydantic models.

---

**PROBLEM 19: `hallucinated_clause` error type is not in `AgentError.error_type` enum**

[contract_parser/agent.py line 112](file:///d:/SupplierGuard/backend/agents/contract_parser/agent.py#L112) creates an error with `"error_type": "hallucinated_clause"`, but this is appended as a raw dict, not an `AgentError` instance. The `AgentError` schema's `error_type` Literal doesn't include `"hallucinated_clause"`.

**Fix:** Either add `"hallucinated_clause"` to the `AgentError.error_type` Literal, or use the existing `"validation_failed"` type with a descriptive message. Use `AgentError()` instances, not raw dicts.

---

**PROBLEM 20: No timeout/circuit-breaker on LLM calls**

Each agent retries LLM failures (via `LLM_RETRY_ATTEMPTS = 3`), but there's no **timeout** per call. A stuck Gemini API call could block the pipeline indefinitely. With many sections × invoices × rules × critic calls, the total pipeline time is unbounded.

**Fix:** Add `asyncio.wait_for(llm_call, timeout=60)` wrappers. Add a global pipeline timeout (e.g., 10 minutes). Track total LLM call count and abort if it exceeds a maximum (prevent runaway loops with huge contracts).

---

### 📋 IMPLEMENTATION PRIORITY ORDER

| Priority | Problem # | What | Effort |
|---|---|---|---|
| 🔴 P0 | 1 | Fix pipeline to parallel/independent execution | Medium |
| 🔴 P0 | 3 | Implement `AnnualAdjustmentEvaluator`, fix `EVALUATOR_MAP` | Medium |
| 🔴 P0 | 5, 9 | Fix float→Decimal, remove duplicate arithmetic check | Small |
| 🔴 P0 | 6 | Enforce 0.75 confidence threshold gate | Small |
| 🔴 P0 | 4 | Fix `MilestonePenaltyEvaluator` zero-return | Small |
| 🟠 P1 | 2 | Remove rulebook dependency from invoice extractor | Small |
| 🟠 P1 | 12 | Make LLM calls non-blocking (async) | Medium |
| 🟠 P1 | 13 | Implement cross-reference resolution pass | Medium |
| 🟠 P1 | 11 | Add `mapped_contract_item` to fuzzy matching | Small |
| 🟡 P2 | 7, 8 | Sync schema field names between arch doc and code | Small |
| 🟡 P2 | 18 | Regenerate DATA_SCHEMAS.md | Small |
| 🟡 P2 | 16 | Add compliance_score to AuditSummary | Small |
| 🟡 P2 | 20 | Add timeouts and circuit breakers | Medium |
| 🟡 P2 | 14, 15, 17, 19 | Dead code cleanup, singleton safety, doc fixes | Small |

---

Want me to start implementing these fixes? I'd suggest tackling P0s first — they directly affect audit correctness. I can do them in one session.
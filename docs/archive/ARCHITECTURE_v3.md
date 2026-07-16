# ARCHITECTURE.md — SupplierGuard System Design (v3)
# Canonical reference — supersedes v1 and v2 master context architecture sections
# Core principle: independent extraction → deterministic cross-validation → bounded LLM judgment → Python-only arithmetic

---

## 0. WHAT CHANGED FROM v1/v2 AND WHY

| Issue in v1/v2 | Fix in v3 |
|---|---|
| Contract Parser depended on Invoice Extractor output, which depended on Contract Parser output (circular) | Both run in parallel, fully independent. No cross-dependency at extraction time. |
| Invoice-driven RAG only retrieves contract sections matching what's billed — can't detect *omitted* charges (e.g. missing SLA penalty never billed) | Contract Parser does FULL extraction of every pricing rule, regardless of what's on the invoice |
| Two-pass draft/critic rule-matching tripled LLM calls for marginal gain | Single-pass matching, but pre-filtered by a deterministic fuzzy-match candidate list (cheaper AND more accurate) |
| Critic could silently override a correct Python-computed discrepancy → "log as compliant line" (black box, breaks auditability) | Critic can only output CONFIRMED or NEEDS_HUMAN_REVIEW. It can never erase a finding — only flag it for a human |
| No structural check for "rule exists but invoice has no data to evaluate it" until deep in compliance checking | New Stage 1 cross-validation gate catches this BEFORE any compliance LLM calls, deterministically |
| Arithmetic self-check (qty × price = total) existed but wasn't used to gate confidence | Now used immediately — failed arithmetic = automatic low-confidence flag on that line item |

---

## 1. SYSTEM OVERVIEW

SupplierGuard is a 6-node LangGraph pipeline. Nodes 1–2 run in parallel (fan-out/fan-in).
Node 3 is pure Python (no LLM). Nodes 4–6 are sequential.

```
                    ┌─────────────────────┐
                    │   START              │
                    └──────────┬───────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                  ▼
   ┌────────────────────┐           ┌────────────────────────┐
   │ Node 1:             │           │ Node 2:                 │
   │ Contract Parser     │           │ Invoice Extractor        │
   │ (LLM, full extract) │           │ (LLM + deterministic     │
   │                     │           │  arithmetic check)        │
   └──────────┬──────────┘           └───────────┬─────────────┘
              │                                   │
              └────────────────┬──────────────────┘
                                ▼
                  ┌──────────────────────────────┐
                  │ Node 3: Cross-Validation Gate  │
                  │ (PURE PYTHON — no LLM)         │
                  │ fuzzy-match line items↔rules   │
                  │ flag unmapped / no-data /      │
                  │ low-confidence items           │
                  └──────────────┬─────────────────┘
                                  ▼
                  ┌──────────────────────────────┐
                  │ Node 4: Compliance Checker     │
                  │  4a. Rule matching (LLM,       │
                  │      pre-filtered candidates)  │
                  │  4b. Arithmetic (Python only)  │
                  │  4c. Critic (LLM, flag-only)   │
                  └──────────────┬─────────────────┘
                                  ▼
                  ┌──────────────────────────────┐
                  │ Node 5: Report Generator (LLM) │
                  └──────────────┬─────────────────┘
                                  ▼
                              ┌───────┐
                              │  END  │
                              └───────┘
```

---

## 2. SHARED STATE (PipelineState)

```python
# models/schemas.py

from typing import TypedDict, Optional, Literal
from pydantic import BaseModel

class PipelineState(TypedDict):
    audit_id:            str
    contract_path:       str
    invoice_paths:       list[str]
    contract_text:       str
    invoice_texts:       list[str]

    # Node 1 output
    rulebook:            Optional[dict]        # ContractRulebook

    # Node 2 output
    invoice_data:        Optional[list[dict]]  # InvoiceData[]

    # Node 3 output (NEW)
    cross_validation:    Optional[dict]        # CrossValidationResult
    candidate_map:       Optional[dict]        # {line_id: [rule_id, ...]}

    # Node 4 output
    discrepancies:       Optional[list[dict]]  # DiscrepancyList
    data_required_flags: Optional[list[dict]]  # DataRequiredFlag[]
    review_flags:        Optional[list[dict]]  # ReviewFlag[] (from critic)

    # Node 5 output
    audit_report:        Optional[dict]

    errors:              list[dict]
    current_agent:       str
    halt:                bool
```

---

## 3. NODE 1 — CONTRACT PARSER (Full Extraction)

**File:** `backend/agents/contract_parser/agent.py`
**Prompt:** `backend/agents/contract_parser/prompt.txt`

### Process
```
1. Chunk contract_text by section (heading-based, ~1500-2500 tokens per chunk,
   with 200-token overlap between adjacent chunks to avoid splitting a clause)
2. For EACH chunk:
     - LLM call with response_schema = list[PricingRule]
     - Extract ALL pricing-relevant rules found in this chunk
     - If chunk references another section ("see Schedule B"), note the
       reference; do NOT attempt cross-chunk resolution yet
3. Merge all extracted rules into one list
4. Resolution pass (1 additional LLM call, given the FULL contract_text):
     - For any rule with an unresolved cross-reference, re-extract using
       full contract_text as context
     - Deduplicate rules that appear in multiple chunks (same clause,
       different chunk overlap)
5. Validate merged list against ContractRulebook Pydantic schema
6. If validation fails → retry once with correction prompt
7. If second failure → AgentError, halt=True
8. Write state["rulebook"]
```

### Why full extraction, not invoice-driven RAG
An audit must detect BOTH overcharges AND omissions (e.g. a mandatory SLA
penalty clause exists but was never applied/billed). Invoice-driven retrieval
can only ever find rules matching what's already billed — it is structurally
blind to omissions. Full extraction costs more LLM calls but is the only
approach that can find "the rule that should have fired but didn't."

### Each PricingRule includes
```python
class PricingRule(BaseModel):
    rule_id: str                  # R001, R002, ...
    rule_type: Literal["volume_tier","flat_rate","sla_penalty",
                        "early_payment_discount","bundle_discount",
                        "cap_rate","annual_adjustment",
                        "milestone_penalty","unknown"]
    description: str              # plain-English summary
    applies_to: str                # item/category this rule governs
    clause_text: str               # EXACT quote from contract_text
    clause_reference: str           # e.g. "Section 4.2"
    # Type-specific fields (NOT a generic dict — Pydantic validates each):
    flat_unit_price: Decimal | None
    tiers: list[VolumeTier] | None
    cap_amount: Decimal | None
    sla_threshold_pct: float | None
    penalty_pct: Decimal | None
    discount_pct: Decimal | None
    bundle_threshold: Decimal | None
    bundle_price: Decimal | None
    # ... (see schemas.py PricingRule for full list)
    extraction_confidence: float    # 0.0-1.0
```

### Verification step (deterministic, no LLM)
After validation, Python checks: does `clause_text` for every rule appear
as a substring (normalized whitespace) of `contract_text`? If not →
set `extraction_confidence = 0.0` and add to a `hallucinated_clause`
list in `errors`. This catches the LLM inventing or paraphrasing quotes.

---

## 4. NODE 2 — INVOICE EXTRACTOR

**File:** `backend/agents/invoice_extractor/agent.py`
**Prompt:** `backend/agents/invoice_extractor/prompt.txt`

### Process
```
1. For each invoice text (independent — no rulebook access):
   a. Extract header: invoice_id, date, billing_period, supplier_name, total
   b. Extract line items: description, quantity, unit_price, line_total
   c. Extract notes: footer text, milestone status statements,
      "Penalties Applied: X" lines, SLA actual performance figures
      if stated
   d. Extract any explicit fields useful for conditional rules:
      sla_actual_pct, milestone_date, milestone_status (if present
      anywhere in the document)
2. DETERMINISTIC arithmetic check (Python, tools.py):
     computed_total = sum(qty * unit_price for each line)
     if |computed_total - invoice_total| > ₹1 → invoice-level flag
     for each line: if |qty*unit_price - line_total| > ₹0.01 → line-level flag
3. Any line/invoice failing the arithmetic check gets
   extraction_confidence capped at 0.5, regardless of LLM-reported confidence
4. Validate against InvoiceData Pydantic schema
5. Write state["invoice_data"]
```

### InvoiceData / LineItem fields (key additions vs v1/v2)
```python
class LineItem(BaseModel):
    line_id: str
    description: str
    quantity: float
    unit_price_charged: float
    line_total_charged: float
    extraction_confidence: float
    arithmetic_valid: bool
    # Conditional-rule support data (Bug 2/4 from master context)
    sla_actual_pct: Optional[float] = None
    milestone_date: Optional[str] = None
    milestone_status: Optional[str] = None

class InvoiceData(BaseModel):
    invoice_id: str
    supplier_name: str
    billing_period: str
    invoice_total: float
    line_items: list[LineItem]
    notes: str = ""
    milestone_statements: list[str] = []
    penalties_applied: Optional[float] = None
    invoice_arithmetic_valid: bool
```

---

## 5. NODE 3 — CROSS-VALIDATION GATE (Pure Python, NEW)

**File:** `backend/agents/cross_validator/validator.py`
**No LLM calls in this node.**

This is the most important new addition. It runs deterministic checks
BEFORE any interpretation-stage LLM calls, dramatically cutting the
search space for Node 4 and catching whole classes of error structurally.

### Process
```python
def cross_validate(rulebook: ContractRulebook,
                    invoices: list[InvoiceData]) -> CrossValidationResult:

    candidate_map: dict[str, list[str]] = {}   # line_id -> [rule_id,...]
    unmapped_lines: list[str] = []
    rules_without_data: list[dict] = []        # conditional rules, no invoice data
    rules_never_billed: list[str] = []          # rule exists, nothing matches

    matched_rule_ids = set()

    for invoice in invoices:
        for item in invoice.line_items:
            # 1. Fuzzy candidate matching (rapidfuzz token_sort_ratio,
            #    threshold 60 — DELIBERATELY LOOSE; this is a candidate
            #    LIST for the LLM, not a final decision)
            candidates = [
                rule.rule_id for rule in rulebook.rules
                if fuzzy_score(item.description, rule.applies_to) >= 60
                or fuzzy_score(item.description, rule.description) >= 60
            ]
            if not candidates:
                unmapped_lines.append(item.line_id)
            else:
                candidate_map[item.line_id] = candidates
                matched_rule_ids.update(candidates)

    # 2. Conditional rules without supporting data (Bug 2 — caught HERE,
    #    structurally, not per-line during compliance checking)
    CONDITIONAL_TYPES = {"sla_penalty", "milestone_penalty"}
    for rule in rulebook.rules:
        if rule.rule_type in CONDITIONAL_TYPES:
            has_data = any(
                item.sla_actual_pct is not None or item.milestone_date is not None
                for invoice in invoices for item in invoice.line_items
                if rule.rule_id in candidate_map.get(item.line_id, [])
            )
            if not has_data:
                rules_without_data.append({
                    "rule_id": rule.rule_id,
                    "clause_section": rule.clause_section,
                    "reason": "Conditional rule has no corresponding "
                              "performance data (sla_actual_pct / "
                              "milestone_date) in any invoice"
                })

    # 3. Rules that exist in contract but matched NOTHING on any invoice
    #    (potential omission — flagged for report, not auto-discrepancy)
    rules_never_billed = [
        r.rule_id for r in rulebook.rules
        if r.rule_id not in matched_rule_ids
        and r.rule_type not in CONDITIONAL_TYPES  # those handled above
    ]

    return CrossValidationResult(
        candidate_map=candidate_map,
        unmapped_lines=unmapped_lines,
        rules_without_data=rules_without_data,
        rules_never_billed=rules_never_billed,
    )
```

### Outputs feed forward
- `candidate_map` → Node 4a uses this to give the LLM a SHORT pre-filtered
  list of candidate rules per line item (instead of the whole rulebook),
  which is both cheaper and reduces mismatch errors.
- `unmapped_lines` → these line items skip Node 4 entirely, go straight
  to `review_flags` with reason "no plausible contract rule found —
  possible out-of-contract item or extraction error"
- `rules_without_data` → these become `DataRequiredFlag` objects directly
  (Bug 2 fix), bypassing Node 4 entirely — no LLM ever asked to evaluate
  a conditional rule with no data
- `rules_never_billed` → surfaced in the final report as
  "rules in contract with no matching invoice activity" — informational,
  human reviews whether this is a missed charge or simply not applicable
  this period

---

## 6. NODE 4 — COMPLIANCE CHECKER

**File:** `backend/agents/compliance_checker/agent.py`
**Rule engine:** `backend/agents/compliance_checker/rule_engine.py`

### 4a. Rule Matching (LLM, single pass, pre-filtered)
```
For each line_item NOT in unmapped_lines:
  candidates = candidate_map[line_item.line_id]   # e.g. ["R003","R007"]
  LLM call: "Given this line item and these candidate rules ONLY
             (full text provided), which apply? Return rule_ids
             with per-rule confidence 0.0-1.0 and brief justification."
  → Validate: every returned rule_id must be in `candidates`
    (hard constraint — LLM cannot select outside the pre-filtered set)
  → If ALL candidates score < RULE_MATCH_CONFIDENCE_THRESHOLD (0.75):
      line item → review_flags, reason "no high-confidence rule match"
```

Single pass is sufficient here because Node 3 already did the heavy
filtering — the LLM is choosing among 1-4 plausible candidates, not
searching the whole rulebook. This is cheaper than v1's two-pass
draft/critic AND more accurate, because the candidate set is
pre-validated to be relevant.

### 4b. Rule Application (Python only — UNCHANGED principle from v1/v2)
```python
class RuleEvaluator(ABC):
    @abstractmethod
    def compute_expected(self, line_item: LineItem, rule: PricingRule) -> Decimal: ...

# Evaluator classes — ALL must be implemented before go-live:
EVALUATOR_MAP = {
    "volume_tier":            VolumeTierEvaluator,
    "flat_rate":              FlatRateEvaluator,
    "cap_rate":               CapRateEvaluator,          # Bug 1 fix applied
    "sla_penalty":            SLAPenaltyEvaluator,
    "early_payment_discount": EarlyPaymentDiscountEvaluator,
    "bundle_discount":        BundleDiscountEvaluator,
    "annual_adjustment":      AnnualAdjustmentEvaluator,
    "milestone_penalty":      MilestonePenaltyEvaluator, # Bug 2 fix applied
}

# CapRateEvaluator — Bug 1 corrected version
class CapRateEvaluator(RuleEvaluator):
    def compute_expected(self, line_item, rule) -> Decimal:
        charged_per_unit = Decimal(str(line_item.unit_price_charged))
        cap = Decimal(str(rule.cap_amount))  # typed field, not parameters dict
        expected_per_unit = min(charged_per_unit, cap)
        return expected_per_unit * Decimal(str(line_item.quantity))

for each (line_item, matched_rule) where rule confidence >= 0.75:
    evaluator = EVALUATOR_MAP[matched_rule.rule_type]()
    expected = evaluator.compute_expected(line_item, matched_rule)
    delta = expected - Decimal(str(line_item.line_total_charged))
    if abs(delta) < MINIMUM_MATERIAL_THRESHOLD:  # ₹100
        continue   # compliant, no finding
    → create candidate Discrepancy(rule_id, clause_text, expected,
                                    charged, delta, confidence=rule.confidence)
```

### 4c. Critic — FLAG ONLY, NEVER OVERRIDE (key fix from v1)
```
For each candidate Discrepancy:
  LLM call: "Given this clause text and this computed discrepancy,
             does the arithmetic interpretation align with the
             contract clause's actual scope and conditions?
             Respond CONFIRMED or NEEDS_HUMAN_REVIEW with reasoning."

  - CONFIRMED        → append to state["discrepancies"]
  - NEEDS_HUMAN_REVIEW → ALSO append to state["discrepancies"]
                         (the number is NOT deleted)
                         AND append to state["review_flags"]
                         with the critic's reasoning attached

The critic NEVER removes a Python-computed finding. It can only add
an annotation. This preserves full auditability — every number that
reaches the report is traceable to rule_engine.py, with or without
a critic annotation.
```

### Final validation
Every Discrepancy MUST have: `rule_id, clause_text, clause_section,
expected, charged, delta, confidence, critic_status`.
Validate `DiscrepancyList` against Pydantic schema → write to state.

---

## 7. NODE 5 — REPORT GENERATOR

**File:** `backend/agents/report_generator/agent.py`

### Process
```
1. Aggregate stats:
   total_leakage    = sum(d.delta for d in discrepancies if d.delta < 0)
   total_lines      = sum(len(inv.line_items) for inv in invoices)
   disputed_line_ids = {d.line_id for d in discrepancies}
   compliant_lines  = total_lines - len(disputed_line_ids)
   compliance_score = (compliant_lines / total_lines) * 100   # Bug 3 fix

2. Sort discrepancies: CRITICAL → HIGH → MEDIUM
   (CRITICAL >= ₹10,000 | HIGH >= ₹1,000 | MEDIUM < ₹1,000 — all |delta|)

3. Recommendation (deterministic):
   overcharge/missing_credit/unapplied_penalty + CRITICAL/HIGH → DISPUTE
   overcharge/missing_credit/unapplied_penalty + MEDIUM        → MONITOR
   period_mismatch/incorrect_rate                              → ESCALATE
   review_flags items                                          → REVIEW

4. LLM call: executive_summary (2-3 sentences, CFO-readable)
5. LLM call (per finding, batched if possible): plain-English narrative

6. Report sections:
   - executive_summary
   - confirmed_discrepancies   (critic_status = CONFIRMED)
   - flagged_for_review         (critic_status = NEEDS_HUMAN_REVIEW,
                                  AND unmapped_lines from Node 3)
   - data_required_flags        (from Node 3, conditional rules w/o data)
   - rules_never_billed          (informational, from Node 3)
   - compliance_score, total_leakage, total_lines, compliant_lines

7. Validate AuditReport schema → persist → status = COMPLETE
```

---

## 8. LANGGRAPH GRAPH DEFINITION

```python
from langgraph.graph import StateGraph, END

def build_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)

    # Single entry node runs both extractors sequentially (logically independent).
    # Neither reads the other's output. One's failure doesn't block the other.
    graph.add_node("parallel_extractors", run_parallel_extractors)
    graph.add_node("cross_validator",    run_cross_validator)   # pure Python
    graph.add_node("compliance_checker", run_compliance_checker)
    graph.add_node("report_generator",   run_report_generator)

    graph.set_entry_point("parallel_extractors")

    # Conditional edges (halt check) after each node — NO regular edges
    # (LangGraph doesn't allow both conditional and regular from same node)
    graph.add_conditional_edges(
        "parallel_extractors",
        lambda s: END if s.get("halt") else "cross_validator"
    )
    graph.add_conditional_edges(
        "cross_validator",
        lambda s: END if s.get("halt") else "compliance_checker"
    )
    graph.add_conditional_edges(
        "compliance_checker",
        lambda s: END if s.get("halt") else "report_generator"
    )
    graph.add_edge("report_generator", END)

    return graph.compile()
```

> Note: LangGraph's exact fan-out/fan-in syntax depends on the version
> installed — if true parallel execution isn't available, run
> contract_parser and invoice_extractor as two sequential nodes at the
> start (order doesn't matter since they're now independent) before
> cross_validator. Either gives correct results; true parallelism just
> saves wall-clock time.

---

## 9. NEW/UPDATED PYDANTIC MODELS SUMMARY

```python
class CrossValidationResult(BaseModel):
    candidate_map: dict[str, list[str]]
    unmapped_lines: list[str]
    rules_without_data: list[dict]
    rules_never_billed: list[str]

class DataRequiredFlag(BaseModel):
    rule_id: str
    clause_section: str
    reason: str

class ReviewFlag(BaseModel):
    line_id: Optional[str] = None
    rule_id: Optional[str] = None
    reason: str
    critic_reasoning: Optional[str] = None

class Discrepancy(BaseModel):
    rule_id: str
    line_id: str
    clause_text: str
    clause_section: str
    expected: Decimal
    charged: Decimal
    delta: Decimal
    confidence: float
    severity: Literal["CRITICAL","HIGH","MEDIUM"]
    recommendation: Literal["DISPUTE","ESCALATE","MONITOR","REVIEW"]
    critic_status: Literal["CONFIRMED","NEEDS_HUMAN_REVIEW"]
    critic_reasoning: Optional[str] = None
    narrative: Optional[str] = None
```

---

## 10. NON-NEGOTIABLE RULES (carried forward + new)

1.  Contract Parser and Invoice Extractor run independently — neither
    reads the other's output
2.  Contract Parser extracts EVERY rule, not just invoice-relevant ones
3.  Every PricingRule.clause_text must be a verified substring of
    contract_text (Python check) — fails → confidence = 0.0
4.  Cross-validation gate runs BEFORE any Node 4 LLM call
5.  Conditional rules (sla_penalty, milestone_penalty) without
    supporting invoice data NEVER reach the compliance LLM — they
    become DataRequiredFlag at Node 3
6.  Node 4a rule matching restricted to Node 3's candidate_map —
    LLM cannot select a rule outside the pre-filtered candidates
7.  LLM NEVER computes financial arithmetic — rule_engine.py always does
8.  All monetary values: Python Decimal, never float
9.  Critic (4c) can ONLY add NEEDS_HUMAN_REVIEW annotations — it can
    never remove or alter a computed Discrepancy
10. Every Discrepancy has: rule_id, clause_text, clause_section,
    expected, charged, delta, confidence, critic_status
11. RULE_MATCH_CONFIDENCE_THRESHOLD = 0.75; below → review_flags
12. MINIMUM_MATERIAL_THRESHOLD = ₹100; below → not a finding
13. Compliance score = compliant_lines / total_lines, derived from
    discrepancies + unmapped_lines, never a hardcoded/assumed value
14. All LLM calls use response_mime_type="application/json" +
    Pydantic-derived JSON schema
15. All prompts live in .txt files, never hardcoded in Python

---

END OF ARCHITECTURE v3

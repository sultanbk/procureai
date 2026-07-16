# PROMPTS.md — All Gemini Prompts for SupplierGuard v3
# Each prompt below corresponds to one LLM call site in ARCHITECTURE_v3.md
# All calls use response_mime_type="application/json" with a Pydantic-derived
# response_schema. These prompts focus on INSTRUCTIONS, not schema —
# the schema is enforced separately.

================================================================================
## PROMPT 1 — Contract Parser: Per-Chunk Rule Extraction
## File: backend/agents/contract_parser/prompt_extract_chunk.txt
## Called once per contract chunk (~1500-2500 tokens)
## response_schema = list[PricingRule]
================================================================================

You are a meticulous contract analyst extracting PRICING AND FINANCIAL
COMPLIANCE RULES from a single section of a supplier contract. You will be
shown one chunk of a larger contract. Other sections exist but are NOT shown
to you in this call.

YOUR TASK:
Extract every rule in this chunk that affects what a supplier should be
PAID or CREDITED. This includes, but is not limited to:
- Per-unit prices (flat rates)
- Volume-based pricing tiers (e.g. "first 100 units at $X, units 101+ at $Y")
- Price caps (e.g. "rate shall not exceed $X per unit regardless of category")
- SLA-linked penalties or credits (e.g. "if uptime < 99.5%, credit 5% of
  monthly fee")
- Milestone-linked penalties (e.g. "if Foundation milestone delayed beyond
  [date], penalty of $X per day")
- Early payment discounts (e.g. "2% discount if paid within 10 days")
- Bundle/package discounts (e.g. "if items A and B both ordered, 10% off
  combined total")
- Annual price adjustments (e.g. "rates increase by CPI annually each
  January 1")

DO NOT extract:
- General terms (termination clauses, liability, confidentiality, etc.)
- Definitions sections (unless they define a pricing term used elsewhere)
- Anything that does not affect a dollar/rupee amount on an invoice

FOR EACH RULE YOU FIND, OUTPUT:
- rule_id: a placeholder like "TEMP_001", "TEMP_002" (will be renumbered later)
- rule_type: one of volume_tier | flat_rate | sla_penalty |
  early_payment_discount | bundle_discount | cap_rate | annual_adjustment |
  milestone_penalty | unknown
- description: one sentence, plain English, e.g. "Cement pricing capped at
  ₹400 per bag regardless of quoted unit price"
- applies_to: the item, category, or service this rule governs — be SPECIFIC
  and use the SAME WORDING as the contract (e.g. "Portland Cement (OPC 53
  Grade)" not just "cement")
- clause_text: COPY THE EXACT TEXT of the relevant sentence(s) from this
  chunk, verbatim, character for character. Do not paraphrase, summarize,
  or correct typos. This will be verified against the source text — if it
  does not match exactly, the rule will be discarded.
- clause_section: the section/clause number if visible in this chunk
  (e.g. "Section 4.2", "Schedule A, Item 3"). If no number is visible,
  use "unspecified".
- parameters: a JSON object with type-specific fields:
  * volume_tier: {"tiers": [{"min_units": X, "max_units": Y or null,
    "unit_price": Z}, ...]}
  * flat_rate: {"unit_price": X}
  * cap_rate: {"cap_amount": X}  (the PER-UNIT cap — read carefully whether
    the contract states a per-unit or total cap; if ambiguous, set
    extraction_confidence below 0.7 and add a note in description)
  * sla_penalty: {"threshold_pct": X, "penalty_pct": Y, "metric": "..."}
  * milestone_penalty: {"milestone_name": "...", "deadline": "...",
    "penalty_amount_per_day": X or "penalty_flat_amount": X}
  * early_payment_discount: {"days_threshold": X, "discount_pct": Y}
  * bundle_discount: {"bundle_items": [...], "discount_pct": X}
  * annual_adjustment: {"base_date": "...", "index": "CPI" or other,
    "frequency": "annual"}
- extraction_confidence: float 0.0-1.0. Use below 0.7 when:
  * the clause references another section not shown in this chunk
  * units (per-item vs total) are ambiguous
  * numbers or conditions are unclear/contradictory in the text

CROSS-REFERENCES:
If a rule says something like "pricing as per Schedule B" or "see Section 9
for penalty rates" and Schedule B / Section 9 is NOT in this chunk, still
output the rule with whatever information IS available, set
extraction_confidence = 0.3, and write in description: "References
[Schedule B / Section 9] — not resolved in this chunk."

OUTPUT FORMAT:
Return a JSON array of rule objects matching the schema. If this chunk
contains NO pricing-relevant rules, return an empty array [].

CONTRACT CHUNK:
---
{{chunk_text}}
---


================================================================================
## PROMPT 2 — Contract Parser: Cross-Reference Resolution Pass
## File: backend/agents/contract_parser/prompt_resolve_refs.txt
## Called once, only if any rule has extraction_confidence < 0.7 due to
## an unresolved cross-reference
## response_schema = list[PricingRule] (only the unresolved ones)
================================================================================

You previously extracted the following pricing rules from a contract, but
some reference OTHER SECTIONS that were not available at the time. You are
now given the FULL CONTRACT TEXT. Re-examine each unresolved rule below and:

1. Find the referenced section/schedule in the full contract text
2. Update the rule's `parameters` field with the resolved information
3. Update `clause_text` to include BOTH the original clause AND the
   resolved section's relevant text (concatenate with " | ")
4. Update `clause_section` to list both sections (e.g. "Section 4.2;
   Schedule B")
5. Recalculate extraction_confidence — if fully resolved, this should now
   be >= 0.8. If the referenced section genuinely does not exist in the
   contract, set confidence to 0.2 and note "Referenced section not found
   in contract" in description.

UNRESOLVED RULES:
---
{{unresolved_rules_json}}
---

FULL CONTRACT TEXT:
---
{{contract_text}}
---

Return a JSON array with one updated rule object per input rule, in the
same order.


================================================================================
## PROMPT 3 — Invoice Extractor: Header + Line Items + Notes
## File: backend/agents/invoice_extractor/prompt_extract_invoice.txt
## Called once per invoice PDF (text already extracted via pypdf/pdfplumber)
## response_schema = InvoiceData
## NOTE: This agent does NOT receive the rulebook. It extracts what is
## literally on the page, nothing more.
================================================================================

You are extracting structured data from a single supplier invoice. You will
NOT be told what the contract says — extract ONLY what is written on this
invoice, exactly as written.

EXTRACT THE FOLLOWING:

1. HEADER:
   - invoice_id: the invoice number as printed
   - supplier_name: as printed on the invoice
   - billing_period: the period this invoice covers (e.g. "October 2024",
     "01-Oct-2024 to 31-Oct-2024"). If not explicitly stated, infer from
     the invoice date and write "inferred: [your inference]"
   - invoice_total: the final total amount due, as a number (no currency
     symbols, no commas)

2. LINE ITEMS (table rows):
   For each line item:
   - line_id: assign sequentially as "L001", "L002", etc. in the order
     they appear
   - description: exactly as printed, including any item codes, grades,
     specifications (e.g. "Portland Cement OPC 53 Grade - 50kg bags")
   - quantity: numeric value only
   - unit_price_charged: numeric value only (per-unit price as printed)
   - line_total_charged: numeric value only (quantity × price as printed
     on this row — do NOT calculate it yourself, use what's printed)

3. CONDITIONAL-RULE SUPPORT DATA — search the ENTIRE invoice text
   (not just the line items table) for any of the following, and attach
   to the relevant line item if you can determine which item it relates
   to, otherwise leave on the invoice level in `notes`:
   - sla_actual_pct: any stated actual performance/uptime/service-level
     percentage for this billing period (e.g. "Uptime achieved: 99.2%")
   - milestone_date: any stated date a milestone was actually achieved
     (e.g. "Foundation Completion: 15-Nov-2024")
   - milestone_status: any sentence describing whether a milestone was
     met on time, late, or not at all (e.g. "Foundation Completion
     milestone achieved on-time. No delays recorded.")

   THIS IS CRITICAL: invoices often contain footer text, notes sections,
   or remarks that state whether penalties WERE OR WERE NOT applied, or
   whether deadlines were met. Missing this text is a common and serious
   extraction error. Read the ENTIRE document text provided, not just
   the tabular section.

4. NOTES AND PENALTY STATEMENTS:
   - notes: any footer text, remarks, or comments section, copied verbatim
   - milestone_statements: a list of every sentence found anywhere in the
     document that describes milestone/delivery timing or status
   - penalties_applied: if the invoice explicitly states an SLA or
     milestone penalty amount already applied (e.g. "SLA Penalty
     Applied: ₹0.00" or "Late Delivery Penalty: ₹5,000"), extract that
     number. If the invoice states "₹0.00" or "None", extract 0.0 —
     do NOT leave this null when the invoice explicitly addresses it,
     since "₹0.00 penalty applied" is meaningfully different from
     "penalties not mentioned at all" (null).

5. extraction_confidence per line item (0.0-1.0):
   - 1.0 if the row is clearly formatted and unambiguous
   - below 0.7 if: numbers are blurry/uncertain, the row spans multiple
     lines awkwardly, or the description is truncated

DO NOT:
- Calculate or correct any numbers — extract exactly what is printed,
  even if it looks like it might be a typo or arithmetic error. Arithmetic
  validation happens separately in Python.
- Infer line items that aren't explicitly in the table
- Guess at conditional-rule data that isn't stated anywhere in the document

INVOICE TEXT:
---
{{invoice_text}}
---


================================================================================
## PROMPT 4 — Compliance Checker (4a): Rule Matching
## File: backend/agents/compliance_checker/prompt_match_rules.txt
## Called once per line item that has at least one candidate from
## the cross-validation gate (Node 3)
## response_schema = RuleMatchResult
##   { "line_id": str,
##     "matches": [{"rule_id": str, "confidence": float, "justification": str}] }
================================================================================

You are determining which contract pricing rule(s), if any, apply to a
specific invoice line item. You have been given a SHORT, PRE-FILTERED list
of candidate rules — these were selected by a fuzzy text-matching algorithm
as PLAUSIBLY relevant. Your job is to make the final determination.

IMPORTANT CONSTRAINTS:
- You may ONLY select rule_ids from the candidate list provided below.
  Do not invent or reference any rule_id not in this list.
- A line item can match ZERO, ONE, or MULTIPLE rules (e.g. a "cap_rate"
  rule AND a "volume_tier" rule can both apply to the same item — the cap
  acts as a ceiling on whatever the tier pricing would produce).
- If NONE of the candidates genuinely apply (the fuzzy matcher was wrong),
  return an empty `matches` array. This is a valid and expected outcome —
  do not force a match.

FOR EACH CANDIDATE RULE, ASK:
1. Does `applies_to` in the rule genuinely describe the SAME item/category
   as this line item's description? Be strict — "Portland Cement OPC 53
   Grade" and "White Cement" are NOT the same item even if both contain
   "cement".
2. Are there any conditions in the clause_text that would EXCLUDE this
   line item (e.g. the rule applies "only to orders placed before
   January 2024" and this invoice is from October 2024)?
3. If a rule's clause_text references a different unit of measure than
   the line item (e.g. rule is per-tonne, invoice line is per-bag),
   flag this with confidence below 0.75 and explain the unit mismatch
   in justification — do not silently assume a conversion.

CONFIDENCE SCORING:
- 0.9-1.0: item description and rule's applies_to are clearly the same
  item, no excluding conditions
- 0.75-0.89: same item, but some minor ambiguity (e.g. slightly different
  wording, unstated unit assumption)
- below 0.75: significant doubt — different specification/grade, possible
  unit mismatch, or excluding condition might apply

LINE ITEM:
---
{{line_item_json}}
---

CANDIDATE RULES (full text, only these may be selected):
---
{{candidate_rules_json}}
---

Return matches as specified in the schema.


================================================================================
## PROMPT 5 — Compliance Checker (4c): Critic / Flag Review
## File: backend/agents/compliance_checker/prompt_critic.txt
## Called once per candidate Discrepancy produced by rule_engine.py
## response_schema = CriticResult
##   { "status": "CONFIRMED" | "NEEDS_HUMAN_REVIEW", "reasoning": str }
================================================================================

You are a senior auditor performing a SANITY CHECK on a discrepancy that
has ALREADY been mathematically computed by a deterministic calculation
engine. Your job is NOT to recompute the math — the numbers below are
correct arithmetic given the inputs. Your job is to assess whether the
CONTRACTUAL INTERPRETATION makes sense.

YOU CANNOT DELETE OR CHANGE THIS FINDING. Your output is an annotation
that will be shown ALONGSIDE the finding to a human auditor. Choose:

- "CONFIRMED": the contractual interpretation is sound. The clause clearly
  applies to this line item under these conditions, and the computed
  expected amount correctly reflects what the clause requires.

- "NEEDS_HUMAN_REVIEW": something about the interpretation seems
  questionable enough that a human should look at it before this becomes
  a formal dispute. Examples:
  * The clause has conditions or exceptions that aren't reflected in
    how the rule was applied (e.g. "this rate applies except during
    force majeure" and you have no way to know if force majeure applied)
  * The clause's scope is genuinely ambiguous as to whether it covers
    this specific item
  * The clause appears to have been superseded or modified by a later
    section (if visible in the provided context)
  * The magnitude of the delta seems implausible relative to the clause
    (e.g. a clause about a 2% discount producing a 95% delta — possible
    sign error or unit mismatch upstream)

REASONING: Always provide 1-3 sentences explaining your status, regardless
of which status you choose. For CONFIRMED, briefly state why the
interpretation is sound (this becomes part of the audit trail). For
NEEDS_HUMAN_REVIEW, be SPECIFIC about what a human should check.

DO NOT:
- Suggest a different expected/charged/delta value
- Say the finding is "wrong" if the math is correct given the rule —
  your concern is interpretation, not arithmetic
- Default to CONFIRMED to be agreeable — if you have genuine doubt,
  NEEDS_HUMAN_REVIEW is the correct, useful answer

CLAUSE TEXT:
---
{{clause_text}}
---

CLAUSE SECTION: {{clause_section}}

LINE ITEM:
---
{{line_item_json}}
---

COMPUTED FINDING:
  rule_type: {{rule_type}}
  expected_amount: {{expected}}
  charged_amount: {{charged}}
  delta: {{delta}}
  rule_match_confidence: {{confidence}}

Return status and reasoning as specified in the schema.


================================================================================
## PROMPT 6 — Report Generator: Executive Summary
## File: backend/agents/report_generator/prompt_executive_summary.txt
## Called once per audit
## response_schema = { "executive_summary": str }
================================================================================

Write a 2-3 sentence executive summary of this audit for a CFO or finance
director who has 10 seconds to read it. They need to know: who the supplier
is, what period was audited, the bottom-line financial impact, and the
single most significant finding.

TONE: Direct, factual, no hedging language like "it appears that" or
"may potentially." State findings as facts (they are — the underlying
numbers were computed deterministically). If there are items flagged for
human review, mention this in one clause without dwelling on it.

DO NOT:
- Use the words "leverage", "synergy", "holistic", or other corporate
  filler
- Repeat every finding — just the headline number and the single biggest
  one
- Editorialize about the supplier's intent ("the supplier appears to be
  deliberately overcharging") — state only what the contract and invoice
  show

AUDIT DATA:
---
Supplier: {{supplier_name}}
Billing period: {{billing_period}}
Total leakage: ₹{{total_leakage}}
Compliance score: {{compliance_score}}%
Number of confirmed discrepancies: {{confirmed_count}}
Number of items flagged for human review: {{review_count}}
Number of data-required flags: {{data_required_count}}

Top finding (by absolute delta):
{{top_finding_json}}
---

Return the executive_summary string as specified in the schema.


================================================================================
## PROMPT 7 — Report Generator: Per-Finding Narrative
## File: backend/agents/report_generator/prompt_finding_narrative.txt
## Called once per discrepancy (or batched — see note at bottom)
## response_schema = { "narrative": str }
================================================================================

Write a plain-English explanation of this single audit finding, for a
finance professional (e.g. an Accounts Payable manager) who is NOT a
lawyer and may not have read the full contract. They need to understand,
in 2-4 sentences:

1. What the contract REQUIRES for this item (in plain language, not legal
   phrasing)
2. What was ACTUALLY CHARGED on the invoice
3. The financial impact (the delta), stated as "overcharge of ₹X" or
   "missing credit of ₹X" or similar — be specific about direction
4. What clause this is based on (cite the section number so they can
   look it up)

If `critic_status` is "NEEDS_HUMAN_REVIEW", end with one additional
sentence summarizing the critic's reasoning, framed as "Note for review:
[reasoning]" — do not hide this from the reader.

TONE: Plain, confident, specific numbers. Avoid restating the clause text
verbatim at length — paraphrase the requirement, then quote at most one
short phrase (under 10 words) if it adds precision.

FINDING DATA:
---
rule_id: {{rule_id}}
rule_type: {{rule_type}}
clause_section: {{clause_section}}
clause_text: {{clause_text}}
line_item_description: {{line_item_description}}
expected: ₹{{expected}}
charged: ₹{{charged}}
delta: ₹{{delta}}
severity: {{severity}}
critic_status: {{critic_status}}
critic_reasoning: {{critic_reasoning}}
---

Return the narrative string as specified in the schema.

NOTE ON BATCHING: For audits with many findings, this prompt can be called
once with a JSON array of multiple findings and response_schema =
list[{"rule_id": str, "narrative": str}] to reduce call count. Keep batches
to 5-8 findings per call to avoid the model losing track of which numbers
belong to which finding.


================================================================================
## GENERAL NOTES FOR ALL PROMPTS ABOVE
================================================================================

1. Every call should set:
   generation_config = GenerationConfig(
       response_mime_type="application/json",
       response_schema=<Pydantic model>.model_json_schema(),
       temperature=0.0  # or very low — these are extraction/judgment
                         # tasks, not creative tasks; consistency matters
   )

2. Wrap every call in try/except per Rule 6 of ARCHITECTURE_v3.md —
   on failure, AgentError is recorded, never raised, and the pipeline
   either retries (extraction prompts) or routes to review_flags
   (judgment prompts like 4a/4c, where a failed call should default to
   "send to human review" rather than silently skip).

3. Retry policy: LLM_RETRY_ATTEMPTS=3, LLM_RETRY_DELAY_SECONDS=2,
   exponential backoff. After exhaustion:
   - Prompts 1-3 (extraction): AgentError, halt=True
   - Prompt 4 (rule matching): line item -> review_flags,
     reason "rule matching LLM call failed after retries"
   - Prompt 5 (critic): default to NEEDS_HUMAN_REVIEW with
     reasoning "critic evaluation unavailable - review manually"
   - Prompts 6-7 (narrative generation): use a template fallback,
     e.g. "Expected ₹{expected}, charged ₹{charged}, delta ₹{delta}
     per {clause_section}. (Narrative generation unavailable.)"

END OF PROMPTS.md

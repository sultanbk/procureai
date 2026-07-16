"""
FILE CANONICAL IDENTIFIER: backend/agents/cross_validator/validator.py
MODULE ROLE: Deterministic cross-validation gate (Node 3) that runs BEFORE any interpretation-stage LLM calls.
SYSTEM BOUNDARY: Pure Python logic. No LLM integration. Updates PipelineState.
"""

import structlog
from decimal import Decimal
from rapidfuzz import fuzz

from backend.models.schemas import PipelineState, ContractRulebook, InvoiceData, CrossValidationResult
from backend.core.db import AsyncSessionLocal
from backend.models.audit import Audit
from sqlalchemy import select

from backend.core.unit_normalizer import extract_unit, units_are_compatible, convert_unit_price

logger = structlog.get_logger()

def fuzzy_score(s1: str, s2: str) -> float:
    if not s1 or not s2:
        return 0.0
    return fuzz.token_sort_ratio(str(s1).lower(), str(s2).lower())

async def run_cross_validator(state: PipelineState) -> PipelineState:
    """
    Node 3: Cross-Validation Gate
    - Fuzzy-matches invoice line items to contract rules
    - Detects unit mismatches between invoice and contract
    - Flags conditional rules missing supporting data
    - Identifies rules never billed on any invoice
    """
    state["current_agent"] = "cross_validator"
    
    try:
        rulebook_data = state.get("rulebook")
        invoices_data = state.get("invoice_data")
        
        if not rulebook_data or not invoices_data:
            raise ValueError("Missing rulebook or invoice data in state. Cannot cross-validate.")
            
        rulebook = ContractRulebook.model_validate(rulebook_data)
        invoices = [InvoiceData.model_validate(inv) for inv in invoices_data]
        
        candidate_map = {}
        unit_conversions = {}  # v4: {line_id: {rule_id: {"from": str, "to": str, "ratio_explanation": str}}}
        unmapped_line_details = []  # list[dict] with line_id + desc for review_flags
        rules_without_data = []
        rules_never_billed = []
        unit_mismatch_warnings = []  # v4: lines with unit issues
        
        matched_rule_ids = set()
        
        # Pre-extract units from all rules (cache for performance)
        rule_units = {}
        for rule in rulebook.rules:
            rule_unit = extract_unit(
                (rule.clause_text or "") + " " + (rule.applies_to or "") + " " + (rule.description or "")
            )
            rule_units[rule.rule_id] = rule_unit
        
        # 1. Fuzzy candidate matching with unit awareness
        for invoice in invoices:
            for item in invoice.line_items:
                candidates = []
                line_unit = extract_unit(
                    (item.raw_description or "") + " " + (item.mapped_contract_item or "")
                )
                
                for rule in rulebook.rules:
                    # fuzzy match against applies_to and description using BOTH
                    # raw_description (exact invoice text) and mapped_contract_item
                    # (LLM's semantic mapping to contract terminology)
                    score_raw_applies = fuzzy_score(item.raw_description, rule.applies_to)
                    score_raw_desc = fuzzy_score(item.raw_description, rule.description)
                    score_mapped_applies = fuzzy_score(item.mapped_contract_item, rule.applies_to)
                    score_mapped_desc = fuzzy_score(item.mapped_contract_item, rule.description)
                    best_score = max(score_raw_applies, score_raw_desc, score_mapped_applies, score_mapped_desc)
                    
                    if best_score >= 60:
                        # v4: Unit compatibility check
                        r_unit = rule_units.get(rule.rule_id)
                        
                        if line_unit and r_unit:
                            if not units_are_compatible(line_unit, r_unit):
                                # Incompatible units — skip this candidate entirely
                                logger.info(
                                    "cross_validator: skipping candidate due to incompatible units",
                                    line_id=item.line_id, rule_id=rule.rule_id,
                                    line_unit=line_unit, rule_unit=r_unit,
                                )
                                continue
                            
                            if line_unit.lower() != r_unit.lower():
                                # Compatible but different units — record conversion needed
                                conversion = convert_unit_price(
                                    Decimal("1"), line_unit, r_unit
                                )
                                if conversion:
                                    unit_conversions.setdefault(item.line_id, {})[rule.rule_id] = {
                                        "from_unit": line_unit,
                                        "to_unit": r_unit,
                                        "explanation": conversion[1],
                                    }
                                    unit_mismatch_warnings.append({
                                        "line_id": item.line_id,
                                        "rule_id": rule.rule_id,
                                        "line_unit": line_unit,
                                        "rule_unit": r_unit,
                                    })
                        
                        candidates.append(rule.rule_id)
                
                if not candidates:
                    unmapped_line_details.append({"line_id": item.line_id, "desc": item.raw_description})
                else:
                    candidate_map[item.line_id] = candidates
                    matched_rule_ids.update(candidates)
                    
        # 2. Conditional rules without supporting data
        import re
        DATE_PATTERN = re.compile(
            r"(?:\b\d{1,2}[-/\s]\d{1,2}[-/\s]\d{2,4}\b)|"
            r"(?:\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-/\s]?\d{1,2}(?:st|nd|rd|th)?[-/\s]?,?\s?\d{2,4}\b)|"
            r"(?:\b\d{4}-\d{2}-\d{2}\b)",
            re.IGNORECASE
        )
        
        CONDITIONAL_TYPES = {"sla_penalty", "milestone_penalty"}
        for rule in rulebook.rules:
            if rule.rule_type in CONDITIONAL_TYPES:
                has_data = False
                for invoice in invoices:
                    if rule.rule_type == "sla_penalty":
                        # Check if any line item in the invoice has SLA data
                        if any(item.sla_actual_pct is not None for item in invoice.line_items):
                            has_data = True
                            break
                    elif rule.rule_type == "milestone_penalty":
                        # Check if any line item has a milestone date
                        if any(item.milestone_date is not None for item in invoice.line_items):
                            has_data = True
                            break
                        # Check milestone statements in the invoice
                        if invoice.milestone_statements and any(bool(stmt.strip()) for stmt in invoice.milestone_statements):
                            has_data = True
                            break
                        # Check if invoice notes contains any date pattern
                        if invoice.notes and DATE_PATTERN.search(invoice.notes):
                            has_data = True
                            break
                        # Check if any line item notes contains a date pattern
                        if any(item.notes and DATE_PATTERN.search(item.notes) for item in invoice.line_items):
                            has_data = True
                            break
                            
                if not has_data:
                    rules_without_data.append({
                        "rule_id": rule.rule_id,
                        "clause_section": getattr(rule, "clause_reference", "Unknown"),
                        "reason": f"Conditional rule has no corresponding performance data ({'sla_actual_pct' if rule.rule_type == 'sla_penalty' else 'milestone_date'}) in any invoice"
                    })
                    
        # Remove rules without data from candidate_map and recalculate matched_rule_ids
        rules_without_data_ids = {r["rule_id"] for r in rules_without_data}
        if rules_without_data_ids:
            for line_id in list(candidate_map.keys()):
                updated_candidates = [c for c in candidate_map[line_id] if c not in rules_without_data_ids]
                if not updated_candidates:
                    # Line item no longer has any valid candidate rules.
                    # Remove it from candidate_map and add to unmapped_line_details.
                    del candidate_map[line_id]
                    if not any(u["line_id"] == line_id for u in unmapped_line_details):
                        # Find raw description for line
                        raw_desc = ""
                        for invoice in invoices:
                            for item in invoice.line_items:
                                if item.line_id == line_id:
                                    raw_desc = item.raw_description
                                    break
                            if raw_desc:
                                break
                        unmapped_line_details.append({"line_id": line_id, "desc": raw_desc})
                else:
                    candidate_map[line_id] = updated_candidates
                    
            # Recalculate matched_rule_ids
            matched_rule_ids = set()
            for candidates in candidate_map.values():
                matched_rule_ids.update(candidates)
                    
        # 3. Rules that exist in contract but matched NOTHING on any invoice
        for rule in rulebook.rules:
            if rule.rule_id not in matched_rule_ids and rule.rule_type not in CONDITIONAL_TYPES:
                rules_never_billed.append(rule.rule_id)
                
        # 4. Write back to state
        cv_result = CrossValidationResult(
            candidate_map=candidate_map,
            unmapped_lines=[u["line_id"] for u in unmapped_line_details],
            rules_without_data=rules_without_data,
            rules_never_billed=rules_never_billed
        )
        
        state["cross_validation"] = cv_result.model_dump()
        state["candidate_map"] = candidate_map
        state["data_required_flags"] = rules_without_data
        state["unit_conversions"] = unit_conversions  # v4: stored for compliance_checker
        
        # Merge unmapped lines into review_flags
        review_flags = state.get("review_flags", [])
        if review_flags is None:
            review_flags = []
            
        for item in unmapped_line_details:
            review_flags.append({
                "line_id": item["line_id"],
                "reason": "no plausible contract rule found — possible out-of-contract item or extraction error",
                "clause_text": item["desc"]
            })
            
        state["review_flags"] = review_flags
        
        audit_id = state.get("audit_id")
        async with AsyncSessionLocal() as session:
            stmt = select(Audit).where(Audit.id == audit_id)
            result = await session.execute(stmt)
            db_audit = result.scalar_one_or_none()
            if db_audit:
                db_audit.status = "CHECKING_COMPLIANCE"
                await session.commit()
        
    except Exception as e:
        logger.error(f"Cross Validator failed: {str(e)}")
        state.setdefault("errors", []).append({
            "agent": "cross_validator",
            "error_type": "validation_failed",
            "message": str(e),
            "recoverable": False
        })
        state["halt"] = True
        
    return state

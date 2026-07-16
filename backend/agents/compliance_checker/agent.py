"""
FILE CANONICAL IDENTIFIER: backend/agents/compliance_checker/agent.py
MODULE ROLE: Cognitive agent that maps contract rules to invoice line items and evaluates them for billing compliance.
SYSTEM BOUNDARY: Integrates with Google Generative AI (Gemini) and SQLite DB (Audit schema updates). Performs mathematical evaluations of rates via the external rule_engine module.
STATE DEPENDENCY / DATA CONTRACTS: Consumes rulebook and invoice_data from PipelineState. Outputs serialized DiscrepancyList schema (backend.models.schemas.DiscrepancyList) containing findings and compliant lines to PipelineState.
CRITICAL LOGIC: Combines LLM rule-to-line mapping with deterministic calculation loops. Bypasses deltas below MINIMUM_MATERIAL_THRESHOLD. Synthesizes finding narratives using Gemini, and catches whole-invoice SLA/milestone penalties using dummy line-item generation.
"""

import json
import structlog
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Optional
from decimal import Decimal
import google.generativeai as genai

from backend.models.schemas import (
    PipelineState,
    DiscrepancyList,
    Discrepancy,
    CompliantLine,
    LineItem,
    InvoiceData,
    PricingRule,
    AgentError
)
from backend.core.llm_client import get_llm
from backend.core.prompt_loader import load_prompt
from backend.core.db import AsyncSessionLocal
from backend.models.audit import Audit
from sqlalchemy import select
from backend.core.audit_logger import log_audit_event

from backend.agents.compliance_checker.tools import (
    MINIMUM_MATERIAL_THRESHOLD,
    round_money,
    compute_severity,
    compute_recommendation
)
from backend.agents.compliance_checker.rule_engine import evaluate_line_rule
from backend.core.unit_normalizer import convert_unit_price, convert_quantity

logger = structlog.get_logger()


def _rule_is_effective_for_invoice(rule: PricingRule, invoice: InvoiceData) -> bool:
    """
    Checks whether a pricing rule's effective date range overlaps with the
    invoice's billing period.  Returns True (apply the rule) when:
      - The rule has no effective_from / effective_until set, OR
      - The date ranges overlap.
    """
    from datetime import datetime as _dt

    def _parse_date(val: str | None) -> _dt | None:
        if not val:
            return None
        for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%Y-%m"):
            try:
                return _dt.strptime(val.strip(), fmt)
            except ValueError:
                continue
        return None

    def _parse_billing_period(bp: str) -> tuple[_dt | None, _dt | None]:
        """Parse 'October 2024' into (2024-10-01, 2024-10-31)."""
        if not bp:
            return None, None
        d = _parse_date(f"{bp.strip()} 1, " if "," not in bp else bp)
        # Try  "Month Year" → "Month 1, Year"
        parts = bp.strip().split()
        if len(parts) == 2:
            try:
                start = _dt.strptime(f"{parts[0]} 1, {parts[1]}", "%B %d, %Y")
                import calendar
                last_day = calendar.monthrange(start.year, start.month)[1]
                end = start.replace(day=last_day)
                return start, end
            except ValueError:
                pass
        return None, None

    rule_from = _parse_date(rule.effective_from)
    rule_until = _parse_date(rule.effective_until)

    # If no date constraints on the rule, it always applies
    if rule_from is None and rule_until is None:
        return True

    bp_start, bp_end = _parse_billing_period(invoice.billing_period)
    if bp_start is None:
        # Cannot determine billing period — apply rule conservatively
        return True

    # Check overlap: rule period intersects billing period
    if rule_from and bp_end and bp_end < rule_from:
        return False  # billing period ends before rule starts
    if rule_until and bp_start and bp_start > rule_until:
        # Check if the rule is an invoice level credit rule, as milestone penalties shouldn't expire just because the target date passed
        description = (rule.description or "").lower()
        applies_to = (rule.applies_to or "").lower()
        clause_text = (rule.clause_text or "").lower()
        combined = " ".join([description, applies_to, clause_text])
        if rule.rule_type == "sla_penalty" or any(t in combined for t in ("milestone", "delay penalty", "penalty credit", "shall credit", "liquidated damages")):
            return True
            
        return False  # billing period starts after rule expires

    return True


def _compute_composite_confidence(
    line_item: LineItem | None,
    rule: PricingRule,
    base_eval_confidence: float = 0.95,
) -> float:
    """
    Computes a real confidence score from:
      mapping_confidence  × extraction_confidence × base_eval_confidence
    instead of always returning 0.95.
    """
    mapping_conf = float(line_item.mapping_confidence) if line_item else 1.0
    extraction_conf = float(rule.extraction_confidence)
    return round(mapping_conf * extraction_conf * base_eval_confidence, 4)

# --- Local schemas for structured LLM outputs ---

class LineRuleMapping(BaseModel):
    line_id: str
    applicable_rule_ids: List[str]
    confidence: float = 1.0
    justification: str = "Mapped by compliance checker."

class InvoiceRuleMapping(BaseModel):
    mappings: List[LineRuleMapping]

class DiscrepancyNarrative(BaseModel):
    description: str
    clause_text: str

from typing import Literal
class CriticReflection(BaseModel):
    status: Literal["CONFIRMED", "NEEDS_HUMAN_REVIEW"]
    reasoning: str

async def run_compliance_checker(state: PipelineState) -> PipelineState:
    """
    Agent 3: Compliance Checker
    Input:  state["rulebook"], state["invoice_data"]
    Output: state["discrepancies"], state["current_agent"] = "compliance_checker"
    Error:  state["errors"].append(...), state["halt"] = True if unrecoverable
    """
    state["current_agent"] = "compliance_checker"
    audit_id = state.get("audit_id")
    await log_audit_event(audit_id, "Compliance Checker agent started.", "INFO", "compliance_checker")
    
    # Update status in database
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        db_audit = result.scalar_one_or_none()
        if db_audit:
            db_audit.status = "CHECKING_COMPLIANCE"
            await session.commit()

            
    try:
        rulebook_raw = state.get("rulebook")
        if not rulebook_raw:
            raise ValueError("Contract rulebook is missing from state.")
            
        invoice_data_raw = state.get("invoice_data", [])
        if not invoice_data_raw:
            raise ValueError("Invoice data is missing or empty in state.")
            
        # Parse Pydantic objects from dicts
        # Pydantic allows model_validate for parsed dicts
        rules_map: Dict[str, PricingRule] = {
            r["rule_id"]: PricingRule.model_validate(r)
            for r in rulebook_raw.get("rules", [])
        }
        
        invoices: List[InvoiceData] = [
            InvoiceData.model_validate(inv) for inv in invoice_data_raw
        ]
        
        llm = get_llm()
        prompt_template_match = load_prompt("compliance_checker", "prompt_match_rules.txt")
        prompt_template_critic = load_prompt("compliance_checker", "prompt_critic.txt")
        prompt_template_narrative = load_prompt("compliance_checker", "prompt.txt")
        
        discrepancies: List[Discrepancy] = []
        compliant_lines: List[CompliantLine] = []
        skipped_lines: List[str] = []
        finding_index = 1
        
        # Initialize token usage tracking for auditing
        token_accumulator = {
            "prompt_tokens": 0,
            "response_tokens": 0,
            "llm_calls": 0
        }
        
        # Process each invoice
        for invoice in invoices:
            await log_audit_event(audit_id, f"Evaluating billing compliance for invoice: {invoice.invoice_id} ({len(invoice.line_items)} lines).", "INFO", "compliance_checker")
            
            # Step 1: Rule Matching (LLM - Single Pass)
            candidate_map = state.get("candidate_map", {})
            cv_unmapped = state.get("cross_validation", {}).get("unmapped_lines", [])
            
            # Only map lines that have candidates
            invoice_to_map = invoice.model_copy()
            invoice_to_map.line_items = [li for li in invoice.line_items if li.line_id not in cv_unmapped and li.line_id in candidate_map]
            
            if invoice_to_map.line_items:
                mappings = await match_invoice_rules(llm, prompt_template_match, invoice_to_map, rules_map, candidate_map, token_accumulator)
            else:
                mappings = InvoiceRuleMapping(mappings=[])
            
            # Index rules applied to this invoice to find unapplied whole-invoice rules later
            applied_rule_ids = set()
            
            # v3 architecture: RULE_MATCH_CONFIDENCE_THRESHOLD = 0.75
            RULE_MATCH_CONFIDENCE_THRESHOLD = 0.75
            
            # Step 2: Rule Application (with confidence gate)
            data_required_rule_ids = {f["rule_id"] for f in state.get("data_required_flags", []) if isinstance(f, dict) and "rule_id" in f}
            
            for mapping in mappings.mappings:
                line_id = mapping.line_id
                applicable_rule_ids = mapping.applicable_rule_ids
                
                # v3 gate: if ALL candidates score below threshold → review_flags
                if mapping.confidence < RULE_MATCH_CONFIDENCE_THRESHOLD:
                    await log_audit_event(
                        audit_id,
                        f"Line {line_id}: all rule match confidences ({mapping.confidence:.2f}) "
                        f"below threshold {RULE_MATCH_CONFIDENCE_THRESHOLD}. Sending to review_flags.",
                        "INFO", "compliance_checker"
                    )
                    review_flags = state.get("review_flags", [])
                    if review_flags is None:
                        review_flags = []
                    review_flags.append({
                        "line_id": line_id,
                        "reason": f"No high-confidence rule match (best confidence: {mapping.confidence:.2f}, "
                                  f"threshold: {RULE_MATCH_CONFIDENCE_THRESHOLD})",
                    })
                    state["review_flags"] = review_flags
                    continue
                
                # Find the line item
                line_item = next((item for item in invoice.line_items if item.line_id == line_id), None)
                if not line_item:
                    await log_audit_event(audit_id, f"Warning: Mapped line ID {line_id} not found in invoice {invoice.invoice_id}.", "WARNING", "compliance_checker")
                    continue
                    
                for rule_id in applicable_rule_ids:
                    rule = rules_map.get(rule_id)
                    if not rule:
                        await log_audit_event(audit_id, f"Warning: Mapped rule ID {rule_id} not found in rulebook.", "WARNING", "compliance_checker")
                        continue
                    if rule_id in data_required_rule_ids:
                        continue
                    if is_invoice_level_credit_rule(rule):
                        continue
                    
                    # Billing period validation: skip rules not effective during this invoice
                    if not _rule_is_effective_for_invoice(rule, invoice):
                        await log_audit_event(
                            audit_id,
                            f"Skipping rule {rule_id} for invoice {invoice.invoice_id} — "
                            f"rule effective period ({rule.effective_from} to {rule.effective_until}) "
                            f"does not overlap with billing period '{invoice.billing_period}'.",
                            "INFO", "compliance_checker"
                        )
                        skipped_lines.append(f"{line_id}:{rule_id}:period_mismatch")
                        continue
                        
                    applied_rule_ids.add(rule_id)
                    
                    # Calculate expected total
                    try:
                        # v4: Apply unit conversions if present in state
                        unit_conversions = state.get("unit_conversions", {})
                        conversion_info = unit_conversions.get(line_id, {}).get(rule_id) if unit_conversions else None
                        
                        if conversion_info:
                            from_unit = conversion_info.get("from_unit")
                            to_unit = conversion_info.get("to_unit")
                            
                            adjusted_line = line_item.model_copy()
                            
                            # 1. Convert quantity
                            qty_res = convert_quantity(line_item.quantity, from_unit, to_unit)
                            if qty_res:
                                adjusted_line.quantity = qty_res[0]
                                
                            # 2. Convert unit price charged
                            price_res = convert_unit_price(line_item.unit_price_charged, from_unit, to_unit)
                            if price_res:
                                adjusted_line.unit_price_charged = price_res[0]
                                
                            await log_audit_event(
                                audit_id,
                                f"Applying unit conversion for line {line_id}: "
                                f"{line_item.quantity} {from_unit} @ INR {line_item.unit_price_charged} -> "
                                f"{adjusted_line.quantity} {to_unit} @ INR {adjusted_line.unit_price_charged}",
                                "INFO", "compliance_checker"
                            )
                            expected_total = evaluate_line_rule(adjusted_line, rule, invoice)
                        else:
                            expected_total = evaluate_line_rule(line_item, rule, invoice)
                    except Exception as e:
                        await log_audit_event(audit_id, f"Warning: Failed to evaluate rule {rule_id} on line item {line_id}: {str(e)}", "WARNING", "compliance_checker")
                        continue
                        
                    charged_total = Decimal(str(line_item.line_total_charged))
                    delta = expected_total - charged_total
                    
                    # Check threshold
                    if abs(delta) > MINIMUM_MATERIAL_THRESHOLD:
                        # LLM Critic check (Flag Only)
                        critic_result = await verify_discrepancy_with_critic(llm, prompt_template_critic, line_item, rule, delta, invoice, token_accumulator)
                        if critic_result.status == "NEEDS_HUMAN_REVIEW":
                            await log_audit_event(audit_id, f"Critic flagged discrepancy on line {line_id} for human review. Reasoning: {critic_result.reasoning}", "INFO", "compliance_checker")
                            review_flags = state.get("review_flags", [])
                            if review_flags is None:
                                review_flags = []
                            review_flags.append({
                                "line_id": line_id,
                                "rule_id": rule_id,
                                "reason": critic_result.reasoning
                            })
                            state["review_flags"] = review_flags
                            
                        await log_audit_event(audit_id, f"Discrepancy detected on line {line_id} under rule {rule_id}. Expected: INR {expected_total}, Charged: INR {charged_total}, Delta: INR {delta}.", "INFO", "compliance_checker")
                        
                        # Step 3: Evidence Assembly (LLM)
                        # Determine discrepancy type based on rule type
                        discrepancy_type = classify_discrepancy_type(rule.rule_type)
                        
                        narrative = await generate_evidence_narrative(
                            llm, prompt_template_narrative, line_item, rule, delta, invoice, token_accumulator
                        )
                        
                        severity = compute_severity(delta)
                        rec = compute_recommendation(severity, discrepancy_type)
                        
                        qty = Decimal(str(line_item.quantity))
                        unit_charged = Decimal(str(line_item.unit_price_charged))
                        unit_expected = round_money(expected_total / qty) if qty > 0 else Decimal("0.00")
                        
                        # v4: Apply historical feedback calibration
                        base_confidence = _compute_composite_confidence(line_item, rule)
                        description_text = narrative.description
                        
                        historical = await lookup_feedback_history(
                            supplier_name=rulebook_raw.get("supplier_name", ""),
                            rule_type=rule.rule_type,
                            applies_to=rule.applies_to
                        )
                        
                        if historical.false_positive_rate > 0.5:
                            base_confidence *= 0.5
                            description_text += " [Historical: this rule match has a high false-positive rate]"
                            rec = "REVIEW"
                            await log_audit_event(
                                audit_id,
                                f"Historical Calibration: Reduced confidence for rule {rule_id} "
                                f"due to high false-positive rate ({historical.false_positive_rate*100:.1f}%).",
                                "INFO", "compliance_checker"
                            )
                        
                        disc = Discrepancy(
                            finding_id=f"F{finding_index:03d}",
                            invoice_id=invoice.invoice_id,
                            line_id=line_id,
                            rule_id=rule_id,
                            discrepancy_type=discrepancy_type,
                            description=description_text,
                            clause_reference=rule.clause_reference,
                            clause_text=narrative.clause_text or rule.clause_text,
                            quantity=qty,
                            unit_price_charged=unit_charged,
                            unit_price_expected=unit_expected,
                            line_total_charged=charged_total,
                            line_total_expected=expected_total,
                            delta=delta,
                            severity=severity,
                            recommendation=rec,
                            confidence=base_confidence,
                            critic_status=critic_result.status,
                            critic_reasoning=critic_result.reasoning
                        )
                        discrepancies.append(disc)
                        finding_index += 1
                    else:
                        compliant = CompliantLine(
                            line_id=line_id,
                            rule_id=rule_id,
                            description=f"Line item matches pricing under contract rule {rule_id} ({rule.description})."
                        )
                        compliant_lines.append(compliant)
                        
            # Check for unapplied whole-invoice rules (like SLA penalties and milestone delays)
            for rule_id, rule in rules_map.items():
                if rule_id in applied_rule_ids:
                    continue
                    
                if rule_id in data_required_rule_ids:
                    continue
                    
                # Evaluate SLA penalty rules and milestone penalty rules at invoice level.
                if is_invoice_level_credit_rule(rule):
                    # Billing period validation for whole-invoice rules too
                    if not _rule_is_effective_for_invoice(rule, invoice):
                        await log_audit_event(
                            audit_id,
                            f"Skipping whole-invoice rule {rule_id} — "
                            f"not effective during '{invoice.billing_period}'.",
                            "INFO", "compliance_checker"
                        )
                        continue
                    
                    # Create a dummy line item to evaluate
                    dummy_line = LineItem(
                        line_id="V001",
                        raw_description=rule.applies_to,
                        mapped_contract_item=rule.applies_to,
                        mapping_confidence=1.0,
                        quantity=Decimal("1"),
                        unit_price_charged=Decimal("0.00"),
                        line_total_charged=Decimal("0.00"),
                        notes=""
                    )
                    
                    try:
                        expected_total = evaluate_line_rule(dummy_line, rule, invoice)
                    except Exception as e:
                        await log_audit_event(audit_id, f"Warning: Failed to evaluate whole-invoice rule {rule_id}: {str(e)}", "WARNING", "compliance_checker")
                        continue
                        
                    # Expected total should be negative if penalty/credit was triggered
                    if expected_total < 0:
                        delta = expected_total  # since charged is 0
                        discrepancy_type = "unapplied_penalty"
                        
                        critic_result = await verify_discrepancy_with_critic(llm, prompt_template_critic, dummy_line, rule, delta, invoice, token_accumulator)
                        if critic_result.status == "NEEDS_HUMAN_REVIEW":
                            await log_audit_event(audit_id, f"Critic flagged whole-invoice discrepancy under rule {rule_id}. Reasoning: {critic_result.reasoning}", "INFO", "compliance_checker")
                            review_flags = state.get("review_flags", [])
                            if review_flags is None:
                                review_flags = []
                            review_flags.append({
                                "line_id": "N/A",
                                "rule_id": rule_id,
                                "reason": critic_result.reasoning
                            })
                            state["review_flags"] = review_flags

                        await log_audit_event(audit_id, f"Discrepancy detected for whole-invoice rule {rule_id} ({rule.rule_type}). Penalty/credit triggered: INR {expected_total}.", "INFO", "compliance_checker")
                        
                        narrative = await generate_evidence_narrative(
                            llm, prompt_template_narrative, dummy_line, rule, delta, invoice, token_accumulator
                        )
                        
                        severity = compute_severity(delta)
                        rec = compute_recommendation(severity, discrepancy_type)
                        
                        # v4: Apply historical feedback calibration
                        base_confidence = _compute_composite_confidence(dummy_line, rule)
                        description_text = narrative.description
                        
                        historical = await lookup_feedback_history(
                            supplier_name=rulebook_raw.get("supplier_name", ""),
                            rule_type=rule.rule_type,
                            applies_to=rule.applies_to
                        )
                        
                        if historical.false_positive_rate > 0.5:
                            base_confidence *= 0.5
                            description_text += " [Historical: this rule match has a high false-positive rate]"
                            rec = "REVIEW"
                            await log_audit_event(
                                audit_id,
                                f"Historical Calibration: Reduced confidence for whole-invoice rule {rule_id} "
                                f"due to high false-positive rate ({historical.false_positive_rate*100:.1f}%).",
                                "INFO", "compliance_checker"
                            )
                        
                        disc = Discrepancy(
                            finding_id=f"F{finding_index:03d}",
                            invoice_id=invoice.invoice_id,
                            line_id="N/A",
                            rule_id=rule_id,
                            discrepancy_type=discrepancy_type,
                            description=description_text,
                            clause_reference=rule.clause_reference,
                            clause_text=narrative.clause_text or rule.clause_text,
                            quantity=Decimal("1"),
                            unit_price_charged=Decimal("0.00"),
                            unit_price_expected=expected_total,
                            line_total_charged=Decimal("0.00"),
                            line_total_expected=expected_total,
                            delta=delta,
                            severity=severity,
                            recommendation=rec,
                            confidence=base_confidence,
                            critic_status=critic_result.status,
                            critic_reasoning=critic_result.reasoning
                        )
                        discrepancies.append(disc)
                        finding_index += 1


        # 3. Construct confidence map for auditor review
        confidence_map = {}
        for d in discrepancies:
            mapping_conf = 1.0
            if d.line_id != "N/A":
                for inv in invoices:
                    for li in inv.line_items:
                        if li.line_id == d.line_id:
                            mapping_conf = float(li.mapping_confidence)
                            break
            
            extraction_conf = 1.0
            if d.rule_id in rules_map:
                extraction_conf = float(rules_map[d.rule_id].extraction_confidence)
                
            confidence_map[d.finding_id] = {
                "line_id": d.line_id,
                "rule_id": d.rule_id,
                "mapping_confidence": mapping_conf,
                "extraction_confidence": extraction_conf,
                "evaluation_confidence": float(d.confidence),
                "composite_confidence": round(mapping_conf * extraction_conf * float(d.confidence), 4)
            }

        # 4. Construct final DiscrepancyList Pydantic object
        total_delta = sum(d.delta for d in discrepancies)
        
        audit_metadata = {
            "note": "Checked compliance across all lines against rules. Found overcharges.",
            "token_audit_logs": token_accumulator,
            "confidence_map": confidence_map
        }
        
        discrepancy_list_obj = DiscrepancyList(
            audit_id=audit_id,
            discrepancies=discrepancies,
            compliant_lines=compliant_lines,
            skipped_lines=skipped_lines,
            total_delta=total_delta,
            checker_notes=json.dumps(audit_metadata, default=str)
        )
        
        # 5. Write back to state
        state["discrepancies"] = discrepancy_list_obj.model_dump()
        
        # 6. Save in database and set status to GENERATING_REPORT
        async with AsyncSessionLocal() as session:
            stmt = select(Audit).where(Audit.id == audit_id)
            result = await session.execute(stmt)
            db_audit = result.scalar_one_or_none()
            if db_audit:
                db_audit.discrepancies = json.dumps(discrepancy_list_obj.model_dump(), default=str)
                db_audit.total_leakage = float(abs(total_delta))
                db_audit.status = "GENERATING_REPORT"
                await session.commit()
                
        # Structured log audit trail for compliance checking decisions
        await log_audit_event(
            audit_id,
            f"Compliance check complete. Audited lines: {sum(len(inv.line_items) for inv in invoices)}. "
            f"Found {len(discrepancies)} discrepancies. Total Leakage: INR {abs(total_delta)}.",
            "INFO",
            "compliance_checker"
        )
        
    except Exception as e:
        await log_audit_event(audit_id, f"Compliance Checker agent failed: {str(e)}", "ERROR", "compliance_checker")
        error = AgentError(
            agent="compliance_checker",
            error_type="rule_application_failed" if "engine" in str(e).lower() else "llm_call_failed",
            message=str(e),
            recoverable=False
        )
        state.setdefault("errors", []).append(error.model_dump())
        state["halt"] = True
        
        async with AsyncSessionLocal() as session:
            stmt = select(Audit).where(Audit.id == audit_id)
            result = await session.execute(stmt)
            db_audit = result.scalar_one_or_none()
            if db_audit:
                db_audit.status = "FAILED"
                db_audit.error_detail = str(e)
                await session.commit()

                
    return state

# --- Helpers ---

def classify_discrepancy_type(rule_type: str) -> str:
    if rule_type == "volume_tier":
        return "overcharge"
    if rule_type == "flat_rate":
        return "incorrect_rate"
    if rule_type == "sla_penalty":
        return "unapplied_penalty"
    if rule_type == "early_payment_discount":
        return "missed_discount"
    if rule_type == "bundle_discount":
        return "missed_discount"
    if rule_type == "cap_rate":
        return "overcharge"
    return "overcharge"


def is_invoice_level_credit_rule(rule: PricingRule) -> bool:
    """
    Returns true for rules that create a separate credit/penalty obligation.
    These should not be used as the expected price for an ordinary invoice line.
    """
    description = (rule.description or "").lower()
    applies_to = (rule.applies_to or "").lower()
    clause_text = (rule.clause_text or "").lower()
    combined = " ".join([description, applies_to, clause_text])

    if rule.rule_type == "sla_penalty":
        return True

    return any(
        token in combined
        for token in (
            "milestone",
            "delay penalty",
            "penalty credit",
            "shall credit",
            "liquidated damages",
        )
    )

def get_token_counts(contents, response) -> dict:
    """Helper to safely retrieve or estimate token usage for a model call."""
    prompt_tokens = 0
    response_tokens = 0
    
    # Try to extract from real model response metadata first
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
        response_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)
    
    # Fallback to estimating based on character counts (1 token ≈ 4 characters)
    if prompt_tokens == 0:
        total_prompt_char = 0
        if isinstance(contents, list):
            for part in contents:
                total_prompt_char += len(str(part))
        else:
            total_prompt_char += len(str(contents))
        prompt_tokens = max(1, total_prompt_char // 4)
        
    if response_tokens == 0 and hasattr(response, "text"):
        response_tokens = max(1, len(str(response.text)) // 4)
        
    return {
        "prompt_tokens": prompt_tokens,
        "response_tokens": response_tokens,
        "total_tokens": prompt_tokens + response_tokens
    }

async def match_invoice_rules(
    llm, prompt_template: str, invoice: InvoiceData, rules_map: dict, candidate_map: dict, token_accumulator: Optional[dict] = None
) -> InvoiceRuleMapping:
    """
    Asks LLM to map rules to invoice line items from a constrained list of candidates.
    """
    # Build a minimal context of candidates
    candidate_context = {}
    for li in invoice.line_items:
        c_ids = candidate_map.get(li.line_id, [])
        candidates_for_line = []
        for rid in c_ids:
            if rid in rules_map:
                r = rules_map[rid]
                candidates_for_line.append(r.model_dump(exclude_none=True))
        candidate_context[li.line_id] = candidates_for_line

    input_text = (
        f"Please perform [TASK 1: RULE MAPPING] for this invoice.\n\n"
        f"=== INVOICE DATA ===\n"
        f"{invoice.model_dump_json(indent=2)}\n\n"
        f"=== CANDIDATE RULES PER LINE ===\n"
        f"For each line item, you MUST ONLY choose from the rules listed below for that specific line_id.\n"
        f"{json.dumps(candidate_context, indent=2, default=str)}\n"
    )
    
    response = await llm.async_generate_content(
        contents=[prompt_template, input_text],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=InvoiceRuleMapping.model_json_schema(),
            temperature=0.0
        )
    )
    
    if token_accumulator is not None:
        counts = get_token_counts([prompt_template, input_text], response)
        token_accumulator["prompt_tokens"] += counts["prompt_tokens"]
        token_accumulator["response_tokens"] += counts["response_tokens"]
        token_accumulator["llm_calls"] += 1
        
    try:
        return InvoiceRuleMapping.model_validate_json(response.text)
    except ValidationError:
        logger.warning("Rule mapping failed schema validation, returning empty mappings...")
        return InvoiceRuleMapping(mappings=[])

async def generate_evidence_narrative(
    llm, prompt_template: str, line_item: LineItem, rule: PricingRule, delta: Decimal, invoice: InvoiceData, token_accumulator: Optional[dict] = None
) -> DiscrepancyNarrative:
    """
    Asks LLM to generate plain-English explanation and copy exact clause text for a finding.
    """
    input_text = (
        f"Please perform [TASK 2: EVIDENCE NARRATION] for the following detected discrepancy.\n\n"
        f"=== CONTRACT RULE ===\n"
        f"Rule ID: {rule.rule_id}\n"
        f"Description: {rule.description}\n"
        f"Clause Reference: {rule.clause_reference}\n"
        f"Quoted Contract Text: {rule.clause_text}\n\n"
        f"=== INVOICE DETAIL ===\n"
        f"Supplier Name: {invoice.supplier_name}\n"
        f"Invoice ID: {invoice.invoice_id}\n"
        f"Line item description: {line_item.raw_description}\n"
        f"Quantity: {line_item.quantity}\n"
        f"Charged Unit Price: {line_item.unit_price_charged}\n"
        f"Charged Line Total: {line_item.line_total_charged}\n\n"
        f"=== ARITHMETIC DISCREPANCY ===\n"
        f"Calculated expected cost: {Decimal(str(line_item.line_total_charged)) + delta}\n"
        f"Delta (Expected - Charged): {delta}\n"
    )
    
    response = await llm.async_generate_content(
        contents=[prompt_template, input_text],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=DiscrepancyNarrative.model_json_schema(),
            temperature=0.0
        )
    )
    
    if token_accumulator is not None:
        counts = get_token_counts([prompt_template, input_text], response)
        token_accumulator["prompt_tokens"] += counts["prompt_tokens"]
        token_accumulator["response_tokens"] += counts["response_tokens"]
        token_accumulator["llm_calls"] += 1
        
    try:
        return DiscrepancyNarrative.model_validate_json(response.text)
    except ValidationError as e:
        logger.warning("Evidence narrative failed schema validation, retrying with correction prompt...")
        correction_prompt = (
            f"Your previous output failed schema validation against the DiscrepancyNarrative schema.\n"
            f"Validation Error: {str(e)}\n"
            f"Original Input:\n{input_text}\n\n"
            f"Your invalid JSON response:\n{response.text}\n\n"
            f"Please output corrected, valid JSON matching the schema."
        )
        retry_response = await llm.async_generate_content(
            contents=[prompt_template, correction_prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=DiscrepancyNarrative.model_json_schema(),
                temperature=0.0
            )
        )
        if token_accumulator is not None:
            counts = get_token_counts([prompt_template, correction_prompt], retry_response)
            token_accumulator["prompt_tokens"] += counts["prompt_tokens"]
            token_accumulator["response_tokens"] += counts["response_tokens"]
            token_accumulator["llm_calls"] += 1
        return DiscrepancyNarrative.model_validate_json(retry_response.text)

async def verify_discrepancy_with_critic(
    llm, prompt_template: str, line_item: LineItem, rule: PricingRule, delta: Decimal, invoice: InvoiceData, token_accumulator: Optional[dict] = None
) -> CriticReflection:
    """
    Asks LLM to verify if a mathematically calculated discrepancy aligns with the logical reality of the contract text.
    """
    input_text = (
        f"Please perform [TASK 3: CRITIC REFLECTION] for the following calculated discrepancy.\n\n"
        f"=== CONTRACT RULE ===\n"
        f"Rule ID: {rule.rule_id}\n"
        f"Description: {rule.description}\n"
        f"Quoted Contract Text: {rule.clause_text}\n\n"
        f"=== INVOICE DETAIL ===\n"
        f"Line item description: {line_item.raw_description}\n"
        f"Quantity: {line_item.quantity}\n"
        f"Charged Line Total: {line_item.line_total_charged}\n\n"
        f"=== ARITHMETIC DISCREPANCY ===\n"
        f"Calculated expected cost: {Decimal(str(line_item.line_total_charged)) + delta}\n"
        f"Delta (Expected - Charged): {delta}\n"
    )
    
    response = await llm.async_generate_content(
        contents=[prompt_template, input_text],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=CriticReflection.model_json_schema(),
            temperature=0.0
        )
    )
    
    if token_accumulator is not None:
        counts = get_token_counts([prompt_template, input_text], response)
        token_accumulator["prompt_tokens"] += counts["prompt_tokens"]
        token_accumulator["response_tokens"] += counts["response_tokens"]
        token_accumulator["llm_calls"] += 1
        
    try:
        return CriticReflection.model_validate_json(response.text)
    except ValidationError as e:
        logger.warning("Critic reflection failed schema validation, retrying...")
        correction_prompt = (
            f"Your previous output failed schema validation against the CriticReflection schema.\n"
            f"Validation Error: {str(e)}\n"
            f"Original Input:\n{input_text}\n\n"
            f"Your invalid JSON response:\n{response.text}\n\n"
            f"Please output corrected, valid JSON matching the schema."
        )
        retry_response = await llm.async_generate_content(
            contents=[prompt_template, correction_prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=CriticReflection.model_json_schema(),
                temperature=0.0
            )
        )
        if token_accumulator is not None:
            counts = get_token_counts([prompt_template, correction_prompt], retry_response)
            token_accumulator["prompt_tokens"] += counts["prompt_tokens"]
            token_accumulator["response_tokens"] += counts["response_tokens"]
            token_accumulator["llm_calls"] += 1
        return CriticReflection.model_validate_json(retry_response.text)


class HistoricalFeedbackStats:
    def __init__(self, total_count: int, false_positive_count: int):
        self.total_count = total_count
        self.false_positive_count = false_positive_count
        self.false_positive_rate = (
            float(false_positive_count) / total_count if total_count > 0 else 0.0
        )


async def lookup_feedback_history(
    supplier_name: str,
    rule_type: str,
    applies_to: str,
) -> HistoricalFeedbackStats:
    from sqlalchemy import select
    from backend.models.audit import FindingFeedback
    from backend.core.db import AsyncSessionLocal
    from rapidfuzz import fuzz
    
    async with AsyncSessionLocal() as session:
        stmt = (
            select(FindingFeedback)
            .where(
                FindingFeedback.supplier_name == supplier_name,
                FindingFeedback.rule_type == rule_type
            )
        )
        results = (await session.execute(stmt)).scalars().all()
        
        total_count = 0
        fp_count = 0
        
        target_applies = (applies_to or "").lower().strip()
        for fb in results:
            fb_applies = (fb.applies_to or "").lower().strip()
            score = fuzz.token_sort_ratio(target_applies, fb_applies) if target_applies and fb_applies else 100
            if (not target_applies and not fb_applies) or score >= 80:
                total_count += 1
                if fb.human_verdict == "FALSE_POSITIVE":
                    fp_count += 1
                    
        return HistoricalFeedbackStats(total_count, fp_count)


"""
FILE CANONICAL IDENTIFIER: backend/agents/reverse_sweep/agent.py
MODULE ROLE: v4 Node 5 — Bidirectional verification. Checks contract rules that SHOULD have
    triggered but produced no corresponding invoice credit/discount/penalty line.
SYSTEM BOUNDARY: Pure Python trigger checks + bounded LLM for ambiguous cases only.
STATE DEPENDENCY / DATA CONTRACTS: Reads rulebook, invoice_data, discrepancies from PipelineState.
    Writes ReverseSweepResult with missing credit findings.
CRITICAL LOGIC: Focuses on credit/discount/penalty rules that suppliers commonly "forget."
    Each trigger check is deterministic Python. LLM is only used for narrative explanation.
"""

import structlog
from decimal import Decimal
from typing import List, Optional
from rapidfuzz import fuzz

from backend.models.schemas import (
    PipelineState,
    ContractRulebook,
    InvoiceData,
    PricingRule,
)
from backend.core.audit_logger import log_audit_event

logger = structlog.get_logger()

# Rule types where the contract GIVES something to the client (credit, discount, penalty in client's favor)
CREDIT_RULE_TYPES = {
    "early_payment_discount",
    "sla_penalty",
    "bundle_discount",
}


class TriggerResult:
    """Result of checking whether a contract rule should have triggered."""
    def __init__(
        self,
        should_have_applied: bool,
        evidence: str = "",
        expected_credit: Optional[Decimal] = None,
    ):
        self.should_have_applied = should_have_applied
        self.evidence = evidence
        self.expected_credit = expected_credit


def check_early_payment_trigger(rule: PricingRule, invoice: InvoiceData) -> TriggerResult:
    """
    Checks if the invoice has evidence of early payment that should trigger a discount.

    Looks for:
    - Invoice notes mentioning payment within X days
    - Invoice date vs billing period suggesting early settlement
    - Explicit "paid" or "payment received" mentions

    Returns TriggerResult with expected credit calculated as:
        invoice_total * discount_pct
    """
    if rule.payment_window_days is None or rule.discount_pct is None:
        return TriggerResult(False, "Rule missing payment_window_days or discount_pct parameters")

    # Check invoice notes for payment timing evidence
    notes_lower = (invoice.notes or "").lower()
    all_text = notes_lower

    # Also check line item notes
    for item in invoice.line_items:
        all_text += " " + (item.notes or "").lower()

    # Payment timing patterns
    early_payment_patterns = [
        "paid within", "payment received within", "early payment",
        "settled within", "paid on", "payment date", "net 10",
        "net 15", "net 7", "prompt payment",
    ]

    has_payment_evidence = any(pattern in all_text for pattern in early_payment_patterns)

    if has_payment_evidence:
        expected_credit = (invoice.invoice_total * Decimal(str(rule.discount_pct))).quantize(Decimal("0.01"))
        return TriggerResult(
            should_have_applied=True,
            evidence=f"Invoice contains early payment evidence. "
                     f"Contract rule {rule.rule_id} offers {rule.discount_pct*100}% discount "
                     f"for payment within {rule.payment_window_days} days.",
            expected_credit=expected_credit,
        )

    return TriggerResult(False, "No payment timing evidence found in invoice")


def check_sla_penalty_trigger(rule: PricingRule, invoice: InvoiceData) -> TriggerResult:
    """
    Checks if any line item shows SLA breach (sla_actual_pct < sla_threshold_pct)
    that should trigger a penalty credit but no penalty line exists.
    """
    if rule.sla_threshold_pct is None or rule.penalty_pct is None:
        return TriggerResult(False, "Rule missing sla_threshold_pct or penalty_pct parameters")

    for item in invoice.line_items:
        if item.sla_actual_pct is not None:
            if item.sla_actual_pct < rule.sla_threshold_pct:
                # SLA was breached — penalty should apply
                expected_credit = (invoice.invoice_total * Decimal(str(rule.penalty_pct))).quantize(Decimal("0.01"))
                return TriggerResult(
                    should_have_applied=True,
                    evidence=f"SLA breach detected: actual {item.sla_actual_pct*100:.1f}% "
                             f"< threshold {rule.sla_threshold_pct*100:.1f}% "
                             f"(Line {item.line_id}). "
                             f"Contract rule {rule.rule_id} mandates {rule.penalty_pct*100}% penalty.",
                    expected_credit=expected_credit,
                )

    return TriggerResult(False, "No SLA breach data found in invoice line items")


def check_bundle_trigger(rule: PricingRule, invoice: InvoiceData) -> TriggerResult:
    """
    Checks if total quantity for the rule's applies_to items exceeds bundle_threshold,
    but standard (non-bundle) pricing was charged instead of bundle pricing.
    """
    if rule.bundle_threshold is None or rule.bundle_price is None:
        return TriggerResult(False, "Rule missing bundle_threshold or bundle_price parameters")

    # Find matching line items by fuzzy matching applies_to
    total_quantity = Decimal("0")
    total_charged = Decimal("0")
    matching_lines = []

    for item in invoice.line_items:
        score = max(
            fuzz.token_sort_ratio(item.mapped_contract_item.lower(), rule.applies_to.lower()),
            fuzz.token_sort_ratio(item.raw_description.lower(), rule.applies_to.lower()),
        )
        if score >= 60:
            total_quantity += item.quantity
            total_charged += item.line_total_charged
            matching_lines.append(item.line_id)

    if total_quantity > Decimal(str(rule.bundle_threshold)):
        # Bundle should have triggered
        expected_total = total_quantity * rule.bundle_price
        if total_charged > expected_total:
            expected_credit = (total_charged - expected_total).quantize(Decimal("0.01"))
            return TriggerResult(
                should_have_applied=True,
                evidence=f"Total quantity ({total_quantity}) for '{rule.applies_to}' "
                         f"exceeds bundle threshold ({rule.bundle_threshold}). "
                         f"Charged ₹{total_charged} but bundle price would be ₹{expected_total}. "
                         f"Lines: {', '.join(matching_lines)}.",
                expected_credit=expected_credit,
            )

    return TriggerResult(False, f"Total quantity ({total_quantity}) below bundle threshold ({rule.bundle_threshold})")


def find_credit_line(invoice: InvoiceData, rule: PricingRule) -> bool:
    """
    Checks if the invoice already contains a credit/discount line
    corresponding to this rule.
    """
    credit_keywords = [
        "credit", "discount", "rebate", "penalty",
        "deduction", "adjustment", "less:", "less ",
    ]

    for item in invoice.line_items:
        desc_lower = (item.raw_description or "").lower()
        mapped_lower = (item.mapped_contract_item or "").lower()
        combined = desc_lower + " " + mapped_lower

        # Check if this line looks like a credit for this rule
        has_credit_keyword = any(kw in combined for kw in credit_keywords)
        matches_rule = fuzz.token_sort_ratio(
            combined, (rule.applies_to or "").lower() + " " + (rule.description or "").lower()
        ) >= 50

        # Negative amount is a strong indicator of a credit line
        is_negative = item.line_total_charged < 0

        if (has_credit_keyword or is_negative) and matches_rule:
            return True

    return False


async def run_reverse_sweep(state: PipelineState) -> PipelineState:
    """
    v4 Node 5: Reverse Sweep — Bidirectional Verification

    For each credit-type contract rule (early_payment_discount, sla_penalty,
    bundle_discount), checks whether it SHOULD have triggered based on invoice
    evidence. If it should have but no credit line exists, generates a
    MissingCreditFinding.

    This catches the most common real-world invoice error: suppliers "forgetting"
    to apply credits/discounts/penalties.
    """
    state["current_agent"] = "reverse_sweep"
    audit_id = state.get("audit_id", "unknown")

    try:
        rulebook_data = state.get("rulebook")
        invoices_data = state.get("invoice_data")
        discrepancies_data = state.get("discrepancies")

        if not rulebook_data or not invoices_data:
            await log_audit_event(
                audit_id,
                "Reverse sweep skipped: missing rulebook or invoice data.",
                "WARNING", "reverse_sweep"
            )
            state["reverse_sweep"] = {
                "missing_credits": [],
                "verified_rules": [],
                "inconclusive": [],
            }
            return state

        rulebook = ContractRulebook.model_validate(rulebook_data)
        invoices = [InvoiceData.model_validate(inv) for inv in invoices_data]

        # Collect rule_ids already flagged by the compliance checker (Node 4)
        already_found_rule_ids = set()
        if discrepancies_data:
            disc_list = discrepancies_data if isinstance(discrepancies_data, list) else discrepancies_data.get("discrepancies", [])
            for finding in disc_list:
                if isinstance(finding, dict):
                    already_found_rule_ids.add(finding.get("rule_id", ""))

        missing_credits = []
        verified_rules = []
        inconclusive = []
        finding_counter = 0

        # Trigger function dispatch
        TRIGGER_CHECKERS = {
            "early_payment_discount": check_early_payment_trigger,
            "sla_penalty": check_sla_penalty_trigger,
            "bundle_discount": check_bundle_trigger,
        }

        for rule in rulebook.rules:
            if rule.rule_type not in CREDIT_RULE_TYPES:
                continue

            if rule.rule_id in already_found_rule_ids:
                # Already flagged by compliance checker — skip
                verified_rules.append(rule.rule_id)
                continue

            checker = TRIGGER_CHECKERS.get(rule.rule_type)
            if not checker:
                inconclusive.append(rule.rule_id)
                continue

            for invoice in invoices:
                trigger = checker(rule, invoice)

                if trigger.should_have_applied:
                    # Check if a credit line already exists on this invoice
                    credit_exists = find_credit_line(invoice, rule)

                    if credit_exists:
                        verified_rules.append(rule.rule_id)
                        logger.info(
                            "reverse_sweep: credit line found for triggered rule",
                            rule_id=rule.rule_id, invoice_id=invoice.invoice_id,
                        )
                    else:
                        finding_counter += 1
                        finding_id = f"MC{finding_counter:03d}"

                        # Determine severity based on expected credit amount
                        severity = "MEDIUM"
                        if trigger.expected_credit:
                            if trigger.expected_credit >= Decimal("10000"):
                                severity = "CRITICAL"
                            elif trigger.expected_credit >= Decimal("1000"):
                                severity = "HIGH"

                        missing_credits.append({
                            "finding_id": finding_id,
                            "rule_id": rule.rule_id,
                            "rule_type": rule.rule_type,
                            "invoice_id": invoice.invoice_id,
                            "trigger_evidence": trigger.evidence,
                            "expected_credit": str(trigger.expected_credit) if trigger.expected_credit else None,
                            "severity": severity,
                            "clause_reference": rule.clause_reference,
                            "description": (
                                f"Missing credit: {rule.description}. "
                                f"{trigger.evidence} "
                                f"No corresponding credit/discount line found on invoice {invoice.invoice_id}."
                                + (f" Estimated missing credit: ₹{trigger.expected_credit}." if trigger.expected_credit else "")
                            ),
                        })

                        logger.warning(
                            "reverse_sweep: missing credit detected",
                            finding_id=finding_id,
                            rule_id=rule.rule_id,
                            invoice_id=invoice.invoice_id,
                            expected_credit=str(trigger.expected_credit),
                        )
                else:
                    # Rule doesn't appear to be triggered — that's fine
                    verified_rules.append(rule.rule_id)

        result = {
            "missing_credits": missing_credits,
            "verified_rules": list(set(verified_rules)),
            "inconclusive": inconclusive,
        }

        state["reverse_sweep"] = result

        await log_audit_event(
            audit_id,
            f"Reverse sweep complete. "
            f"Checked {len([r for r in rulebook.rules if r.rule_type in CREDIT_RULE_TYPES])} credit rules. "
            f"Found {len(missing_credits)} missing credit(s), "
            f"{len(set(verified_rules))} verified, "
            f"{len(inconclusive)} inconclusive.",
            "INFO", "reverse_sweep"
        )

    except Exception as e:
        logger.error(f"Reverse Sweep failed: {str(e)}")
        state.setdefault("errors", []).append({
            "agent": "reverse_sweep",
            "error_type": "validation_failed",
            "message": str(e),
            "recoverable": True  # Non-fatal
        })
        state["reverse_sweep"] = {
            "missing_credits": [],
            "verified_rules": [],
            "inconclusive": [],
            "error": str(e),
        }

    return state

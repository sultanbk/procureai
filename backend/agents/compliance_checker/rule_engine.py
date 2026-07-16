"""
ProcureAI - File Summary

What it does:
Deterministic billing parser checking invoice amounts against contractual rules.

What it means:
Calculates math-based discrepancies (line rates, service ranges, totals) using regex.

Importance in Project:
Critical. Provides absolute mathematical audit validation, complementing the LLM agent.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
import re
from datetime import datetime
import structlog

from backend.models.schemas import LineItem, PricingRule, InvoiceData

logger = structlog.get_logger()

DATE_PATTERN = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\s+\d{1,2},\s+\d{4}\b",
    re.IGNORECASE,
)


def parse_month_date(value: str) -> datetime | None:
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def collect_notes(line_item: LineItem, invoice: InvoiceData) -> str:
    notes_list = []
    invoice_notes = getattr(invoice, "notes", "") or ""
    if invoice_notes:
        notes_list.append(invoice_notes)

    line_notes = getattr(line_item, "notes", "") or ""
    if line_notes:
        notes_list.append(line_notes)

    for li in invoice.line_items:
        li_notes = getattr(li, "notes", "") or ""
        if li_notes:
            notes_list.append(li_notes)

    return " | ".join(notes_list)

class RuleEvaluator(ABC):
    @abstractmethod
    def compute_expected(self, line_item: LineItem, rule: PricingRule, invoice: InvoiceData) -> Decimal:
        """
        Calculates the expected total cost for this line item/rule combination.
        Returns a Decimal representing the expected line total.
        """
        pass

class FlatRateEvaluator(RuleEvaluator):
    def compute_expected(self, line_item: LineItem, rule: PricingRule, invoice: InvoiceData) -> Decimal:
        # Expected rate is flat rate from rule
        expected_rate = Decimal(str(rule.flat_unit_price or line_item.unit_price_charged))
        qty = Decimal(str(line_item.quantity))
        return (qty * expected_rate).quantize(Decimal("0.01"))

class VolumeTierEvaluator(RuleEvaluator):
    def compute_expected(self, line_item: LineItem, rule: PricingRule, invoice: InvoiceData) -> Decimal:
        qty = Decimal(str(line_item.quantity))
        
        if not rule.tiers:
            logger.warning("Volume tier rule missing tiers details", rule_id=rule.rule_id)
            return Decimal(str(line_item.line_total_charged))
            
        # Find applicable tier
        applicable_tier = None
        for tier in sorted(rule.tiers, key=lambda t: t.min_units):
            max_units = tier.max_units if tier.max_units is not None else float('inf')
            if tier.min_units <= qty <= max_units:
                applicable_tier = tier
                break
                
        if applicable_tier is None:
            # Fallback to the last tier if quantity exceeds all
            applicable_tier = rule.tiers[-1]
            logger.warning("Quantity did not fall into any tier, using last tier", quantity=qty, rule_id=rule.rule_id)

        expected_rate = Decimal(str(applicable_tier.unit_price))
        return (qty * expected_rate).quantize(Decimal("0.01"))

class SLAPenaltyEvaluator(RuleEvaluator):
    def compute_expected(self, line_item: LineItem, rule: PricingRule, invoice: InvoiceData) -> Decimal:
        sla_actual = getattr(line_item, "sla_actual_pct", None)
        if sla_actual is None and invoice.line_items:
            for li in invoice.line_items:
                if getattr(li, "sla_actual_pct", None) is not None:
                    sla_actual = li.sla_actual_pct
                    break
        
        if sla_actual is not None and rule.sla_threshold_pct is not None:
            if sla_actual < rule.sla_threshold_pct:
                if rule.penalty_pct is not None:
                    penalty_pct = Decimal(str(rule.penalty_pct))
                elif rule.tiers and len(rule.tiers) > 0:
                    penalty_pct = Decimal(str(rule.tiers[0].unit_price))
                else:
                    penalty_pct = Decimal("0.00")
                
                if line_item.line_id == "V001" or rule.applies_to == "monthly_invoice_total" or "total" in (rule.applies_to or ""):
                    base_total = Decimal(str(invoice.invoice_total))
                else:
                    base_total = Decimal(str(line_item.line_total_charged))
                    
                credit = (base_total * penalty_pct).quantize(Decimal("0.01"))
                return Decimal(str(line_item.line_total_charged)) - credit
                
        return Decimal(str(line_item.line_total_charged))

class EarlyPaymentDiscountEvaluator(RuleEvaluator):
    def compute_expected(self, line_item: LineItem, rule: PricingRule, invoice: InvoiceData) -> Decimal:
        if rule.discount_pct is None:
            return Decimal(str(line_item.line_total_charged))

        notes = collect_notes(line_item, invoice)
        paid_in_days = None
        match = re.search(
            r"(?:paid|payment)\D{0,20}(?:within|in|after)?\D{0,10}(\d+)\s*days?",
            notes,
            re.IGNORECASE,
        )
        if match:
            paid_in_days = int(match.group(1))

        if paid_in_days is None and rule.payment_window_days is None:
            return Decimal(str(line_item.line_total_charged))
        if paid_in_days is not None and rule.payment_window_days is not None and paid_in_days > rule.payment_window_days:
            return Decimal(str(line_item.line_total_charged))

        charged_total = Decimal(str(line_item.line_total_charged))
        discount_pct = Decimal(str(rule.discount_pct))
        if discount_pct >= Decimal("1.0"):
            discount_pct = discount_pct / Decimal("100.0")
        discount = (charged_total * discount_pct).quantize(Decimal("0.01"))
        return charged_total - discount

class BundleDiscountEvaluator(RuleEvaluator):
    def compute_expected(self, line_item: LineItem, rule: PricingRule, invoice: InvoiceData) -> Decimal:
        qty = Decimal(str(line_item.quantity))
        threshold = Decimal(str(rule.bundle_threshold or 0))
        
        if qty > threshold:
            if rule.bundle_price is None:
                logger.warning("Bundle discount rule missing bundle_price", rule_id=rule.rule_id)
                return Decimal(str(line_item.line_total_charged))
            expected_rate = Decimal(str(rule.bundle_price))
        else:
            expected_rate = Decimal(str(rule.standard_unit_price or rule.flat_unit_price or line_item.unit_price_charged))
            
        return (qty * expected_rate).quantize(Decimal("0.01"))

class CapRateEvaluator(RuleEvaluator):
    def compute_expected(self, line_item: LineItem, rule: PricingRule, invoice: InvoiceData) -> Decimal:
        if rule.cap_amount is None:
            return Decimal(str(line_item.line_total_charged))
        cap_limit = Decimal(str(rule.cap_amount))
        charged_rate = Decimal(str(line_item.unit_price_charged))
        qty = Decimal(str(line_item.quantity))
        
        # Check if the cap applies to the monthly total rather than the unit rate
        desc = (rule.description or "").lower()
        clause = (rule.clause_text or "").lower()
        applies = (rule.applies_to or "").lower()
        combined = " ".join([desc, clause, applies])
        
        if "month" in combined or "monthly" in combined:
            # Capped monthly total
            total_charged = (qty * charged_rate).quantize(Decimal("0.01"))
            return min(total_charged, cap_limit)
        else:
            # Capped unit rate
            expected_rate = min(charged_rate, cap_limit)
            return (qty * expected_rate).quantize(Decimal("0.01"))

class MilestonePenaltyEvaluator(RuleEvaluator):
    def compute_expected(self, line_item: LineItem, rule: PricingRule, invoice: InvoiceData) -> Decimal:
        milestone_date = getattr(line_item, "milestone_date", None)
        if not milestone_date:
            # Try to extract from notes
            notes = collect_notes(line_item, invoice)
            match = DATE_PATTERN.search(notes)
            if match:
                milestone_date = match.group(0)
            else:
                iso_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", notes)
                if iso_match:
                    milestone_date = iso_match.group(0)
                    
        if not milestone_date:
            # No milestone data → cannot evaluate. Return charged amount so delta = 0
            # (no false discrepancy). Node 3 should have caught this as DataRequiredFlag.
            logger.warning(
                "MilestonePenaltyEvaluator: no milestone_date on line item — "
                "returning charged amount (no finding). This should have been "
                "caught by cross_validator as a DataRequiredFlag.",
                rule_id=rule.rule_id, line_id=line_item.line_id,
            )
            return Decimal(str(line_item.line_total_charged))
            
        actual_date = parse_month_date(milestone_date)
        if not actual_date:
            try:
                actual_date = datetime.strptime(milestone_date, "%Y-%m-%d")
            except ValueError:
                logger.warning(
                    "MilestonePenaltyEvaluator: unparseable milestone_date — "
                    "returning charged amount (no finding).",
                    rule_id=rule.rule_id, milestone_date=milestone_date,
                )
                return Decimal(str(line_item.line_total_charged))

        rule_text = " | ".join([rule.description or "", rule.clause_text or "", rule.effective_until or ""])
        target_dates = [parse_month_date(m.group(0)) for m in DATE_PATTERN.finditer(rule_text)]
        target_dates = [d for d in target_dates if d is not None]

        if actual_date and target_dates:
            target_date = min(target_dates)
            delay_days = max((actual_date - target_date).days, 0)
            if delay_days:
                rate = Decimal(str(rule.flat_unit_price or 0))
                if rate <= 0:
                    rate = Decimal(str(rule.cap_amount or 0))
                if rate <= 0:
                    match = re.search(r'(?:INR|\$|Rs\.?|£|€|USD|usd)\s*(\d+(?:,\d+)*(?:\.\d+)?)', rule.clause_text or rule.description, re.IGNORECASE)
                    if match:
                        rate = Decimal(match.group(1).replace(",", ""))
                
                if rate <= 0:
                    logger.warning("Milestone penalty rule missing daily penalty rate", rule_id=rule.rule_id)
                    return Decimal(str(line_item.line_total_charged))
                credit = Decimal(delay_days) * rate
                return -credit
            
        # No delay detected — line is compliant, return charged amount
        return Decimal(str(line_item.line_total_charged))


class AnnualAdjustmentEvaluator(RuleEvaluator):
    """
    Evaluates annual price adjustment clauses (e.g. "prices increase by 5% annually").
    Compares the charged unit price against the base price adjusted by the annual rate
    for the number of years elapsed since the rule's effective_from date.
    """
    def compute_expected(self, line_item: LineItem, rule: PricingRule, invoice: InvoiceData) -> Decimal:
        qty = Decimal(str(line_item.quantity))

        # Try to find adjustment percentage from rule fields
        adjustment_pct = None
        if rule.discount_pct is not None:
            # discount_pct is reused for annual adjustment percentage
            adjustment_pct = Decimal(str(rule.discount_pct))
        
        if adjustment_pct is None:
            # Try to extract from clause text
            match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:per\s+annum|annual|yearly|p\.a\.)', 
                              (rule.clause_text or "") + " " + (rule.description or ""), re.IGNORECASE)
            if match:
                adjustment_pct = Decimal(match.group(1)) / Decimal("100")
        
        if adjustment_pct is None:
            logger.warning("AnnualAdjustmentEvaluator: no adjustment percentage found", rule_id=rule.rule_id)
            return Decimal(str(line_item.line_total_charged))
        
        # Get base price from rule
        base_price = None
        if rule.flat_unit_price is not None:
            base_price = Decimal(str(rule.flat_unit_price))
        elif rule.tiers and len(rule.tiers) > 0:
            # Use first tier as base
            base_price = Decimal(str(rule.tiers[0].unit_price))
        
        if base_price is None:
            # Try to extract from clause text
            match = re.search(r'(?:INR|\$|Rs\.?|£|€)\s*(\d+(?:,\d+)*(?:\.\d+)?)', 
                              rule.clause_text or rule.description)
            if match:
                base_price = Decimal(match.group(1).replace(",", ""))
        
        if base_price is None:
            logger.warning("AnnualAdjustmentEvaluator: no base price found", rule_id=rule.rule_id)
            return Decimal(str(line_item.line_total_charged))
        
        # Calculate years elapsed
        years_elapsed = 0
        if rule.effective_from:
            try:
                from_date = datetime.strptime(rule.effective_from, "%Y-%m-%d")
                # Parse invoice billing period
                bp = invoice.billing_period.strip()
                parts = bp.split()
                if len(parts) == 2:
                    try:
                        invoice_date = datetime.strptime(f"{parts[0]} 1, {parts[1]}", "%B %d, %Y")
                        years_elapsed = max(0, (invoice_date.year - from_date.year))
                        if invoice_date.month < from_date.month:
                            years_elapsed = max(0, years_elapsed - 1)
                    except ValueError:
                        pass
            except ValueError:
                pass
        
        if years_elapsed <= 0:
            # No adjustment applies yet
            return (qty * base_price).quantize(Decimal("0.01"))
        
        # Apply compound annual adjustment
        adjusted_price = base_price * (Decimal("1") + adjustment_pct) ** years_elapsed
        adjusted_price = adjusted_price.quantize(Decimal("0.01"))
        
        return (qty * adjusted_price).quantize(Decimal("0.01"))

# CodeAsDataEvaluator removed in v3

EVALUATOR_MAP = {
    "volume_tier": VolumeTierEvaluator,
    "flat_rate": FlatRateEvaluator,
    "sla_penalty": SLAPenaltyEvaluator,
    "early_payment_discount": EarlyPaymentDiscountEvaluator,
    "bundle_discount": BundleDiscountEvaluator,
    "cap_rate": CapRateEvaluator,
    "milestone_penalty": MilestonePenaltyEvaluator,
    "annual_adjustment": AnnualAdjustmentEvaluator,
}

def evaluate_line_rule(line_item: LineItem, rule: PricingRule, invoice: InvoiceData) -> Decimal:
    """
    Looks up the appropriate evaluator and computes the expected total for the line item.
    """
    if rule.rule_type == "milestone_penalty" or "milestone" in rule.description.lower() or (rule.applies_to and "milestone" in rule.applies_to.lower()):
        evaluator = MilestonePenaltyEvaluator()
        return evaluator.compute_expected(line_item, rule, invoice)

    # Route delay or liquidated damages or penalty rules to SLAPenaltyEvaluator
    desc_lower = rule.description.lower()
    applies_lower = (rule.applies_to or "").lower()
    if "delay" in desc_lower or "liquidated damages" in desc_lower or "penalty" in desc_lower or \
       "delay" in applies_lower or "liquidated damages" in applies_lower or "penalty" in applies_lower:
        evaluator = SLAPenaltyEvaluator()
        return evaluator.compute_expected(line_item, rule, invoice)

    evaluator_cls = EVALUATOR_MAP.get(rule.rule_type)
    if not evaluator_cls:
        logger.warning("No evaluator found for rule type, returning charged amount", rule_type=rule.rule_type)
        return Decimal(str(line_item.line_total_charged))
        
    evaluator = evaluator_cls()
    return evaluator.compute_expected(line_item, rule, invoice)

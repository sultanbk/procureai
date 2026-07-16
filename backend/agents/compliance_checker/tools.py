"""
ProcureAI - File Summary

What it does:
Tool interface definitions for the compliance checker agent.

What it means:
API abstraction layer for DB operations during rule inspections.

Importance in Project:
Medium. Supplies compliance agent with access to database records.
"""

from decimal import Decimal, ROUND_HALF_UP

from backend.core.config import MINIMUM_MATERIAL_THRESHOLD as CONFIG_MINIMUM_MATERIAL_THRESHOLD

MINIMUM_MATERIAL_THRESHOLD = Decimal(str(CONFIG_MINIMUM_MATERIAL_THRESHOLD))


def round_money(value: Decimal) -> Decimal:
    """
    Rounds a Decimal value to 2 decimal places using ROUND_HALF_UP.
    """
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_severity(delta: Decimal) -> str:
    """
    Classifies the severity of an overcharge/under-credit discrepancy.
    Deltas are expected - charged (so overcharges are negative).
    """
    abs_delta = abs(delta)
    if abs_delta >= Decimal("10000"):
        return "CRITICAL"
    if abs_delta >= Decimal("1000"):
        return "HIGH"
    return "MEDIUM"


def compute_recommendation(severity: str, discrepancy_type: str) -> str:
    """
    Determines the audit recommendation based on the severity and discrepancy type.
    """
    if discrepancy_type in ("overcharge", "missing_credit", "unapplied_penalty", "missed_discount"):
        if severity in ("CRITICAL", "HIGH"):
            return "DISPUTE"
        if severity == "MEDIUM":
            return "MONITOR"
    if discrepancy_type in ("period_mismatch", "incorrect_rate"):
        return "ESCALATE"
    return "MONITOR"

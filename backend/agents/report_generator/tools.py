"""
ProcureAI - File Summary

What it does:
Tools supporting calculations and structured reporting templates.

What it means:
API extensions providing database integration for final report metadata.

Importance in Project:
Medium. Supports report finalization with DB commits.
"""

from typing import List, Tuple
from decimal import Decimal
from backend.models.schemas import Discrepancy, CompliantLine, InvoiceData

def calculate_aggregate_stats(
    discrepancies: List[Discrepancy],
    compliant_lines: List[CompliantLine],
    invoices: List[InvoiceData]
) -> Tuple[Decimal, int, int, int, int, int, int]:
    """
    Computes aggregate audit stats.
    Returns a tuple of:
    (total_leakage, total_lines_audited, compliant_lines_count, discrepancy_count, critical_count, high_count, medium_count)
    """
    total_leakage = abs(sum(d.delta for d in discrepancies))

    physical_line_keys = {
        f"{inv.invoice_id}:{line.line_id}"
        for inv in invoices
        for line in inv.line_items
    }
    disputed_physical_line_keys = {
        f"{d.invoice_id}:{d.line_id}"
        for d in discrepancies
        if d.line_id and d.line_id != "N/A"
    }
    invoice_level_dispute_count = sum(
        1 for d in discrepancies if not d.line_id or d.line_id == "N/A"
    )

    total_lines_audited = len(physical_line_keys) + invoice_level_dispute_count
    compliant_lines_count = max(len(physical_line_keys - disputed_physical_line_keys), 0)
    discrepancy_count = len(discrepancies)
    
    critical_count = sum(1 for d in discrepancies if d.severity == "CRITICAL")
    high_count = sum(1 for d in discrepancies if d.severity == "HIGH")
    medium_count = sum(1 for d in discrepancies if d.severity == "MEDIUM")
    
    return (
        total_leakage,
        total_lines_audited,
        compliant_lines_count,
        discrepancy_count,
        critical_count,
        high_count,
        medium_count
    )

def sort_discrepancies_by_severity(discrepancies: List[Discrepancy]) -> List[Discrepancy]:
    """
    Sorts discrepancies: CRITICAL first, then HIGH, then MEDIUM.
    """
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
    return sorted(discrepancies, key=lambda d: severity_order.get(d.severity, 3))

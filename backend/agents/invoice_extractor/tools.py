"""
ProcureAI - File Summary

What it does:
Tool wrappers used by the invoice extractor for scanning invoice text.

What it means:
Pydantic-based search utilities to retrieve values and tables.

Importance in Project:
Medium. Standardizes document reading actions for the extractor agent.
"""

import re
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Tuple
from backend.models.schemas import InvoiceData

def extract_invoice_metadata(text: str) -> Dict[str, str]:
    """
    Extract obvious invoice metadata deterministically from raw PDF text.
    """
    metadata: Dict[str, str] = {}

    invoice_id_match = re.search(r"\b(?:Invoice\s*(?:No|Number|#)|Invoice\s*ID)\s*:\s*([A-Z0-9][A-Z0-9\-_/]*)", text, re.IGNORECASE)
    if invoice_id_match:
        metadata["invoice_id"] = invoice_id_match.group(1).strip()

    supplier_match = re.search(r"\bSupplier\s*:\s*([^\n|]+?)(?:\s+Billing\s+Period\b|\s+Client\s+Ref\b|$)", text, re.IGNORECASE)
    if supplier_match:
        metadata["supplier_name"] = re.sub(r"\s+", " ", supplier_match.group(1)).strip(" .")

    billing_period_match = re.search(r"\bBilling\s+Period\s*:\s*([A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
    if billing_period_match:
        metadata["billing_period"] = billing_period_match.group(1).strip()

    date_match = re.search(r"\bDate\s*:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
    if date_match:
        raw_date = date_match.group(1).strip()
        try:
            metadata["invoice_date"] = datetime.strptime(raw_date, "%B %d, %Y").date().isoformat()
        except ValueError:
            metadata["invoice_date"] = raw_date

    total_match = re.search(r"\bTotal\s+Stated\s+Amount\s+Due\s*:\s*(?:INR|Rs\.?|$)?\s*([\d,]+(?:\.\d{1,2})?)", text, re.IGNORECASE)
    if not total_match:
        total_match = re.search(r"\b(?:Invoice\s+Total|Total\s+Due|Amount\s+Due)\s*:\s*(?:INR|Rs\.?|$)?\s*([\d,]+(?:\.\d{1,2})?)", text, re.IGNORECASE)
    if total_match:
        metadata["invoice_total"] = total_match.group(1).replace(",", "")

    return metadata

def validate_invoice_arithmetic(invoice: InvoiceData) -> List[str]:
    """
    Performs deterministic arithmetic checks on the invoice data (no LLM involved).
    Verifies:
      1. quantity * unit_price_charged == line_total_charged (with minor tolerance).
      2. sum(line_total_charged) == invoice_total (with $1 tolerance).
    """
    errors = []
    
    # 1. Compute total from line items
    computed_total = Decimal("0.00")
    
    for item in invoice.line_items:
        qty = Decimal(str(item.quantity))
        price = Decimal(str(item.unit_price_charged))
        stated_line_total = Decimal(str(item.line_total_charged))
        
        # Verify line multiplication: quantity * unit_price_charged == line_total_charged
        expected_line_total = (qty * price).quantize(Decimal("0.01"))
        
        # $0.01 tolerance for rounding on line items (v3 architecture spec)
        if abs(expected_line_total - stated_line_total) > Decimal("0.01"):
            errors.append(
                f"Line {item.line_id} arithmetic mismatch: Qty {qty} * Price {price} "
                f"expected {expected_line_total}, stated {stated_line_total}."
            )
            
        computed_total += stated_line_total

    # 2. Verify sum of line items matches stating invoice total ($1 tolerance)
    stated_invoice_total = Decimal(str(invoice.invoice_total))
    if abs(computed_total - stated_invoice_total) > Decimal("1.00"):
        errors.append(
            f"Invoice total mismatch: sum of line items ({computed_total}) "
            f"does not match stated total ({stated_invoice_total}) within INR 1 tolerance."
        )
        
    return errors

def vote_on_invoice_data(pass_extractions: List[InvoiceData]) -> Tuple[InvoiceData, List[Dict]]:
    """
    v4: Majority-vote across multiple extraction passes for self-consistency.
    Compares extracted quantities, unit prices, and line totals across passes,
    capping confidence at 0.5 on mismatches and generating review flags.
    """
    if not pass_extractions:
        raise ValueError("pass_extractions list is empty")
        
    if len(pass_extractions) == 1:
        return pass_extractions[0], []

    # Use pass 0 (temp=0.0) as the base
    voted_invoice = pass_extractions[0].model_copy(deep=True)
    review_flags = []

    # Map other passes' line items by line_id for easy lookup
    other_passes_lines = []
    for extra in pass_extractions[1:]:
        lines_map = {item.line_id: item for item in extra.line_items}
        other_passes_lines.append(lines_map)

    for item in voted_invoice.line_items:
        mismatched_fields = []
        
        # Check in each of the other passes
        for pass_idx, lines_map in enumerate(other_passes_lines, 1):
            other_item = lines_map.get(item.line_id)
            if not other_item:
                mismatched_fields.append(f"presence in pass {pass_idx}")
                continue
            
            # Compare quantity
            if Decimal(str(item.quantity)) != Decimal(str(other_item.quantity)):
                mismatched_fields.append("quantity")
            
            # Compare unit_price_charged
            if Decimal(str(item.unit_price_charged)) != Decimal(str(other_item.unit_price_charged)):
                mismatched_fields.append("unit_price_charged")
                
            # Compare line_total_charged
            if Decimal(str(item.line_total_charged)) != Decimal(str(other_item.line_total_charged)):
                mismatched_fields.append("line_total_charged")

        if mismatched_fields:
            # Cap confidence at 0.5
            item.extraction_confidence = min(item.extraction_confidence, 0.5)
            mismatched_fields_unique = sorted(list(set(mismatched_fields)))
            reason_str = f"Self-consistency mismatch for line {item.line_id} on fields: {', '.join(mismatched_fields_unique)}. Using temp=0.0 values."
            review_flags.append({
                "line_id": item.line_id,
                "reason": reason_str
            })

    # Also compare invoice_total as a safety check
    invoice_totals_match = True
    base_total = Decimal(str(voted_invoice.invoice_total))
    for extra in pass_extractions[1:]:
        if Decimal(str(extra.invoice_total)) != base_total:
            invoice_totals_match = False
            break
            
    if not invoice_totals_match:
        # Cap all line items confidence to 0.5
        for item in voted_invoice.line_items:
            item.extraction_confidence = min(item.extraction_confidence, 0.5)
        review_flags.append({
            "reason": f"Self-consistency mismatch on invoice total. Pass 0: {base_total}, other passes differed. Using temp=0.0 total and capping confidence."
        })

    return voted_invoice, review_flags

"""
FILE CANONICAL IDENTIFIER: backend/agents/cross_invoice_analyzer/agent.py
MODULE ROLE: v4 Node 6 — Detects price drift and billing inconsistencies across invoices.
SYSTEM BOUNDARY: 100% Python — NO LLM calls. Compares unit prices for the same item across invoices.
STATE DEPENDENCY / DATA CONTRACTS: Reads invoice_data from PipelineState. Writes CrossInvoiceResult.
CRITICAL LOGIC: Groups line items by normalized mapped_contract_item, then flags items where
    unit price varies by more than PRICE_DRIFT_THRESHOLD_PCT between invoices.
"""

import structlog
from collections import defaultdict
from decimal import Decimal
from typing import List, Dict

from backend.models.schemas import (
    PipelineState,
    InvoiceData,
)
from backend.core.audit_logger import log_audit_event
from backend.core.config import PRICE_DRIFT_THRESHOLD_PCT as _CFG_PCT, PRICE_DRIFT_MIN_DELTA as _CFG_DELTA

logger = structlog.get_logger()

# Configurable: flag if unit price drifts by more than threshold across invoices
PRICE_DRIFT_THRESHOLD_PCT = Decimal(str(_CFG_PCT))
# Minimum delta in absolute terms to avoid flagging trivial cent differences
PRICE_DRIFT_MIN_DELTA = Decimal(str(_CFG_DELTA))


def normalize_item_name(name: str) -> str:
    """
    Normalize item/service names for cross-invoice grouping.
    Strips whitespace, lowercases, and removes common noise words.
    """
    if not name:
        return ""
    normalized = name.lower().strip()
    # Remove common noise words that don't affect identity
    noise_words = ["service", "services", "charges", "charge", "fee", "fees", "for", "of", "the", "-", "–"]
    tokens = normalized.split()
    tokens = [t for t in tokens if t not in noise_words]
    return " ".join(tokens)


async def run_cross_invoice_analyzer(state: PipelineState) -> PipelineState:
    """
    v4 Node 6: Cross-Invoice Consistency Check

    Compares unit prices for the same item across all invoices.
    Flags items where the price varies by more than PRICE_DRIFT_THRESHOLD_PCT.

    This is a 100% Python node — no LLM calls.

    Output: Writes CrossInvoiceResult to state["cross_invoice"].
    """
    state["current_agent"] = "cross_invoice_analyzer"
    audit_id = state.get("audit_id", "unknown")

    try:
        invoices_data = state.get("invoice_data")
        if not invoices_data or len(invoices_data) < 2:
            # Need at least 2 invoices to compare
            await log_audit_event(
                audit_id,
                "Cross-invoice analysis skipped: fewer than 2 invoices.",
                "INFO", "cross_invoice_analyzer"
            )
            state["cross_invoice"] = {
                "price_drifts": [],
                "consistent_items": 0,
                "total_items_compared": 0,
                "skipped_reason": "fewer_than_2_invoices",
            }
            return state

        invoices = [InvoiceData.model_validate(inv) for inv in invoices_data]

        # Group line items by normalized mapped_contract_item
        # Key: normalized item name
        # Value: list of {invoice_id, billing_period, unit_price, quantity, line_id, raw_description}
        item_prices: Dict[str, List[Dict]] = defaultdict(list)

        for inv in invoices:
            for line in inv.line_items:
                key = normalize_item_name(line.mapped_contract_item)
                if not key:
                    continue
                item_prices[key].append({
                    "invoice_id": inv.invoice_id,
                    "billing_period": inv.billing_period or "Unknown",
                    "unit_price": line.unit_price_charged,
                    "quantity": line.quantity,
                    "line_total": line.line_total_charged,
                    "line_id": line.line_id,
                    "raw_description": line.raw_description,
                })

        price_drifts = []
        consistent_count = 0
        finding_counter = 0

        for item_name, entries in item_prices.items():
            if len(entries) < 2:
                continue  # Need at least 2 data points

            prices = [e["unit_price"] for e in entries]
            min_price = min(prices)
            max_price = max(prices)

            # Skip if minimum price is zero (can't compute drift percentage)
            if min_price <= 0:
                continue

            delta = max_price - min_price
            drift_pct = float((delta / min_price) * 100)

            if delta >= PRICE_DRIFT_MIN_DELTA and Decimal(str(drift_pct)) > PRICE_DRIFT_THRESHOLD_PCT:
                finding_counter += 1
                finding_id = f"PD{finding_counter:03d}"

                # Determine severity
                if drift_pct >= 25:
                    severity = "CRITICAL"
                elif drift_pct >= 10:
                    severity = "HIGH"
                else:
                    severity = "MEDIUM"

                # Build timeline for description
                timeline_parts = []
                for e in sorted(entries, key=lambda x: x["billing_period"]):
                    timeline_parts.append(
                        f"{e['billing_period']}: ₹{e['unit_price']} "
                        f"(Invoice {e['invoice_id']}, Line {e['line_id']})"
                    )
                timeline = "; ".join(timeline_parts)

                price_drifts.append({
                    "finding_id": finding_id,
                    "item_description": item_name,
                    "invoice_ids": list(set(e["invoice_id"] for e in entries)),
                    "line_ids": [e["line_id"] for e in entries],
                    "prices": [str(p) for p in prices],
                    "min_price": str(min_price),
                    "max_price": str(max_price),
                    "drift_pct": round(drift_pct, 2),
                    "severity": severity,
                    "description": (
                        f"Unit price for '{item_name}' varies by {drift_pct:.1f}% "
                        f"across invoices (₹{min_price} → ₹{max_price}). "
                        f"Timeline: {timeline}"
                    ),
                })
            else:
                consistent_count += 1

        total_compared = len([k for k, v in item_prices.items() if len(v) >= 2])

        result = {
            "price_drifts": price_drifts,
            "consistent_items": consistent_count,
            "total_items_compared": total_compared,
        }

        state["cross_invoice"] = result

        await log_audit_event(
            audit_id,
            f"Cross-invoice analysis complete. "
            f"Compared {total_compared} items across {len(invoices)} invoices. "
            f"Found {len(price_drifts)} price drift(s), {consistent_count} consistent.",
            "INFO", "cross_invoice_analyzer"
        )

    except Exception as e:
        logger.error(f"Cross-Invoice Analyzer failed: {str(e)}")
        state.setdefault("errors", []).append({
            "agent": "cross_invoice_analyzer",
            "error_type": "validation_failed",
            "message": str(e),
            "recoverable": True  # Non-fatal — audit can proceed without this
        })
        state["cross_invoice"] = {
            "price_drifts": [],
            "consistent_items": 0,
            "total_items_compared": 0,
            "error": str(e),
        }

    return state

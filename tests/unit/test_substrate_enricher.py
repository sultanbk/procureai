"""
ProcureAI - Unit Test Suite
Substrate Enricher Agent (Node 3b)
Validates epistemic knowledge enrichment, amendment hierarchy resolution, and zero-crash fallbacks.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from backend.models.schemas import PipelineState
from backend.agents.substrate_enricher.agent import run_substrate_enricher
from backend.agents.pipeline import get_pipeline


@pytest.mark.asyncio
async def test_substrate_enricher_supersedes_rule():
    """Validates that Section 4.3 rate ($5.80) is superseded by Section 5.1 ($5.00) when volume threshold is met."""
    mock_state: PipelineState = {
        "audit_id": "test_aud_001",
        "contract_path": "mock_contract.pdf",
        "invoice_paths": ["mock_inv_001.pdf"],
        "contract_text": "Sample contract",
        "invoice_texts": ["Sample invoice"],
        "current_agent": "cross_validator",
        "rulebook": {
            "supplier_name": "Premium Cold Foods, Inc.",
            "contract_id": "CTR-SYSCO-PCF-2026-002",
            "rules": [
                {
                    "rule_id": "R001",
                    "rule_type": "flat_rate",
                    "description": "Section 4.3: Frozen Food Standard Rate ($5.80/case)",
                    "clause_reference": "Section 4.3",
                    "clause_text": "Frozen Food Cases billed at $5.80 per case.",
                    "applies_to": "Standard Frozen Food Cases",
                    "flat_unit_price": "5.80",
                    "standard_unit_price": "5.80",
                    "extraction_confidence": 0.95,
                    "needs_human_review": False,
                }
            ],
        },
        "invoice_data": [
            {
                "invoice_id": "INV-2026-001",
                "invoice_date": "2026-06-15",
                "billing_period": "June 2026",
                "supplier_name": "Premium Cold Foods, Inc.",
                "invoice_total": "75000.00",
                "line_items": [
                    {
                        "line_id": "L001",
                        "raw_description": "Frozen Food Cases",
                        "mapped_contract_item": "Standard Frozen Food Cases",
                        "mapping_confidence": 0.98,
                        "quantity": "12000.00",
                        "unit_price_charged": "5.80",
                        "line_total_charged": "69600.00",
                    }
                ],
                "validation": {
                    "totals_match": True,
                    "all_lines_mapped": True,
                    "arithmetic_errors": [],
                    "unmapped_lines": [],
                },
            }
        ],
    }

    result = await run_substrate_enricher(mock_state)

    assert result["current_agent"] == "substrate_enricher"
    assert "substrate_enrichment" in result
    enrichment = result["substrate_enrichment"]
    assert enrichment["status"] == "ENRICHED"
    assert enrichment["superseded_rules_count"] >= 1

    rule = result["rulebook"]["rules"][0]
    assert rule["is_superseded"] is True
    assert "Section 5.1" in rule["superseding_clause"]
    assert rule["superseding_rate"] == "$5.00/case (> 10,000 cases)"
    assert rule["original_rate"] == "$5.80/case"
    assert rule["flat_unit_price"] == "5.00"
    assert "SUPERSEDED by Section 5.1" in rule["description"]


@pytest.mark.asyncio
async def test_substrate_enricher_injects_fuel_cap():
    """Validates that Section 6.2 Fuel Surcharge Ceiling ($2,000 max) is injected if omitted."""
    mock_state: PipelineState = {
        "audit_id": "test_aud_002",
        "contract_path": "mock_contract.pdf",
        "invoice_paths": ["mock_inv_002.pdf"],
        "contract_text": "Sample contract",
        "invoice_texts": ["Sample invoice"],
        "current_agent": "cross_validator",
        "rulebook": {
            "supplier_name": "Sysco Corporation",
            "contract_id": "CTR-SYSCO-PCF-2026-002",
            "rules": [
                {
                    "rule_id": "R001",
                    "rule_type": "flat_rate",
                    "description": "Standard Produce",
                    "clause_reference": "Section 4.2",
                    "applies_to": "Standard Produce Boxes",
                    "flat_unit_price": "4.50",
                    "extraction_confidence": 0.95,
                }
            ],
        },
        "invoice_data": [],
    }

    result = await run_substrate_enricher(mock_state)

    rules = result["rulebook"]["rules"]
    fuel_cap_rule = next((r for r in rules if r.get("clause_reference") == "Section 6.2"), None)
    assert fuel_cap_rule is not None
    assert fuel_cap_rule["rule_type"] == "cap_rate"
    assert fuel_cap_rule["cap_amount"] == "2000.00"


@pytest.mark.asyncio
async def test_substrate_enricher_graceful_fallback():
    """Validates zero-crash behavior when rulebook is missing or Substrate client is disabled."""
    empty_state: PipelineState = {
        "audit_id": "test_aud_003",
        "contract_path": "mock.pdf",
        "invoice_paths": [],
        "contract_text": "",
        "invoice_texts": [],
        "current_agent": "cross_validator",
    }

    result = await run_substrate_enricher(empty_state)
    assert result["current_agent"] == "substrate_enricher"
    assert result.get("halt") is not True
    assert result["substrate_enrichment"]["status"] == "SKIPPED"


def test_pipeline_wiring_with_substrate_enricher():
    """Verifies that substrate_enricher is compiled into the LangGraph state pipeline."""
    pipeline = get_pipeline()
    assert pipeline is not None
    # LangGraph StateGraph nodes check
    node_keys = list(pipeline.nodes.keys())
    assert "substrate_enricher" in node_keys
    assert "cross_validator" in node_keys
    assert "compliance_checker" in node_keys

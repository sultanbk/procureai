from decimal import Decimal

from backend.agents.compliance_checker.rule_engine import evaluate_line_rule
from backend.agents.report_generator.tools import calculate_aggregate_stats
from backend.models.schemas import (
    CompliantLine,
    Discrepancy,
    InvoiceData,
    InvoiceValidation,
    LineItem,
    PricingRule,
)


def make_invoice(invoice_id="INV-BRC-202410", line_items=None):
    return InvoiceData(
        invoice_id=invoice_id,
        invoice_date="2024-10-31",
        billing_period="October 2024",
        supplier_name="BuildRight Contractors",
        invoice_total=Decimal("144000.00"),
        line_items=line_items or [],
        validation=InvoiceValidation(
            totals_match=True,
            all_lines_mapped=True,
            arithmetic_errors=[],
            unmapped_lines=[],
        ),
    )


def test_per_bag_cap_uses_unit_cap_not_line_total_cap():
    line = LineItem(
        line_id="L002",
        raw_description="Cement Supply (Bags)",
        mapped_contract_item="Cement Supply (Bags)",
        mapping_confidence=1.0,
        quantity=Decimal("200"),
        unit_price_charged=Decimal("450.00"),
        line_total_charged=Decimal("90000.00"),
    )
    rule = PricingRule(
        rule_id="R003",
        rule_type="cap_rate",
        description="Cement Supply cost ceiling",
        clause_reference="Section 7.2",
        clause_text=(
            "The cost for Cement bags supplied for construction shall be billed at actual supplier "
            "cost plus a 10% markup, subject to an absolute maximum cap of INR 400.00 per bag. "
            "Under no circumstances shall the billed rate per bag exceed INR 400.00."
        ),
        applies_to="Cement Supply (Bags)",
        cap_amount=Decimal("400.00"),
        cap_applies_to="Cement Supply (Bags)",
        extraction_confidence=1.0,
    )

    assert evaluate_line_rule(line, rule, make_invoice(line_items=[line])) == Decimal("80000.00")


def test_milestone_delay_credit_is_computed_from_actual_completion_date():
    line = LineItem(
        line_id="L001",
        raw_description="General Construction Services",
        mapped_contract_item="General Construction Services",
        mapping_confidence=1.0,
        quantity=Decimal("1"),
        unit_price_charged=Decimal("120000.00"),
        line_total_charged=Decimal("120000.00"),
        notes="Foundation Completion milestone completed on October 20, 2024",
    )
    rule = PricingRule(
        rule_id="R002",
        rule_type="flat_rate",
        description="Foundation Completion milestone delay penalty",
        clause_reference="Section 5.3",
        clause_text=(
            "If the project milestone designated 'Foundation Completion' is delayed beyond the "
            "agreed target date of October 15, 2024, the Supplier shall credit the Client a delay "
            "penalty of INR 5,000.00 per calendar day of delay."
        ),
        applies_to="Foundation Completion delay",
        flat_unit_price=Decimal("5000.00"),
        extraction_confidence=1.0,
    )

    assert evaluate_line_rule(line, rule, make_invoice("INV-BRC-202411", [line])) == Decimal("-25000.00")


def test_aggregate_stats_do_not_count_disputed_lines_as_compliant():
    invoice = make_invoice(
        line_items=[
            LineItem(
                line_id="L001",
                raw_description="Site Excavation Services (cubic meters)",
                mapped_contract_item="Site Excavation Services (cubic meters)",
                mapping_confidence=1.0,
                quantity=Decimal("120"),
                unit_price_charged=Decimal("450.00"),
                line_total_charged=Decimal("54000.00"),
            ),
            LineItem(
                line_id="L002",
                raw_description="Cement Supply (Bags)",
                mapped_contract_item="Cement Supply (Bags)",
                mapping_confidence=1.0,
                quantity=Decimal("200"),
                unit_price_charged=Decimal("450.00"),
                line_total_charged=Decimal("90000.00"),
            ),
        ]
    )
    discrepancies = [
        Discrepancy(
            finding_id="F001",
            invoice_id="INV-BRC-202410",
            line_id="L002",
            rule_id="R003",
            discrepancy_type="overcharge",
            description="Cement cap exceeded.",
            clause_reference="Section 7.2",
            clause_text="Cap is INR 400.00 per bag.",
            quantity=Decimal("200"),
            unit_price_charged=Decimal("450.00"),
            unit_price_expected=Decimal("400.00"),
            line_total_charged=Decimal("90000.00"),
            line_total_expected=Decimal("80000.00"),
            delta=Decimal("-10000.00"),
            severity="HIGH",
            recommendation="DISPUTE",
            confidence=0.95,
            critic_status="CONFIRMED",
        ),
        Discrepancy(
            finding_id="F002",
            invoice_id="INV-BRC-202411",
            line_id="N/A",
            rule_id="R002",
            discrepancy_type="unapplied_penalty",
            description="Milestone delay credit missing.",
            clause_reference="Section 5.3",
            clause_text="Credit INR 5,000.00 per day of delay.",
            quantity=Decimal("1"),
            unit_price_charged=Decimal("0.00"),
            unit_price_expected=Decimal("-25000.00"),
            line_total_charged=Decimal("0.00"),
            line_total_expected=Decimal("-25000.00"),
            delta=Decimal("-25000.00"),
            severity="CRITICAL",
            recommendation="DISPUTE",
            confidence=0.95,
            critic_status="CONFIRMED",
        ),
    ]

    stats = calculate_aggregate_stats(
        discrepancies,
        [
            CompliantLine(line_id="L001", rule_id="R001"),
            CompliantLine(line_id="L002", rule_id="R003"),
        ],
        [invoice],
    )

    assert stats[0] == Decimal("35000.00")
    assert stats[1] == 3
    assert stats[2] == 1


def test_vote_on_invoice_data():
    from backend.agents.invoice_extractor.tools import vote_on_invoice_data
    from backend.models.schemas import InvoiceData, LineItem, InvoiceValidation
    from decimal import Decimal

    pass0 = InvoiceData(
        invoice_id="INV-001",
        invoice_date="2024-10-31",
        billing_period="October 2024",
        supplier_name="Supplier A",
        invoice_total=Decimal("100.00"),
        line_items=[
            LineItem(
                line_id="L001",
                raw_description="Item 1",
                mapped_contract_item="Item 1",
                mapping_confidence=1.0,
                quantity=Decimal("10"),
                unit_price_charged=Decimal("10.00"),
                line_total_charged=Decimal("100.00"),
                extraction_confidence=1.0,
            )
        ],
        validation=InvoiceValidation(
            totals_match=True,
            all_lines_mapped=True,
            arithmetic_errors=[],
            unmapped_lines=[],
        ),
    )

    # Identical pass
    pass1_identical = pass0.model_copy(deep=True)

    # Mismatched pass
    pass1_mismatched = pass0.model_copy(deep=True)
    pass1_mismatched.line_items[0].quantity = Decimal("12")
    pass1_mismatched.line_items[0].unit_price_charged = Decimal("8.00")

    # Test identical passes
    voted_id, flags_id = vote_on_invoice_data([pass0, pass1_identical])
    assert len(flags_id) == 0
    assert voted_id.line_items[0].extraction_confidence == 1.0

    # Test mismatched passes
    voted_mis, flags_mis = vote_on_invoice_data([pass0, pass1_mismatched])
    assert len(flags_mis) == 1
    assert voted_mis.line_items[0].extraction_confidence == 0.5
    assert "quantity, unit_price_charged" in flags_mis[0]["reason"]

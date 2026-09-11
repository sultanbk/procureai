import json
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.audit import Audit
from backend.models.schemas import AuditReport, AuditSummary, Discrepancy
from backend.api.routes.audit import find_proof_location_in_pdf, resolve_finding_proof


def test_find_proof_location_in_pdf_handles_nonexistent_file():
    loc = find_proof_location_in_pdf("nonexistent/path/doc.pdf", ["Rate Sheet Clause 4.2"])
    assert loc == {"page_number": 1, "total_pages": 1, "top_percent": 35.0, "height_percent": 8.0}


def test_find_proof_location_in_pdf_locates_string_on_target_page():
    mock_page_1 = MagicMock()
    mock_page_1.extract_text.return_value = "ProcureAI Contract\nHeader\nTable of Contents"

    mock_page_2 = MagicMock()
    mock_page_2.extract_text.return_value = (
        "Schedule B: Commercial Terms\n"
        "Section 4.2: Maximum ceiling rate for Senior Engineering shall not exceed $120/hr.\n"
        "All invoices billed above this rate shall be penalized."
    )

    mock_reader = MagicMock()
    mock_reader.pages = [mock_page_1, mock_page_2]

    with patch("backend.api.routes.audit.PdfReader", return_value=mock_reader):
        with patch("os.path.exists", return_value=True):
            loc = find_proof_location_in_pdf("mock.pdf", ["Section 4.2", "Senior Engineering"])

    assert loc["page_number"] == 2
    assert loc["total_pages"] == 2
    assert 12.0 <= loc["top_percent"] <= 80.0
    assert loc["height_percent"] == 8.0


def test_resolve_finding_proof_success():
    discrepancy = Discrepancy(
        finding_id="F-001",
        invoice_id="INV-1001",
        line_id="L-01",
        rule_id="R-01",
        discrepancy_type="overcharge",
        description="Overcharge on cloud hosting tier",
        clause_reference="Section 3.1",
        clause_text="Cloud hosting standard unit rate is $100.00.",
        quantity=Decimal("10"),
        unit_price_charged=Decimal("150.00"),
        unit_price_expected=Decimal("100.00"),
        line_total_charged=Decimal("1500.00"),
        line_total_expected=Decimal("1000.00"),
        delta=Decimal("-500.00"),
        severity="CRITICAL",
        recommendation="DISPUTE",
        confidence=0.98,
        critic_status="CONFIRMED",
    )

    report = AuditReport(
        audit_id="audit-visual-123",
        summary=AuditSummary(
            supplier_name="Acme Corp",
            contract_id="CNT-01",
            audit_date="2026-09-10T12:00:00Z",
            billing_period="August 2026",
            total_leakage=Decimal("500.00"),
            total_lines_audited=1,
            compliant_lines=0,
            compliance_score=0.0,
            discrepancy_count=1,
            critical_count=1,
            high_count=0,
            medium_count=0,
            executive_summary="Leakage found.",
        ),
        discrepancies=[discrepancy],
        compliant_lines=[],
        recommendations=["Withhold payment on line item L-01."],
        report_generated_at="2026-09-10T12:00:00Z",
    )

    db_audit = Audit(
        id="audit-visual-123",
        status="COMPLETE",
        contract_file="uploads/contracts/contract_acme.pdf",
        invoice_files=json.dumps(["uploads/invoices/inv_1001.pdf"]),
        audit_report=report.model_dump_json(),
    )

    proof = resolve_finding_proof(db_audit, "F-001")

    assert proof["finding_id"] == "F-001"
    assert proof["audit_id"] == "audit-visual-123"
    assert proof["severity"] == "CRITICAL"
    assert proof["recommendation"] == "DISPUTE"
    assert float(proof["delta"]) == -500.0

    # Contract Viewport
    contract_data = proof["contract"]
    assert contract_data["document_id"] == "contract"
    assert contract_data["clause_reference"] == "Section 3.1"
    assert contract_data["clause_text"] == "Cloud hosting standard unit rate is $100.00."
    assert contract_data["page_number"] >= 1
    assert "pdf_url" in contract_data
    assert contract_data["pdf_url"].startswith("/api/audit/audit-visual-123/documents/contract#page=")
    assert "bounding_box" in contract_data
    assert "top_percent" in contract_data["bounding_box"]
    assert "height_percent" in contract_data["bounding_box"]

    # Invoice Viewport
    invoice_data = proof["invoice"]
    assert invoice_data["document_id"] == "invoice-0"
    assert invoice_data["invoice_id"] == "INV-1001"
    assert invoice_data["line_id"] == "L-01"
    assert invoice_data["unit_price_charged"] == "150.00"
    assert invoice_data["unit_price_expected"] == "100.00"
    assert invoice_data["pdf_url"].startswith("/api/audit/audit-visual-123/documents/invoice-0#page=")
    assert "bounding_box" in invoice_data


def test_resolve_finding_proof_missing_report_raises_400():
    db_audit = Audit(id="audit-no-report", status="PENDING", audit_report=None)
    with pytest.raises(HTTPException) as exc_info:
        resolve_finding_proof(db_audit, "F-001")
    assert exc_info.value.status_code == 400


def test_resolve_finding_proof_nonexistent_finding_raises_404():
    report = AuditReport(
        audit_id="audit-empty-findings",
        summary=AuditSummary(
            supplier_name="Acme",
            contract_id="C-1",
            audit_date="2026-09-10T00:00:00Z",
            billing_period="Aug 2026",
            total_leakage=Decimal("0.00"),
            total_lines_audited=0,
            compliant_lines=0,
            compliance_score=100.0,
            discrepancy_count=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            executive_summary="None",
        ),
        discrepancies=[],
        compliant_lines=[],
        recommendations=[],
        report_generated_at="2026-09-10T00:00:00Z",
    )

    db_audit = Audit(id="audit-empty-findings", status="COMPLETE", audit_report=report.model_dump_json())
    with pytest.raises(HTTPException) as exc_info:
        resolve_finding_proof(db_audit, "F-NONEXISTENT")
    assert exc_info.value.status_code == 404


from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_get_finding_proof_endpoint_404_on_missing_audit():
    with patch("backend.api.routes.audit.AsyncSessionLocal") as mock_session_ctx:
        mock_session = MagicMock()
        mock_session_ctx.return_value.__aenter__.return_value = mock_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        client = TestClient(app)
        response = client.get("/api/audit/nonexistent-audit-id/proof/F001")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_finding_proof_endpoint_200_success():
    discrepancy = Discrepancy(
        finding_id="F-100",
        invoice_id="INV-99",
        line_id="L-1",
        rule_id="R-1",
        discrepancy_type="overcharge",
        description="Hourly rate discrepancy",
        clause_reference="Clause 5",
        clause_text="Rate is $50/hr",
        quantity=Decimal("5"),
        unit_price_charged=Decimal("75.00"),
        unit_price_expected=Decimal("50.00"),
        line_total_charged=Decimal("375.00"),
        line_total_expected=Decimal("250.00"),
        delta=Decimal("-125.00"),
        severity="HIGH",
        recommendation="DISPUTE",
        confidence=0.9,
        critic_status="CONFIRMED",
    )

    report = AuditReport(
        audit_id="aud-success-1",
        summary=AuditSummary(
            supplier_name="Vendor",
            contract_id="C-99",
            audit_date="2026-09-10T00:00:00Z",
            billing_period="Sept 2026",
            total_leakage=Decimal("125.00"),
            total_lines_audited=1,
            compliant_lines=0,
            compliance_score=0.0,
            discrepancy_count=1,
            critical_count=0,
            high_count=1,
            medium_count=0,
            executive_summary="Discrepancy found.",
        ),
        discrepancies=[discrepancy],
        compliant_lines=[],
        recommendations=["Dispute line L-1."],
        report_generated_at="2026-09-10T00:00:00Z",
    )

    mock_audit = Audit(
        id="aud-success-1",
        status="COMPLETE",
        contract_file=None,
        invoice_files=json.dumps([]),
        audit_report=report.model_dump_json(),
    )

    with patch("backend.api.routes.audit.AsyncSessionLocal") as mock_session_ctx:
        mock_session = MagicMock()
        mock_session_ctx.return_value.__aenter__.return_value = mock_session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_audit
        mock_session.execute = AsyncMock(return_value=mock_result)

        client = TestClient(app)
        res = client.get("/api/audit/aud-success-1/proof/F-100")
        assert res.status_code == 200
        data = res.json()
        assert data["finding_id"] == "F-100"
        assert data["contract"]["clause_reference"] == "Clause 5"
        assert data["invoice"]["line_id"] == "L-1"

        # Also test get_all_finding_proofs
        res_all = client.get("/api/audit/aud-success-1/proofs")
        assert res_all.status_code == 200
        all_data = res_all.json()
        assert "proofs" in all_data
        assert "F-100" in all_data["proofs"]

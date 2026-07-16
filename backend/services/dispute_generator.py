"""
ProcureAI - File Summary

What it does:
Drafts and formats professional supplier dispute letters based on audit discrepancies.

What it means:
Automated email/letter generator for supplier communication.

Importance in Project:
High. Converts raw leakage findings into recovery assets.
"""

import json

import google.generativeai as genai
import structlog
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.llm_client import get_llm
from backend.core.prompt_loader import load_prompt
from backend.models.schemas import (
    AuditReport,
    DisputeLetterRequest,
    DisputeLetterResponse,
    DisputeLetterRevisionRequest,
)

logger = structlog.get_logger()


class DisputeLetterLLMResponse(BaseModel):
    letter_text: str
    letter_html: str


async def generate_dispute_letter(
    request: DisputeLetterRequest,
    audit_report: AuditReport,
    db: AsyncSession,
) -> DisputeLetterResponse:
    dispute_findings = [
        f for f in audit_report.discrepancies
        if f.recommendation == "DISPUTE"
    ]

    if not dispute_findings:
        raise ValueError("No DISPUTE-recommended findings in this audit report.")

    total_disputed = sum(abs(f.delta) for f in dispute_findings)

    findings_summary = []
    for finding in dispute_findings:
        findings_summary.append({
            "finding_id": finding.finding_id,
            "description": finding.description,
            "clause_reference": finding.clause_reference,
            "clause_text": finding.clause_text,
            "unit_price_charged": str(finding.unit_price_charged),
            "unit_price_expected": str(finding.unit_price_expected),
            "quantity": str(finding.quantity),
            "charged": str(finding.line_total_charged),
            "expected": str(finding.line_total_expected),
            "delta": str(abs(finding.delta)),
            "discrepancy_type": finding.discrepancy_type,
        })

    prompt_template = load_prompt("dispute_generator")
    schema_json = json.dumps(DisputeLetterLLMResponse.model_json_schema(), indent=2)
    system_prompt = prompt_template.replace("{schema}", schema_json)

    input_text = (
        f"=== DISPUTE REQUEST DETAILS ===\n"
        f"Company Name: {request.company_name}\n"
        f"Signatory Name: {request.signatory_name}\n"
        f"Signatory Title: {request.signatory_title}\n"
        f"Supplier Contact: {request.supplier_contact}\n"
        f"Supplier Name: {audit_report.summary.supplier_name}\n"
        f"Due Date: {request.due_date}\n"
        f"Reference Number: {request.reference_number or 'N/A'}\n"
        f"Audit Date: {audit_report.summary.audit_date}\n"
        f"Billing Period: {audit_report.summary.billing_period}\n"
        f"Contract ID: {audit_report.summary.contract_id}\n"
        f"Total Disputed Amount: INR {total_disputed:,.2f}\n\n"
        f"=== FINDINGS SUMMARY ===\n"
        f"{json.dumps(findings_summary, indent=2)}\n"
    )

    logger.info("Invoking Gemini to generate dispute letter", audit_id=request.audit_id)
    llm = get_llm()
    response = await llm.async_generate_content(
        contents=[system_prompt, input_text],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=DisputeLetterLLMResponse.model_json_schema(),
        ),
    )

    try:
        llm_data = DisputeLetterLLMResponse.model_validate_json(response.text)
    except Exception as exc:
        logger.warning("Dispute letter JSON validation failed, retrying...")
        correction_prompt = (
            f"Your previous JSON output failed validation against the schema.\n"
            f"Error: {str(exc)}\n"
            f"Original Input:\n{input_text}\n\n"
            f"Your invalid JSON response:\n{response.text}\n\n"
            f"Please output a corrected, strictly compliant JSON object matching the schema."
        )
        retry_response = await llm.async_generate_content(
            contents=[system_prompt, correction_prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=DisputeLetterLLMResponse.model_json_schema(),
            ),
        )
        llm_data = DisputeLetterLLMResponse.model_validate_json(retry_response.text)

    return DisputeLetterResponse(
        letter_text=llm_data.letter_text,
        letter_html=llm_data.letter_html,
        findings_count=len(dispute_findings),
        total_disputed=f"INR {total_disputed:,.2f}",
        supplier_email=request.supplier_email,
    )


async def revise_dispute_letter(
    request: DisputeLetterRevisionRequest,
    existing_letter_html: str = "",
    supplier_email: str | None = None,
    findings_count: int = 0,
    total_disputed: str = "",
) -> DisputeLetterResponse:
    schema_json = json.dumps(DisputeLetterLLMResponse.model_json_schema(), indent=2)
    system_prompt = (
        "You revise formal supplier invoice dispute letters. Preserve the legal tone, "
        "supplier/audit facts, dates, disputed amounts, and evidence unless the user "
        "explicitly requests a wording or formatting change. Return only JSON that "
        f"matches this schema:\n{schema_json}"
    )
    input_text = (
        "=== CURRENT LETTER TEXT ===\n"
        f"{request.current_letter_text}\n\n"
        "=== USER REQUESTED CHANGES ===\n"
        f"{request.change_request}\n\n"
        "Revise the letter text and matching HTML version."
    )

    logger.info("Invoking Gemini to revise dispute letter", audit_id=request.audit_id)
    llm = get_llm()
    response = await llm.async_generate_content(
        contents=[system_prompt, input_text],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=DisputeLetterLLMResponse.model_json_schema(),
        ),
    )
    llm_data = DisputeLetterLLMResponse.model_validate_json(response.text)

    return DisputeLetterResponse(
        letter_text=llm_data.letter_text,
        letter_html=llm_data.letter_html or existing_letter_html,
        findings_count=findings_count,
        total_disputed=total_disputed,
        supplier_email=supplier_email,
    )

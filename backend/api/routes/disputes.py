"""
ProcureAI - File Summary

What it does:
Routes to fetch, regenerate, and download dispute letter drafts.

What it means:
Controller managing final vendor correspondence outputs.

Importance in Project:
Medium. Connects the user with action-oriented letters resolving flagged leakages.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.db import get_db
from backend.core.time import utc_now
from backend.models.audit import Audit, DisputeLetter
from backend.models.schemas import (
    AuditReport,
    DisputeLetterRequest,
    DisputeLetterResponse,
    DisputeLetterRevisionRequest,
)
from backend.services.dispute_generator import (
    generate_dispute_letter,
    revise_dispute_letter,
)

router = APIRouter(prefix="/api", tags=["disputes"])


def dispute_response_from_record(record: DisputeLetter) -> DisputeLetterResponse:
    return DisputeLetterResponse(
        letter_text=record.letter_text,
        letter_html=record.letter_html,
        findings_count=record.findings_count,
        total_disputed=record.total_disputed or "",
        supplier_email=record.supplier_email,
    )


async def get_audit_or_404(audit_id: str, db: AsyncSession) -> Audit:
    stmt = select(Audit).where(Audit.id == audit_id)
    result = await db.execute(stmt)
    db_audit = result.scalar_one_or_none()
    if not db_audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID {audit_id} not found.",
        )
    return db_audit


def parse_complete_report(db_audit: Audit) -> AuditReport:
    if db_audit.status != "COMPLETE" or not db_audit.audit_report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audit report is not complete yet. Current status: {db_audit.status}.",
        )
    try:
        return AuditReport.model_validate_json(db_audit.audit_report)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse audit report from database: {str(exc)}",
        ) from exc


@router.get("/disputes/{audit_id}", response_model=DisputeLetterResponse)
async def api_get_dispute_letter(
    audit_id: str,
    db: AsyncSession = Depends(get_db),
):
    record = await db.get(DisputeLetter, audit_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No saved dispute letter for this audit.",
        )
    return dispute_response_from_record(record)


@router.post("/disputes/generate", response_model=DisputeLetterResponse)
async def api_generate_dispute_letter(
    request: DisputeLetterRequest,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.get(DisputeLetter, request.audit_id)
    if existing:
        return dispute_response_from_record(existing)

    db_audit = await get_audit_or_404(request.audit_id, db)
    audit_report = parse_complete_report(db_audit)

    try:
        response = await generate_dispute_letter(request, audit_report, db)
        record = DisputeLetter(
            audit_id=request.audit_id,
            letter_text=response.letter_text,
            letter_html=response.letter_html,
            request_payload=request.model_dump_json(),
            findings_count=response.findings_count,
            total_disputed=response.total_disputed,
            supplier_email=response.supplier_email,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        try:
            db.add(record)
            await db.commit()
        except Exception:
            await db.rollback()
            existing = await db.get(DisputeLetter, request.audit_id)
            if existing:
                return dispute_response_from_record(existing)
            raise
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during dispute letter generation: {str(exc)}",
        ) from exc


@router.post("/disputes/revise", response_model=DisputeLetterResponse)
async def api_revise_dispute_letter(
    request: DisputeLetterRevisionRequest,
    db: AsyncSession = Depends(get_db),
):
    if not request.change_request.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter the changes to apply.",
        )

    await get_audit_or_404(request.audit_id, db)
    existing = await db.get(DisputeLetter, request.audit_id)

    current_text = request.current_letter_text.strip()
    if existing and not current_text:
        current_text = existing.letter_text
    if not current_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No current letter text was provided to revise.",
        )

    request.current_letter_text = current_text
    response = await revise_dispute_letter(
        request,
        existing_letter_html=existing.letter_html if existing else "",
        supplier_email=existing.supplier_email if existing else None,
        findings_count=existing.findings_count if existing else 0,
        total_disputed=existing.total_disputed if existing else "",
    )

    if existing:
        existing.letter_text = response.letter_text
        existing.letter_html = response.letter_html
        existing.updated_at = utc_now()
    else:
        existing = DisputeLetter(
            audit_id=request.audit_id,
            letter_text=response.letter_text,
            letter_html=response.letter_html,
            request_payload=json.dumps({"revision_only": True}),
            findings_count=response.findings_count,
            total_disputed=response.total_disputed,
            supplier_email=response.supplier_email,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        db.add(existing)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        # Merge/update the existing one
        existing = await db.get(DisputeLetter, request.audit_id)
        if existing:
            existing.letter_text = response.letter_text
            existing.letter_html = response.letter_html
            existing.updated_at = utc_now()
            await db.commit()
        else:
            raise
    return response

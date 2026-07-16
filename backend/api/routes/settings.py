"""
ProcureAI - File Summary

What it does:
Routers for editing and fetching application settings and notification configs.

What it means:
Controller mapping customizable threshold tolerances to system settings.

Importance in Project:
Medium. Supports real-time adjustments of confidence scores and billing parameters.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel
from decimal import Decimal

from backend.core.db import get_db
from backend.core.config import FRONTEND_BASE_URL
from backend.core.time import utc_now_iso
from backend.models.audit import NotificationSettings
from backend.models.schemas import AuditReport, AuditSummary

router = APIRouter(prefix="/api", tags=["settings"])

class NotificationSettingsUpdate(BaseModel):
    slack_enabled:        Optional[bool] = None
    slack_webhook_url:    Optional[str] = None
    email_enabled:        Optional[bool] = None
    email_to:             Optional[str] = None
    email_from:           Optional[str] = None
    smtp_host:            Optional[str] = None
    smtp_port:            Optional[int] = None
    smtp_user:            Optional[str] = None
    smtp_password:        Optional[str] = None
    alert_on_critical:    Optional[bool] = None
    alert_on_high:        Optional[bool] = None
    alert_threshold_inr:  Optional[float] = None
    alert_on_any_finding: Optional[bool] = None

class NotificationSettingsResponse(BaseModel):
    slack_enabled:        bool
    slack_webhook_url:    Optional[str] = None
    email_enabled:        bool
    email_to:             Optional[str] = None
    email_from:           Optional[str] = None
    smtp_host:            Optional[str] = None
    smtp_port:            int
    smtp_user:            Optional[str] = None
    alert_on_critical:    bool
    alert_on_high:        bool
    alert_threshold_inr:  float
    alert_on_any_finding: bool

    class Config:
        from_attributes = True

class TestSlackRequest(BaseModel):
    webhook_url: Optional[str] = None

class TestEmailRequest(BaseModel):
    email_to:             Optional[str] = None
    email_from:           Optional[str] = None
    smtp_host:            Optional[str] = None
    smtp_port:            Optional[int] = None
    smtp_user:            Optional[str] = None
    smtp_password:        Optional[str] = None

@router.get("/settings/notifications", response_model=NotificationSettingsResponse)
async def get_notification_settings(db: AsyncSession = Depends(get_db)):
    stmt = select(NotificationSettings).where(NotificationSettings.id == 1)
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()
    if not settings:
        # Auto-create if somehow missing
        settings = NotificationSettings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings

@router.put("/settings/notifications", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    update_data: NotificationSettingsUpdate,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(NotificationSettings).where(NotificationSettings.id == 1)
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()
    if not settings:
        settings = NotificationSettings(id=1)
        db.add(settings)

    for field, value in update_data.model_dump(exclude_unset=True).items():
        if value is not None:
            if isinstance(value, bool):
                setattr(settings, field, 1 if value else 0)
            else:
                setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)
    return settings

@router.post("/settings/notifications/test-slack")
async def test_slack_notification(
    request: TestSlackRequest,
    db: AsyncSession = Depends(get_db)
):
    from backend.services.notifier import send_slack

    webhook_url = request.webhook_url
    if not webhook_url:
        stmt = select(NotificationSettings).where(NotificationSettings.id == 1)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()
        if settings:
            webhook_url = settings.slack_webhook_url

    if not webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slack Webhook URL is required for testing."
        )

    test_message = {
        "severity_emoji": "⚠️",
        "supplier_name": "Test Supplier Inc.",
        "billing_period": "June 2026",
        "total_leakage": "$15,000.00",
        "discrepancy_count": 1,
        "critical_count": 0,
        "high_count": 1,
        "medium_count": 0,
        "top_finding": "Incorrect consulting rate — $15,000.00 (Section 4.1)",
        "audit_id": "aud_test_123",
        "report_url": f"{FRONTEND_BASE_URL.rstrip('/')}/audit/aud_test_123"
    }

    try:
        await send_slack(webhook_url, test_message, raise_on_error=True)
        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/settings/notifications/test-email")
async def test_email_notification(
    request: TestEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    from backend.services.notifier import send_email

    # Load saved settings first as fallback
    stmt = select(NotificationSettings).where(NotificationSettings.id == 1)
    result = await db.execute(stmt)
    saved = result.scalar_one_or_none()

    # Merge passed values with saved values as fallback
    settings_obj = NotificationSettings(
        email_to=request.email_to or (saved.email_to if saved else None),
        email_from=request.email_from or (saved.email_from if saved else None),
        smtp_host=request.smtp_host or (saved.smtp_host if saved else None),
        smtp_port=request.smtp_port or (saved.smtp_port if saved else 587),
        smtp_user=request.smtp_user or (saved.smtp_user if saved else None),
        smtp_password=request.smtp_password or (saved.smtp_password if saved else None),
    )

    if not settings_obj.email_to or not settings_obj.smtp_host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient email and SMTP Host are required for testing."
        )

    test_message = {
        "severity_emoji": "⚠️",
        "supplier_name": "Test Supplier Inc.",
        "billing_period": "June 2026",
        "total_leakage": "$15,000.00",
        "discrepancy_count": 1,
        "critical_count": 0,
        "high_count": 1,
        "medium_count": 0,
        "top_finding": "Incorrect consulting rate — $15,000.00 (Section 4.1)",
        "audit_id": "aud_test_123",
        "report_url": f"{FRONTEND_BASE_URL.rstrip('/')}/audit/aud_test_123"
    }

    report = AuditReport(
        audit_id="aud_test_123",
        summary=AuditSummary(
            supplier_name="Test Supplier Inc.",
            contract_id="MSA-2026-TEST",
            audit_date=utc_now_iso(),
            billing_period="June 2026",
            total_leakage=Decimal("15000.00"),
            total_lines_audited=10,
            compliant_lines=9,
            discrepancy_count=1,
            critical_count=0,
            high_count=1,
            medium_count=0,
            executive_summary="Test audit summary description."
        ),
        discrepancies=[],
        compliant_lines=[],
        recommendations=[],
        report_generated_at=utc_now_iso()
    )

    try:
        send_email(settings_obj, report, test_message, raise_on_error=True)
        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}

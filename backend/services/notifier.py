"""
ProcureAI - File Summary

What it does:
Handles alert notifications for high-leakage audits and low-score events.

What it means:
Simulated dispatcher routing messages to simulated email/slack logs.

Importance in Project:
Medium. Notifies admin users when discrepancies exceed configured thresholds.
"""

import httpx
import smtplib
import structlog
from email.mime.text import MIMEText
from decimal import Decimal

from backend.models.schemas import AuditReport
from backend.models.audit import NotificationSettings
from backend.core.config import FRONTEND_BASE_URL

logger = structlog.get_logger()

async def send_notifications(
    audit_report: AuditReport,
    settings: NotificationSettings
) -> None:
    """
    Fire-and-forget. Called after audit completes.
    Checks conditions, sends Slack + email if configured.
    Never raises — logs errors silently.
    """
    try:
        # Check if any condition is met
        should_alert = False
        critical_count = audit_report.summary.critical_count
        total_leakage = audit_report.summary.total_leakage

        if settings.alert_on_critical and critical_count > 0:
            should_alert = True
        if settings.alert_on_high and audit_report.summary.high_count > 0:
            should_alert = True
        if total_leakage >= Decimal(str(settings.alert_threshold_inr)):
            should_alert = True
        if settings.alert_on_any_finding and audit_report.summary.discrepancy_count > 0:
            should_alert = True

        if not should_alert:
            logger.info("Alert conditions not met; skipping notifications.", audit_id=audit_report.audit_id)
            return

        # Build message content
        top_finding = audit_report.discrepancies[0] if audit_report.discrepancies else None
        message = build_message(audit_report, top_finding)

        # Send Slack
        if settings.slack_enabled and settings.slack_webhook_url:
            await send_slack(settings.slack_webhook_url, message)

        # Send email
        if settings.email_enabled and settings.email_to and settings.smtp_host:
            send_email(settings, audit_report, message)

    except Exception as exc:
        logger.error(f"Unexpected error in notification service: {exc}", audit_id=audit_report.audit_id)


def build_message(report: AuditReport, top_finding) -> dict:
    severity_emoji = "🚨" if report.summary.critical_count > 0 else "⚠️"
    top_finding_text = "None"
    if top_finding:
        top_finding_text = (
            f"{top_finding.discrepancy_type.replace('_',' ').title()} — "
            f"${abs(top_finding.delta):,.2f} ({top_finding.clause_reference})"
        )
    return {
        "severity_emoji":    severity_emoji,
        "supplier_name":     report.summary.supplier_name,
        "billing_period":    report.summary.billing_period,
        "total_leakage":     f"${report.summary.total_leakage:,.2f}",
        "discrepancy_count": report.summary.discrepancy_count,
        "critical_count":    report.summary.critical_count,
        "high_count":        report.summary.high_count,
        "medium_count":      report.summary.medium_count,
        "top_finding":       top_finding_text,
        "audit_id":          report.audit_id,
        "report_url":        f"{FRONTEND_BASE_URL.rstrip('/')}/audit/{report.audit_id}"
    }


async def send_slack(webhook_url: str, message: dict, raise_on_error: bool = False) -> None:
    payload = {
        "text": (
            f"{message['severity_emoji']} *ProcureAI Alert*\n"
            f"*Supplier:* {message['supplier_name']}\n"
            f"*Period:* {message['billing_period']}\n"
            f"*Total Leakage:* {message['total_leakage']}\n"
            f"*Findings:* {message['discrepancy_count']} "
            f"({message['critical_count']} CRITICAL, "
            f"{message['high_count']} HIGH, "
            f"{message['medium_count']} MEDIUM)\n"
            f"*Top Finding:* {message['top_finding']}\n"
            f"→ <{message['report_url']}|View Full Report>"
        )
    }
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(webhook_url, json=payload, timeout=5.0)
            r.raise_for_status()
            logger.info("Slack notification sent successfully.")
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            if raise_on_error:
                raise e


def send_email(settings: NotificationSettings, report: AuditReport, message: dict, raise_on_error: bool = False) -> None:
    subject = (
        f"[ProcureAI] {message['severity_emoji']} "
        f"{message['supplier_name']} — ${report.summary.total_leakage:,.2f} leakage detected"
    )
    body = f"""
ProcureAI Audit Alert

Supplier:      {message['supplier_name']}
Period:        {message['billing_period']}
Total Leakage: {message['total_leakage']}
Findings:      {message['discrepancy_count']} total
               {message['critical_count']} CRITICAL
               {message['high_count']} HIGH
               {message['medium_count']} MEDIUM

Top Finding:   {message['top_finding']}

View full report: {message['report_url']}

---
This alert was sent automatically by ProcureAI.
    """.strip()

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = settings.email_to

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
            logger.info("Email notification sent successfully.")
    except Exception as e:
        logger.error(f"Email notification failed: {e}")
        if raise_on_error:
            raise e

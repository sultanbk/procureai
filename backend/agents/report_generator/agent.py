"""
FILE CANONICAL IDENTIFIER: backend/agents/report_generator/agent.py
MODULE ROLE: Synthesizes the final compliance audit report, computes supplier scorecard metrics, and triggers alerts/notifications.
SYSTEM BOUNDARY: Integrates with Google Generative AI (Gemini) for summarization, SQLite DB (Audit and SupplierScore schemas), and external Slack/SMTP notification services.
STATE DEPENDENCY / DATA CONTRACTS: Consumes rulebook, invoice_data, and discrepancies from PipelineState. Outputs serialized AuditReport (backend.models.schemas.AuditReport) to PipelineState.
CRITICAL LOGIC: Python-driven aggregation and sorting of finding metrics, followed by LLM-driven generation of executive summaries and recommendations (with validation retries). Automatically computes and commits SupplierScore compliance ratings.
"""

import json
import structlog
from pydantic import BaseModel, ValidationError
from typing import List
import google.generativeai as genai

from backend.models.schemas import (
    PipelineState,
    AuditReport,
    AuditSummary,
    Discrepancy,
    CompliantLine,
    InvoiceData,
    AgentError,
    DataRequiredFlag,
    ReviewFlag
)
from backend.core.llm_client import get_llm
from backend.core.prompt_loader import load_prompt
from backend.core.db import AsyncSessionLocal
from backend.core.time import utc_now, utc_now_iso
from backend.models.audit import Audit
from backend.agents.report_generator.tools import (
    calculate_aggregate_stats,
    sort_discrepancies_by_severity
)
from sqlalchemy import select

from backend.core.audit_logger import log_audit_event

logger = structlog.get_logger()

class ReportShorthand(BaseModel):
    executive_summary: str
    recommendations: List[str]

async def run_report_generator(state: PipelineState) -> PipelineState:
    """
    Agent 4: Report Generator
    Input:  state["discrepancies"], state["rulebook"], state["invoice_data"]
    Output: state["audit_report"], state["current_agent"] = "report_generator"
    Error:  state["errors"].append(...), state["halt"] = True if unrecoverable
    """
    state["current_agent"] = "report_generator"
    audit_id = state.get("audit_id")
    await log_audit_event(audit_id, "Report Generator agent started.", "INFO", "report_generator")
    
    # Update status in database
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        db_audit = result.scalar_one_or_none()
        if db_audit:
            db_audit.status = "GENERATING_REPORT"
            await session.commit()

            
    try:
        discrepancy_list_raw = state.get("discrepancies")
        if not discrepancy_list_raw:
            raise ValueError("Discrepancies list is missing in state.")
            
        rulebook_raw = state.get("rulebook")
        if not rulebook_raw:
            raise ValueError("Rulebook is missing in state.")
            
        invoice_data_raw = state.get("invoice_data")
        if not invoice_data_raw:
            raise ValueError("Invoice data is missing in state.")
            
        # Parse Pydantic objects from dicts
        discrepancies: List[Discrepancy] = [
            Discrepancy.model_validate(d) for d in discrepancy_list_raw.get("discrepancies", [])
        ]
        compliant_lines: List[CompliantLine] = [
            CompliantLine.model_validate(c) for c in discrepancy_list_raw.get("compliant_lines", [])
        ]
        
        invoices: List[InvoiceData] = [
            InvoiceData.model_validate(inv) for inv in invoice_data_raw
        ]
        
        # Extract v3 flags
        cv_result = state.get("cross_validation", {})
        rules_never_billed = cv_result.get("rules_never_billed", [])
        
        data_required_flags: List[DataRequiredFlag] = [
            DataRequiredFlag.model_validate(f) for f in state.get("data_required_flags", [])
        ]
        
        review_flags: List[ReviewFlag] = [
            ReviewFlag.model_validate(f) for f in state.get("review_flags", [])
        ]
        
        # 1. Compute aggregate stats in Python using tools
        (
            total_leakage,
            total_lines_audited,
            compliant_lines_count,
            discrepancy_count,
            critical_count,
            high_count,
            medium_count
        ) = calculate_aggregate_stats(discrepancies, compliant_lines, invoices)
        
        # 2. Sort discrepancies using tools
        sorted_discrepancies = sort_discrepancies_by_severity(discrepancies)
        
        # 3. Call LLM to generate executive summary & recommendations
        llm = get_llm()
        llm_status = llm.status_label() if hasattr(llm, "status_label") else "LLM"
        await log_audit_event(audit_id, f"Generating executive summary narrative and recommendations using {llm_status}.", "INFO", "report_generator")
        prompt_template = load_prompt("report_generator", "prompt_executive_summary.txt")

        
        schema_json = json.dumps(ReportShorthand.model_json_schema(), indent=2)
        system_prompt = prompt_template.replace("{schema}", schema_json)
        
        input_text = (
            f"Please generate the executive summary and recommendations for the following audit findings.\n\n"
            f"=== SUPPLIER ===\n"
            f"Supplier Name: {rulebook_raw.get('supplier_name')}\n"
            f"Contract ID: {rulebook_raw.get('contract_id')}\n\n"
            f"=== METRICS ===\n"
            f"Total Billing Leakage: INR {total_leakage}\n"
            f"Total Lines Audited: {total_lines_audited}\n"
            f"Compliant Lines: {compliant_lines_count}\n"
            f"Discrepancies Found: {discrepancy_count} (Critical: {critical_count}, High: {high_count}, Medium: {medium_count})\n\n"
            f"=== DETECTED DISCREPANCIES ===\n"
        )
        
        for d in sorted_discrepancies:
            input_text += (
                f"- Finding {d.finding_id} ({d.discrepancy_type} - {d.severity}):\n"
                f"  Invoice: {d.invoice_id}, Line: {d.line_id}\n"
                f"  Charged Amount: INR {d.line_total_charged}, Expected: INR {d.line_total_expected}, Delta: INR {d.delta}\n"
                f"  Rule Description: {d.description}\n"
                f"  Clause Reference: {d.clause_reference}\n"
                f"  Clause Text: {d.clause_text}\n\n"
            )
            
        response = await llm.async_generate_content(
            contents=[system_prompt, input_text],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ReportShorthand.model_json_schema(),
                temperature=0.0
            )
        )
        
        try:
            shorthand = ReportShorthand.model_validate_json(response.text)
        except ValidationError as val_err:
            logger.warning("Report shorthand validation failed on first attempt. Retrying with correction prompt...")
            correction_prompt = (
                f"Your previous JSON output failed validation against the ReportShorthand schema.\n"
                f"Validation Error: {str(val_err)}\n"
                f"Original Input:\n{input_text}\n\n"
                f"Your invalid JSON response:\n{response.text}\n\n"
                f"Please output a corrected, strictly compliant JSON object matching the schema."
            )
            retry_response = await llm.async_generate_content(
                contents=[system_prompt, correction_prompt],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=ReportShorthand.model_json_schema(),
                    temperature=0.0
                )
            )
            shorthand = ReportShorthand.model_validate_json(retry_response.text)
            
        # 4. Construct final AuditReport Pydantic object
        report_generated_at = utc_now_iso()
        
        # Aggregate billing periods across all invoices (not just the first)
        if invoices:
            unique_periods = sorted(set(inv.billing_period for inv in invoices if inv.billing_period))
            aggregated_billing_period = " – ".join(unique_periods) if unique_periods else "Unknown"
        else:
            aggregated_billing_period = "Unknown"
        
        # v3 architecture: compliance_score = (compliant_lines / total_lines) * 100
        compliance_score = round(
            (compliant_lines_count / total_lines_audited * 100) if total_lines_audited > 0 else 0.0,
            2
        )
        
        summary = AuditSummary(
            supplier_name=rulebook_raw.get("supplier_name", "Unknown"),
            contract_id=rulebook_raw.get("contract_id", "Unknown"),
            audit_date=report_generated_at,
            billing_period=aggregated_billing_period,
            total_leakage=total_leakage,
            total_lines_audited=total_lines_audited,
            compliant_lines=compliant_lines_count,
            compliance_score=compliance_score,
            discrepancy_count=discrepancy_count,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            executive_summary=shorthand.executive_summary
        )
        
        # v4: Collect data from reverse sweep and cross-invoice analyzer
        reverse_sweep_data = state.get("reverse_sweep", {})
        missing_credits = reverse_sweep_data.get("missing_credits", []) if reverse_sweep_data else []
        
        cross_invoice_data = state.get("cross_invoice", {})
        price_drifts = cross_invoice_data.get("price_drifts", []) if cross_invoice_data else []
        
        audit_report_obj = AuditReport(
            audit_id=audit_id,
            summary=summary,
            discrepancies=sorted_discrepancies,
            compliant_lines=compliant_lines,
            recommendations=shorthand.recommendations,
            report_generated_at=report_generated_at,
            data_required_flags=data_required_flags,
            review_flags=review_flags,
            rules_never_billed=rules_never_billed,
            missing_credits=missing_credits,
            price_drifts=price_drifts,
        )
        
        # 5. Write back to state
        state["audit_report"] = audit_report_obj.model_dump()
        
        # 6. Save in database and set status to COMPLETE
        async with AsyncSessionLocal() as session:
            stmt = select(Audit).where(Audit.id == audit_id)
            result = await session.execute(stmt)
            db_audit = result.scalar_one_or_none()
            if db_audit:
                db_audit.audit_report = json.dumps(audit_report_obj.model_dump(), default=str)
                db_audit.total_leakage = float(total_leakage)
                db_audit.status = "COMPLETE"
                db_audit.completed_at = utc_now()

                from backend.services.scoring import compute_score
                score_val = compute_score(audit_report_obj)

                from backend.models.audit import SupplierScore
                supplier_score = SupplierScore(
                    supplier_name=audit_report_obj.summary.supplier_name,
                    audit_id=audit_id,
                    score=score_val,
                    total_lines=audit_report_obj.summary.total_lines_audited,
                    compliant_lines=audit_report_obj.summary.compliant_lines,
                    critical_count=audit_report_obj.summary.critical_count,
                    high_count=audit_report_obj.summary.high_count,
                    medium_count=audit_report_obj.summary.medium_count,
                    total_leakage=float(audit_report_obj.summary.total_leakage)
                )
                session.add(supplier_score)
                await session.commit()
                await log_audit_event(audit_id, f"Computed compliance score {score_val} for supplier {audit_report_obj.summary.supplier_name} and recorded scorecard entry.", "INFO", "report_generator")

                # Trigger notifications
                try:
                    from backend.models.audit import NotificationSettings
                    from backend.services.notifier import send_notifications
                    
                    stmt_settings = select(NotificationSettings).where(NotificationSettings.id == 1)
                    result_settings = await session.execute(stmt_settings)
                    settings_obj = result_settings.scalar_one_or_none()
                    if settings_obj:
                        settings_copy = NotificationSettings(
                            slack_enabled=settings_obj.slack_enabled,
                            slack_webhook_url=settings_obj.slack_webhook_url,
                            email_enabled=settings_obj.email_enabled,
                            email_to=settings_obj.email_to,
                            email_from=settings_obj.email_from,
                            smtp_host=settings_obj.smtp_host,
                            smtp_port=settings_obj.smtp_port,
                            smtp_user=settings_obj.smtp_user,
                            smtp_password=settings_obj.smtp_password,
                            alert_on_critical=settings_obj.alert_on_critical,
                            alert_on_high=settings_obj.alert_on_high,
                            alert_threshold_inr=settings_obj.alert_threshold_inr,
                            alert_on_any_finding=settings_obj.alert_on_any_finding
                        )
                        import asyncio
                        asyncio.create_task(send_notifications(audit_report_obj, settings_copy))
                        await log_audit_event(audit_id, "Notification checks started in background.", "INFO", "report_generator")
                except Exception as notify_err:
                    logger.error("Failed to trigger background notifications", error=str(notify_err))
                    await log_audit_event(audit_id, f"Failed to trigger notifications: {str(notify_err)}", "WARNING", "report_generator")
                    
        await log_audit_event(audit_id, "Report generation complete. Persisting final report and concluding compliance audit.", "INFO", "report_generator")
        
    except Exception as e:
        await log_audit_event(audit_id, f"Report generator agent failed: {str(e)}", "ERROR", "report_generator")
        error = AgentError(
            agent="report_generator",
            error_type="llm_call_failed",
            message=str(e),
            recoverable=False
        )
        state.setdefault("errors", []).append(error.model_dump())
        state["halt"] = True
        
        async with AsyncSessionLocal() as session:
            stmt = select(Audit).where(Audit.id == audit_id)
            result = await session.execute(stmt)
            db_audit = result.scalar_one_or_none()
            if db_audit:
                db_audit.status = "FAILED"
                db_audit.error_detail = str(e)
                await session.commit()
                
    return state

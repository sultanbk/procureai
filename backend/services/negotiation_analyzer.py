import json
import uuid
import os
import asyncio
import google.generativeai as genai
from decimal import Decimal
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.audit import Audit, NegotiationBrief
from backend.models.schemas import SupplierViolationSummary, NegotiationBrief as NegotiationBriefSchema
from backend.core.llm_client import get_llm
from backend.core.db import AsyncSessionLocal

def load_prompt(name: str) -> str:
    path = os.path.join(
        os.path.dirname(__file__),
        "..", "agents", name, "prompt.txt"
    )
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

async def aggregate_supplier_violations(
    supplier_name: str,
    db: AsyncSession
) -> SupplierViolationSummary:
    """
    Pull all COMPLETE audits for this supplier.
    Aggregate violations across all findings in all audits.
    """
    stmt = select(Audit).where(
        Audit.supplier_name == supplier_name,
        Audit.status == "COMPLETE"
    ).order_by(Audit.completed_at.asc())
    result = await db.execute(stmt)
    audits = result.scalars().all()

    if len(audits) < 2:
        raise ValueError(
            f"Need at least 2 completed audits for {supplier_name}. "
            f"Found: {len(audits)}"
        )

    # Aggregate all findings
    clause_violations = defaultdict(lambda: {
        "count": 0,
        "total_leakage": Decimal("0"),
        "invoices_affected": set(),
        "clause_references": set(),
        "example_finding": None
    })

    total_leakage = Decimal("0")
    total_findings = 0
    monthly_leakage = {}  # {month_str: Decimal}

    for audit in audits:
        if not audit.discrepancies:
            continue
        disc_data = json.loads(audit.discrepancies)
        month = audit.completed_at.strftime("%Y-%m") if audit.completed_at else "unknown"

        for finding in disc_data.get("discrepancies", []):
            dtype = finding.get("discrepancy_type", "unknown")
            delta = abs(Decimal(str(finding.get("delta", 0))))

            clause_violations[dtype]["count"] += 1
            clause_violations[dtype]["total_leakage"] += delta
            clause_violations[dtype]["invoices_affected"].add(audit.id)
            
            clause_ref = finding.get("clause_reference")
            if clause_ref:
                clause_violations[dtype]["clause_references"].add(clause_ref)
                
            if not clause_violations[dtype]["example_finding"]:
                clause_violations[dtype]["example_finding"] = {
                    "description": finding.get("description", ""),
                    "clause_text": finding.get("clause_text", ""),
                    "delta": str(delta)
                }

            total_leakage += delta
            total_findings += 1
            monthly_leakage[month] = monthly_leakage.get(month, Decimal("0")) + delta

    # Compute trend
    monthly_values = [float(v) for v in monthly_leakage.values()]
    trend = "improving" if (
        len(monthly_values) >= 2 and
        monthly_values[-1] < monthly_values[0]
    ) else "worsening"

    return SupplierViolationSummary(
        supplier_name=supplier_name,
        audits_analysed=len(audits),
        audit_period_start=audits[0].completed_at.isoformat() if audits[0].completed_at else "",
        audit_period_end=audits[-1].completed_at.isoformat() if audits[-1].completed_at else "",
        total_leakage=total_leakage,
        total_findings=total_findings,
        clause_violations={
            k: {**v, "invoices_affected": len(v["invoices_affected"]),
                "clause_references": list(v["clause_references"])}
            for k, v in clause_violations.items()
        },
        leakage_trend=trend,
        monthly_leakage={k: str(v) for k, v in monthly_leakage.items()}
    )


async def generate_negotiation_brief(
    summary: SupplierViolationSummary
) -> NegotiationBriefSchema:
    prompt = load_prompt("negotiation_analyzer")
    
    # Inject full summary JSON into prompt
    full_prompt = f"{prompt}\n\n[SUPPLIER VIOLATION SUMMARY]\n{summary.model_dump_json(indent=2)}"

    from backend.core.llm_client import get_llm
    import google.generativeai as genai
    from pydantic import BaseModel
    
    llm = get_llm()
    config = {
        "response_mime_type": "application/json",
        "response_schema": NegotiationBriefSchema.model_json_schema(),
        "temperature": 0.2
    }
    
    response = await llm.async_generate_content(
        full_prompt,
        generation_config=config
    )
    
    data = json.loads(response.text)
    
    # Add server-side fields
    data["brief_id"] = str(uuid.uuid4())
    data["supplier_name"] = summary.supplier_name
    
    from backend.core.time import utc_now
    data["generated_at"] = utc_now().isoformat()
    
    data["audits_analysed"] = summary.audits_analysed
    data["audit_period"] = f"{summary.audit_period_start} to {summary.audit_period_end}"
    data["total_leakage_basis"] = str(summary.total_leakage)
    
    return NegotiationBriefSchema(**data)

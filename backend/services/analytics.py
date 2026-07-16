"""
ProcureAI - File Summary

What it does:
Computes historical and aggregate database analytics.

What it means:
Business intelligence engine tracking leakage savings and vendor metrics.

Importance in Project:
Medium. Performs complex SQL aggregate queries for visual dashboard display.
"""

import json
from decimal import Decimal
from collections import defaultdict
from typing import List, Dict, Any
from backend.models.audit import Audit

def compute_analytics(
    audits: List[Audit],
    prev_audits: List[Audit],
    period_label: str,
    has_previous: bool
) -> Dict[str, Any]:
    """
    Computes all leakage and analytics data from the list of audits.
    """
    # 1. KPI calculations
    total_leakage_identified = sum(Decimal(str(a.total_leakage or 0)) for a in audits)
    total_audits_run = len(audits)
    avg_leakage_per_audit = (total_leakage_identified / total_audits_run) if total_audits_run > 0 else Decimal("0.00")
    
    # Unique supplier names
    unique_suppliers = {a.supplier_name for a in audits if a.supplier_name}
    total_suppliers_audited = len(unique_suppliers)

    # Trend calculation vs previous same period
    if has_previous:
        previous_period_leakage = sum(Decimal(str(a.total_leakage or 0)) for a in prev_audits)
        if previous_period_leakage > 0:
            leakage_trend_pct = float(((total_leakage_identified - previous_period_leakage) / previous_period_leakage) * 100)
        else:
            leakage_trend_pct = 0.0
    else:
        leakage_trend_pct = 0.0

    # 2. Leakage by month (chronological order)
    month_data = defaultdict(lambda: {"total_leakage": Decimal("0.00"), "audit_count": 0})
    for a in audits:
        if not a.completed_at:
            continue
        m = a.completed_at.strftime("%Y-%m")
        month_data[m]["total_leakage"] += Decimal(str(a.total_leakage or 0))
        month_data[m]["audit_count"] += 1

    leakage_by_month = []
    for m in sorted(month_data.keys()):
        leakage_by_month.append({
            "month": m,
            "total_leakage": month_data[m]["total_leakage"],
            "audit_count": month_data[m]["audit_count"]
        })

    # 3. Leakage by supplier (top 10 sorted descending)
    supplier_data = defaultdict(lambda: {"total_leakage": Decimal("0.00"), "audit_count": 0})
    for a in audits:
        if not a.supplier_name:
            continue
        supplier_data[a.supplier_name]["total_leakage"] += Decimal(str(a.total_leakage or 0))
        supplier_data[a.supplier_name]["audit_count"] += 1

    leakage_by_supplier = [
        {
            "supplier_name": name,
            "total_leakage": data["total_leakage"],
            "audit_count": data["audit_count"]
        }
        for name, data in supplier_data.items()
    ]
    leakage_by_supplier.sort(key=lambda x: x["total_leakage"], reverse=True)
    leakage_by_supplier = leakage_by_supplier[:10]

    # 4. Leakage by type & severity breakdown
    leakage_by_type_map = defaultdict(lambda: {"count": 0, "total_leakage": Decimal("0.00")})
    severity_breakdown = {
        "CRITICAL": {"count": 0, "total_leakage": Decimal("0.00")},
        "HIGH": {"count": 0, "total_leakage": Decimal("0.00")},
        "MEDIUM": {"count": 0, "total_leakage": Decimal("0.00")}
    }
    top_findings = []

    for a in audits:
        if not a.discrepancies:
            continue
        try:
            disc_data = json.loads(a.discrepancies)
            for finding in disc_data.get("discrepancies", []):
                dtype = finding.get("discrepancy_type", "unknown")
                delta = abs(Decimal(str(finding.get("delta", 0))))
                severity = finding.get("severity", "MEDIUM")

                # Accumulate type stats
                leakage_by_type_map[dtype]["count"] += 1
                leakage_by_type_map[dtype]["total_leakage"] += delta

                # Accumulate severity stats
                if severity in severity_breakdown:
                    severity_breakdown[severity]["count"] += 1
                    severity_breakdown[severity]["total_leakage"] += delta
                else:
                    severity_breakdown.setdefault(severity, {"count": 0, "total_leakage": Decimal("0.00")})
                    severity_breakdown[severity]["count"] += 1
                    severity_breakdown[severity]["total_leakage"] += delta

                # Register finding candidate
                top_findings.append({
                    "supplier_name": a.supplier_name or "Unknown",
                    "discrepancy_type": dtype,
                    "delta": delta,
                    "severity": severity,
                    "audit_date": a.completed_at.strftime("%Y-%m-%d") if a.completed_at else (a.created_at.strftime("%Y-%m-%d") if a.created_at else ""),
                    "clause_reference": finding.get("clause_reference", "N/A")
                })
        except Exception:
            # Ignore parsing errors for robust fallback
            pass

    leakage_by_type = [
        {
            "discrepancy_type": dtype,
            "count": val["count"],
            "total_leakage": val["total_leakage"]
        }
        for dtype, val in leakage_by_type_map.items()
    ]
    # Sort by leakage amount descending
    leakage_by_type.sort(key=lambda x: x["total_leakage"], reverse=True)

    # Get top 5 largest findings
    top_findings.sort(key=lambda x: x["delta"], reverse=True)
    top_findings = top_findings[:5]

    return {
        "period_label": period_label,
        "kpis": {
            "total_leakage_identified": total_leakage_identified,
            "total_audits_run": total_audits_run,
            "avg_leakage_per_audit": avg_leakage_per_audit,
            "total_suppliers_audited": total_suppliers_audited,
            "leakage_trend_pct": leakage_trend_pct
        },
        "leakage_by_month": leakage_by_month,
        "leakage_by_supplier": leakage_by_supplier,
        "leakage_by_type": leakage_by_type,
        "severity_breakdown": severity_breakdown,
        "top_findings": top_findings
    }


# --- Clause Violation Heatmap Analytics ---

from pydantic import BaseModel
from backend.models.schemas import ClauseInsight
from backend.core.llm_client import get_llm
import google.generativeai as genai

class ClauseRecommendation(BaseModel):
    clause_type: str
    recommendation: str

class ClauseRecommendationList(BaseModel):
    recommendations: list[ClauseRecommendation]

async def generate_insights(column_totals: dict) -> list[ClauseInsight]:
    """
    Calls the LLM to generate negotiation insights for top violated clause types,
    and returns a combined list of ClauseInsight objects.
    """
    sorted_clauses = sorted(
        column_totals.items(),
        key=lambda x: x[1]["total"],
        reverse=True
    )
    
    # Select top 3 violated clauses for the LLM prompt
    top_3 = [item for item in sorted_clauses if item[1]["count"] > 0][:3]
    
    rec_map = {}
    if top_3:
        llm_input_data = {
            name: {
                "count": val["count"],
                "total_leakage": str(val["total"])
            }
            for name, val in top_3
        }
        
        prompt = f"""
        You are a procurement contract expert. Based on these clause violation
        patterns from supplier invoice audits, generate a specific, actionable
        contract negotiation recommendation for each clause type.

        Violation data: {json.dumps(llm_input_data)}

        Return JSON matching the schema with recommendations for each of the provided clause types.
        Recommendations must be concrete (max 2 sentences each).
        Focus on what to add or change in future contract drafts.
        """
        
        try:
            llm = get_llm()
            response = await llm.async_generate_content(
                contents=[prompt],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=ClauseRecommendationList.model_json_schema()
                )
            )
            rec_list = ClauseRecommendationList.model_validate_json(response.text)
            rec_map = {r.clause_type: r.recommendation for r in rec_list.recommendations}
        except Exception:
            # Silent fallback if LLM client is mock or error occurs
            pass

    # Standard fallback recommendations
    default_recs = {
        "overcharge": "Add invoice certification requirement for unit pricing in future contracts. Require suppliers to show tier calculation on each invoice line.",
        "unapplied_penalty": "Automate SLA data collection. Current manual process misses penalty triggers. Add contractual obligation for suppliers to self-report SLA breaches.",
        "missed_discount": "Standardize early payment discount terms and configure automated accounts payable alerts to capture discount windows.",
        "incorrect_rate": "Require pre-billing validation of billing rates against active contract schedule before invoice submission.",
        "missing_credit": "Establish quarterly reconciliation protocol to audit credit memo status against volume adjustments.",
        "period_mismatch": "Specify strict billing calendar terms in the contract, enforcing that invoices must only cover single calendar months.",
        "unknown": "Review contractual terms and audit protocols to clarify billing rules and invoice validation procedures."
    }

    insights_list = []
    # Build complete ClauseInsight objects for all types with violations
    for name, val in sorted_clauses:
        if val["count"] > 0:
            rec = rec_map.get(name) or default_recs.get(name, default_recs["unknown"])
            insights_list.append(ClauseInsight(
                clause_type=name,
                total_count=val["count"],
                total_leakage=val["total"],
                recommendation=rec
            ))
            
    return insights_list

async def compute_heatmap(audits: List[Audit]) -> dict:
    """
    Computes grid counts, totals, and insights for the clause heatmap dashboard.
    """
    clause_types = [
        "overcharge",
        "missed_discount",
        "unapplied_penalty",
        "incorrect_rate",
        "missing_credit",
        "period_mismatch"
    ]
    
    # Find all unique suppliers
    suppliers = sorted(list({a.supplier_name for a in audits if a.supplier_name}))
    
    # Initialize grid structure
    grid = {}
    for s in suppliers:
        grid[s] = {}
        for c in clause_types:
            grid[s][c] = {
                "count": 0,
                "total_leakage": Decimal("0.00")
            }
            
    column_totals = {}
    for c in clause_types:
        column_totals[c] = {
            "count": 0,
            "total_leakage": Decimal("0.00")
        }
        
    row_totals = {}
    for s in suppliers:
        row_totals[s] = {
            "count": 0,
            "total_leakage": Decimal("0.00")
        }

    # Aggregate violations from audits
    for a in audits:
        supplier = a.supplier_name
        if not supplier or not a.discrepancies:
            continue
            
        try:
            disc_data = json.loads(a.discrepancies)
            for finding in disc_data.get("discrepancies", []):
                dtype = finding.get("discrepancy_type", "unknown")
                if dtype not in clause_types:
                    continue
                delta = abs(Decimal(str(finding.get("delta", 0))))
                
                # Increment cells and aggregates
                grid[supplier][dtype]["count"] += 1
                grid[supplier][dtype]["total_leakage"] += delta
                
                column_totals[dtype]["count"] += 1
                column_totals[dtype]["total_leakage"] += delta
                
                row_totals[supplier]["count"] += 1
                row_totals[supplier]["total_leakage"] += delta
        except Exception:
            pass

    # Identify most violated clause type
    most_violated_clause_type = None
    max_violations = -1
    for c, val in column_totals.items():
        if val["count"] > max_violations:
            max_violations = val["count"]
            most_violated_clause_type = c
            
    # Identify most problematic supplier
    most_problematic_supplier = None
    max_supplier_leakage = Decimal("-1.00")
    for s, val in row_totals.items():
        if val["total_leakage"] > max_supplier_leakage:
            max_supplier_leakage = val["total_leakage"]
            most_problematic_supplier = s

    # Generate insights from column totals
    insight_totals = {
        c: {
            "count": val["count"],
            "total": val["total_leakage"]
        }
        for c, val in column_totals.items()
    }
    
    clause_insights = await generate_insights(insight_totals)
    
    insights = {
        "most_violated_clause_type": most_violated_clause_type if max_violations > 0 else None,
        "most_problematic_supplier": most_problematic_supplier if max_supplier_leakage > 0 else None,
        "clause_insights": clause_insights
    }

    return {
        "suppliers": suppliers,
        "clause_types": clause_types,
        "grid": grid,
        "column_totals": column_totals,
        "row_totals": row_totals,
        "insights": insights
    }


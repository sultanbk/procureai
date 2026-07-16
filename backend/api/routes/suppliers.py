"""
ProcureAI - File Summary

What it does:
Routers for fetching active suppliers, compliance indices, and history lists.

What it means:
Controller managing vendor profiles and scorecard rankings.

Importance in Project:
Medium. Delivers comparative supplier metrics to the client UI.
"""

from typing import List
from decimal import Decimal
from collections import defaultdict
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, desc

from backend.core.db import AsyncSessionLocal
from backend.models.audit import SupplierScore
from backend.models.schemas import SupplierScoreCard, SupplierSummaryKPIs

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])

@router.get("", response_model=List[SupplierScoreCard])
async def list_suppliers():
    """
    Returns list of all unique suppliers with scorecard details,
    sorted by latest compliance score ascending (riskiest first).
    """
    async with AsyncSessionLocal() as session:
        stmt = select(SupplierScore).order_by(SupplierScore.supplier_name, desc(SupplierScore.computed_at))
        result = await session.execute(stmt)
        scores = result.scalars().all()

    if not scores:
        return []

    # Group score records by supplier
    supplier_groups = defaultdict(list)
    for s in scores:
        supplier_groups[s.supplier_name].append(s)

    response_data = []
    for name, s_list in supplier_groups.items():
        latest = s_list[0]
        previous = s_list[1] if len(s_list) > 1 else None
        
        audit_count = len(s_list)
        total_leakage = Decimal(str(sum(score.total_leakage for score in s_list)))
        last_audit_date = latest.computed_at.isoformat()
        
        # Calculate trend
        if previous is None:
            trend = "new"
        else:
            diff = latest.score - previous.score
            if diff > 2.0:
                trend = "improving"
            elif diff < -2.0:
                trend = "worsening"
            else:
                trend = "stable"
                
        # Calculate risk band
        if latest.score >= 80.0:
            risk_band = "green"
        elif latest.score >= 50.0:
            risk_band = "amber"
        else:
            risk_band = "red"
            
        response_data.append(SupplierScoreCard(
            supplier_name=name,
            latest_score=latest.score,
            previous_score=previous.score if previous else None,
            trend=trend,
            audit_count=audit_count,
            total_leakage_identified=total_leakage,
            last_audit_date=last_audit_date,
            risk_band=risk_band
        ))

    # Sort by score ascending (riskiest first)
    response_data.sort(key=lambda x: x.latest_score)
    return response_data

@router.get("/summary", response_model=SupplierSummaryKPIs)
async def get_summary_kpis():
    """
    Returns aggregate scorecard KPIs across all suppliers.
    """
    async with AsyncSessionLocal() as session:
        stmt = select(SupplierScore).order_by(SupplierScore.supplier_name, desc(SupplierScore.computed_at))
        result = await session.execute(stmt)
        scores = result.scalars().all()

    if not scores:
        return SupplierSummaryKPIs(
            total_suppliers_tracked=0,
            average_score=0.0,
            suppliers_in_red_zone=0,
            total_leakage_all_time=Decimal("0.00"),
            most_at_risk_supplier=None,
            most_improved_supplier=None
        )

    # Group scores by supplier
    supplier_groups = defaultdict(list)
    for s in scores:
        supplier_groups[s.supplier_name].append(s)

    total_suppliers_tracked = len(supplier_groups)
    latest_scores = []
    red_zone_count = 0
    most_at_risk_supplier = None
    lowest_score = 101.0
    
    max_delta = -1000.0
    most_improved_supplier = None

    for name, s_list in supplier_groups.items():
        latest = s_list[0]
        latest_scores.append(latest.score)
        
        # Count red zone
        if latest.score < 50.0:
            red_zone_count += 1
            
        # Lowest latest score is most at risk
        if latest.score < lowest_score:
            lowest_score = latest.score
            most_at_risk_supplier = name
            
        # Track biggest positive score delta
        if len(s_list) > 1:
            previous = s_list[1]
            delta = latest.score - previous.score
            if delta > 0 and delta > max_delta:
                max_delta = delta
                most_improved_supplier = name

    # total leakage all-time is sum of total_leakage across all score rows in database
    total_leakage_all_time = Decimal(str(sum(s.total_leakage for s in scores)))
    
    average_score = sum(latest_scores) / len(latest_scores) if latest_scores else 0.0
    
    return SupplierSummaryKPIs(
        total_suppliers_tracked=total_suppliers_tracked,
        average_score=round(average_score, 1),
        suppliers_in_red_zone=red_zone_count,
        total_leakage_all_time=total_leakage_all_time,
        most_at_risk_supplier=most_at_risk_supplier,
        most_improved_supplier=most_improved_supplier
    )

@router.get("/{supplier_name}/history")
async def get_supplier_history(supplier_name: str):
    """
    Returns audit scorecard history for a single supplier.
    """
    async with AsyncSessionLocal() as session:
        # Fetch scores for this supplier ordered by computed_at desc
        stmt = select(SupplierScore).where(SupplierScore.supplier_name == supplier_name).order_by(desc(SupplierScore.computed_at))
        result = await session.execute(stmt)
        scores = result.scalars().all()

    if not scores:
        return {
            "history": [],
            "score_history": []
        }

    # Sort chronologically for sparkline (oldest first)
    chronological_scores = sorted(scores, key=lambda x: x.computed_at)

    history_list = [
        {
            "audit_id": s.audit_id,
            "score": s.score,
            "total_leakage": Decimal(str(s.total_leakage)),
            "created_at": s.computed_at.isoformat(),
            "discrepancy_count": s.critical_count + s.high_count + s.medium_count
        }
        for s in scores
    ]

    score_history = [
        {
            "date": s.computed_at.strftime("%Y-%m-%d"),
            "score": s.score
        }
        for s in chronological_scores
    ]

    return {
        "history": history_list,
        "score_history": score_history
    }

import json
from backend.models.audit import NegotiationBrief
from backend.services.negotiation_analyzer import aggregate_supplier_violations, generate_negotiation_brief
from backend.models.schemas import NegotiationBrief as NegotiationBriefSchema

@router.post("/{supplier_name}/negotiation-brief", response_model=NegotiationBriefSchema)
async def create_negotiation_brief(supplier_name: str):
    async with AsyncSessionLocal() as session:
        try:
            summary = await aggregate_supplier_violations(supplier_name, session)
            brief_schema = await generate_negotiation_brief(summary)
            
            new_brief = NegotiationBrief(
                id=brief_schema.brief_id,
                supplier_name=supplier_name,
                audits_analysed=brief_schema.audits_analysed,
                total_leakage_basis=brief_schema.total_leakage_basis,
                brief_json=brief_schema.model_dump_json()
            )
            session.add(new_brief)
            await session.commit()
            
            return brief_schema
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to generate brief: {str(e)}")

@router.get("/{supplier_name}/negotiation-briefs")
async def list_negotiation_briefs(supplier_name: str):
    async with AsyncSessionLocal() as session:
        stmt = select(NegotiationBrief).where(NegotiationBrief.supplier_name == supplier_name).order_by(desc(NegotiationBrief.generated_at))
        result = await session.execute(stmt)
        briefs = result.scalars().all()
        
    return [
        {
            "brief_id": b.id,
            "generated_at": b.generated_at.isoformat() if hasattr(b.generated_at, 'isoformat') else str(b.generated_at),
            "audits_analysed": b.audits_analysed,
            "total_leakage_basis": float(b.total_leakage_basis) if b.total_leakage_basis else 0.0
        } for b in briefs
    ]

@router.get("/{supplier_name}/negotiation-briefs/{brief_id}", response_model=NegotiationBriefSchema)
async def get_negotiation_brief(supplier_name: str, brief_id: str):
    async with AsyncSessionLocal() as session:
        stmt = select(NegotiationBrief).where(NegotiationBrief.id == brief_id, NegotiationBrief.supplier_name == supplier_name)
        result = await session.execute(stmt)
        brief = result.scalar_one_or_none()
        
    if not brief or not brief.brief_json:
        raise HTTPException(status_code=404, detail="Brief not found")
        
    return NegotiationBriefSchema.model_validate_json(brief.brief_json)

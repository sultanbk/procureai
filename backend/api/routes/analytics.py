"""
ProcureAI - File Summary

What it does:
Provides endpoint routes for analytics, savings summaries, and supplier score distributions.

What it means:
Controller delivering visual statistics and dashboard metrics to frontend views.

Importance in Project:
Medium. Direct backend data provider for the analytics dashboard charts.
"""

from datetime import timedelta
from typing import Literal
from fastapi import APIRouter, Query
from sqlalchemy import select

from backend.core.db import AsyncSessionLocal
from backend.core.time import utc_now
from backend.models.audit import Audit
from backend.services.analytics import compute_analytics, compute_heatmap
from backend.models.schemas import HeatmapData

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/overview")
async def get_analytics_overview(
    period: Literal["30d", "90d", "1y", "all"] = Query("30d")
):
    """
    Returns an aggregated overview of procurement leakage and audit counts
    over the specified time period.
    """
    now = utc_now()
    
    has_previous = False
    cutoff = None
    prev_cutoff = None
    period_label = "All Time"

    if period == "30d":
        cutoff = now - timedelta(days=30)
        prev_cutoff = cutoff - timedelta(days=30)
        has_previous = True
        period_label = "Last 30 days"
    elif period == "90d":
        cutoff = now - timedelta(days=90)
        prev_cutoff = cutoff - timedelta(days=90)
        has_previous = True
        period_label = "Last 90 days"
    elif period == "1y":
        cutoff = now - timedelta(days=365)
        prev_cutoff = cutoff - timedelta(days=365)
        has_previous = True
        period_label = "Last year"
    else:  # "all"
        has_previous = False
        period_label = "All Time"

    async with AsyncSessionLocal() as session:
        # Fetch current period audits
        if cutoff:
            stmt = select(Audit).where(
                Audit.status == "COMPLETE",
                Audit.completed_at >= cutoff
            )
        else:
            stmt = select(Audit).where(
                Audit.status == "COMPLETE"
            )
        result = await session.execute(stmt)
        audits = result.scalars().all()

        # Fetch previous period audits for trend calculation
        prev_audits = []
        if has_previous and prev_cutoff and cutoff:
            prev_stmt = select(Audit).where(
                Audit.status == "COMPLETE",
                Audit.completed_at >= prev_cutoff,
                Audit.completed_at < cutoff
            )
            prev_result = await session.execute(prev_stmt)
            prev_audits = prev_result.scalars().all()

    # Compute stats using the service
    analytics_data = compute_analytics(
        audits=list(audits),
        prev_audits=list(prev_audits),
        period_label=period_label,
        has_previous=has_previous
    )

    return analytics_data

@router.get("/heatmap", response_model=HeatmapData)
async def get_analytics_heatmap(
    period: Literal["30d", "90d", "1y", "all"] = Query("30d")
):
    """
    Returns data for the clause violation heatmap, showing suppliers as rows,
    clause types as columns, and violation counts/leakages as cells.
    """
    now = utc_now()
    cutoff = None

    if period == "30d":
        cutoff = now - timedelta(days=30)
    elif period == "90d":
        cutoff = now - timedelta(days=90)
    elif period == "1y":
        cutoff = now - timedelta(days=365)

    async with AsyncSessionLocal() as session:
        if cutoff:
            stmt = select(Audit).where(
                Audit.status == "COMPLETE",
                Audit.completed_at >= cutoff
            )
        else:
            stmt = select(Audit).where(
                Audit.status == "COMPLETE"
            )
        result = await session.execute(stmt)
        audits = result.scalars().all()

    # Compute heatmap
    heatmap_data = await compute_heatmap(list(audits))
    
    return heatmap_data

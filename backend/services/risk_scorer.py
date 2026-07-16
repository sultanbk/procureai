import json
from decimal import Decimal
from dataclasses import dataclass
from collections import defaultdict
from sqlalchemy.orm import Session
from backend.models.audit import Audit

@dataclass
class RiskScore:
    level:              str       # "HIGH" | "MEDIUM" | "LOW" | "NEW_SUPPLIER"
    score:              float     # 0.0 to 100.0 (100 = highest risk)
    supplier_name:      str
    reason:             str       # one sentence explanation
    focus_areas:        list[str] # specific clause types to watch
    audits_analysed:    int
    avg_leakage:        Decimal
    violation_rate:     float     # violations per audit


from sqlalchemy import select

async def compute_risk_score(supplier_name: str, db) -> RiskScore:
    """
    Deterministic heuristic scorer. No LLM. No ML.
    All math uses Decimal.
    """

    # Load all completed audits for this supplier
    stmt = select(Audit).where(
        Audit.supplier_name == supplier_name,
        Audit.status == "COMPLETE"
    )
    result = await db.execute(stmt)
    audits = result.scalars().all()

    # NEW SUPPLIER — no history
    if not audits:
        return RiskScore(
            level="NEW_SUPPLIER",
            score=50.0,
            supplier_name=supplier_name,
            reason="No audit history available for this supplier.",
            focus_areas=[],
            audits_analysed=0,
            avg_leakage=Decimal("0"),
            violation_rate=0.0
        )

    # Aggregate metrics
    total_leakage = sum(
        Decimal(str(a.total_leakage or 0)) for a in audits
    )
    avg_leakage = total_leakage / len(audits)

    audits_with_violations = sum(
        1 for a in audits
        if a.total_leakage and Decimal(str(a.total_leakage)) > 0
    )
    violation_rate = audits_with_violations / len(audits)  # 0.0 to 1.0

    # Count critical and high findings across all audits
    critical_total = 0
    high_total = 0
    clause_type_counts = defaultdict(int)

    for audit in audits:
        if not audit.discrepancies: continue
        data = json.loads(audit.discrepancies)
        for f in data.get("discrepancies", []):
            if f["severity"] == "CRITICAL": critical_total += 1
            if f["severity"] == "HIGH":     high_total += 1
            clause_type_counts[f["discrepancy_type"]] += 1

    # Check recency — did last audit have violations?
    latest_audit = max(audits, key=lambda a: a.completed_at if a.completed_at else a.created_at)
    latest_had_violations = (
        latest_audit.total_leakage and
        Decimal(str(latest_audit.total_leakage)) > 100
    )

    # Compute composite score (0–100, higher = riskier)
    score = 0.0
    score += violation_rate * 40          # up to 40 pts: how often they violate
    score += min(float(avg_leakage) / 1000, 30)  # up to 30 pts: avg leakage size
    score += min(critical_total * 5, 20)  # up to 20 pts: critical findings
    score += 10 if latest_had_violations else 0   # 10 pts: recent violation

    score = min(100.0, round(score, 1))

    # Classify
    if score >= 60:      level = "HIGH"
    elif score >= 30:    level = "MEDIUM"
    else:                level = "LOW"

    # Build reason
    if level == "HIGH":
        reason = (
            f"{supplier_name} violated contract terms in "
            f"{audits_with_violations} of {len(audits)} audits "
            f"with ${avg_leakage:,.2f} average leakage."
        )
    elif level == "MEDIUM":
        reason = (
            f"{supplier_name} has {audits_with_violations} violation(s) "
            f"across {len(audits)} audits. "
            f"Average leakage: ${avg_leakage:,.2f}."
        )
    else:
        reason = (
            f"{supplier_name} has a strong compliance record "
            f"across {len(audits)} audits."
        )

    # Focus areas: top 3 most violated clause types
    focus_areas = [
        k.replace("_", " ").title()
        for k, _ in sorted(
            clause_type_counts.items(),
            key=lambda x: x[1], reverse=True
        )[:3]
    ]

    return RiskScore(
        level=level,
        score=score,
        supplier_name=supplier_name,
        reason=reason,
        focus_areas=focus_areas,
        audits_analysed=len(audits),
        avg_leakage=avg_leakage,
        violation_rate=violation_rate
    )

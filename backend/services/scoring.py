"""
ProcureAI - File Summary

What it does:
Calculates normalized compliance scores for audit runs.

What it means:
Algorithmic scorer weighting severity and counts.

Importance in Project:
Medium. Standardizes supplier performance benchmarks.
"""

from backend.models.schemas import AuditReport

def compute_score(audit_report: AuditReport) -> float:
    """
    Computes a compliance score for the supplier based on audit results.
    
    Formula:
      base_score = (compliant_lines / total_lines_audited) * 100
      penalties:
        each CRITICAL finding: -8 points
        each HIGH finding:     -4 points
        each MEDIUM finding:   -1 point
      score = max(0.0, min(100.0, base_score - total_penalties))
      rounded to 1 decimal place.
    """
    summary = audit_report.summary
    total_lines = summary.total_lines_audited
    compliant_lines = summary.compliant_lines
    
    if total_lines == 0:
        base_score = 100.0
    else:
        # Calculate percentage of compliant lines
        base_score = (compliant_lines / total_lines) * 100.0
        
    # Calculate penalty points
    penalties = (
        (summary.critical_count * 8.0) +
        (summary.high_count * 4.0) +
        (summary.medium_count * 1.0)
    )
    
    # Calculate final score bounded by [0.0, 100.0]
    score = max(0.0, min(100.0, base_score - penalties))
    
    return round(score, 1)

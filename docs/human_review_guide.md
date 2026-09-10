# Human Review Guide

**Audience:** Developers, auditors, and business reviewers.

The human review loop in ProcureAI operates at two complementary levels:
1. **Item-Level Review:** For individual discrepancies flagged by the LLM Critic or flagged by low-confidence contract extraction rules (`extraction_confidence < 0.70`).
2. **Audit-Level Release Gate (`PENDING_REVIEW`):** For audits that uncover `CRITICAL` severity discrepancies, preventing automated release or closure until signed off by a human auditor.

## Implementation Summary

```mermaid
flowchart TD
    A[Invoice line and matched rule] --> B[Python rule engine]
    B --> C{Material discrepancy?}
    C -- no --> D[Compliant line]
    C -- yes --> CR{Rule flagged<br/>needs_human_review?}
    CR -- yes (Low Confidence) --> H[Force NEEDS_HUMAN_REVIEW<br/>(Bypass Critic)]
    CR -- no --> E[LLM critic]
    E --> F{Critic status}
    F -- CONFIRMED --> G[Confirmed discrepancy]
    F -- NEEDS_HUMAN_REVIEW --> H
    G --> I[Audit report]
    H --> I
    I --> CG{Any CRITICAL<br/>findings?}
    CG -- yes --> PR["Audit Status: PENDING_REVIEW<br/>(Amber Review Banner)"]
    CG -- no --> AC["Audit Status: COMPLETE"]
    PR --> Appr["POST /api/audit/{id}/approve<br/>(Click 'Approve Audit')"]
    Appr --> AC
    I --> J[Frontend review UI]
    J --> K[POST finding feedback]
    K --> L[finding_feedback table]
```


## Key Code Paths

| Area | File |
|---|---|
| Discrepancy creation and critic call | `backend/agents/compliance_checker/agent.py` |
| Critic prompt | `backend/agents/compliance_checker/prompt_critic.txt` |
| Report generation | `backend/agents/report_generator/agent.py` |
| Feedback endpoint | `backend/api/routes/audit.py` |
| Feedback table | `backend/models/audit.py` (`FindingFeedback`) |
| Frontend report UI | `frontend/src/pages/AuditReport.jsx` |
| Frontend API wrapper | `frontend/src/api.js` (`submitFindingFeedback`) |

## Critic Behavior

The critic can return:

- `CONFIRMED`
- `NEEDS_HUMAN_REVIEW`

The critic must not delete or rewrite the Python-computed finding. When it returns `NEEDS_HUMAN_REVIEW`, the finding remains in the report and a review flag is added with reasoning.

## Feedback Payload

```json
{
  "verdict": "CORRECT",
  "reason": "Reviewer confirmed this charge violates the contract.",
  "adjusted_delta": null,
  "reviewed_by": "human_reviewer"
}
```

Supported verdicts are documented in the route model comment as:

- `CORRECT`
- `FALSE_POSITIVE`
- `FALSE_NEGATIVE`
- `ADJUSTED`

## Database Storage

Feedback is stored in `finding_feedback` with audit ID, finding ID, supplier metadata, rule metadata when available, human verdict, adjusted delta, reason, reviewer, and review timestamp.

## Reviewer Guidance

Use human review for cases such as:

- Ambiguous contract wording.
- Missing operational data, such as SLA evidence or milestone responsibility.
- Supplier notes that conflict with simple rule application.
- Out-of-contract invoice items that may have separate approval.
- Historical false-positive patterns.

A reviewer should leave enough reason text for future auditors to understand the decision.

## Audit-Level Release Gate (`PENDING_REVIEW`)

When an audit uncovers one or more findings with `severity == Severity.CRITICAL` (such as major unapproved rate increases, billing discrepancies exceeding ₹50,000, or invalid contract clauses), the system places the entire audit on hold:

1. **State Transition:** The audit is assigned `status = "PENDING_REVIEW"` instead of `COMPLETE`.
2. **Review Alert:** The report page (`AuditReport.jsx`) displays an Amber Warning Banner indicating that critical discrepancies require procurement management approval.
3. **Approval Action:** Clicking the **"Approve Audit"** button calls `POST /api/audit/{audit_id}/approve`. Upon receiving approval, the audit status updates to `COMPLETE`, clearing the hold and finalizing the report.


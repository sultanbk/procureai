# User Guide

**Audience:** End users and business reviewers.

SupplierGuard helps procurement, finance, and operations teams audit supplier invoices against contract terms.

## Run a Manual Audit

1. Open the web app at `http://localhost:5173`.
2. Select the audit upload view.
3. Upload one contract PDF.
4. Upload one or more invoice PDFs.
5. Optionally enter a supplier name override.
6. Start the audit.
7. Wait for the progress view to reach `COMPLETE`.
8. Review the report, findings, recommendations, and supporting evidence.

If the system finds an identical prior audit and the UI exposes a rerun option, rerun with force to bypass duplicate detection.

## Review an Audit Report

Completed reports include:

- Executive summary
- Total leakage
- Compliance score
- Discrepancy list
- Severity and recommendation
- Contract clause evidence
- Human review flags
- Missing credits and price drift findings when available
- Audit logs and uploaded document views

Use document viewing and breach-page download actions to inspect source PDFs.

## Human Review Flags

Some findings are marked `NEEDS_HUMAN_REVIEW`. These are not deleted by the AI. They remain visible with critic reasoning so a human reviewer can decide whether the finding is correct, false positive, false negative, or adjusted.

The feedback is stored and can be used by future compliance logic to calibrate similar findings.

## Dispute Letters

For a completed audit:

1. Open the dispute letter modal.
2. Enter company, signatory, supplier contact, due date, and optional reference details.
3. Generate the letter.
4. Revise it by entering change instructions when needed.

Generated letters are stored in the database.

## Contract Library

The contract library stores reusable supplier contracts.

You can:

- Upload a contract PDF.
- Enter supplier name and aliases.
- Set validity dates.
- Archive, restore, or permanently delete contracts.
- Let the backend parse a baseline rulebook for future use.

Aliases help the auto-audit watcher match invoice supplier names to contract records.

## Auto-Audit Watcher

The backend watches:

```text
watched_invoices/
```

When a PDF invoice appears:

1. The watcher extracts the supplier name.
2. It searches active contracts by exact name, aliases, then partial match.
3. If matched, it runs an audit automatically.
4. Processed files move to `watched_invoices/processed/`.
5. Unmatched files move to `watched_invoices/unmatched/`.

Use the Auto-Audit view to pause, resume, inspect history, and retry unmatched files with a selected contract.

## Supplier Scorecards and Analytics

Supplier views show scorecards, risk bands, audit history, leakage trends, and negotiation briefs.

Analytics views show:

- Leakage over time
- Leakage by supplier
- Leakage by discrepancy type
- Severity breakdown
- Top findings
- Clause violation heatmap

## Contract Q&A

Completed audits can expose a contract Q&A drawer. Answers are generated from contract rulebook/chunk context and include confidence metadata plus citations when available.

## Limitations

- Scanned image-only PDFs are not supported unless they contain extractable text.
- Live LLM quality depends on configured Gemini/Vertex credentials and model behavior.
- The app is local-development oriented unless deployed behind production-grade security controls.

# Database Guide

**Audience:** Developers and operators.

## Engine

`backend/core/db.py` creates an async SQLAlchemy engine. SQLite URLs beginning with `sqlite://` are converted to `sqlite+aiosqlite://`.

For SQLite connections, the backend enables:

- `PRAGMA foreign_keys=ON`
- `PRAGMA journal_mode=WAL`

## Initialization

```powershell
python -m scripts.seed_db
```

`scripts/seed_db.py` imports ORM models and calls `Base.metadata.create_all`.

## Migration Helper

```powershell
python -m scripts.migrate_db
```

The migration helper currently checks and adds selected `contracts` and `contract_chunks` columns/indexes for older local databases. It is not a general migration framework.

## Primary Tables

| Table | Notes |
|---|---|
| `audits` | Central audit record; stores JSON outputs for rulebook, invoice data, discrepancies, and report |
| `audit_logs` | Pipeline telemetry and user-visible logs |
| `dispute_letters` | One generated/revised dispute letter per audit |
| `supplier_scores` | Score snapshots derived from completed reports |
| `notification_settings` | Singleton settings row with `id=1` |
| `contract_chunks` | Chunks used for RAG contract Q&A |
| `contracts` | Contract library records with aliases, file hash, version, validity dates, and rulebook |
| `watched_files` | Auto-audit watcher history |
| `comparisons` | Contract comparison jobs |
| `negotiation_briefs` | Supplier negotiation brief JSON |
| `finding_feedback` | Human verdict records |

## JSON Columns

Several columns are `Text` fields containing JSON:

- `audits.invoice_files`
- `audits.rulebook`
- `audits.invoice_data`
- `audits.discrepancies`
- `audits.audit_report`
- `contracts.supplier_aliases`
- `contracts.rulebook`
- `comparisons.diff_result`
- `negotiation_briefs.brief_json`
- `dispute_letters.request_payload`

When updating these fields, serialize through Pydantic `model_dump` / `model_dump_json` where possible to keep schemas stable.

## Data Retention Behavior

Deleting an audit removes related audit logs, supplier scores, contract chunks, dispute letters, and the audit record. It also tries to delete uploaded files under the configured upload directory. It does not delete files outside the upload directory.

Archiving a contract sets `is_active=0`. Permanent contract deletion also removes related chunks and baseline audit logs.

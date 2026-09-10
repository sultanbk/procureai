# API Reference

**Audience:** Developers integrating with the backend or maintaining the frontend.

Base URL in local development:

```text
http://localhost:8000
```

Most application endpoints are under `/api`. The OpenAPI UI is available at `/docs` while the backend is running.

## Authentication

`frontend/src/api.js` sends `X-API-Key` when `VITE_API_KEY` is configured. `backend/api/middleware.py` implements API-key middleware, but `backend/main.py` does not currently mount it. Unless that middleware is registered, endpoints are not API-key protected.

## Health

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Root welcome message |
| `GET` | `/api/health` | Basic health check |
| `GET` | `/api/health/runtime` | Runtime configuration/status check |

## Uploads

### Upload Contract

```http
POST /api/upload/contract
Content-Type: multipart/form-data
```

Form fields:

| Field | Type | Required |
|---|---|---|
| `file` | PDF file | yes |

Response:

```json
{
  "file_id": "contract_abcd1234_contract.pdf",
  "filename": "contract.pdf",
  "size_bytes": 123456,
  "file_type": "contract"
}
```

### Upload Invoice

```http
POST /api/upload/invoice
Content-Type: multipart/form-data
```

Same response shape as contract upload with `file_type` set to `invoice`.

## Audits

### Run Audit

```http
POST /api/audit/run
Content-Type: application/json
```

```json
{
  "contract_file_id": "contract_abcd1234_contract.pdf",
  "invoice_file_ids": ["invoice_1234_invoice.pdf"],
  "supplier_name": "Optional Supplier Override",
  "force": false
}
```

Returns `202 Accepted`:

```json
{
  "audit_id": "aud_1234abcd",
  "status": "PENDING"
}
```

If the same contract and invoice set already exists and `force` is false, the API returns the existing audit ID with status `EXISTS`.

### Audit Status

```http
GET /api/audit/{audit_id}
```

Returns `AuditStatusResponse`, including status, progress percentage, current agent, partial counts, and completed report when available.

### Other Audit Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/audit/{audit_id}/report` | Completed `AuditReport` only |
| `POST` | `/api/audit/{audit_id}/approve` | Approve audit in `PENDING_REVIEW` and transition to `COMPLETE` |
| `GET` | `/api/audit/{audit_id}/documents` | List contract and invoice documents for an audit |
| `GET` | `/api/audit/{audit_id}/documents/{document_id}` | Inline PDF response for `contract` or `invoice-{index}` |
| `GET` | `/api/audit/{audit_id}/breach-pages/{finding_id}` | Download contract pages related to a finding |
| `GET` | `/api/audits` | List non-baseline audits |
| `DELETE` | `/api/audit/{audit_id}` | Delete audit and related records/files under upload directory |
| `GET` | `/api/audit/{audit_id}/logs` | Audit log entries |
| `POST` | `/api/predict/risk` | Supplier risk prediction by supplier name or invoice file ID |
| `POST` | `/api/audit/{audit_id}/findings/{finding_id}/feedback` | Store human review verdict |
| `WS` | `/api/audit/{audit_id}/ws` | Stream status and audit logs |

### Approve Audit

```http
POST /api/audit/{audit_id}/approve
```

Used by authorized reviewers to approve an audit that is held in `PENDING_REVIEW` state due to `CRITICAL` severity findings. Transitions the audit status to `COMPLETE`.

Response (`200 OK`):
```json
{
  "message": "Audit aud_1234abcd approved successfully",
  "audit_id": "aud_1234abcd",
  "status": "COMPLETE"
}
```

Error Responses:
- `404 Not Found`: Audit does not exist.
- `400 Bad Request`: Audit is not in `PENDING_REVIEW` state (e.g. already `COMPLETE` or `FAILED`).

### Finding Feedback

```json
{
  "verdict": "CORRECT",
  "reason": "Confirmed by procurement reviewer",
  "adjusted_delta": null,
  "reviewed_by": "analyst@example.com"
}
```

Allowed verdict values are documented in code comments as `CORRECT`, `FALSE_POSITIVE`, `FALSE_NEGATIVE`, and `ADJUSTED`.

### Audit Lifecycle Statuses

| Status | Description |
|---|---|
| `PENDING` | Audit registered in database and queued for execution |
| `RUNNING` | Audit pipeline currently executing through agent graph |
| `PENDING_REVIEW` | Audit pipeline finished, but one or more `CRITICAL` severity discrepancies were identified; held awaiting auditor approval |
| `COMPLETE` | Audit finished and fully approved/cleared; reports and dispute letters unlocked |
| `FAILED` | Pipeline crashed or unrecoverable error encountered |
| `CANCELLED` | Audit cancelled by operator |


## Contract Library

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/contracts` | Register contract PDF and start baseline parsing |
| `GET` | `/api/contracts?show_archived=false` | List active or archived contracts |
| `DELETE` | `/api/contracts/{id}?permanent=false` | Archive or permanently delete a contract |
| `POST` | `/api/contracts/{id}/restore` | Restore archived contract |
| `PATCH` | `/api/contracts/{id}/aliases` | Replace supplier aliases |
| `POST` | `/api/contracts/{audit_id}/chat` | Streaming contract Q&A over audit context |

Register contract form fields:

| Field | Type | Required |
|---|---|---|
| `file` | PDF file | yes |
| `supplier_name` | string | no |
| `supplier_aliases` | comma-separated string | no |
| `valid_from` | ISO datetime/date string | no |
| `valid_until` | ISO datetime/date string | no |

Alias request:

```json
{
  "aliases": ["Apex", "Apex Logistics Ltd"]
}
```

## Contract Comparison

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/compare/upload` | Upload old and new contract PDFs for comparison |
| `GET` | `/api/compare/{comparison_id}` | Fetch comparison status or result |
| `GET` | `/api/compare` | List comparisons |

Upload form fields:

- `old_contract`
- `new_contract`

## Suppliers and Analytics

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/suppliers` | Supplier scorecards |
| `GET` | `/api/suppliers/summary` | Supplier KPI summary |
| `GET` | `/api/suppliers/{supplier_name}/history` | Supplier audit history |
| `POST` | `/api/suppliers/{supplier_name}/negotiation-brief` | Generate negotiation brief |
| `GET` | `/api/suppliers/{supplier_name}/negotiation-briefs` | List briefs |
| `GET` | `/api/suppliers/{supplier_name}/negotiation-briefs/{brief_id}` | Fetch brief |
| `GET` | `/api/analytics/overview?period=30d` | Leakage and severity analytics |
| `GET` | `/api/analytics/heatmap?period=30d` | Supplier-by-clause heatmap |

Valid analytics periods: `30d`, `90d`, `1y`, `all`.

## Disputes

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/disputes/{audit_id}` | Get saved dispute letter |
| `POST` | `/api/disputes/generate` | Generate dispute letter for completed audit |
| `POST` | `/api/disputes/revise` | Revise existing dispute letter text |

Generate request:

```json
{
  "audit_id": "aud_1234abcd",
  "company_name": "Buyer Company",
  "signatory_name": "Jane Doe",
  "signatory_title": "Head of Procurement",
  "supplier_contact": "Supplier Accounts Team",
  "supplier_email": "ap@example.com",
  "due_date": "2026-07-31",
  "reference_number": "REF-1001"
}
```

## Settings and Notifications

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/settings/notifications` | Read notification settings |
| `PUT` | `/api/settings/notifications` | Update notification settings |
| `POST` | `/api/settings/notifications/test-slack` | Send test Slack notification |
| `POST` | `/api/settings/notifications/test-email` | Send test email notification |

## File Watcher

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/watcher/status` | Watcher state and queue count |
| `POST` | `/api/watcher/pause` | Pause watching |
| `POST` | `/api/watcher/resume` | Resume and scan existing files |
| `GET` | `/api/watcher/history` | Last 50 watcher records |
| `GET` | `/api/watcher/unmatched` | Files waiting for manual contract match |
| `POST` | `/api/watcher/retry/{filename}` | Retry unmatched invoice with selected contract |

Retry body:

```json
{
  "contract_id": "ctr_supplier_abcd"
}
```

## Context Substrate & Knowledge Graph

Endpoints providing access to the Prodapt SynaptAI 4-Store TriStore, visual reasoning subgraphs, 5-stage retrieval pass cards, corporate dispute recovery SOP DAGs, and Context Provider management.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/context-substrate/status` | Read Substrate connection health, active mode, and store statistics |
| `POST` | `/api/context-substrate/query` | Execute grounded semantic query across TriStore (returns answer, subgraph, pass card) |
| `GET` | `/api/context-substrate/graph/{contract_id}` | Fetch full entity-relationship graph for a contract |
| `GET` | `/api/context-substrate/subgraph/discrepancy/{finding_id}` | Generate focused visual proof subgraph for an invoice audit finding |
| `GET` | `/api/context-substrate/procedures/{intent}` | Retrieve corporate Standard Operating Procedure as a sequential DAG (`PRECEDES`) |
| `GET` | `/api/context-substrate/amendments/{contract_id}/{clause_name}` | Resolve latest governing rate by traversing `SUPERSEDES` relationships |
| `GET` | `/api/context-substrate/providers` | List active Context Provider sandbox namespaces |
| `POST` | `/api/context-substrate/providers` | Register a new Context Provider with customized extraction settings |
| `DELETE` | `/api/context-substrate/providers/{provider_id}` | Remove a Context Provider sandbox namespace |

### Query Substrate Request

```http
POST /api/context-substrate/query
Content-Type: application/json
```

```json
{
  "query": "What is the revised bandwidth rate in Amendment 1?",
  "provider_id": "procureai",
  "contract_id": "doc_msa_apex",
  "max_hops": 2,
  "min_confidence": 0.70
}
```

### Response Shape

Returns `ContextSubstrateQueryResponse`:
- `answer`: Grounded synthesis from verbatim contract clauses.
- `reasoning_subgraph`: Graph nodes and directed edges (`SUPERSEDES`, `GOVERNED_BY`, `BILLED_ON`) used for visual inspection.
- `pass_card`: 5-Stage scorecard (Knowledge Store, Context Graph, Procedure Store, Fusion Layer, Generation Groundedness) with `hallucination_probability_pct`.
- `sources`: Verbatim clause chunks and citation metadata.


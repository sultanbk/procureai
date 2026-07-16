# Graph Report - .  (2026-06-13)

## Corpus Check
- 177 files · ~101,390 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 891 nodes · 2248 edges · 77 communities (51 shown, 26 thin omitted)
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 444 edges (avg confidence: 0.51)
- Token cost: 139,589 input · 4,892 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]

## God Nodes (most connected - your core abstractions)
1. `Audit` - 62 edges
2. `InvoiceData` - 52 edges
3. `PricingRule` - 46 edges
4. `AuditReport` - 45 edges
5. `authFetch()` - 37 edges
6. `PipelineState` - 35 edges
7. `LineItem` - 35 edges
8. `AgentError` - 30 edges
9. `Discrepancy` - 27 edges
10. `CompliantLine` - 27 edges

## Surprising Connections (you probably didn't know these)
- `StateGraph` --uses--> `PipelineState`  [INFERRED]
  backend/agents/pipeline.py → backend/models/schemas.py
- `Contract` --uses--> `Audit`  [INFERRED]
  backend/services/file_watcher.py → backend/api/routes/audit.py
- `Observer` --uses--> `Audit`  [INFERRED]
  backend/services/file_watcher.py → backend/api/routes/audit.py
- `_load_environment()` --calls--> `Path`  [INFERRED]
  backend/core/config.py → backend/services/file_watcher.py
- `test_agent()` --calls--> `PipelineState`  [EXTRACTED]
  scripts/test_real_ippb_parser.py → backend/models/schemas.py

## Import Cycles
- 1-file cycle: `backend/agents/compliance_checker/agent.py -> backend/agents/compliance_checker/agent.py`
- 1-file cycle: `backend/agents/compliance_checker/rule_engine.py -> backend/agents/compliance_checker/rule_engine.py`
- 1-file cycle: `backend/agents/compliance_checker/tools.py -> backend/agents/compliance_checker/tools.py`
- 1-file cycle: `backend/agents/report_generator/tools.py -> backend/agents/report_generator/tools.py`
- 1-file cycle: `backend/main.py -> backend/main.py`
- 1-file cycle: `backend/core/time.py -> backend/core/time.py`
- 1-file cycle: `backend/models/schemas.py -> backend/models/schemas.py`

## Communities (77 total, 26 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (99): ABC, AgentProgressBar Component, FILE CANONICAL IDENTIFIER: backend/agents/pipeline.py MODULE ROLE: Orchestrates, bool, Decimal, float, InvoiceData, LineItem (+91 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (84): PipelineState, AsyncSession, Audit, AuditReport, DisputeLetterRequest, DisputeLetterResponse, DisputeLetterRevisionRequest, str (+76 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (67): build_pipeline(), Builds the linear LangGraph state pipeline.     Flow: Invoice Extractor -> Cont, PipelineState, str, str, str, Any, float (+59 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (49): ContractRulebook, str, bool, ContractRulebook, PricingRule, str, float, PipelineState (+41 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (41): str, Any, str, datetime, lifespan(), FILE CANONICAL IDENTIFIER: backend/main.py MODULE ROLE: Entrypoint for the Fast, str, Contract (+33 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (45): get_pipeline(), Returns the compiled LangGraph pipeline singleton., AuditRequest, Audit, BackgroundTasks, int, str, Any (+37 more)

### Community 6 - "Community 6"
Cohesion: 0.10
Nodes (41): AliasUpdate, BackgroundTasks, str, UploadFile, bool, bytes, str, UploadFile (+33 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (41): audit_id, audit_report, audit_id, compliant_lines, discrepancies, recommendations, report_generated_at, summary (+33 more)

### Community 8 - "Community 8"
Cohesion: 0.13
Nodes (30): AuditDocumentPanel(), authFetch(), deleteAudit(), deleteContract(), downloadBreachPages(), fetchAuditDocumentBlob(), getAuditDocuments(), getAudits() (+22 more)

### Community 9 - "Community 9"
Cohesion: 0.06
Nodes (33): dependencies, jspdf, lucide-react, react, react-dom, recharts, devDependencies, autoprefixer (+25 more)

### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (15): bool, bytes, str, str, get_llm(), is_mock_llm_enabled(), FILE CANONICAL IDENTIFIER: backend/core/llm_client.py MODULE ROLE: Interfaces w, Returns a configured SmartGenerativeModel client instance (singleton).     Atte (+7 more)

### Community 11 - "Community 11"
Cohesion: 0.38
Nodes (25): add_clause(), add_header(), add_section(), build_c001_apex_logistics(), build_c001_apex_logistics_v2(), build_c002_techsoft_solutions(), build_c003_buildright_contractors(), build_c004_medisupply() (+17 more)

### Community 12 - "Community 12"
Cohesion: 0.20
Nodes (5): Table(), TableBody(), TableCell(), TableHead(), TableRow()

### Community 13 - "Community 13"
Cohesion: 0.12
Nodes (4): getAuditLogs(), getAuditStatus(), severityVariant(), variants

### Community 14 - "Community 14"
Cohesion: 0.13
Nodes (14): DisputeLetterModal(), AuditList(), AutoAudit(), ContractLibrary(), Settings(), generateDisputeLetter(), getDisputeLetter(), reviseDisputeLetter() (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.16
Nodes (14): Analytics(), CLAUSE_DISPLAY_NAMES, CLAUSE_ICONS, MonthTooltip(), PERIOD_TABS, PIE_COLORS, SupplierTooltip(), TypeTooltip() (+6 more)

### Community 16 - "Community 16"
Cohesion: 0.12
Nodes (4): suggestedQuestions, chatWithContract(), sizes, variants

### Community 17 - "Community 17"
Cohesion: 0.26
Nodes (7): APIKeyMiddleware, LoggingMiddleware, RateLimitMiddleware, ProcureAI - File Summary  What it does: Implements custom FastAPI middleware, BaseHTTPMiddleware, Request, Response

### Community 18 - "Community 18"
Cohesion: 0.24
Nodes (10): str, SupplierScoreCard, SupplierSummaryKPIs, get_summary_kpis(), get_supplier_history(), list_suppliers(), ProcureAI - File Summary  What it does: Routers for fetching active suppliers, Returns audit scorecard history for a single supplier. (+2 more)

### Community 19 - "Community 19"
Cohesion: 0.24
Nodes (10): bool, float, int, str, get_bool(), get_float(), get_int(), get_list() (+2 more)

### Community 20 - "Community 20"
Cohesion: 0.22
Nodes (9): run_contract_parser, run_invoice_extractor, Audit, run_audit_pipeline, Contract Parser Prompt, ContractRulebook, InvoiceData, enrich_pricing_rule (+1 more)

### Community 21 - "Community 21"
Cohesion: 0.47
Nodes (8): add_clause(), add_header(), add_section(), build_acme_contract(), build_acme_invoice(), create_pdf(), generate_invoice_table(), get_custom_styles()

### Community 22 - "Community 22"
Cohesion: 0.29
Nodes (3): isAuditFlowActive(), NAV_GROUPS, NavContent()

### Community 23 - "Community 23"
Cohesion: 0.33
Nodes (6): evaluate_line_rule, FlatRateEvaluator, MilestonePenaltyEvaluator, RuleEvaluator, SLAPenaltyEvaluator, VolumeTierEvaluator

### Community 24 - "Community 24"
Cohesion: 0.70
Nodes (4): build_ippb_invoice(), create_pdf(), generate_invoice_table(), get_custom_styles()

### Community 25 - "Community 25"
Cohesion: 0.40
Nodes (4): db_engine(), db_session(), Create a test database engine., Create a new database session for a test.

### Community 26 - "Community 26"
Cohesion: 0.67
Nodes (3): run_report_generator, PipelineState, run_cross_validator

## Ambiguous Edges - Review These
- `Dispute Generator Prompt` → `Dispute Generator Prompt`  [AMBIGUOUS]
  backend/agents/dispute_generator/prompt.txt · relation: conceptually_related_to

## Knowledge Gaps
- **136 isolated node(s):** `str`, `str`, `bool`, `int`, `float` (+131 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Dispute Generator Prompt` and `Dispute Generator Prompt`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `get_llm()` connect `Community 10` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `Audit` connect `Community 5` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 6`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `Audit` connect `Community 2` to `Community 0`, `Community 1`, `Community 4`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 59 inferred relationships involving `Audit` (e.g. with `AliasUpdate` and `AuditRequest`) actually correct?**
  _`Audit` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `InvoiceData` (e.g. with `bool` and `Decimal`) actually correct?**
  _`InvoiceData` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `PricingRule` (e.g. with `bool` and `Decimal`) actually correct?**
  _`PricingRule` has 37 INFERRED edges - model-reasoned connections that need verification._
# ProcureAI & Prodapt SynaptAI: Context Substrate Comprehensive Reference

> **The definitive guide to how SynaptAI Context Substrate is architected, integrated, and used across ProcureAI.**
> Covers exact file locations, frontend components, backend services, data structures, and end-to-end execution workflows.

---

## 1. Executive Summary & Purpose

**ProcureAI** is an autonomous enterprise contract compliance and invoice audit platform. It solves multi-million dollar billing leakage across telecom, cloud, and logistics procurement agreements.

Enterprise contract auditing presents a fatal challenge for standard AI (ChatGPT, raw LLMs, or standard RAG):
* **The Amendment Trap:** Contracts are constantly modified. A baseline 2022 Master Services Agreement states circuit rates are **$1,200/month**. In 2024, **Amendment 1** supersedes that rate to **$950/month**. Standard vector search retrieves both passages, cannot resolve temporal legal hierarchy, and hallucinates or audits against obsolete rates.
* **Lack of Procedural Governance:** When an overcharge is discovered, enterprise CFOs cannot simply deduct money without following corporate Standard Operating Procedures (SOPs) and notice periods. Standard LLMs have no concept of sequential procedural rules.

### The Solution: ProcureAI's Dual-Brain Architecture
ProcureAI pairs two specialized engines:

```
                           ┌───────────────────────────────────────────┐
                           │        ProcureAI Dual-Brain Engine        │
                           └─────────────────────┬─────────────────────┘
                                                 │
                    ┌────────────────────────────┴────────────────────────────┐
                    ▼                                                         ▼
         ┌──────────────────────────────┐                         ┌──────────────────────────────┐
         │ Deterministic Math Engine    │                         │  SynaptAI Context Substrate  │
         │ (backend/core/rule_engine.py)│                         │  (Epistemic Knowledge Brain) │
         │ - Pure Decimal arithmetic    │                         │ - Neo4j Concept Graph        │
         │ - Overcharge calculation     │                         │ - Amendment supersession     │
         │ - ZERO-MATH LLM RULE         │                         │ - Corporate dispute SOP DAGs │
         │ - Tax, GST, volume brackets  │                         │ - Verbatim clause provenance │
         └──────────────┬───────────────┘                         └──────────────┬───────────────┘
                        │                                                         │
                        └────────────────────────────┬────────────────────────────┘
                                                     ▼
                           ┌───────────────────────────────────────────┐
                           │    Enterprise Grounded Audit & Proof      │
                           │  1. Unambiguous Clause Grounding          │
                           │  2. Visual Reasoning Subgraph Proof       │
                           │  3. 5-Stage Retrieval Pass Card Score     │
                           │  4. Dispute Letter with SOP DAG Execution │
                           └───────────────────────────────────────────┘
```

1. **Deterministic Financial Math Engine (`rule_engine.py`):** Python `Decimal` performs 100% of monetary math. Large Language Models and vector databases are strictly forbidden from performing arithmetic.
2. **Epistemic Knowledge Brain (SynaptAI Context Substrate):** A governed 4-store knowledge substrate that supplies unambiguous contractual truth, tracks amendment supersessions, and orchestrates dispute recovery playbooks.

---

## 2. The 4-Store Unified Epistemic Topology

Context Substrate combines four distinct storage technologies into a unified graph-vector brain:

```
                          ┌─────────────────────────────────────────┐
                          │    Context Substrate (The 4 Stores)     │
                          └────────────────────┬────────────────────┘
                                               │
     ┌──────────────────┬──────────────────────┴─────┬──────────────────┐
     ▼                  ▼                            ▼                  ▼
┌──────────────┐ ┌──────────────┐             ┌──────────────┐   ┌──────────────┐
│ 1. Neo4j     │ │ 2. Milvus KS │             │ 3. Milvus PS │   │ 4. Milvus GN │
│ Concept Graph│ │KnowledgeStore│             │ProcedureStore│   │Node Index    │
│ (The Web)    │ │ (The Text)   │             │ (Playbooks)  │   │ (The GPS)    │
└──────────────┘ └──────────────┘             └──────────────┘   └──────────────┘
```

1. **Neo4j Concept Graph (The Skeleton):** Stores entities (Vendors, Customers, Contracts), legal propositions, and directed relationships (`SUPERSEDES`, `GOVERNED_BY`, `BILLED_ON`, `PRECEDES`).
2. **Milvus Knowledge Store / KS (The Text):** Dense vector embeddings of contract chunks. Delivers semantic text retrieval, section hierarchy, and verbatim evidence citations.
3. **Milvus Procedural Store / PS (The Playbooks):** Standard Operating Procedures indexed as Directed Acyclic Graphs (DAGs) for recovery workflows and dispute escalations.
4. **Milvus Graph Node Index / GN (The GPS):** Semantic vector index of graph node descriptions mapped directly to Neo4j Node IDs. Bridges natural language queries directly to graph anchor entry points without string matching.

---

## 3. WHERE Context Substrate is Used in This Project

The table below provides a comprehensive map of every file, endpoint, and component implementing Context Substrate:

### A. Backend Architecture & Services

| File Path | Role & Purpose | Key Functions / Symbols |
| :--- | :--- | :--- |
| [`backend/core/config.py`](file:///d:/sultan/ProcureAI/procureai/backend/core/config.py) | Central configuration tokens, endpoints, and credentials. | `CONTEXT_SUBSTRATE_ENABLED`, `CONTEXT_SUBSTRATE_MODE`, `CONTEXT_SUBSTRATE_URL`, `SYNAPT_MCP_URL`, `SYNAPT_AGENT_TOKEN`, `SYNAPT_AGENT_CLIENT_ID` |
| [`backend/core/context_substrate_client.py`](file:///d:/sultan/ProcureAI/procureai/backend/core/context_substrate_client.py) | The core client connector. Implements Trident MCP client, live REST TriStore queries, and resilient embedded fallback engine. | `ContextSubstrateClient`, `get_status()`, `query_tristore()`, `get_contract_graph()`, `get_procedure_dag()`, `get_discrepancy_subgraph()`, `resolve_amendment_hierarchy()` |
| [`backend/models/schemas.py`](file:///d:/sultan/ProcureAI/procureai/backend/models/schemas.py) | Pydantic data schemas representing graph nodes, edges, pass cards, and SOP DAGs. | `GraphNode`, `GraphEdge`, `ReasoningSubgraph`, `StageScore`, `RetrievalPassCard`, `ProcedureStep`, `ProcedureDAG`, `ContextSubstrateQueryResponse`, `ContextSubstrateStatusResponse` |
| [`backend/core/mock_substrate_data.py`](file:///d:/sultan/ProcureAI/procureai/backend/core/mock_substrate_data.py) | High-fidelity embedded benchmark dataset (Apex Telecom MSA, Amendment 1 rate revision, SLA 10% credit, dispute DAG). | `SAMPLE_KNOWLEDGE_GRAPH`, `MOCK_PROCEDURE_DAGS`, `generate_default_pass_card()` |
| [`backend/api/routes/context_substrate.py`](file:///d:/sultan/ProcureAI/procureai/backend/api/routes/context_substrate.py) | FastAPI route controller exposing substrate REST endpoints under `/api/context-substrate`. | `get_status()`, `query_substrate()`, `get_contract_graph()`, `get_discrepancy_subgraph()`, `get_procedure_dag()`, `resolve_amendment()`, `list_providers()`, `create_provider()` |
| [`backend/api/routes/contracts.py`](file:///d:/sultan/ProcureAI/procureai/backend/api/routes/contracts.py) | Streaming Contract Q&A assistant that enriches citations with reasoning subgraphs and pass cards. | `ask_contract_question()`, citation enrichment pipeline |
| [`backend/services/dispute_generator.py`](file:///d:/sultan/ProcureAI/procureai/backend/services/dispute_generator.py) | Vendor dispute letter engine. Injects corporate recovery SOP DAGs from Milvus PS into formal dispute responses. | `generate_dispute_letter()`, `DisputeLetterResponse.procedure_dag` |
| [`context_substrate/demo-agent-ipl/`](file:///d:/sultan/ProcureAI/procureai/context_substrate/demo-agent-ipl/) | Official Prodapt Trident MCP Registered Agent SDK. Enables CLI tools and external S2S agent connectivity. | `query.py`, `query_agent/agent.py` (`QueryAgent`), `query_agent/mcp_client.py` (`SynaptMCP`), `query_agent/s2s.py` (`SecretTokenSource`, `StaticTokenSource`) |

---

### B. Frontend Screens & Visual Components

| Component / Screen | Visual Role in UI | Key Features |
| :--- | :--- | :--- |
| [`frontend/src/pages/Settings.jsx`](file:///d:/sultan/ProcureAI/procureai/frontend/src/pages/Settings.jsx) | **Context Substrate Control Center** (Tab 3 in Settings). | Live status indicators, 4-store architecture overview, **Run Diagnostic Query** runner, and Context Provider management cards. |
| [`frontend/src/components/ContractQADrawer.jsx`](file:///d:/sultan/ProcureAI/procureai/frontend/src/components/ContractQADrawer.jsx) | **Interactive Contract Q&A Assistant** (Right slide-over drawer in Contracts). | Answers grounded in live contracts; displays **View Subgraph** button and **5-Stage Pass Card** badge for every citation. |
| [`frontend/src/components/EvidenceBlock.jsx`](file:///d:/sultan/ProcureAI/procureai/frontend/src/components/EvidenceBlock.jsx) | **Audit Finding Evidence Inspector** (In Invoice Audit finding cards). | Displays contract clause grounding with an inline **View Reasoning Subgraph** button for CFO/auditor verification. |
| [`frontend/src/components/DisputeLetterModal.jsx`](file:///d:/sultan/ProcureAI/procureai/frontend/src/components/DisputeLetterModal.jsx) | **Vendor Dispute Letter Generator & Dispatcher**. | Renders formal dispute letters with a **View SOP Recovery Playbook** toggle showing step-by-step withholding rules. |
| [`frontend/src/components/ReasoningSubgraphModal.jsx`](file:///d:/sultan/ProcureAI/procureai/frontend/src/components/ReasoningSubgraphModal.jsx) | **Interactive Visual Knowledge Graph Modal**. | SVG force-directed/radial graph viewer with glowing semantic anchors, typed edges (`SUPERSEDES`, `GOVERNED_BY`), edge-type filters, zoom/pan, and Node Inspector drawer. |
| [`frontend/src/components/RetrievalPassCard.jsx`](file:///d:/sultan/ProcureAI/procureai/frontend/src/components/RetrievalPassCard.jsx) | **5-Stage Verification Scorecard**. | Stepper displaying 0–100 scores across KS, Graph, PS, Fusion, and Generation, with explicit risk indicators (Hallucination Risk %, Knowledge Gap %). |
| [`frontend/src/components/ProcedureDAGViewer.jsx`](file:///d:/sultan/ProcureAI/procureai/frontend/src/components/ProcedureDAGViewer.jsx) | **Interactive SOP Execution Stepper**. | Renders corporate Standard Operating Procedures as sequential checklists with `PRECEDES` connection badges and checkmark status. |
| [`frontend/src/components/CreateProviderModal.jsx`](file:///d:/sultan/ProcureAI/procureai/frontend/src/components/CreateProviderModal.jsx) | **3-Step Provider Provisioning Wizard**. | In-app modal matching Synapt Admin: Step 1 (Identity & Pack), Step 2 (Context Scope & Depth), Step 3 (Client ID & Token TTL). |

---

## 4. HOW Context Substrate is Used (Execution Workflows)

### Workflow 1: Contract Q&A & Semantic Verification
When an auditor asks a question about a contract (e.g., *"What is the revised bandwidth rate under Amendment 1?"*):

```
Auditor Question
      │
      ▼
1. Query Embed & Anchor Search ──► Queries Milvus GN to locate anchor nodes in Neo4j.
      │
      ▼
2. Multi-Hop BFS Traversal     ──► Neo4j walks 2 hops: discovers Amendment 1 supersedes Clause 4.1 ($1,200 -> $950).
      │
      ▼
3. Verbatim Chunk Fetch (KS)   ──► Milvus KS retrieves verbatim clause excerpt.
      │
      ▼
4. Pass Card Computation       ──► 5-Stage scorecard generated:
                                   • Knowledge Store: 92/100
                                   • Context Graph: 96/100
                                   • Hallucination Risk: 4%
      │
      ▼
5. Frontend Presentation       ──► Answer displayed in ContractQADrawer with:
                                   • [View Subgraph] button (opens SVG visual graph)
                                   • [5-Stage Pass Card] widget showing green verification
```

---

### Workflow 2: Invoice Discrepancy & Amendment Resolution
During an automated invoice compliance audit:

1. **Ingest Invoice Line Item:** Invoice charges `$1,200.00` for a 100Mbps dedicated DIA circuit.
2. **Context Substrate Lookup:** ProcureAI queries `context_substrate_client.resolve_amendment_hierarchy("doc_msa", "Section 4.1")`.
3. **Graph Traversal:** The client follows `SUPERSEDES` relationships:
   $$\text{Section 4.1 (\$1,200)} \xleftarrow{\textbf{SUPERSEDES}} \text{Amendment 1, Section 2 (\$950)}$$
4. **Governed Extraction:** Context Substrate confirms the legally governing rate is **$950.00**, effective June 1, 2024.
5. **Deterministic Python Math:** `rule_engine.py` subtracts:
   $$\text{Overcharge} = \$1,200.00 - \$950.00 = \$250.00$$
6. **Reasoning Subgraph Generation:** A localized subgraph is constructed connecting `Invoice Line Item` $\rightarrow$ `Circuit 448` $\rightarrow$ `Amendment 1 Rule` $\rightarrow$ `Old Section 4.1`.
7. **Auditor Verification:** In the UI finding card, the auditor clicks **"View Reasoning Subgraph"** to inspect visual proof of the overcharge before notifying the vendor.

---

### Workflow 3: Dispute Notice Generation with SOP DAG Execution
When an audit finding is approved for dispute recovery:

1. **Intent Matching:** `dispute_generator.py` queries `context_substrate_client.get_procedure_dag("dispute_recovery")`.
2. **Milvus PS Retrieval:** Retrieves the corporate Standard Operating Procedure **"Enterprise Overcharge Recovery Playbook"**.
3. **Sequential Step Resolution:** Returns ordered steps with `PRECEDES` relationships:
   * **Step 1:** Flag Discrepancy & Calculate Material Leakage
   * **Step 2:** Isolate Contract Grounding & Governing Amendment
   * **Step 3:** Issue Formal Dispute Notice with 14-Day Cure Period
   * **Step 4:** Remit Undisputed Balance & Withhold Disputed Delta
   * **Step 5:** Log Vendor Credit Memo or Escalate to Procurement Legal
4. **Dispute Letter Modal:** In ProcureAI, clicking **"Draft Dispute Letter"** embeds this interactive checklist, ensuring accounts payable complies with legal withholding protocol.

---

### Workflow 4: Enterprise Administration & S2S Connectivity
In the **Settings** $\rightarrow$ **Context Substrate** tab:

1. **System Health Probe:** On page load, `getContextSubstrateStatus()` probes the live connection. If authenticated, displays `CONNECTED (LIVE)`; if offline, automatically activates `ACTIVE (EMBEDDED)`.
2. **Interactive Diagnostics:** Clicking **"Run Diagnostic Query"** triggers a live multi-hop query, rendering the 5-stage Pass Card and interactive graph.
3. **Provider Provisioning:** Clicking **"+ Create Provider"** opens the 3-step provisioning modal to create isolated knowledge namespaces.
4. **CLI Diagnostics:** Developers can run `query.py` directly from the terminal to query live contracts through the Trident MCP protocol.

---

## 5. Environment Configuration Reference

The following settings in `backend/.env` control Context Substrate:

```env
# =====================================================================
# SynaptAI Context Substrate (Trident MCP & 4-Store TriStore)
# =====================================================================
CONTEXT_SUBSTRATE_ENABLED=true
CONTEXT_SUBSTRATE_MODE=live                  # live | auto | mock
CONTEXT_SUBSTRATE_URL=https://beta.synapt.ai # TriStore REST API base URL
CONTEXT_SUBSTRATE_PROVIDER_ID=procureai      # Active Context Provider namespace
CONTEXT_SUBSTRATE_API_KEY=eyJ...             # Bearer authentication token

# =====================================================================
# Trident MCP Settings (Official Prodapt IPL Reference SDK)
# =====================================================================
SYNAPT_MCP_URL=https://beta.synapt.ai/api/mcp
SYNAPT_PROVIDER_ID=procureai
SYNAPT_AGENT_CLIENT_ID=20e0ce925bad15e51a4713630637befbc4f6bedeb639e244af92efb92c131004
SYNAPT_AGENT_CLIENT_SECRET=
SYNAPT_AGENT_TOKEN=eyJ...
SYNAPT_VERIFY_SSL=false                      # Bypass TLS inspection on internal domains
```

---

## 6. Verification & Automated Testing

The entire integration is continuously validated via automated tests in `tests/test_context_substrate.py`:

```bash
# Run all Context Substrate integration tests
.venv\Scripts\pytest tests/test_context_substrate.py -v
```

### Covered Test Cases:
1. `test_client_status`: Validates connectivity, node counts, and store health.
2. `test_tristore_query_resolution`: Validates semantic query anchoring, grounded generation, and pass cards.
3. `test_procedure_dag_retrieval`: Validates Milvus PS retrieval and `PRECEDES` step sequencing.
4. `test_amendment_supersession`: Validates `SUPERSEDES` edge traversal and latest rate resolution.
5. `test_discrepancy_subgraph_generation`: Validates dynamic subgraph creation for invoice audit findings.
6. `test_api_status_endpoint`: Validates REST `/api/context-substrate/status`.
7. `test_api_query_endpoint`: Validates REST `/api/context-substrate/query`.
8. `test_api_providers_crud`: Validates 3-step provider provisioning, listing, and deletion.

---

## 7. Key Architectural Invariants

* **Zero-Math Invariant:** LLMs and knowledge graphs **never perform arithmetic**. All financial calculations occur in Python using `Decimal` precision in `rule_engine.py`.
* **Zero-Fail Invariant:** If live remote connections are unreachable, `CONTEXT_SUBSTRATE_MODE=auto` seamlessly falls back to the embedded 4-store engine, ensuring zero downtime during demos or offline environments.
* **Explainability Invariant:** Every audit finding must be backed by a **Reasoning Subgraph** and a **5-Stage Retrieval Pass Card**, providing CFOs with indisputable mathematical and contractual evidence.

# Prodapt SynaptAI: Context Substrate Comprehensive Guide

> **A plain-English, deep-dive reference manual explaining what Context Substrate is, how its 4-store architecture operates, and how it powers ProcureAI as the governed Enterprise Knowledge Brain.**

---

## 1. Executive Summary: What is Context Substrate?

**SynaptAI Context Substrate** is an **Enterprise Knowledge Brain**. It converts unstructured documents (contracts, amendments, invoices, standard operating procedures, and technical specifications) into a **structured, queryable knowledge graph paired with vector stores**.

### The Core Problem: Why Traditional AI (ChatGPT / Basic RAG) Fails on Contracts

Traditional Large Language Models (LLMs) and standard Retrieval-Augmented Generation (RAG) treat documents as flat text:
1. They chop a 60-page PDF into small arbitrary squares ("chunks") of 500 tokens each.
2. When a user asks a question, the vector database retrieves 3 to 5 chunks that look mathematically similar to the query.
3. The LLM tries to guess an answer based only on those disjointed chunks.

**Why this breaks down in real enterprise contracts:**
* **The Amendment Trap:** In enterprise procurement, contracts are constantly modified by Amendments, Statements of Work (SOWs), and Addendums. 
  * *Clause 4.1 in 2022* specifies a circuit rate of **$1,200/month**.
  * *Amendment 1 in 2024* states: *"Section 4.1 is hereby superseded; the revised rate is $950/month."*
  * A traditional RAG system retrieves **both** chunks, cannot understand temporal legal hierarchy, and either hallucinates or cites the wrong rate.
* **Lack of Procedural Awareness:** Standard AI has no concept of sequence (e.g., *"Step 1 must be completed before Step 2"*).

### How Context Substrate Solves This
Instead of a flat pile of text chunks, Context Substrate builds a **connected web (Knowledge Graph)** where entities, rules, and documents have explicit semantic relationships:
* `Amendment 1` $\xrightarrow{\textbf{SUPERSEDES}}$ `Section 4.1`
* `Invoice Line Item` $\xrightarrow{\textbf{BILLED ON}}$ `Rate Card Item`
* `Contract Rule` $\xrightarrow{\textbf{GOVERNED BY}}$ `Master Services Agreement`
* `Dispute Notice` $\xrightarrow{\textbf{PRECEDES}}$ `Payment Withholding`

When querying Context Substrate, it doesn't just read words—it **walks the graph path** to find the ground truth.

---

## 2. The 4-Store Architecture

Context Substrate does not rely on a single database. It orchestrates **four specialized stores** working in synchrony:

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

| Store | Technology | What it Contains | Role in System |
| :--- | :--- | :--- | :--- |
| **1. Concept Graph** | **Neo4j** | Entities, concepts, legal rules, propositions, and multi-hop relationships. | **The Skeleton**: Stores the structural connections, legal hierarchies, and amendment overrides. |
| **2. Knowledge Store (KS)** | **Milvus** | Embedded document text chunks with source metadata and heading context. | **The Flesh**: Raw source material indexed by meaning for semantic passage retrieval. |
| **3. Procedural Store (PS)** | **Milvus** | Embedded Standard Operating Procedures (SOPs) and corporate recovery workflows. | **The Playbooks**: Enables finding how-to procedures and escalation flows by describing intent. |
| **4. Graph Node Index (GN)**| **Milvus** | Embedded semantic signatures of all graph nodes linked directly to Neo4j IDs. | **The GPS**: Bridges semantic text search directly to graph anchor entry points without fuzzy text matching. |

---

## 3. Core Concepts & Terminology

### A. What is a "Context Provider"?
A **Context Provider** is an **isolated knowledge namespace (a private database/sandbox)**.
* In multi-tenant enterprise environments, you never want Vendor A's contracts mixing with Vendor B's data.
* Each Provider receives its own isolated Neo4j subgraph and its own Milvus collections.
* In ProcureAI, our provider is named `ProcureAI-Enterprise`.

### B. Semantic Resolution & Entity Deduplication
When documents are ingested, the system automatically checks if a newly extracted entity already exists in the graph:
* If the embedding similarity of an entity $\ge 0.85$, it **merges** into the existing node rather than duplicating.
* If a concept definition similarity $\ge 0.82$, it merges as an alias.
* Example: *"BT Group"*, *"British Telecom"*, and *"BT"* resolve to a single unified graph node.

### C. Extraction Modes & Density
Controls how thoroughly the AI extractor processes each document chunk:
* `fast`: Captures only the most salient entities (minimal tokens, fastest speed).
* `balanced` *(Default)*: Recommended for most contracts; captures rules, parties, and commercial terms.
* `deep`: Multi-pass thorough reasoning for complex, dense 100+ page contracts.
* `fact_dense`: Optimized for factual triples (subject, predicate, object).

### D. The Edge (Relationship) Vocabulary
Context Substrate uses a standardized semantic taxonomy. Key relationship types for contract compliance:
* `SUPERSEDES`: A later amendment replaces an older clause.
* `GOVERNED_BY`: A schedule or SOW is legally bound by a Master Services Agreement.
* `BILLED_ON`: An invoice line item references a specific rate card rule.
* `PRECEDES`: In an SOP, Step A must be completed before Step B can begin.
* `HAS_STEP`: A corporate procedure contains this specific operational step.
* `DEFINES`: A contract chunk defines a legal concept (e.g., Monthly Recurring Charge).

---

## 4. Document Ingestion: The 5-Stage Factory Line

When you upload a contract PDF or Markdown file via the **Data Ingestion** tab, it flows through a 5-microservice pipeline:

```
[Upload Document]
       │
       ▼
1. synapt0001 (Ingestion)      ──► Accepts the raw file, registers a tracking Job ID, and emits to Kafka.
       │
       ▼
2. synapt0002 (Normalize)      ──► Detects format, extracts tables cleanly, strips PDF artifacts into Markdown.
       │
       ▼
3. synapt0003 (Chunk)          ──► Slices Markdown into logical chunks respecting clause headings and token limits.
       │
       ▼
4. synapt0004 (Knowledge)      ──► AI reads each chunk: extracts entities, rules, relationships, and dedupes them.
       │
       ▼
5. synapt0005 (Store)          ──► Persists: graph nodes/edges to Neo4j, chunks to Milvus KS, procedures to Milvus PS.
       │
       ▼
[Job Complete — Queryable Brain Active]
```

---

## 5. How Context Substrate Answers Questions

When an auditor or agent queries Context Substrate, it executes a governed multi-stage process:

```
User Query: "What is the revised DIA port rate under Amendment 1?"
     │
     ▼
[Step 1: Embed Query]         ──► Vector representation generated using embedding model.
     │
     ▼
[Step 2: Search GN (GPS)]     ──► Milvus GN identifies semantic anchor nodes directly in Neo4j.
     │
     ▼
[Step 3: BFS Graph Traversal] ──► Neo4j expands 2 hops from anchors, discovering:
                                  Section 4.1 ($1,200) <──[SUPERSEDES]── Amendment 1 ($950).
     │
     ▼
[Step 4: Milvus KS Search]    ──► Retrieves verbatim text chunks of Amendment 1.
     │
     ▼
[Step 5: Milvus PS Search]    ──► Checks if query relates to an SOP (dispute or decommission).
     │
     ▼
[Step 6: Grounded Generation] ──► Generates answer citing exact graph paths and clause chunks.
     │
     ▼
[Output: Answer + Reasoning Subgraph + 5-Stage Retrieval Pass Card]
```

---

## 6. The Explainability Layer: Trust & Auditing

Enterprise CFOs and legal teams cannot act on a "black-box" recommendation. Context Substrate provides two audit artifacts for every response:

### A. The Reasoning Subgraph
A visual force-directed diagram showing:
* **The Traversed Path:** The exact nodes (Entities, Clauses, Documents) and edges (`SUPERSEDES`, `BILLED_ON`) used to answer the question.
* **Semantic Anchors:** Glowing indicators highlighting where the search entered the graph.
* **Node Inspector:** Auditors can click any node to inspect its verbatim text and custom properties.

### B. The 5-Stage Retrieval Pass Card
Every query receives a 0–100 scorecard evaluating the five stages of the retrieval engine:
1. **Knowledge Store (Milvus KS):** Chunk similarity, text coverage, and source diversity.
2. **Context Graph (Neo4j):** Entity match confidence and graph relevance.
3. **Procedure Store (Milvus PS):** SOP match score and policy alignment.
4. **Fusion Layer:** Cross-store consensus and agreement score.
5. **Generation:** Groundedness score, citation coverage, and **Hallucination Probability %**.

*Score bands:*
* `70–100`: **Green (High Grounding / Low Risk)**
* `40–70`: **Orange (Moderate Confidence / Inferred)**
* `0–40`: **Red (Low Grounding / High Risk)**

---

## 7. How ProcureAI Integrates with Context Substrate

ProcureAI pairs its **deterministic compliance engine** with Context Substrate's **epistemic brain**:

```
                  ┌───────────────────────────────────────────┐
                  │        ProcureAI Dual-Brain Engine        │
                  └─────────────────────┬─────────────────────┘
                                        │
           ┌────────────────────────────┴────────────────────────────┐
           ▼                                                         ▼
┌──────────────────────────────┐                         ┌──────────────────────────────┐
│ Deterministic Math Engine    │                         │  SynaptAI Context Substrate  │
│ (rule_engine.py - Python)    │                         │  (Epistemic Knowledge Brain) │
│ - Pure Decimal arithmetic    │                         │ - Neo4j Concept Graph        │
│ - Rate bracket math          │                         │ - Amendment supersession     │
│ - Overcharge calculation     │                         │ - Corporate dispute SOP DAGs │
│ - Zero-math LLM rule         │                         │ - Clause graph provenance    │
└──────────────┬───────────────┘                         └──────────────┬───────────────┘
               │                                                         │
               └────────────────────────────┬────────────────────────────┘
                                            ▼
                  ┌───────────────────────────────────────────┐
                  │    Enterprise Grounded Audit & Recovery   │
                  │  1. Unambiguous Clause Grounding          │
                  │  2. Visual Reasoning Subgraph Inspection  │
                  │  3. 5-Stage Retrieval Pass Card Proof     │
                  │  4. Dispute Notice with SOP DAG Execution │
                  └───────────────────────────────────────────┘
```

1. **Zero-Math Invariant:** In strict compliance with project architecture, Context Substrate **never computes financial math**. All addition, subtraction, rate conversions, and leakage calculations occur deterministically in Python using `Decimal` precision.
2. **Amendment Resolution:** When an invoice line item is audited, Context Substrate checks for active `SUPERSEDES` edges so the audit engine always evaluates against the latest governing rate.
3. **Dispute Playbooks (SOP as DAG):** When ProcureAI flags an overcharge, it fetches the corporate dispute recovery SOP from Milvus PS. The Dispute Letter Modal displays an interactive **Workflow Progress DAG** with sequential steps (`PRECEDES`).

---

## 8. Quick-Reference Glossary

| Term | Meaning in SynaptAI | Role in ProcureAI |
| :--- | :--- | :--- |
| **Context Provider** | An isolated knowledge base with its own graph and vector collections. | Identifies our audit sandbox (`ProcureAI-Enterprise`). |
| **Neo4j** | Graph database storing structural nodes and relationships. | Resolves clause hierarchies and amendment supersessions. |
| **Milvus KS** | Vector store of embedded text passages. | Provides verbatim contract citations for audit reports. |
| **Milvus PS** | Vector store of standard operating procedures. | Supplies dispute recovery SOPs for vendor remediation. |
| **Milvus GN** | Vector index of node signatures with direct Neo4j IDs. | Enables instant semantic jumps into the graph. |
| **SUPERSEDES** | An edge indicating that a newer rule or document overrides an older one. | Prevents billing against outdated baseline contract terms. |
| **SOP as DAG** | Standard Operating Procedure represented as a Directed Acyclic Graph. | Powers the step-by-step dispute recovery checklist. |
| **Reasoning Subgraph**| The exact slice of nodes and edges traversed to validate a finding. | Provides 1-click visual proof for auditors and CFOs. |
| **Retrieval Pass Card**| A 5-stage scorecard showing groundedness and hallucination risk. | Guarantees audit findings are backed by document evidence. |

---

## 9. Live Deployment & Verified Ingested Contracts

### A. Live Environment Details

ProcureAI is actively connected to Prodapt's live SynaptAI Context Substrate infrastructure:
* **Host URL:** `https://beta.synapt.ai`
* **Context Provider Namespace:** `procureai`
* **MCP Protocol Service:** `https://beta.synapt.ai/api/mcp`
* **Agent Integration SDK:** [`context_substrate/demo-agent-ipl/`](file:///d:/sultan/ProcureAI/procureai/context_substrate/demo-agent-ipl/)

### B. Live Ingested Enterprise Contracts

The live `procureai` knowledge substrate holds five enterprise contracts available for live semantic search and compliance validation:
1. **Cloud Infrastructure Master Agreement:** Master cloud hosting, dedicated DIA circuits, tiered compute rates, and SLA penalty credits.
2. **Master Services Agreement for Logistics & Transport Services (`MSA-2024-APX-001` & `MSA-2025-APX-002`):** Logistics dispatch, fuel surcharge formulas, demurrage allowances, and governing rate revisions.
3. **Professional Services Master Agreement (`MSA-2024-PSC-006`):** Time-and-materials rate cards, overtime billing caps, and milestone acceptance criteria.
4. **Software Services & Consulting Contract (`MSA-2024-TSS-002`):** Enterprise software licensing, tier-1 technical support commitments, and warranty terms.
5. **Construction Services Agreement:** Capital project milestones, retainage withholding percentages, and delay damages clauses.

### C. How to Test & Query

#### 1. Via the Web Interface
1. Navigate to `http://localhost:5173`.
2. Go to **Settings** $\rightarrow$ **Context Substrate** tab.
3. Observe the connection indicator:
   - When remote tokens are active: **`CONNECTED (LIVE)`**
   - When offline or during token renewal: **`ACTIVE (EMBEDDED)`** (seamless auto-fallback)
4. Click **Run Diagnostic Query** to see the 5-stage Pass Card and visual knowledge graph in action.

#### 2. Via the Official Trident MCP Agent CLI
From the project root:

```bash
# Query the live SynaptAI TriStore
.venv\Scripts\python context_substrate/demo-agent-ipl/query.py "What are the main enterprise contracts in this system?" --sources
```

#### 3. Automated Test Suite
Continuous validation is executed via Pytest:

```bash
.venv\Scripts\pytest tests/test_context_substrate.py -v
```
All 8 integration tests validate client status, TriStore queries, amendment supersession, SOP DAG retrieval, discrepancy subgraphs, and REST API controllers.


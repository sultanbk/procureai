# IPL Contest Brief

## Purpose

This document captures all known information about Prodapt's Innovation Premier League (IPL) and how SupplierGuard / ProcureAI should prepare to score well in the competition.

Update this file whenever new contest information is received from the IPL team, including scoring criteria, judging format, demo rules, timelines, required submissions, and available Synapt IP access.

---

## Executive Summary

SupplierGuard / ProcureAI should be positioned as a **governed multi-agent procurement assurance solution** for enterprise and telecom/TMT customers.

The contest submission should prove three things clearly:

1. **Customer value:** Supplier invoice leakage is a real, recurring enterprise problem.
2. **Synapt IP usage:** SupplierGuard is a strong fit for AgentHub, Context Substrate, and Data Transformation.
3. **Measurable impact:** The prototype can identify recoverable leakage, reduce manual audit effort, and create dispute-ready evidence.

The highest-scoring story:

> SupplierGuard turns static supplier contracts into live financial controls. It uses governed AI agents to audit invoices against contract terms, detect leakage, cite evidence, calculate recoverable value, and prepare human-approved dispute actions.

Important positioning rule:

> Be honest about integration status. If AgentHub or Context Substrate is not fully integrated, say "AgentHub-ready" or "Context Substrate-ready" rather than claiming completed integration.

---

## Contest Overview

**Competition name:** Innovation Premier League (IPL)  
**Organizer:** Prodapt  
**Registration opened:** July 29, 2026  
**League duration:** 6 weeks  
**Prototype submission deadline:** September 11, 2026  
**Grand Finale:** September 23, 2026, Wednesday, at Lakshya 2026

IPL is a global internal innovation competition where Prodaptians build, implement, and showcase solutions for real business challenges. The goal is not only to create prototypes, but to identify solutions that could become larger innovations supporting customer success.

---

## Evaluation And Submission Requirements

The competition rewards solutions that demonstrate:

- A meaningful real-world business problem
- A working implementation, not only slides
- Clear customer or enterprise value
- Use of Prodapt IP where relevant
- Strong demo storytelling
- Potential to become reusable IP or customer-facing capability
- Responsible and governable use of AI agents

Official scoring weights:

| Criteria | Weightage | What To Evaluate |
| --- | ---: | --- |
| Customer Environment Potential | 20% | Potential and readiness for deployment/adoption in a customer environment |
| IP Usage | 20% | Use of selected Prodapt IP/Accelerator. IP usage is a qualifier; additional IP usage can be an advantage where relevant |
| Quantifiable Business Impact | 20% | Clearly defined KPI with measurable before/after or expected quantitative business/customer impact |
| Innovativeness / Differentiation | 15% | Originality and creativity of the solution and how effectively the IP is applied |
| Scalability / Reusability | 15% | Ability to scale/reuse across customers, Telco/TMT use cases, and potentially beyond TMT |
| Complexity of Business Problem | 10% | Complexity, relevance, and significance of the business problem being addressed |

Each parameter is scored directly out of its own weight. For example, a strong answer in a 20-point category should land around 16/20 or higher.

Required submission:

- 5-slide presentation
- 3-minute demo video

For SupplierGuard / ProcureAI, the strongest contest narrative is:

> SupplierGuard turns supplier contracts into live financial controls. It uses governed AI agents to audit invoices against contract terms, detect leakage, cite evidence, calculate recoverable value, and prepare human-approved dispute actions.

Submission priority:

1. Build a clear 5-slide story around the scoring criteria.
2. Record a crisp 3-minute demo video showing the working product.
3. Include visible Synapt IP alignment without overclaiming.
4. Quantify business impact using demo numbers and annualized potential.
5. Keep the demo stable; do not risk the core flow for last-minute integrations.

---

## Source Notes

This brief currently uses:

- IPL contest announcement and Synapt suite overview shared by the team
- Agent Hub workshop transcript shared by the team
- Agent Hub catalog list shared by the team
- Context Substrate wiki summary shared by the team
- `AgentHub_User_Guide_v1.0.pdf`, Version 1.0, July 2026, Draft for Review

The AgentHub guide is reference material for understanding the platform. Any action for SupplierGuard should still be based on the user's explicit request and the access actually provided by the IPL/Synapt teams.

---

## Relevant Synapt IP Suites

### Synapt Context Substrate

**Applicability:** High

SupplierGuard needs enterprise context across contracts, supplier history, SLA records, dispute history, procurement policies, and SOPs. Invoice and payment records can remain in transactional systems, while Context Substrate provides the knowledge and reasoning layer around them.

Potential use:

- Contract clause knowledge graph
- Supplier and invoice context retrieval
- Historical dispute outcome lookup
- Context grounding for audit agents

Updated understanding:

Synapt Context Substrate is best understood as a queryable enterprise knowledge brain. It combines graph reasoning and semantic search so agents can ask questions over complex enterprise documents and receive grounded, traceable answers.

It uses a four-store architecture:

| Store | Role |
| --- | --- |
| Neo4j Concept Graph | Stores entities, concepts, procedures, facts, and relationships |
| Milvus Knowledge Store | Stores raw document chunks for semantic search |
| Milvus Procedure Store | Stores SOPs and procedures for intent-based procedure retrieval |
| Milvus Graph Node Index | Stores embeddings for graph nodes and links vector hits directly to Neo4j node IDs |

For SupplierGuard, this means Context Substrate should be used for the knowledge side:

- Supplier contracts
- Master service agreements
- Pricing schedules
- SLA clauses
- Procurement policies
- SOPs for invoice disputes
- Vendor onboarding documents
- Historical dispute playbooks or resolution notes

It should not be positioned as the primary store for high-volume transactional data such as every ERP invoice row, order record, payment event, or inventory movement. Those should remain in transactional systems or analytical databases, with Context Substrate used to provide governed knowledge and reasoning context around them.

Recommended positioning:

> Context Substrate gives SupplierGuard a traceable contract and policy brain. ERP and invoice systems provide live transactional facts; Context Substrate provides the clause, policy, supplier, and procedure knowledge needed to reason over those facts.

Important technical ideas from the workshop/wiki:

- Documents are ingested, normalized to Markdown, chunked, extracted, and stored across graph and vector stores.
- Extraction can identify entities, concepts, relationships, and propositions from each chunk.
- Semantic resolution merges similar entities or concepts instead of creating duplicates.
- Querying combines semantic search with graph traversal, rather than simple top-k chunk retrieval.
- Answers can include a reasoning subgraph, showing which nodes and relationships supported the answer.
- Context Providers can isolate knowledge bases, such as by supplier category, business unit, or customer.

SupplierGuard features that would benefit most:

| SupplierGuard Capability | Context Substrate Value |
| --- | --- |
| Contract Q&A | Strong fit: grounded answers with clause traceability |
| Contract parser | Strong fit: graph-backed entity, clause, and relationship extraction |
| Cross-reference resolution | Strong fit: graph traversal can connect clauses, schedules, amendments, and referenced terms |
| Compliance checker | Medium to high fit: retrieve governing clauses and related policies before deterministic calculation |
| Reverse sweep | Medium fit: discover credits, discounts, and penalty obligations that may not appear on invoices |
| Dispute letter generation | Medium fit: retrieve supporting clause evidence and SOP language |
| Supplier scorecard | Medium fit: connect supplier, contract, SLA, and dispute context |
| Raw invoice arithmetic | Low fit: should remain deterministic Python/transactional logic |
| High-volume invoice history | Low fit as primary storage: better handled by DB/analytics layer |

### Synapt Agent Hub

**Applicability:** Very High

SupplierGuard is already structured as a multi-agent system. Agent Hub can provide the lifecycle layer for defining, governing, versioning, testing, deploying, observing, and changing agents.

Potential use:

- Agent manifests for each SupplierGuard agent
- Version history for prompts, tools, and agent definitions
- Human-in-loop controls for dispute approval
- Confidence, KPI, and telemetry tracking
- Governed reuse of catalog agents

Recommended positioning:

> SupplierGuard is Agent Hub-ready: each agent has a clear role, typed inputs and outputs, confidence signals, measurable KPIs, and human approval boundaries.

Updated understanding:

AgentHub is the lifecycle and governance control plane for enterprise agents. It separates the agent definition from the runtime where the agent executes. The central idea is that agents should be managed as versioned, reviewable, portable definitions rather than ungoverned running processes.

Official phrasing from the guide:

> AgentHub is a design and governance plane for enterprise-scale AI agents.

It is deliberately not an orchestration engine or runtime. This matters for SupplierGuard because our existing FastAPI/LangGraph backend can remain the execution layer, while AgentHub can represent the governed definition, versioning, test evidence, deployment package, and observability story.

Core principle:

> Define once, deploy anywhere.

In SupplierGuard terms:

> Define each procurement-audit agent once as a manifest, then make it portable across supported platforms while preserving governance metadata.

Core AgentHub capabilities:

| Capability | What It Means | SupplierGuard Relevance |
| --- | --- | --- |
| Agents Catalog | Searchable library of existing agents across domains | Discover reusable agents before building new SupplierGuard agents |
| Create Agent | Define a new agent using a guided form or YAML manifest import | Create SupplierGuard-specific agent definitions |
| Update Agent | Every edit creates a new version that goes through review and approval | Version prompts, tools, autonomy limits, KPIs, and behavior changes |
| Agent Manifest | Platform-agnostic YAML definition of identity, capabilities, tools, autonomy, governance, and KPIs | Represent Contract Parser, Invoice Extractor, Compliance Checker, etc. as governed assets |
| Agent Builder | Converts manifests into platform-specific packages through adapters | Potential future packaging for SynaptAO or other supported platforms |
| Agent Tester | Runs test cases against an agent version and captures actual vs expected results | Map SupplierGuard golden test cases to AgentHub test evidence |
| Agent Deployer | Deploys built packages to supported runtimes such as SynaptAO | Useful if we receive runtime access and deployment guidance |
| Solutions | BPMN workflows combining agents, systems, and human actors | Model end-to-end contract audit and dispute workflow |
| Governance Lifecycle | Reviewer and Approver roles with audit trail | Strong fit for human-in-loop dispute approval |
| Observability | Runtime telemetry compared against declared KPIs | Track extraction accuracy, confidence, latency, cost, and false positives |
| Audit Log | Platform-wide record of who changed what and when | Helps prove governed AI and responsible lifecycle management |

Important AgentHub principle:

> Nothing is edited in place. Every change creates a new version, and the previous version remains in history.

This is especially important for SupplierGuard because small changes in prompts, clause extraction, or rule mapping could affect financial findings. AgentHub gives a strong answer to the question: "How do you govern AI agents that influence money-related decisions?"

Recommended SupplierGuard AgentHub usage path:

1. Get access to the AgentHub project profile.
2. Search the catalog first for reusable agents.
3. Request porting of the most relevant catalog agents.
4. Create SupplierGuard-specific agents as YAML manifests.
5. Define KPIs and autonomy level for each agent.
6. Add test cases based on the existing SupplierGuard evaluation dataset.
7. Model the overall audit workflow as a Solution with human approval.
8. Use observability/audit log language in the IPL pitch, even if full deployment is not completed before demo day.

SupplierGuard-specific lifecycle mapping:

| AgentHub Lifecycle | SupplierGuard Example |
| --- | --- |
| Ideate | Define procurement leakage detection use case and agent responsibilities |
| Build | Create manifests for parser, extractor, validator, checker, recommender |
| Test | Run known contract/invoice golden cases with expected leakage outputs |
| Deploy | Deploy or demonstrate runtime alignment, depending on available access |
| Observe | Track precision, recall, confidence, latency, token cost, human overrides |
| Change | Update agent versions when tests fail or new clause types are added |

Suggested SupplierGuard agents to create in AgentHub:

| SupplierGuard Agent | Purpose | Autonomy Recommendation |
| --- | --- | --- |
| Contract Parser Agent | Extract pricing, SLA, discount, cap, and penalty rules from contracts | Medium: extracts and proposes structured rules |
| Invoice Extractor Agent | Extract invoice metadata and line items | Medium: extracts structured data |
| Cross Validator Agent | Maps invoice lines to contract rules and validates units/data needs | Low to medium: flags candidates and uncertainty |
| Compliance Checker Agent | Calculates expected vs charged amount using deterministic rules | Medium: creates findings only when evidence is sufficient |
| Reverse Sweep Agent | Detects missed credits, discounts, and penalties | Medium: recommends review of missed entitlements |
| Cross-Invoice Analyzer Agent | Detects repeated leakage and price drift | Medium: identifies patterns |
| Report Generator Agent | Produces audit summary and dispute-ready evidence | Low to medium: drafts outputs |
| Dispute Recommendation Agent | Recommends dispute, escalate, monitor, or human review | Low: recommends only |
| Human Approval Step | Procurement/AP/legal approval before supplier-facing dispute | Human-controlled |

Recommended governance message:

> SupplierGuard automates detection, evidence assembly, calculation, and recommendation. It does not autonomously send supplier disputes. Supplier-facing action is bound to a human approval step, making the workflow auditable and enterprise-safe.

AgentHub access notes:

- Sign in using onboarded credentials at the organization's provisioned AgentHub URL.
- New users require approval before access is active.
- Navigation depends on assigned role and permissions.
- Standard roles include Admin, Sales, User, Developer, Reviewer, and Approver.
- Reviewer and Approver separation is enforced through permissions.
- Support is available through AgentBot, Quick Tour, Wiki, and Contact Us.

### Official AgentHub Availability Notes

Use these to avoid overcommitting during IPL planning.

| Area | Available Now | Partial / Roadmap Notes |
| --- | --- | --- |
| Agents Catalog | Available now with 250+ definitions | Roadmap filters include rating, views, version, autonomy level |
| Create Agent | Available now via form, YAML manifest import, ServiceNow XML import | More import adapters are roadmap |
| Update Agent | Available now with versioned review and approval | No in-place mutation |
| Agent Manifest | Available now as YAML | Manifest is versioned with the agent |
| Agent Builder | Available for supported platforms such as SynaptAO and ServiceNow | Salesforce, Snowflake, GCP, AWS, Azure are roadmap |
| Agent Tester | Available/partially available depending on feature depth | Additional tester capabilities are roadmap |
| Agent Deployer | Docker deployment to SynaptAO available for supported platforms | More deployment targets are roadmap |
| Agent Connectors | Roadmap | Planned for LangChain/LangGraph, ServiceNow, Salesforce, Snowflake, GCP, AWS, Azure |
| Agent Manager | Roadmap | Dev/test/prod environment binding is roadmap |
| Solutions Catalog/Create/Update/Manifest | Available now | Useful for BPMN workflow design |
| Solutions Builder/Deployer/Manager | Roadmap | Workflow deployment is manual today |
| Governance Lifecycle | Available now | Reviewer and Approver roles with audit trail |
| Observability | Available/partially available | Currently focused on SynaptAO telemetry |
| Policy | Roadmap | Tiered model routing, token budgets, prompt caching |

### SupplierGuard Solution Manifest Idea

AgentHub Solutions can model end-to-end workflows using BPMN with agents, systems, and human personas. Each agent step can bind to a specific cataloged agent version.

For SupplierGuard, the Solution could be:

1. Contract uploaded by Procurement Analyst
2. Contract Parser Agent extracts rulebook
3. Invoice uploaded or received from AP system
4. Invoice Extractor Agent extracts line items
5. Cross Validator Agent maps invoice lines to contract clauses
6. Compliance Checker Agent calculates discrepancies
7. Reverse Sweep Agent checks missed credits, discounts, and penalties
8. Report Generator Agent produces audit summary
9. Human approver reviews supplier-facing dispute
10. Dispute communication is generated or sent through the approved workflow

Recommended pitch line:

> In AgentHub, SupplierGuard is not just a set of agents. It is a governed Solution: agents, systems, and human approval steps composed into a versioned audit workflow.

### Synapt Data Transformation

**Applicability:** Medium to High

SupplierGuard produces structured audit, leakage, compliance, and supplier performance data.

Potential use:

- Leakage analytics
- Supplier compliance dashboards
- Conversational BI for CFO/procurement users
- Historical trend analysis
- Predictive risk scoring

Recommended positioning:

> Data Transformation helps turn audit outputs into business intelligence: leakage trends, supplier risk, clause-level leakage patterns, and CFO-ready dashboards.

### Synapt Autonomous Operations

**Applicability:** Medium, depending on positioning

This is less directly aligned than Agent Hub or Context Substrate, but can be relevant if SupplierGuard is positioned for telecom procurement, supplier assurance, vendor operations, or B/OSS-adjacent financial governance.

Potential use:

- Telecom vendor invoice assurance
- Supplier performance governance for operations partners
- SLA and service-credit validation
- Operational dispute workflows

Recommended positioning:

> Autonomous Operations is relevant when SupplierGuard is applied to telecom/TMT supplier ecosystems, such as network vendors, managed service partners, field operations suppliers, construction partners, and service assurance credits.

---

## Agent Hub Applicability

The IPL team has asked teams to identify applicable Agent Hub catalog agents and reach out 1:1 for access. Teams can create their own agents and manage the full lifecycle:

- Ideate
- Build
- Test
- Deploy
- Observe
- Change

They also mentioned that existing catalog agents can be ported into project profiles if requested.

### Highest-Priority Agent Hub Agents For SupplierGuard

| Agent | Applicability |
| --- | --- |
| #23 RAG / Knowledge Agent | Contract clause retrieval, Contract Q&A, SOP lookup, cited evidence search |
| #92 Document Intelligence & Extraction Agent | Structured extraction from contracts, invoices, and procurement documents |
| #98 Invoice & PO Lifecycle Agent | Invoice validation, PO routing, payment tracking, AP workflow alignment |
| #61 Knowledge Summary and Next Best Action Agent | Audit summaries and recommendations such as dispute, escalate, or monitor |
| #103 Recommendation Agent | Dispute strategy, credit-note guidance, and remediation recommendations |
| #62 Audit and SLA Governance Agent | SLA tracking, compliance scoring, audit trails, reporting readiness |

### Secondary Useful Agents

| Agent | Applicability |
| --- | --- |
| #9 Case/Issue Summarizer | Stakeholder-ready summaries of audit findings |
| #6 Ticket Categorization Agent | Routing findings to AP, procurement, legal, or supplier management |
| #29 Ticket Hygiene and Communications Agent | Clean audit records and supplier-facing communications |
| #1 Correlation Agent | Repeated discrepancy detection across invoices and suppliers |
| #2 / #101 Impact Assessment Agent | Financial leakage impact and supplier-level blast radius |
| #96 KPI & Performance Reporting Agent | CFO dashboards and supplier performance reporting |
| #97 Communication & Notification Agent | Alerting stakeholders when leakage or disputes are found |
| #110 Quote Approver | Useful pattern for policy-based approval and human sign-off |

---

## Recommended Agent Hub Request

When reaching out 1:1, request access for the project and ask whether these agents can be ported:

1. #23 RAG / Knowledge Agent
2. #92 Document Intelligence & Extraction Agent
3. #98 Invoice & PO Lifecycle Agent
4. #61 Knowledge Summary and Next Best Action Agent
5. #62 Audit and SLA Governance Agent
6. #103 Recommendation Agent

Suggested message:

```text
Hi [Name],

We are building SupplierGuard / ProcureAI for IPL. It is a governed multi-agent procurement leakage detection platform that audits supplier invoices against contract terms.

We reviewed the Agent Hub catalog and found the following agents applicable to our use case:

- #23 RAG / Knowledge Agent
- #92 Document Intelligence & Extraction Agent
- #98 Invoice & PO Lifecycle Agent
- #61 Knowledge Summary and Next Best Action Agent
- #62 Audit and SLA Governance Agent
- #103 Recommendation Agent

We would like AgentHub access for our project profile so we can create our own SupplierGuard agents and manage the lifecycle: ideate, build, test, deploy, observe, and change.

We would also like guidance on whether the above existing catalog agents can be ported to our profile.

Thanks.
```

---

## SupplierGuard Contest Positioning

### One-Line Pitch

SupplierGuard is a governed multi-agent platform that detects supplier invoice leakage by auditing invoices against contract terms with clause-level evidence, deterministic financial calculations, and human-approved dispute workflows.

### Stronger IPL Version

SupplierGuard extends Synapt-style agentic operations into financial assurance. It turns contracts, invoices, supplier history, and SLA records into a live control layer that prevents procurement leakage before money leaves the enterprise.

### Why This Can Score Well

- Real business problem with measurable financial impact
- Working product demo with contract and invoice PDFs
- Multi-agent architecture already implemented
- Deterministic math layer reduces hallucination risk
- Human-in-loop governance aligns with Agent Hub principles
- Clear fit with Context Substrate, Agent Hub, and Data Transformation
- Extensible to telecom vendor assurance and enterprise procurement

### What Not To Overclaim

- Do not claim full AgentHub runtime deployment unless it is completed.
- Do not claim Context Substrate ingestion/query integration unless it is completed.
- Do not claim autonomous dispute sending; keep supplier-facing action human-approved.
- Do not claim ERP-scale transactional storage inside Context Substrate.
- Do not claim legal interpretation; position the system as evidence-backed audit assistance.

Safe wording:

- AgentHub-ready
- Context Substrate-ready
- Designed to use Synapt IP
- Candidate for AgentHub manifests and Solution workflow
- Prototype demonstrates the end-to-end business value

---

## Current Demo Strengths

- Contract PDF upload
- Invoice PDF upload
- Multi-agent audit pipeline
- Contract rule extraction
- Invoice line-item extraction
- Cross-validation between contract and invoice
- Deterministic discrepancy calculations
- Reverse sweep for missed credits and discounts
- Cross-invoice drift detection
- Supplier scorecards
- Analytics dashboards
- Contract Q&A
- Dispute letter generation

---

## Known Contest Information To Add Later

Use this section as a checklist when new details arrive from the IPL team.

### Scoring Criteria

Status: Known

| Criteria | Weightage | What To Evaluate |
| --- | ---: | --- |
| Customer Environment Potential | 20% | Potential and readiness for deployment/adoption in a customer environment |
| IP Usage | 20% | Use of selected Prodapt IP/Accelerator. IP usage is a qualifier; additional IP usage can be an advantage where relevant |
| Quantifiable Business Impact | 20% | Clearly defined KPI with measurable before/after or expected quantitative business/customer impact |
| Innovativeness / Differentiation | 15% | Originality and creativity of the solution and how effectively the IP is applied |
| Scalability / Reusability | 15% | Ability to scale/reuse across customers, Telco/TMT use cases, and potentially beyond TMT |
| Complexity of Business Problem | 10% | Complexity, relevance, and significance of the business problem being addressed |

### Submission Format

Status: Partially Known

Add details when received:

- Required deck format: 5 slides
- Required demo video: 3 minutes
- Code repository requirements
- Architecture document requirements
- One-pager requirements
- Submission deadline: September 11, 2026
- File upload portal or email process

### Judging Panel

Status: Pending

Add details when received:

- Judges
- Business vs technical evaluation split
- Expected audience
- Q&A format
- Time limit

### Demo Rules

Status: Pending

Add details when received:

- Live demo allowed or not
- Internet access availability
- Use of mock data allowed or not
- Use of synthetic data allowed or not
- Time limit
- Backup video requirements

### Synapt IP Access

Status: Pending

Add details when received:

- AgentHub URL
- User/password access
- Available project profile
- Agents ported to profile
- Sandbox restrictions
- API/SDK documentation
- Demo credentials

### Important Dates

Status: Partially Known

| Date | Event |
| --- | --- |
| July 29, 2026 | Registration opened |
| September 11, 2026 | Prototype submissions close |
| September 23, 2026 | Grand Finale at Lakshya 2026 |

Add more:

- Registration deadline
- Intermediate review dates
- Prototype checkpoint
- Final deck deadline
- Demo rehearsal
- Final submission deadline

---

## Strategy To Score Higher

### 1. Lead With Business Impact

Judges should understand the money problem in the first 30 seconds:

> Enterprises negotiate strong supplier contracts, but AP teams pay invoices without checking every clause. SupplierGuard catches the leakage automatically.

### 2. Show A Working Product

Prioritize a stable, repeatable demo over risky new integrations.

Best demo path:

1. Upload contract
2. Upload invoices
3. Run audit
4. Show leakage found
5. Expand finding with clause evidence and math
6. Generate dispute letter
7. Show supplier scorecard or analytics

### 3. Use Synapt Language

Use words the IPL/Synapt teams are already using:

- Agent lifecycle
- Manifest
- Versioning
- Governance
- Human-in-loop
- Observability
- KPIs
- Confidence scoring
- Context grounding
- Reusable catalog agents

### 4. Be Honest About Integration Status

If Agent Hub is not fully integrated, do not claim it is.

Use:

> Agent Hub-ready

Avoid:

> Fully integrated with Agent Hub

### 5. Highlight Responsible Autonomy

SupplierGuard should not fully automate supplier disputes without review.

Recommended line:

> The system automates detection, evidence assembly, and recommendation. The consequential action, sending a supplier dispute, remains human-approved.

### 6. Make The Architecture Look Intentional

Important message:

> LLMs extract and map. Deterministic Python calculates. Humans approve consequential actions.

This is a strong answer to hallucination concerns.

---

## Submission Plan: 5 Slides

The deck must be concise. Each slide should map directly to the judging criteria and avoid getting lost in implementation detail.

Recommended deck principle:

> Every slide should visibly help win points. Do not create a pure architecture slide unless it directly explains trust, IP usage, scalability, or customer readiness.

### Slide 1: Problem And Customer Environment Potential

Title:

> SupplierGuard: Stop Silent Procurement Leakage

Content:

- Enterprises sign complex supplier contracts but AP teams pay invoices without checking every clause.
- Leakage occurs through wrong rates, missed volume discounts, unapplied SLA credits, cap breaches, and missed early payment discounts.
- Primary customer environments: telecom/TMT operators and large enterprises with recurring supplier/vendor invoices.
- Broader customer environments: manufacturers, utilities, healthcare networks, retail chains, SaaS buyers, logistics-heavy enterprises.
- Pain is cross-functional: procurement negotiates terms, AP pays invoices, finance sees spend but not contract compliance.

Judging criteria covered:

- Customer Environment Potential
- Complexity of Business Problem

### Slide 2: Solution And Demo Flow

Title:

> Governed Multi-Agent Invoice Audit

Content:

- Upload supplier contract and invoice PDFs.
- Agents extract contract rules and invoice line items.
- Deterministic rule engine calculates expected vs charged amounts.
- Findings include clause evidence, exact arithmetic, confidence, and recommendation.
- Human approves supplier-facing dispute letter.

Suggested visual:

Contract PDF + Invoice PDF -> Agent Audit Pipeline -> Leakage Findings -> Dispute Letter / Scorecard

Judging criteria covered:

- Innovativeness / Differentiation
- Complexity of Business Problem

### Slide 3: Prodapt IP Usage

Title:

> Built For Synapt IP: Context + Agent Governance

Content:

- **Context Substrate:** traceable contract, supplier, policy, and SOP knowledge brain.
- **Agent Hub:** manifest-ready agents with lifecycle, versioning, governance, testing, observability, and human-in-loop controls.
- **Data Transformation:** leakage analytics, supplier scorecards, trend dashboards, CFO reporting.
- **Autonomous Operations:** optional fit for telecom/TMT supplier assurance and SLA credit workflows.

AgentHub-ready agents:

- Contract Parser
- Invoice Extractor
- Cross Validator
- Compliance Checker
- Reverse Sweep
- Report Generator
- Dispute Recommendation

Judging criteria covered:

- IP Usage
- Scalability / Reusability

### Slide 4: Differentiation And Technical Trust

Title:

> Not A Chatbot: Evidence, Math, Governance

Content:

- LLMs extract and map; Python Decimal rule engine calculates.
- Cross-validator checks clause/line mapping before findings are produced.
- Reverse sweep finds credits suppliers forgot to apply.
- Cross-invoice analyzer detects slow price drift across months.
- Human-in-loop dispute approval prevents risky autonomous actions.
- Mock/eval harness enables repeatable testing.

Judging criteria covered:

- Innovativeness / Differentiation
- Scalability / Reusability
- Complexity of Business Problem

### Slide 5: Business Impact And Reusability

Title:

> Measurable Financial Recovery, Reusable Across Customers

Content:

- Demo can show recoverable leakage from sample invoices in under 3 minutes.
- Business metrics: leakage found, compliance score, supplier grade, dispute-ready amount, time saved per audit.
- Reusable across supplier categories: logistics, construction, SaaS, cloud, healthcare, raw materials, telecom vendors.
- Roadmap: AgentHub manifests, Context Substrate grounding, ERP/AP integrations, dispute lifecycle tracking.

Suggested quantitative KPIs:

- Manual audit time: 30-45 minutes per invoice
- Prototype audit time: minutes, depending on document size and LLM mode
- Coverage: from sample-based audit to every eligible invoice
- Output: recoverable leakage amount, compliance score, supplier grade, dispute-ready evidence

Judging criteria covered:

- Quantifiable Business Impact
- Customer Environment Potential
- Scalability / Reusability

---

## Submission Plan: 3-Minute Demo Video

The video should prioritize clarity and visible proof. Do not spend too much time on architecture in the video; the deck can carry architecture.

### 0:00-0:25 Problem Hook

Show:

- Contract PDF or Upload screen
- A visible invoice

Say:

> Large enterprises negotiate detailed supplier contracts, but invoices are usually paid without checking every clause. That creates silent leakage through wrong rates, missed discounts, and unapplied SLA credits.

### 0:25-0:50 Solution Setup

Show:

- SupplierGuard upload page
- Contract selected
- Invoice PDFs selected

Say:

> SupplierGuard audits invoices against contracts using a governed multi-agent pipeline. I upload the contract and invoices, then run the audit.

### 0:50-1:25 Agent Pipeline

Show:

- Audit running page
- Agent progress/logs

Say:

> The agents extract contract rules, extract invoice line items, cross-validate mappings, calculate discrepancies, run reverse sweep for missed credits, and generate an audit report. LLMs extract and map; deterministic Python calculates the money.

### 1:25-2:20 Findings And Evidence

Show:

- Audit report summary
- Expand one strong discrepancy
- Clause evidence and calculation

Say:

> Here is the result: total leakage identified, compliance score, and ranked findings. This line was charged at the wrong rate. SupplierGuard cites the exact contract clause, shows the expected charge, the billed charge, and the recoverable overcharge.

### 2:20-2:45 Action

Show:

- Generate dispute letter
- Supplier scorecard or analytics

Say:

> The output is actionable. It drafts a supplier dispute with evidence and gives procurement a supplier compliance score. A human approves the dispute before it is sent.

### 2:45-3:00 Close

Show:

- Analytics dashboard or final report

Say:

> SupplierGuard turns contracts into live financial controls. With Synapt Context Substrate and Agent Hub, this becomes a governed, reusable procurement assurance solution for enterprise customers.

### Demo Video Rules Of Thumb

- Show the product within the first 30 seconds.
- Use large browser zoom so findings are readable in the recording.
- Avoid switching between too many pages.
- Prefer one clean, successful audit flow over multiple partial flows.
- Mention Synapt IP in the narration, but do not spend the video inside theory.
- Keep a backup recording even if a live demo is later allowed.

### Suggested Recording Checklist

- Backend and frontend started before recording.
- Mock/demo mode confirmed if using deterministic data.
- Demo files ready in a visible folder.
- Browser zoom set for readability.
- Notifications, chat popups, and sensitive tabs closed.
- Final report already tested once before recording.
- Audio checked with a 10-second test recording.

---

## Scorecard Mapping For SupplierGuard

| Evaluation Parameter | What To Show |
| --- | --- |
| Customer Environment Potential | Large enterprises with recurring supplier invoices, especially telecom/vendor ecosystems |
| IP Usage | AgentHub-ready manifests, Context Substrate grounding, Data Transformation analytics |
| Quantifiable Business Impact | Leakage found, amount recoverable, audit time reduced, compliance score |
| Innovativeness / Differentiation | Reverse sweep, deterministic math, cross-invoice drift, governed human approval |
| Scalability / Reusability | Works across supplier categories and customer environments; reusable agent workflow |
| Complexity of Business Problem | Legal contracts, conditional pricing, SLA clauses, external data needs, AP/procurement gap |

---

## Point-Maximizing Strategy

Since 60% of the score comes from Customer Environment Potential, IP Usage, and Quantifiable Business Impact, the deck and demo should spend most of their time proving those three.

### Customer Environment Potential: 20 Points

What judges want:

- Can this be deployed in a real customer environment?
- Is the use case relevant to Prodapt customers?
- Is it operationally realistic?

How SupplierGuard should score strongly:

- Position first for telecom/TMT vendor assurance and enterprise procurement.
- Show that it fits real systems: contract repository, AP/ERP, supplier master, SLA/performance sources.
- Show human-in-loop approval for supplier-facing disputes.
- Mention production readiness path: authentication, PostgreSQL, object storage, ERP integrations, observability.

Best line:

> This can sit beside a customer's AP and contract systems as a procurement assurance layer, auditing invoices before payment or during recovery audits.

### IP Usage: 20 Points

What judges want:

- Meaningful use of Prodapt IP/Accelerator.
- IP should not feel name-dropped.
- Additional relevant IP usage can help.

How SupplierGuard should score strongly:

- Make Agent Hub the governance story.
- Make Context Substrate the contract/policy knowledge story.
- Make Data Transformation the analytics/BI story.
- If AgentHub access is available, create at least one SupplierGuard agent manifest or show catalog agent applicability.

Best line:

> SupplierGuard uses Synapt IP where each suite is strongest: Context Substrate for traceable knowledge, Agent Hub for governed agent lifecycle, and Data Transformation for leakage analytics.

### Quantifiable Business Impact: 20 Points

What judges want:

- Clear KPI.
- Before/after comparison.
- Numeric customer/business impact.

How SupplierGuard should score strongly:

- Define KPIs explicitly:
  - Leakage identified per audit
  - Audit time reduction
  - Number of invoices checked
  - Compliance score improvement
  - Dispute-ready recovery value
- Use demo numbers from synthetic dataset.
- Include an annualized scenario.

Example impact statement:

> Manual audit takes 30-45 minutes per invoice and covers only a small sample. SupplierGuard audits contract-backed invoices in minutes and produces dispute-ready leakage findings with exact clause evidence.

Impact formula to use in deck or narration:

```text
Annual recoverable leakage =
monthly supplier invoices audited
× average invoice value
× estimated leakage rate
× recoverability rate
× 12
```

Example wording:

> Even a small leakage rate becomes material at enterprise scale. SupplierGuard makes contract compliance measurable by reporting leakage found, recovery value, and supplier compliance score for every audit.

### Innovativeness / Differentiation: 15 Points

What judges want:

- What is original or meaningfully different?
- Is the IP applied creatively?

How SupplierGuard should score strongly:

- Emphasize that it is not a RAG chatbot.
- Highlight reverse sweep: contract-to-invoice missed entitlement detection.
- Highlight deterministic financial calculation.
- Highlight cross-invoice drift detection.
- Highlight governed human approval.

Best line:

> Most tools ask, "Does this invoice line match a clause?" SupplierGuard also asks, "What benefits did the contract promise that never appeared on the invoice?"

### Scalability / Reusability: 15 Points

What judges want:

- Can it scale across customers and industries?
- Can Prodapt reuse this as IP?
- Does it apply to Telco/TMT and beyond?

How SupplierGuard should score strongly:

- Show reusable agent workflow and rule types.
- Position as a horizontal procurement assurance layer.
- Mention Telco/TMT first, then beyond TMT.
- Show supplier categories: network vendors, field services, logistics, construction, cloud/SaaS, managed services.

Best line:

> The workflow is reusable because supplier contracts share recurring financial control patterns: rates, tiers, caps, credits, penalties, discounts, and amendments.

### Complexity of Business Problem: 10 Points

What judges want:

- Is the problem meaningful and non-trivial?
- Does it require more than a simple chatbot?

How SupplierGuard should score strongly:

- Explain the AP/procurement disconnect.
- Mention long contracts, conditional clauses, cross-references, ambiguous line items, and external data dependencies.
- Show that the system knows when not to make a finding.

Best line:

> The hard part is not reading a PDF. The hard part is converting legal terms into auditable financial controls without inventing unsupported findings.

---

## Recommended Slide Weighting By Score

Because the deck is limited to 5 slides, each slide should intentionally cover multiple scoring buckets.

| Slide | Main Score Buckets |
| --- | --- |
| Slide 1: Problem And Customer Environment | Customer Environment Potential, Complexity |
| Slide 2: Solution And Demo Flow | Complexity, Differentiation |
| Slide 3: Synapt IP Usage | IP Usage, Reusability |
| Slide 4: Differentiation And Trust | Differentiation, Customer Readiness |
| Slide 5: Business Impact And Scale | Quantifiable Impact, Scalability |

Do not bury the 20-point categories. The deck should visibly include:

- Customer fit
- Synapt IP usage
- Quantified impact

---

## Open Questions

- What is the exact submission upload process or portal?
- Is live AgentHub integration required or optional?
- Can an Agent Hub-ready design score if access arrives late?
- Are synthetic contracts and invoices acceptable for demo?
- Will the finale require live internet access?
- Is there a separate technical review before the finale?
- Are customer-facing use cases preferred over internal productivity tools?
- Is there any required template for the 5-slide presentation?
- Is source code review part of scoring, or only deck/video?
- Are teams allowed to include an appendix outside the 5 core slides?

---

## Update Log

| Date | Update |
| --- | --- |
| September 4, 2026 | Created initial IPL contest brief with known contest details, Synapt applicability, Agent Hub mapping, and scoring strategy placeholders. |
| September 4, 2026 | Added official scoring weights, 5-slide submission structure, 3-minute demo plan, AgentHub guide details, Context Substrate positioning, and point-maximizing strategy. |

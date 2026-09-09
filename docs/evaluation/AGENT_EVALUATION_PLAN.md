# Agent Evaluation Plan

Project: **ProcureAI**

---

## 1. Executive Summary

### 1.1 Purpose & Necessity
ProcureAI is an enterprise-grade agentic system designed to audit complex supplier contracts against billing invoices, detect financial leakage (overcharges, unapplied volume discounts, missing SLA penalty credits, price-creep drift), and generate formal dispute documentation. 

Because ProcureAI makes financial recommendations involving significant monetary value, traditional unit testing alone is fundamentally insufficient. Large Language Model (LLM) components introduce non-deterministic text parsing, fuzzy line matching, and semantic reasoning. Evaluating ProcureAI requires a dedicated **Agent Evaluation Framework** that continuously measures agent precision, financial calculation accuracy, trajectory correctness, and overall report reliability.

### 1.2 Problems Solved by the Evaluation Framework
1. **Eliminates Financial Hallucinations**: Ensures that numeric calculations (`charged_amount`, `expected_amount`, `delta`, `total_leakage`) are verified deterministically against source contracts.
2. **Detects Silent Agent Drift**: Catches subtle degradation in prompt performance, model updates, or schema parsing before changes reach production.
3. **Validates Multi-Agent Trajectories**: Ensures that information passed between pipeline nodes in LangGraph remains accurate and uncorrupted.
4. **Distinguishes Component vs. End-to-End Failures**: Pinpoints whether an audit failure originated in PDF text extraction, rule parsing, line matching, or report narrative synthesis.

### 1.3 Testing Hierarchy: Unit vs. Agent vs. E2E Evaluation

* **Unit Testing**: Verifies isolated Python functions with static inputs and expected returns (e.g., verifying `CleanDecimal` parsing or isolated `rule_engine.py` functions). Unit tests cannot evaluate LLM extraction accuracy or prompt quality on unseen contracts.
* **Agent-Level Evaluation**: Evaluates individual agents (e.g., `Contract Parser` or `Invoice Extractor`) in isolation by feeding canonical inputs and grading agent outputs against ground-truth datasets.
* **End-to-End (E2E) Evaluation**: Executes the full multi-agent LangGraph workflow from raw PDFs to the final `AuditReport`, verifying end-to-end precision, recall, total financial leakage accuracy, and execution latency.

### 1.4 Financial Correctness as a Hard Requirement
In ProcureAI, **financial correctness is non-negotiable**. A report containing elegant prose and valid clause references is an **unmitigated failure** if the overcharge delta is wrong or the math contains errors. Financial metrics are subjected to strict zero-tolerance deterministic evaluation gates.

### 1.5 System Boundaries: Guardrails vs. Observability vs. Evaluation

```text
+-----------------------------------------------------------------------+
|                              GUARDRAILS                               |
| Purpose: Prevent unsafe, invalid, or malformed states during runtime  |
| Examples: Pydantic schema validation, halt flags, error handling       |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                            OBSERVABILITY                              |
| Purpose: Record and display what happened during execution            |
| Examples: AuditLog execution traces, step timestamps, status flags     |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                              EVALUATION                               |
| Purpose: Measure whether the result was correct, accurate, and optimal |
| Examples: Precision/Recall, Delta Accuracy, Ground-truth comparison   |
+-----------------------------------------------------------------------+
```

These three layers interact but remain decoupled:
* **Guardrails** halt execution or enforce strict types.
* **Observability** provides visibility into execution logs and trajectory traces.
* **Evaluation** quantifies performance against known ground truth to guide system improvements.

---

## 2. Current ProcureAI Architecture

ProcureAI utilizes a FastAPI backend, a LangGraph stateful multi-agent pipeline, an async SQLite database, and a React/Vite user interface.

### 2.1 Component Overview
* **Frontend**: React 19 + Vite app utilizing state-based view navigation ([`App.jsx`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/frontend/src/App.jsx)).
* **Backend API**: FastAPI application ([`main.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/main.py)) mounting asynchronous routes for uploads, audits, contract library, supplier scorecards, analytics, and file watching.
* **Orchestration Layer**: LangGraph workflow engine ([`pipeline.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/pipeline.py)) executing a 6-node state graph.
* **LLM Client Layer**: Unified gateway ([`llm_client.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/core/llm_client.py)) supporting Gemini API, Vertex AI, and Mock LLM.
* **Deterministic Rule Engine**: Pure Python financial evaluator ([`rule_engine.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/compliance_checker/rule_engine.py)) handling arithmetic deltas, volume tier calculations, cap rates, and SLA penalty formulas.
* **Database & Persistence**: Async SQLAlchemy engine managing SQLite database tables ([`audit.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/models/audit.py)).
* **Evaluation Subsystem**: Benchmarking harness and metric calculation modules ([`harness.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/eval/harness.py), [`metrics.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/eval/metrics.py)).

### 2.2 System Architecture Diagram

```text
+-----------------------------------------------------------------------------------+
|                                 React / Vite UI                                   |
+-----------------------------------------------------------------------------------+
                                          |
                                   HTTP / REST API
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                 FastAPI Backend                                   |
|                          (backend/main.py & api/routes)                           |
+-----------------------------------------------------------------------------------+
       |                                  |                                  |
       v                                  v                                  v
+--------------+                +-------------------+                +--------------+
| SQLite DB    |                | Local File Storage|                | File Watcher |
| (Async ORM)  |                |  (data/uploads)   |                | (background) |
+--------------+                +-------------------+                +--------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        LangGraph Multi-Agent Pipeline                             |
|                         (backend/agents/pipeline.py)                              |
|                                                                                   |
|  [parallel_extractors] --> [cross_validator] --> [compliance_checker]             |
|   (Invoice Extractor +                                (Rule Engine)               |
|    Contract Parser)                                         |                     |
|                                                             v                     |
|  [report_generator]   <-- [cross_invoice_agent] <-- [reverse_sweep_agent]         |
|   (Final Report)           (Price Drift)             (Missing Credits)            |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                          LLM Layer (llm_client.py)                                |
|             Gemini Developer API  |  Vertex AI  |  Mock LLM Router             |
+-----------------------------------------------------------------------------------+
```

---

## 3. Agent Inventory

The repository contains 7 primary pipeline agents/nodes governed by `pipeline.py`, alongside 3 standalone task agents:

| Agent / Node Name | Module Path | Purpose | Primary Input | Primary Output | Execution Type | Key Dependencies | Business Criticality | Test Coverage | Eval Coverage | Primary Evaluation Gaps |
|---|---|---|---|---|---|---|---|---|---|---|
| **Contract Parser** | [`backend/agents/contract_parser/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/contract_parser/agent.py) | Extract pricing rules, volume tiers, SLA terms, and caps from contract text | `contract_text` | `ContractRulebook` | LLM-based (Structured JSON) | Gemini / `llm_client`, Pydantic schemas | **CRITICAL** | Integration tests | Evaluated via `extraction_accuracy` in harness | No clause offset validation; Rule ID re-indexing hack in legacy eval |
| **Invoice Extractor** | [`backend/agents/invoice_extractor/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/invoice_extractor/agent.py) | Extract invoice headers, vendor metadata, line items, and totals | `invoice_texts` | `List[InvoiceData]` | LLM-based (Structured JSON) | Gemini / `llm_client`, `CleanDecimal` | **CRITICAL** | Integration tests | Indirectly evaluated via pipeline recall | No independent line-item precision/recall harness |
| **Cross Validator** | [`backend/agents/cross_validator/validator.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/cross_validator/validator.py) | Perform fuzzy candidate matching between invoice lines and contract rules | `ContractRulebook`, `List[InvoiceData]` | `CrossValidationResult` | Hybrid (Fuzzy matching + LLM) | `difflib`, Pydantic schemas | **HIGH** | Integration tests | Indirectly evaluated via pipeline recall | Candidate candidate map accuracy not evaluated independently |
| **Compliance Checker** | [`backend/agents/compliance_checker/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/compliance_checker/agent.py) | Evaluate line items against candidate rules to identify financial overcharges | `CrossValidationResult`, `ContractRulebook` | `DiscrepancyList` | Deterministic Rule Engine + Critic LLM | [`rule_engine.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/compliance_checker/rule_engine.py), `CleanDecimal` | **CRITICAL** | 32 Unit tests in `test_billing_regressions.py` | Evaluated via `precision`, `recall`, `delta_accuracy` | Evaluation checks matching `rule_id` only, ignoring line numbers & severity |
| **Reverse Sweep** | [`backend/agents/reverse_sweep/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/reverse_sweep/agent.py) | Detect unapplied contract-level credits (SLA uptime breaches, volume rebates, early payment discounts) | `ContractRulebook`, `List[InvoiceData]` | `missing_credits` list | Deterministic + LLM rule matching | Pydantic schemas | **HIGH** | Integration tests | Evaluated via credit appending in harness | No evaluation of false positive unearned credits |
| **Cross Invoice Analyzer** | [`backend/agents/cross_invoice_analyzer/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/cross_invoice_analyzer/agent.py) | Detect price creep and unauthorized rate drift across historical invoices | `List[InvoiceData]` | `price_drifts` list | Deterministic drift calculations | Python math, Pydantic schemas | **MEDIUM** | Integration tests | Not evaluated in harness | No drift threshold sensitivity evaluation |
| **Report Generator** | [`backend/agents/report_generator/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/report_generator/agent.py) | Synthesize findings into an executive `AuditReport` with recommendations | All stage outputs, `discrepancies`, `missing_credits` | `AuditReport` | LLM-based narrative synthesis | Gemini / `llm_client` | **HIGH** | Integration tests | Evaluated via `predicted_leakage` total | Narrative clarity, grounding, and recommendation quality are not evaluated |
| **Contract Q&A Agent** *(Standalone)* | [`backend/agents/contract_qa/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/contract_qa/agent.py) | Answer user questions against indexed contract chunks | `query`, `audit_id` | `ChatResponse` | RAG + LLM | `contract_chunks` DB table | **MEDIUM** | None | None | Complete absence of RAG evaluation (retrieval precision/recall, context relevance) |
| **Dispute Generator** *(Standalone)* | [`backend/agents/dispute_generator/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/dispute_generator/agent.py) | Draft formal dispute letters to suppliers based on audit findings | `audit_id`, `discrepancy_ids` | `DisputeLetter` | LLM-based text generation | `dispute_letters` DB table | **MEDIUM** | Integration tests | None | No evaluation of legal tone, formula accuracy, or claim completeness |
| **Negotiation Analyzer** *(Standalone)* | [`backend/agents/negotiation_analyzer/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/negotiation_analyzer/agent.py) | Generate strategic negotiation briefs for supplier renewal meetings | `supplier_name`, `audit_ids` | `NegotiationBrief` | LLM-based aggregation | `audits` DB table | **LOW** | None | None | No evaluation of strategic narrative validity |

---

## 4. Current Evaluation System

The repository currently contains an evaluation subsystem located in [`backend/eval/`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/eval/).

### 4.1 Evaluation Implementation Structure
* **Test Case Definitions**: [`data/eval/test_cases.json`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/data/eval/test_cases.json) contains 16 synthetic test cases (`TC001` through `TC016`).
* **Evaluation Runner**: [`backend/eval/harness.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/eval/harness.py) executes `run_evaluation()`, loading test cases, executing the LangGraph pipeline, comparing predictions to ground truth, and writing a Markdown report.
* **Metric Calculation**: [`backend/eval/metrics.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/eval/metrics.py) provides functions for precision/recall, delta accuracy, and extraction accuracy.

### 4.2 Legacy Evaluation Workflow

```text
+------------------------------------+
|     data/eval/test_cases.json      |  (16 Synthetic Test Cases)
+------------------------------------+
                  |
                  v
+------------------------------------+
|      backend/eval/harness.py       |  (Async test harness)
+------------------------------------+
                  |
                  v
+------------------------------------+
|   build_pipeline().ainvoke(...)    |  (LangGraph Pipeline Execution)
+------------------------------------+
                  |
                  v
+------------------------------------+
|     backend/eval/metrics.py        |  (Calculate Precision, Recall, Delta Acc)
+------------------------------------+
                  |
                  v
+------------------------------------+
|  data/eval/evaluation_report.md    |  (Markdown Summary Output)
+------------------------------------+
```

### 4.3 Existing Metric Definitions
1. **Precision & Recall** (`calculate_precision_recall`):
   $$\text{Precision} = \frac{TP}{TP + FP}, \quad \text{Recall} = \frac{TP}{TP + FN}$$
   *Current Implementation Logic*: Compares predicted `rule_id` against expected `rule_id`.
2. **Delta Accuracy** (`calculate_delta_accuracy`):
   Calculates the percentage of matched True Positives where $| \text{predicted\_delta} - \text{expected\_delta} | \le \$10.00$.
3. **Extraction Accuracy** (`calculate_extraction_accuracy`):
   Calculates the fraction of expected `rule_id` strings extracted into `ContractRulebook.rules`.

---

## 5. Current Evaluation Gaps

Inspecting [`backend/eval/harness.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/eval/harness.py) and [`backend/eval/metrics.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/eval/metrics.py) reveals significant evaluation gaps that prevent reliable production evaluation:

### 5.1 Agent-Level Evaluation Gap
There is **zero independent evaluation** for individual agents. The current harness only evaluates the pipeline as a single monolith. If `Recall` drops, there is no benchmark mechanism to determine whether `Contract Parser` failed to extract the rule, `Invoice Extractor` misread the quantity, or `Cross Validator` failed to map the line item.

### 5.2 Shallow Finding-Level Matching Gap
In `metrics.py` (`calculate_precision_recall`), a finding match is counted as a **True Positive (TP)** solely based on string equality of `rule_id`:
```python
# From backend/eval/metrics.py (lines 32-35)
for p_rule in predicted_rules:
    if p_rule in expected_rules:
        tp += 1
```
*Issue*: If an agent matches `rule_id="R001"` on line item #1 with a charged amount of $500, but the ground truth was line item #5 with a charged amount of $5,000, **the evaluator records a 100% True Positive pass**. It completely ignores `invoice_line`, `discrepancy_type`, `charged_amount`, `expected_amount`, `severity`, and `recommendation`.

### 5.3 Financial Correctness Gap
* The evaluation permits a loose **$10.00 financial tolerance** (`tolerance = 10.0`) for exact arithmetic calculations.
* It does not verify whether the sign of the delta is correct (e.g., distinguishing between an overcharge `- $500` and an undercharge `+ $500`).
* Total leakage accuracy is measured by floating point comparison rather than strict `Decimal` representation.

### 5.4 Trajectory & Tool-Call Evaluation Gap
* The harness does not record intermediate LangGraph state transitions, retry attempts, or node execution times.
* It does not evaluate tool execution (such as `pdfplumber` text extraction quality or vector chunk retrieval).

### 5.5 Hardcoded Evaluation Hacks & Legacy Artefacts
* **Hardcoded Rule ID Re-mapping**: Lines 143-148 of `harness.py` contain explicit hardcoded overrides to re-map rule IDs produced by Mock LLM to match `test_cases.json`:
  ```python
  rule_mappings = {
      "TC003": {"R001": "R002"},
      "TC004": {"R002": "R003"},
      "TC009": {"R002": "R003"},
      "TC010": {"R001": "R002"}
  }
  ```
  This artificially inflates accuracy by masking model extraction mismatch.
* **Hardcoded User Artifact Path**: Line 254 of `harness.py` contains a hardcoded developer filesystem path (`C:/Users/tipusultan.bk/...`) causing silent failures or invalid path writes when run on alternate environments.
* **Defaulting to Mock LLM**: `harness.py` defaults to `MOCK_LLM="true"`, meaning the evaluation harness tests static canned JSON fixtures rather than actual live Gemini/Vertex model performance unless explicitly overridden.

### 5.6 Dataset & Versioning Gaps
* No versioning metadata tracking which dataset version, model release, prompt template version, or git commit produced an evaluation report.
* No LLM-as-a-Judge semantic grading for executive report narrative quality or dispute letter legal clarity.

---

## 6. Evaluation Philosophy

To achieve enterprise reliability, ProcureAI evaluation adheres to six core principles:

### Principle 1 — Deterministic Where Possible
All financial amounts, line numbers, rule identifiers, dates, and structured schema fields **must be evaluated deterministically** using exact string, integer, or `CleanDecimal` comparison. Never use an LLM to check if $1,240.00 equals $1,240.00.

### Principle 2 — Semantic Evaluation Where Necessary
Use LLM-as-a-Judge evaluation **only** for unstructured output where deterministic evaluation is impossible (e.g., verifying whether an audit executive summary is clear, accurate to source evidence, and professionally formatted).

### Principle 3 — Financial Correctness is a Hard Requirement
Financial accuracy is treated as a **hard gate**. If an audit pipeline identifies the correct contract rule but calculates an incorrect dollar leakage, the evaluation result for that case is an absolute **FAIL**, regardless of overall recall or narrative quality scores.

### Principle 4 — Agent Evaluation + E2E Evaluation
Both evaluation levels are mandatory:
* **Agent Evaluation** verifies component contracts and isolates regressors.
* **E2E Evaluation** verifies systemic behavior, multi-agent handoffs, and final report outputs.

### Principle 5 — Evaluation Must Be Reproducible
Every evaluation run must record complete metadata (`run_id`, git commit SHA, model parameters, temperature, prompt hashes, and dataset version) to ensure 100% bit-for-bit or statistical reproducibility.

### Principle 6 — Guardrails Must Not Hide Evaluation Failures
If a guardrail (e.g., Pydantic model validation or fallback error handler) catches an agent failure and prevents a runtime crash, **the evaluation framework must still log the underlying agent extraction failure**. Runtime resiliency must never obscure benchmark degradation.

---

## 7. Evaluation Levels

ProcureAI evaluation is structured across three distinct tiers:

```text
+---------------------------------------------------------------------------------+
|                           LEVEL 3: END-TO-END (E2E)                             |
| Scope: Full LangGraph workflow (Raw PDFs -> AuditReport & Database)             |
| Focus: Overall recall, total financial leakage, pipeline latency, report quality|
+---------------------------------------------------------------------------------+
                                        ^
                                        |
+---------------------------------------------------------------------------------+
|                        LEVEL 2: INDIVIDUAL AGENT EVAL                           |
| Scope: Single agent node (e.g., Contract Parser in isolation)                   |
| Focus: Input/output schema validation, rule recall, field extraction accuracy  |
+---------------------------------------------------------------------------------+
                                        ^
                                        |
+---------------------------------------------------------------------------------+
|                      LEVEL 1: COMPONENT / UNIT EVALUATION                       |
| Scope: Isolated functions & engines (rule_engine.py, CleanDecimal, PDF extractor)|
| Focus: Pure arithmetic precision, boundary edge cases, parser stability         |
+---------------------------------------------------------------------------------+
```

### 7.1 Level 1 — Component / Unit Evaluation
Evaluates isolated helper methods and calculation engines.
* *Examples*: Verifying `evaluate_line_rule()` in `rule_engine.py` against volume tier edge cases, testing `normalize_decimal()` against corrupt currency strings (`"INR 1,250.00/-"`), testing PDF text extraction against clean vs. scanned PDFs.

### 7.2 Level 2 — Individual Agent Evaluation
Evaluates each agent node independently by mocking upstream inputs and capturing immediate outputs.
* *Example Workflow*:
```text
Canonical Contract Text  --->  [ Contract Parser ]  --->  Predicted Rulebook
                                                                |
                                                                v
                                                    Deterministic Evaluator
                                                     (Compare against GT)
```

### 7.3 Level 3 — End-to-End (E2E) Evaluation
Evaluates the entire ProcureAI workflow starting from raw PDF uploads through graph execution to final JSON persistence and report generation. Measures total system precision, leakage accuracy, trajectory validity, and total runtime latency.

---

## 8. Agent-Specific Evaluation Strategy

Each of the 7 primary pipeline agents requires a tailored evaluation methodology:

### 8.1 Contract Parser
* **Module**: [`backend/agents/contract_parser/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/contract_parser/agent.py)
* **Inputs**: `contract_text` (str)
* **Outputs**: `ContractRulebook` (Pydantic model)
* **Evaluation Focus**:
  * Rule Precision & Recall (ratio of correctly extracted pricing rules).
  * Parameter Accuracy (exact extraction of `base_rate`, `volume_threshold`, `cap_amount`, `penalty_percent`).
  * Clause Reference & Offsets (verifying extracted `clause_reference` matches exact text in source contract).
* **Target Metrics**:
  * Rule Extraction Precision $\ge 95.0\%$
  * Parameter Extraction Accuracy $\ge 98.0\%$
  * False Rule Rate $\le 2.0\%$

### 8.2 Invoice Extractor
* **Module**: [`backend/agents/invoice_extractor/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/invoice_extractor/agent.py)
* **Inputs**: `invoice_texts` (List[str])
* **Outputs**: `List[InvoiceData]` (Pydantic models)
* **Evaluation Focus**:
  * Header Extraction Accuracy (`invoice_id`, `invoice_date`, `supplier_name`, `invoice_total`).
  * Line Item Completeness (detecting all line items without omitting or hallucinating rows).
  * Line Item Field Precision (`description`, `quantity`, `unit_price`, `total_amount`).
  * Arithmetic Consistency (`invoice_arithmetic_valid` check).
* **Target Metrics**:
  * Line Item Extraction Recall $\ge 99.0\%$
  * Numeric Amount Precision $= 100.0\%$ (Zero-tolerance)

### 8.3 Cross Validator
* **Module**: [`backend/agents/cross_validator/validator.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/cross_validator/validator.py)
* **Inputs**: `ContractRulebook`, `List[InvoiceData]`
* **Outputs**: `CrossValidationResult` (candidate mappings and unmapped line flags)
* **Evaluation Focus**:
  * Mapping Precision & Recall (verifying invoice line item is paired with the correct `rule_id`).
  * False Candidate Rate (rejecting incorrect rule matches).
  * Flagging Accuracy (properly setting `data_required_flags` when information is missing).
* **Target Metrics**:
  * Line-to-Rule Mapping Precision $\ge 95.0\%$
  * False Match Rate $\le 1.0\%$

### 8.4 Compliance Checker
* **Module**: [`backend/agents/compliance_checker/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/compliance_checker/agent.py)
* **Inputs**: `CrossValidationResult`, `ContractRulebook`, `List[InvoiceData]`
* **Outputs**: `DiscrepancyList` (Pydantic model)
* **Evaluation Focus**:
  * Overcharge Detection Precision & Recall.
  * Financial Delta Accuracy (exact match on `charged_amount - expected_amount`).
  * Critic Classifier Accuracy (correct assignment of `critic_status` and `recommendation`).
* **Target Metrics**:
  * Discrepancy Detection Recall $\ge 95.0\%$
  * Financial Delta Precision $= 100.0\%$

### 8.5 Reverse Sweep Agent
* **Module**: [`backend/agents/reverse_sweep/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/reverse_sweep/agent.py)
* **Inputs**: `ContractRulebook`, `List[InvoiceData]`
* **Outputs**: `missing_credits` (List[Dict])
* **Evaluation Focus**:
  * SLA Penalty Trigger Accuracy (detecting contract performance breaches from invoice service dates).
  * Unapplied Discount Detection (early payment discounts, volume rebate credits).
* **Target Metrics**:
  * Missing Credit Recall $\ge 90.0\%$
  * Credit Amount Accuracy $\ge 98.0\%$

### 8.6 Cross Invoice Analyzer
* **Module**: [`backend/agents/cross_invoice_analyzer/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/cross_invoice_analyzer/agent.py)
* **Inputs**: `List[InvoiceData]` across multiple billing periods
* **Outputs**: `price_drifts` (List[Dict])
* **Evaluation Focus**:
  * Price Drift Accuracy (calculating exact percentage and unit price increases across consecutive invoices).
  * False Creep Rate (avoiding flagging authorized contract rate step-ups).
* **Target Metrics**:
  * Drift Detection Accuracy $\ge 95.0\%$

### 8.7 Report Generator
* **Module**: [`backend/agents/report_generator/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/report_generator/agent.py)
* **Inputs**: All state findings, discrepancies, missing credits, and price drifts
* **Outputs**: `AuditReport` (Pydantic model)
* **Evaluation Focus**:
  * Total Financial Leakage Summation (must equal the exact sum of verified discrepancies and missing credits).
  * Groundedness & Evidence Citation (every finding narrative must reference valid clause IDs and line numbers).
  * Recommendation Alignment (validating that `DISPUTE` vs. `MONITOR` recommendations reflect discrepancy severity).
* **Target Metrics**:
  * Summary Leakage Accuracy $= 100.0\%$ (Zero-tolerance)
  * Evidence Citation Groundedness $\ge 98.0\%$

---

## 9. Finding-Level Evaluation Model

To eliminate the flaw where matching `rule_id` alone yields a full test pass, finding-level evaluation requires a **multi-field canonical comparison model**.

### 9.1 Canonical Finding Schema
A predicted finding is represented as:
```text
Finding
├── rule_id (str)
├── invoice_id (str)
├── line_id (str / int)
├── discrepancy_type (str) [overcharge | unapplied_penalty | rate_drift | cap_exceeded]
├── charged_amount (Decimal)
├── expected_amount (Decimal)
├── delta (Decimal)
├── severity (str) [LOW | MEDIUM | HIGH | CRITICAL]
├── evidence (str)
└── recommendation (str) [DISPUTE | ESCALATE | MONITOR | REVIEW]
```

### 9.2 Field-Level Match Evaluation Matrix

To qualify as a **True Positive (TP)**, a predicted finding must satisfy criteria across multiple match dimensions:

```text
Predicted Finding  <=======================================>  Ground Truth Finding
                                COMPARISON MATRIX

1. Rule Match           : Exact Match (e.g., "R001" == "R001")             [ MANDATORY ]
2. Line Item Match      : Line Description / ID Match                      [ MANDATORY ]
3. Discrepancy Type     : Exact Category Match                             [ MANDATORY ]
4. Financial Delta      : Abs(Predicted Delta - GT Delta) == 0.00         [ HARD GATE ]
5. Severity Rating      : Exact or Adjacent Level Match                    [ WEIGHT = 0.1 ]
6. Recommendation Match : Exact Recommendation Category                   [ WEIGHT = 0.1 ]
```

### 9.3 Multi-Field Finding Score Calculation
A finding match score $S_{\text{finding}}$ is computed per candidate pair:
$$S_{\text{finding}} = w_{\text{rule}} \cdot M_{\text{rule}} + w_{\text{line}} \cdot M_{\text{line}} + w_{\text{type}} \cdot M_{\text{type}} + w_{\text{delta}} \cdot M_{\text{delta}} + w_{\text{sev}} \cdot M_{\text{sev}}$$

Where:
* $M_{\text{rule}}, M_{\text{line}}, M_{\text{type}}, M_{\text{delta}} \in \{0, 1\}$ are mandatory binary matches.
* Weights are defined as: $w_{\text{rule}}=0.25$, $w_{\text{line}}=0.25$, $w_{\text{type}}=0.20$, $w_{\text{delta}}=0.20$, $w_{\text{sev}}=0.10$.
* If $M_{\text{delta}} = 0$ (financial mismatch), $S_{\text{finding}}$ automatically evaluates to **0.0 (FAIL)** regardless of other field matches.

---

## 10. Financial Accuracy Evaluation

Financial evaluation operates under **zero-tolerance strict equality rules**.

### 10.1 Financial Evaluation Protocol
1. **Decimal Precision**: All currency values are cast to Python `Decimal` types with 2 decimal places (`Decimal("0.00")`). Floating point comparisons are strictly forbidden.
2. **Tolerance**: The default financial tolerance is set to **$\$0.00$**. For complex multi-tier rounding variations, a maximum tolerance of **$\$0.01$** (1 cent) is permitted. The legacy $\$10.00$ tolerance is deprecated.
3. **Sign Verification**: Overcharges must evaluate to negative deltas (`delta < 0`), representing money owed back to the buyer. Undercharges evaluate to positive deltas (`delta > 0`). Sign mismatch is graded as an absolute failure.
4. **Leakage Summation**: Total financial leakage is verified by exact summation:
   $$\text{Total Leakage} = \sum | \text{delta}_{\text{overcharge}} | + \sum | \text{credit}_{\text{missing}} |$$

---

## 11. Ground Truth Strategy

Evaluation reliability depends upon high-integrity, human-verified ground truth datasets.

### 11.1 Ground Truth Pipeline

```text
+------------------------+
|  Raw PDF Documents     |  (Real or synthetic contract & invoice pairs)
+------------------------+
            |
            v
+------------------------+
| Domain Expert Annotator|  (Procurement / Legal Specialist annotates rules & math)
+------------------------+
            |
            v
+------------------------+
| Dual-Review & Verify   |  (Second expert verifies rule parsing & arithmetic delta)
+------------------------+
            |
            v
+------------------------+
| Structured Ground Truth|  (JSON schema containing expected rulebook & findings)
+------------------------+
            |
            v
+------------------------+
|   Evaluation Dataset   |  (Committed to version-controlled data/eval/ repository)
+------------------------+
```

### 11.2 Ground Truth JSON Schema
Ground truth test cases must explicitly define expected intermediate agent states, not just final total leakage:
```json
{
  "test_case_id": "TC_EVAL_001",
  "version": "1.0.0",
  "contract_file": "data/eval/contracts/c001_apex.pdf",
  "invoice_files": ["data/eval/invoices/i001_apex.pdf"],
  "expected_rulebook": {
    "supplier_name": "Apex Logistics",
    "rules": [
      {
        "rule_id": "R001",
        "rule_type": "volume_tier",
        "base_rate": 15.00,
        "clause_reference": "Section 4.1"
      }
    ]
  },
  "expected_invoice_data": [
    {
      "invoice_id": "INV-1001",
      "line_items_count": 4,
      "invoice_total": 12500.00
    }
  ],
  "expected_discrepancies": [
    {
      "rule_id": "R001",
      "line_id": 2,
      "discrepancy_type": "overcharge",
      "charged_amount": 15.00,
      "expected_amount": 12.50,
      "expected_delta": -1240.00,
      "severity": "HIGH",
      "recommendation": "DISPUTE"
    }
  ],
  "expected_total_leakage": 1240.00
}
```

---

## 12. Evaluation Dataset Strategy

The evaluation dataset strategy expands existing synthetic datasets into a comprehensive, multi-category benchmark suite.

### 12.1 Dataset Expansion Matrix (15 Categories)
The dataset will preserve existing `TC001`–`TC016` cases while introducing coverage across 15 distinct operational categories:

1. **Happy Path Clean Control**: Zero discrepancy invoices verifying zero false-positive flags (`TC011`, `TC013`, `TC015`).
2. **Standard Volume Tier Overcharges**: Stepped volume tier pricing miscalculations (`TC001`, `TC007`, `TC012`).
3. **Unapplied SLA Penalty Credits**: Performance uptime or delivery delay SLA breaches (`TC002`, `TC006`, `TC010`).
4. **Monthly / Annual Cap Rate Breaches**: Monthly service rate caps exceeded (`TC004`, `TC005`, `TC008`).
5. **Missed Bundle & Commitment Discounts**: Multi-service bundling discounts ignored (`TC003`, `TC009`).
6. **Multi-Discrepancy Invoices**: Invoices containing 3+ simultaneous overcharge types (`TC012`, `TC014`, `TC016`).
7. **Negative / Undercharge Cases**: Supplier undercharged buyer (validating positive delta handling).
8. **Boundary Edge Cases**: Invoice volume exactly sitting on tier boundaries (e.g., exactly 10,000 units).
9. **Missing Mandatory Fields**: Invoices missing tax IDs, billing period dates, or line descriptions.
10. **Malformed / Scanned PDF Inputs**: Low OCR quality, rotated pages, or noisy formatting.
11. **Ambiguous Contract Clauses**: Contracts with vague tier descriptions testing critic rating calibration.
12. **Conflicting Pricing Amendments**: Multiple active contract addendums with overlapping effectivity dates.
13. **High-Value Discrepancies**: Major enterprise billing errors ($100,000+ leakage).
14. **Adversarial / Prompt-Injection Invoices**: Invoices containing hidden text designed to override LLM system prompts.
15. **Multi-Invoice Rate Drift**: 6-month historical invoice series exhibiting stealth price creep.

### 12.2 Dataset Versioning & Governance
* Evaluation datasets are versioned using Semantic Versioning (`v1.0.0`, `v1.1.0`).
* Datasets are locked in `data/eval/versioned/` and must never be edited in place. New test cases append to a new version manifest.

---

## 13. Trajectory / Workflow Evaluation

Evaluating agent trajectories ensures that the LangGraph state machine follows optimal execution paths without invalid node jumps, redundant loops, or unhandled halts.

### 13.1 State Graph Trajectory Schema
During an evaluation run, every graph transition is captured in an execution trace:

```text
Graph Execution Trajectory Trace:
[Node 1: parallel_extractors]  --> State: {rulebook: OK, invoice_data: OK, halt: False}
[Node 2: cross_validator]      --> State: {candidate_map: 12 lines, halt: False}
[Node 3: compliance_checker]   --> State: {discrepancies: 3 found, halt: False}
[Node 4: reverse_sweep_agent]  --> State: {missing_credits: 1 found, halt: False}
[Node 5: cross_invoice_agent]  --> State: {price_drifts: 0 found, halt: False}
[Node 6: report_generator]     --> State: {audit_report: COMPLETE, halt: False}
[Transition: END]
```

### 13.2 Trajectory Metrics
* **Path Validity Ratio**: Percentage of evaluation runs that follow a valid topological route through the state graph.
* **Halt Correctness**: Verifies that `halt=True` is set **only** when mandatory inputs fail, preventing false early terminations.
* **State Mutation Integrity**: Ensures that downstream nodes do not overwrite or mutate upstream state keys unexpectedly.

---

## 14. Tool-Call Evaluation

For agents utilizing external utilities or tools, evaluation measures tool selection, parameter formatting, and tool execution success.

### 14.1 Tool Target Metrics
1. **PDF Text Extractor ([`pdf_extractor.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/core/pdf_extractor.py))**:
   * Measures fallback activation rate (`pdfplumber` $\rightarrow$ `pypdf`).
   * Evaluates text character extraction accuracy against ground-truth PDF text strings.
2. **Contract Q&A Vector Retrieval ([`contract_qa/agent.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/contract_qa/agent.py))**:
   * **Context Recall**: Percentage of relevant contract chunks retrieved for a Q&A prompt.
   * **Context Precision**: Ratio of relevant vs. irrelevant text chunks returned in the top-k context window.
3. **Auto-Audit File Watcher ([`file_watcher.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/services/file_watcher.py))**:
   * Evaluates contract hash matching accuracy for auto-ingested invoices.

---

## 15. LLM-as-a-Judge Strategy

LLM Judges are deployed **strictly** for subjective quality attributes where deterministic rules cannot operate.

### 15.1 Judge Scope Allocation

```text
+-------------------------------------------------------------------------------+
|                       DETERMINISTIC EVALUATION ENGINE                         |
| Evaluates: Amounts, Line IDs, Rule Matches, Deltas, Totals, Dates, Schemas     |
+-------------------------------------------------------------------------------+
                                       |
                                       v  (Only unstructured outputs passed downstream)
+-------------------------------------------------------------------------------+
|                          LLM-AS-A-JUDGE EVALUATOR                             |
| Evaluates: Report Narrative Quality, Evidence Clarity, Dispute Letter Tone   |
+-------------------------------------------------------------------------------+
```

### 15.2 LLM Judge Rubric & Metrics
For executive summaries and dispute letters, an LLM Judge evaluates responses across 4 rubric dimensions (rated 1 to 5):

1. **Evidence Grounding (1–5)**: Is every assertion in the summary supported by cited clause text and invoice line numbers?
2. **Clarity & Professional Tone (1–5)**: Is the explanation concise, professional, and free of vague fluff?
3. **Actionability of Recommendation (1–5)**: Does the recommendation provide clear next steps for procurement managers?
4. **Absence of Contradictions (1–5)**: Does the narrative narrative conflict with numerical figures presented in the report table?

### 15.3 Judge Governance & Configuration
* **Judge Model**: Fixed model pin (e.g., `gemini-1.5-pro` with `temperature=0.0`).
* **Structured Output**: The judge must return a structured JSON response containing numerical scores and explicit reasoning text.
* **Prohibition**: LLM Judges are **strictly prohibited** from evaluating financial calculations or verifying arithmetic accuracy.

---

## 16. Evaluator Calibration

To prevent "judge drift" or biased semantic scoring, LLM Judges must be continuously calibrated against human domain expert scores.

### 16.1 Calibration Workflow

```text
+------------------------------------+
| Human Benchmark Dataset (50 Cases) |  (Scored by Senior Procurement Auditors)
+------------------------------------+
                  |
                  v
+------------------------------------+
|  LLM Judge Scoring Execution       |  (Run LLM Judge on identical cases)
+------------------------------------+
                  |
                  v
+------------------------------------+
| Inter-Rater Reliability Analysis   |  (Compute Cohen's Kappa / Quadratic Weighted)
+------------------------------------+
                  |
                  v
+------------------------------------+
| Alignment Check: Kappa >= 0.80?    |
+------------------------------------+
         /                  \
   (YES)/                    \(NO)
       v                      v
[Deploy Judge]         [Refine Rubric & Prompt]
```

### 16.2 Alignment Metrics
* **Inter-Rater Reliability**: Measured using **Cohen's Kappa ($\kappa$)** or **Krippendorff's Alpha ($\alpha$)**.
* **Target Calibration Threshold**: $\kappa \ge 0.80$ alignment between human auditors and the LLM Judge before a judge prompt is approved for evaluation pipelines.

---

## 17. Evaluation Run Workflow

A standardized evaluation run executes through a 10-step sequence:

```text
 [1. Select Dataset Version]  --> Loads versioned test cases from data/eval/
              |
              v
 [2. Select Evaluation Scope] --> Local Agent vs. Full E2E Pipeline
              |
              v
 [3. Initialize Sandbox DB]   --> Spins up isolated temporary SQLite DB
              |
              v
 [4. Execute Agent/Pipeline]  --> Invokes LangGraph graph with test case inputs
              |
              v
 [5. Capture Trajectory]      --> Logs execution traces, step latencies, & states
              |
              v
 [6. Run Deterministic Eval]  --> Compares rule IDs, lines, amounts, & deltas (GT)
              |
              v
 [7. Run Semantic Eval]       --> Executes LLM Judge on narratives (if applicable)
              |
              v
 [8. Apply Hard Gates]        --> Evaluates zero-tolerance financial correctness
              |
              v
 [9. Aggregate Metrics]       --> Computes overall Precision, Recall, & Delta Acc
              |
              v
[10. Persist & Report]        --> Writes JSON run artifact & Markdown summary
```

---

## 18. Evaluation Metadata and Reproducibility

Every evaluation execution generates a structured, immutable metadata manifest guaranteeing 100% auditability.

### 18.1 Evaluation Manifest Schema (`eval_run_<id>.json`)
```json
{
  "evaluation_run_id": "eval_run_20260909_143000_a1b2",
  "timestamp_utc": "2026-09-09T14:30:00Z",
  "git_commit_sha": "c1f4a9d7e8b234567890abcdef1234567890abcd",
  "environment": "ci_runner_win32",
  "configuration": {
    "mock_llm": false,
    "llm_provider": "gemini",
    "model_name": "gemini-1.5-flash",
    "temperature": 0.0,
    "dataset_version": "v1.2.0"
  },
  "prompt_versions": {
    "contract_parser_prompt": "hash_a987f654",
    "compliance_checker_prompt": "hash_b123e456",
    "report_generator_prompt": "hash_c789d012"
  },
  "summary_metrics": {
    "total_cases": 16,
    "passed_cases": 16,
    "failed_cases": 0,
    "overall_precision": 1.0,
    "overall_recall": 1.0,
    "financial_delta_accuracy": 1.0,
    "mean_latency_seconds": 4.12
  },
  "hard_gate_status": "PASSED"
}
```

---

## 19. Scoring Strategy

ProcureAI evaluation separates scoring into **Hard Gates** and **Soft Metrics**.

### 19.1 Hard Gates vs. Soft Metrics

```text
+-----------------------------------------------------------------------------------+
|                                    HARD GATES                                     |
| Rule: ANY failure results in an immediate overall EVALUATION FAIL                 |
| Criteria:                                                                         |
|  1. Financial Delta Accuracy = 100.0% (Zero tolerance for math errors)            |
|  2. Total Leakage Summation = Exact Match                                         |
|  3. Pydantic Schema Validation Errors = 0                                         |
|  4. Unhandled Agent Exceptions = 0                                                |
+-----------------------------------------------------------------------------------+
                                         |
                                         v  (Only evaluated if Hard Gates PASS)
+-----------------------------------------------------------------------------------+
|                                   SOFT METRICS                                    |
| Rule: Weighted average score measuring overall system quality                     |
| Components:                                                                       |
|  - Rule Extraction Recall (Weight: 35%)                                           |
|  - Line Matching Precision (Weight: 35%)                                          |
|  - Narrative Groundedness Score (Weight: 15%)                                     |
|  - Execution Latency Score (Weight: 15%)                                          |
+-----------------------------------------------------------------------------------+
```

### 19.2 The Non-Weighted Gate Rule
A high soft metric score **can never compensate for a hard gate failure**. An audit run with $99\%$ precision and perfect narrative quality that miscalculates an overcharge by $\$50.00$ receives an overall score of **FAIL**.

---

## 20. Regression Evaluation

Regression evaluation automatically runs during continuous integration to prevent feature updates from degrading pipeline performance.

### 20.1 CI/CD Regression Workflow

```text
Pull Request Created / Modified
              |
              v
[Step 1: Execute Unit Tests]  --> pytest tests/unit/ (Must PASS 100%)
              |
              v
[Step 2: Execute Agent Eval]  --> Fast synthetic agent benchmarks (16 cases)
              |
              v
[Step 3: Delta Comparison]    --> Compare metrics against baseline run on main branch
              |
              v
[Step 4: Regression Check]    --> Did Recall drop > 0.5% OR Financial Acc drop > 0%?
         /                 \
   (YES)/                   \(NO)
       v                     v
[Block PR Merge]       [Approve Evaluation Gate]
```

### 20.2 Regression Thresholds
* **Financial Accuracy**: $0.0\%$ degradation allowed.
* **Recall / Precision**: Max allowable degradation $\le 0.5\%$ (requires explicit architectural approval).
* **Latency**: Max allowable execution slowdown $\le 10.0\%$.

---

## 21. Evaluation Reporting

Evaluation runs output comprehensive, human-readable Markdown reports alongside machine-readable JSON artifacts.

### 21.1 Standard Report Structure
Evaluation reports generated by the framework must adhere to the following layout:

1. **Run Metadata Header**: Timestamp, Git SHA, Dataset Version, Model Pin, Environment parameters.
2. **Executive Status Banner**: Overall status (`PASSED` / `FAILED`), Hard Gate verdicts.
3. **Summary Metric Table**: Target vs. Actual performance across Precision, Recall, Delta Accuracy, and Latency.
4. **Agent-Level Performance Breakdown**: Individual precision/recall tables for Contract Parser, Invoice Extractor, Cross Validator, and Compliance Checker.
5. **Detailed Failure Diagnostics**: Root-cause analysis for any failed test case (showing Expected vs. Predicted schemas and full error stack traces).
6. **Regression Delta**: Comparative diff against the previous baseline evaluation run.

---

## 22. Proposed Evaluation Architecture

The target evaluation subsystem will introduce a dedicated, modular architecture decoupled from production application paths:

```text
                               +----------------------------------+
                               |    data/eval/versioned/          |
                               |    (Versioned Test Cases JSON)   |
                               +----------------------------------+
                                                |
                                                v
+-----------------------------------------------------------------------------------+
|                              EVALUATION RUNNER ENGINE                             |
|                        (backend/eval/eval_runner.py)                              |
+-----------------------------------------------------------------------------------+
        |                                       |                               |
        v                                       v                               v
+-----------------------+             +-------------------+           +-------------------+
|  Level 2 Agent Runner |             |  Level 3 E2E Graph|           | Trajectory & Log  |
|  (Isolated Agent Node)|             |  (Full Pipeline)  |           | Observer          |
+-----------------------+             +-------------------+           +-------------------+
        |                                       |                               |
        +-----------------------+---------------+-------------------------------+
                                |
                                v
+-----------------------------------------------------------------------------------+
|                             EVALUATION METRIC ENGINE                              |
|                         (backend/eval/eval_engine.py)                             |
|                                                                                   |
|  +-----------------------------------+     +-----------------------------------+  |
|  | Deterministic Evaluator           |     | LLM Judge Evaluator               |  |
|  | (Exact Schemas, Deltas, Decimals) |     | (Narratives, Evidence Quality)    |  |
|  +-----------------------------------+     +-----------------------------------+  |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                            REPORT & ARTIFACT GENERATOR                            |
|                       (backend/eval/eval_reporter.py)                             |
+-----------------------------------------------------------------------------------+
        |                                                               |
        v                                                               v
+-----------------------------------+               +-----------------------------------+
| data/eval/reports/eval_<id>.json  |               | data/eval/reports/eval_<id>.md    |
| (Machine-Readable Manifest)       |               | (Human-Readable Markdown Report)  |
+-----------------------------------+               +-----------------------------------+
```

---

## 23. Evaluation Workflow Types

The framework defines 5 distinct evaluation workflow operational patterns:

### Workflow A: Developer Local Targeted Evaluation
* **Trigger**: Developer modifying an individual agent prompt or utility file.
* **Scope**: Targeted evaluation run against specific affected agents (e.g., testing `Contract Parser` locally after modifying `contract_parser/prompt.txt`).
* **Execution**: `.venv\Scripts\python -m backend.eval.runner --agent contract_parser --cases TC001-TC005`

### Workflow B: Full Regression Evaluation Suite
* **Trigger**: Pull request submission or pre-release release candidate build.
* **Scope**: Complete Level 1, Level 2, and Level 3 evaluation across all 16+ benchmark test cases.

### Workflow C: Dataset Validation Evaluation
* **Trigger**: Addition of new ground-truth test cases to `data/eval/`.
* **Scope**: Validates that new test cases adhere to Pydantic schemas and contain zero internal mathematical contradictions.

### Workflow D: Model & Prompt Iteration Evaluation
* **Trigger**: Evaluating a new model release (e.g., upgrading from `gemini-1.5-flash` to `gemini-2.0-flash` or testing prompt updates).
* **Scope**: Executes side-by-side evaluation benchmarking both model/prompt versions against a fixed baseline dataset to measure quality vs. cost vs. latency trade-offs.

### Workflow E: Production Monitoring & Feedback Loop (Future Vision)
* **Trigger**: Production user flags a discrepancy finding as "Incorrect" via the frontend [`FindingFeedback`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/models/audit.py) UI.
* **Scope**: Converts flagged production audit cases into anonymized candidate ground-truth test cases for human auditor verification and regression suite inclusion.

---

## 24. Failure Taxonomy

Evaluation failures are classified into 18 standardized error codes to accelerate root-cause analysis:

| Failure Category Code | Category Name | Description | Responsible Component |
|---|---|---|---|
| `ERR_EXTRACT_PDF` | PDF Extraction Failure | Text extractor failed to read characters or produced corrupted string output | [`pdf_extractor.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/core/pdf_extractor.py) |
| `ERR_PARSE_CONTRACT` | Contract Rule Omission | Contract Parser missed extracting an active pricing rule or volume tier | [`contract_parser`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/contract_parser/agent.py) |
| `ERR_PARSE_INVOICE` | Invoice Field Omission | Invoice Extractor omitted line items or header metadata | [`invoice_extractor`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/invoice_extractor/agent.py) |
| `ERR_MATCH_RULE` | Candidate Mapping Error | Cross Validator mapped an invoice line item to an incorrect contract rule | [`cross_validator`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/cross_validator/validator.py) |
| `ERR_CALC_DELTA` | Delta Math Mismatch | Compliance Checker calculated an incorrect financial delta amount | [`rule_engine.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/compliance_checker/rule_engine.py) |
| `ERR_CALC_SIGN` | Delta Sign Mismatch | Overcharge calculated with positive sign or vice versa | [`rule_engine.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/compliance_checker/rule_engine.py) |
| `ERR_MISSING_CREDIT` | Unapplied Penalty Omission | Reverse Sweep failed to identify an SLA breach or volume credit | [`reverse_sweep`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/reverse_sweep/agent.py) |
| `ERR_DRIFT_DETECTION` | Price Drift Error | Cross Invoice Analyzer failed to detect multi-period price creep | [`cross_invoice_analyzer`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/cross_invoice_analyzer/agent.py) |
| `ERR_REPORT_LEAKAGE` | Total Leakage Mismatch | Report Generator summary leakage does not match verified findings sum | [`report_generator`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/report_generator/agent.py) |
| `ERR_FALSE_POSITIVE` | False Discrepancy Flag | System flagged a compliant invoice line item as an overcharge | [`compliance_checker`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/compliance_checker/agent.py) |
| `ERR_FALSE_NEGATIVE` | Missed Overcharge | System failed to flag an active overcharge | Pipeline / Compliance |
| `ERR_SEVERITY_MISMATCH` | Severity Rating Error | Discrepancy assigned incorrect severity rating | [`compliance_checker`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/compliance_checker/agent.py) |
| `ERR_GROUNDING_FAIL` | Evidence Citation Failure | Finding narrative cited non-existent contract clause reference | [`report_generator`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/report_generator/agent.py) |
| `ERR_SCHEMA_VALIDATION` | Pydantic Schema Breach | Agent returned JSON failing Pydantic schema validation | Agent LLM Output |
| `ERR_GRAPH_TRAJECTORY` | Invalid State Transition | LangGraph executed out-of-order nodes or unexpected halt | [`pipeline.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/agents/pipeline.py) |
| `ERR_LLM_TIMEOUT` | Gateway API Timeout | LLM provider call timed out or threw unhandled network error | [`llm_client.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/core/llm_client.py) |
| `ERR_TOOL_FAILURE` | Secondary Tool Error | Vector chunk retrieval or DB persistence failed | Tool utility |
| `ERR_PROMPT_INJECTION` | Adversarial Vulnerability | Invoice text successfully overrode system agent instructions | Security Boundary |

---

## 25. Acceptance Criteria

Future implementation of the Agent Evaluation Framework must satisfy 11 strict acceptance criteria:

1. **Independent Agent Testing**: Every primary agent (`Contract Parser`, `Invoice Extractor`, etc.) can be evaluated in isolation with dedicated Level 2 test commands.
2. **Zero-Tolerance Financial Gating**: Financial delta mismatches strictly cause test case failure ($0.00 tolerance).
3. **Multi-Field Finding Validation**: Finding matches evaluate `rule_id`, `invoice_line`, `discrepancy_type`, `charged_amount`, `expected_amount`, `delta`, and `severity`.
4. **Removal of Evaluation Hacks**: `rule_mappings` overrides and hardcoded developer directory strings are completely removed from evaluation code.
5. **Live Model Benchmarking**: Evaluation can execute against live Gemini / Vertex models without forced fallback to Mock LLM.
6. **Immutable Dataset Versioning**: All evaluation runs pin an explicit dataset version tag (`data/eval/versioned/`).
7. **Metadata & Reproducibility**: Evaluation outputs generate machine-readable JSON manifests recording git SHA, model pin, temperature, and prompt hashes.
8. **Trajectory Auditing**: Evaluation logs node execution order, state transition validity, and step latency.
9. **Calibrated Semantic Judges**: LLM Judges used for narrative evaluation demonstrate $\kappa \ge 0.80$ inter-rater reliability against human benchmark scores.
10. **CI/CD Integration**: Regression evaluation runs automatically on pull requests and enforces hard gate build checks.
11. **Decoupled Architecture**: Evaluation code resides cleanly in `backend/eval/` without mutating production application behavior or schema definitions.

---

## 26. Risks and Limitations

### 26.1 Known Risks & Mitigations
* **Risk 1: LLM Non-Determinism**: Minor variations in LLM text generation may cause baseline metric jitter across evaluation runs.
  * *Mitigation*: Pin `temperature=0.0` for all evaluation calls and enforce deterministic Pydantic schema parsing.
* **Risk 2: Dataset Contamination / Overfitting**: Agents may overfit to the 16 synthetic evaluation cases (`TC001`–`TC016`).
  * *Mitigation*: Maintain a private, held-out evaluation dataset used exclusively for release candidate verification.
* **Risk 3: LLM Judge Bias**: LLM judges may favor verbose explanations over concise accurate narratives.
  * *Mitigation*: Calibrate judges continuously against human auditor scores and enforce strict length/grounding rubrics.
* **Risk 4: Evaluation Cost & Latency**: Running full E2E evaluation against live models across large document suites can incur API costs and time delays.
  * *Mitigation*: Implement tiered execution (fast synthetic Level 2 runs on PRs; full E2E evaluation on release candidates).

---

## 27. Future Implementation Phases

Implementation of the evaluation framework will follow a phased roadmap:

```text
+-----------------------------------------------------------------------------------+
| PHASE 1: DOCUMENTATION (Current Step)                                             |
| Deliverable: docs/evaluation/AGENT_EVALUATION_PLAN.md                             |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 2: BASELINE & TEST VERIFICATION                                             |
| Deliverables: Clean legacy eval hacks, verify 85 unit tests, audit baseline metrics|
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 3: GUARDRAILS ENHANCEMENT                                                   |
| Deliverables: Enforce strict Pydantic parsing gates & halt flag runtime safety    |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 4: OBSERVABILITY ARCHITECTURE                                               |
| Deliverables: Trajectory logging, step latency tracking, AuditLog trace expansion |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 5: INDIVIDUAL AGENT EVALUATION SUITE                                        |
| Deliverables: Level 2 evaluation runners for Contract Parser & Invoice Extractor  |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 6: REGRESSION SUITE & CI INTEGRATION                                        |
| Deliverables: Multi-field finding matching, zero-tolerance hard gates in CI/CD    |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 7: CONTINUOUS IMPROVEMENT & JUDGE CALIBRATION                               |
| Deliverables: LLM Judge calibration harness & production feedback evaluation loop |
+-----------------------------------------------------------------------------------+
```

*Note: The current task completes Phase 1 ONLY.*

---

## 28. Implementation Readiness Checklist

| Checklist Item | Description | Status |
|---|---|---|
| `[X]` | Evaluation Architecture Documented | **COMPLETED** |
| `[X]` | Agent Inventory Documented | **COMPLETED** |
| `[X]` | Current Evaluation System Documented | **COMPLETED** |
| `[X]` | Current Evaluation Gaps Identified | **COMPLETED** |
| `[X]` | Agent-Level Metrics Defined | **COMPLETED** |
| `[X]` | E2E Metrics Defined | **COMPLETED** |
| `[X]` | Ground Truth Strategy Defined | **COMPLETED** |
| `[X]` | Dataset Strategy Defined | **COMPLETED** |
| `[X]` | Finding-Level Evaluation Defined | **COMPLETED** |
| `[X]` | Financial Accuracy Evaluation Defined | **COMPLETED** |
| `[X]` | Trajectory Evaluation Defined | **COMPLETED** |
| `[X]` | Tool Evaluation Defined | **COMPLETED** |
| `[X]` | LLM Judge Strategy Defined | **COMPLETED** |
| `[X]` | Calibration Strategy Defined | **COMPLETED** |
| `[X]` | Regression Strategy Defined | **COMPLETED** |
| `[X]` | Evaluation Reporting Strategy Defined | **COMPLETED** |
| `[X]` | Acceptance Criteria Defined | **COMPLETED** |

---

## 29. Existing Evaluation Concerns

A rigorous analysis of the existing codebase ([`backend/eval/harness.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/eval/harness.py) and [`backend/eval/metrics.py`](file:///c:/Users/hansi/OneDrive/Documents/Office_work/procureai/backend/eval/metrics.py)) reveals specific implementation anomalies that must be addressed during Phase 2 refactoring:

1. **Rule ID Remapping Override (`harness.py` lines 143-148)**:
   The evaluation harness actively mutates agent predictions for test cases `TC003`, `TC004`, `TC009`, and `TC010` by mapping extracted rule IDs (e.g., `R001` $\rightarrow$ `R002`). This legacy hack masks extraction inconsistencies produced by Mock LLM fixtures.
2. **Hardcoded Machine-Specific File Path (`harness.py` line 254)**:
   The harness contains a hardcoded local Windows username path (`C:/Users/tipusultan.bk/.gemini/antigravity-ide/brain/...`). Running evaluation on alternate development machines logs file IO warnings or attempts invalid directory writes.
3. **Single-Field Precision/Recall Matching (`metrics.py` lines 32-35)**:
   `calculate_precision_recall` matches predictions against expected findings solely by `rule_id`. A predicted finding on an incorrect invoice line with a wrong dollar amount is incorrectly counted as a True Positive match.
4. **Loose Financial Tolerance ($10.00)**:
   `calculate_delta_accuracy` considers a financial delta accurate if it falls within $\$10.00$ of ground truth. For precision financial auditing, zero-tolerance decimal matching ($0.00) must be enforced.
5. **Forced Mock Execution Default (`harness.py` line 34)**:
   `harness.py` defaults environment variable `MOCK_LLM="true"`. Consequently, running `python -m backend.eval.harness` tests static mock fixtures rather than actual Gemini/Vertex LLM pipeline behavior unless explicitly overridden.

*Constraint Reminder: In accordance with task scope, these legacy evaluation concerns are documented for future correction. No Python files or evaluation scripts were modified during this task.*

---

## 30. Final Recommendation

### Immediate Next Steps
1. **Maintain Scope Discipline**: Do **NOT** begin implementing code changes, guardrails, or evaluation runners immediately.
2. **Proceed to Phase 2 (Baseline & Test Verification)**:
   * Verify that existing 85 unit and integration tests remain 100% passing.
   * Cleanly refactor legacy evaluation anomalies (`rule_mappings` override, hardcoded file paths, loose financial tolerance) in a controlled subsequent step.
   * Establish an un-manipulated baseline metric report for live model execution.
3. **Incremental Rollout Sequence**:
   * Build guardrails first (Phase 3) to protect runtime integrity.
   * Build observability second (Phase 4) to capture trajectory traces.
   * Implement agent-level and E2E evaluation runners third (Phases 5 & 6) to establish automated continuous evaluation gates.

By implementing this evaluation framework incrementally, **ProcureAI** will establish enterprise-grade reliability, zero-hallucination financial precision, and complete audit transparency across all agentic compliance workflows.

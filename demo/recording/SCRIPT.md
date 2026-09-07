# ProcureAI — Master Video Demonstration Script
## 3-Minute Competition Pitch & Recording Production Blueprint

**Target Video Duration**: 03:15 (195 seconds)  
**Target Voiceover Style**: Professional, confident, enterprise-ready, moderately paced, technically credible.  
**Primary Financial Demo Finding**: **$4,340.00** total recoverable leakage identified for **Apex Logistics Ltd**.

---

# Scene 01 — Executive Intro & Problem Statement

## Time
00:00–00:15

## Duration
15 seconds

## Screen
Opening high-tech title card featuring ProcureAI and Prodapt branding over a subtle animated gradient background, transitioning to an enterprise procurement dilemma infographic.

## Playwright Action
Introductory title card display (hold for narration).

## Voice-over
"Large enterprises lose 6 to 12 percent of their annual procurement spend to subtle contract leakage. Accounts Payable teams process thousands of monthly invoices under tight deadlines, leaving less than 5 percent ever verified against complex legal contracts."

## On-screen Text
**ProcureAI**  
*Autonomous Contract Compliance & Financial Leakage Recovery Engine*  
`6–12% Annual Procurement Spend Lost to Unchecked Invoices`

## Transition
Cross-dissolve into the live ProcureAI application interface.

## IPL Criteria
Business Problem & Market Relevance.

---

# Scene 02 — Product Entry & Dashboard

## Time
00:15–00:28

## Duration
13 seconds

## Screen
ProcureAI main Audit History dashboard interface showing active vendor audits, compliance statuses, and system navigation sidebar.

## Playwright Action
`recording.spec.js` opens `http://localhost:5173`, displays landing view (`scene01_product_entry.png`), smoothly moves cursor to the `+ NEW AUDIT` button.

## Voice-over
"ProcureAI bridges this gap with a local-first, autonomous contract compliance and financial leakage recovery engine designed for enterprise procurement."

## On-screen Text
`Local-First Enterprise Audit Infrastructure`

## Transition
Smooth cursor click on `+ NEW AUDIT` navigating to document intake.

## IPL Criteria
User Experience & Design Excellence.

---

# Scene 03 — Automated Document Intake

## Time
00:28–00:44

## Duration
16 seconds

## Screen
New Audit page with drag-and-drop document upload cards for Master Contract and Invoice PDFs.

## Playwright Action
`recording.spec.js` uploads `c001_apex_logistics_contract.pdf` and two invoice PDFs (`c001_invoice_i001.pdf`, `i002.pdf`), fills vendor input with `Apex Logistics Ltd` (`scene03_documents_uploaded.png`).

## Voice-over
"We initiate an audit by selecting the Master Services Agreement for Apex Logistics alongside their monthly freight invoices. ProcureAI ingests unstructured PDFs without requiring manual template pre-configuration."

## On-screen Text
`Multi-PDF Unstructured Ingestion | Zero Manual Formatting`

## Transition
Smooth cursor movement to the `RUN AUDIT` button.

## IPL Criteria
AI Document Understanding & Usability.

---

# Scene 04 — Initiating the Compliance Run

## Time
00:44–00:57

## Duration
13 seconds

## Screen
Document upload confirmation page showing loaded files, ready state, and audit trigger button.

## Playwright Action
`recording.spec.js` clicks `RUN AUDIT`, handles duplicate confirmation modal if present, and routes to the execution progress view (`scene04_audit_started.png`).

## Voice-over
"Triggering the audit dispatches the documents directly into our specialized multi-agent workflow, initializing parallel document extraction and compliance verification."

## On-screen Text
`Autonomous Pipeline Triggered`

## Transition
View shifts smoothly to the Live Agent Execution console.

## IPL Criteria
Technical Rigor & Workflow Integration.

---

# Scene 05 — 7-Agent Orchestrated Pipeline

## Time
00:57–01:18

## Duration
21 seconds

## Screen
Live multi-agent execution page displaying real-time progress bars for each specialized agent and streamed diagnostic log events console.

## Playwright Action
`recording.spec.js` toggles diagnostic log stream and observes live step-by-step progress (`scene05_agent_pipeline.png`).

## Voice-over
"Seven autonomous AI agents execute in sequence: Contract Parser and Invoice Extractor extract structured pricing rules, Cross Validator maps line items, and Compliance Checker runs deterministic Python engines to calculate exact rate math, volume discounts, cap limits, and missed SLA credits."

## On-screen Text
`LangGraph 7-Agent Architecture | Hybrid LLM + Deterministic Math Engine`

## Transition
Progress bars complete 100% and transition directly into the completed Audit Report.

## IPL Criteria
Innovation, Originality & Multi-Agent Architecture.

---

# Scene 06 — Executive Audit Report & Overview

## Time
01:18–01:34

## Duration
16 seconds

## Screen
Completed Audit Report header showing report reference ID, verification badge, timestamp, and audit metadata summary.

## Playwright Action
`recording.spec.js` waits for report summary load (`scene06_audit_report.png`), scrolling to summary cards.

## Voice-over
"Within seconds, the audit completes. ProcureAI provides a C-suite ready compliance brief, highlighting supplier risk status, audited line counts, and verified financial findings."

## On-screen Text
`Audit Execution Complete | Automated Reconciliation`

## Transition
Focus moves smoothly to the primary financial leakage KPI card.

## IPL Criteria
User Experience & Business Relevance.

---

# Scene 07 — Financial Leakage Discovery ($4,340 Recovery)

## Time
01:34–01:52

## Duration
18 seconds

## Screen
Summary Card prominently displaying **$4,340.00** Total Leakage Identified, 25.3% Compliance Score, and Executive Summary Memorandum.

## Playwright Action
`recording.spec.js` scrolls into view and holds on the total leakage KPI card (`scene07_leakage_result.png`).

## Voice-over
"Here is the key business result: ProcureAI uncovered 4,340 dollars in total recoverable financial leakage across these invoices, identifying an overall supplier compliance score of just 25.3 percent."

## On-screen Text
`PRIMARY FINDING: $4,340.00 Recoverable Financial Leakage Identified`

## Transition
Smooth scroll down to the detailed Discrepancy Findings table.

## IPL Criteria
Business Value & Financial Impact (WOW Moment).

---

# Scene 08 — Discrepancy & Unit Calculation Analysis

## Time
01:52–02:07

## Duration
15 seconds

## Screen
Interactive Discrepancy Table displaying severity tags (CRITICAL, HIGH), line item descriptions, and dollar deltas.

## Playwright Action
`recording.spec.js` clicks and expands the primary freight overcharge finding (`scene08_discrepancy_details.png`).

## Voice-over
"Expanding the primary discrepancy reveals a direct freight rate overcharge. While the contract specifies an agreed rate of 11 dollars and 50 cents per unit, the vendor billed 12 dollars and 50 cents—resulting in a 1,240 dollar overcharge on this single line item."

## On-screen Text
`Line Overcharge: Billed $12.50/unit vs Contracted $11.50/unit`

## Transition
Cursor moves down to the verbatim Evidence & Contract Clause section.

## IPL Criteria
Technical Rigor & Mathematical Accuracy.

---

# Scene 09 — Verbatim Contract Evidence & Math Proof

## Time
02:07–02:22

## Duration
15 seconds

## Screen
EvidenceBlock section displaying verbatim contract section text quote and side-by-side pricing calculation.

## Playwright Action
`recording.spec.js` highlights the verbatim contract clause quote (`scene09_evidence_clause.png`).

## Voice-over
"ProcureAI eliminates guesswork by linking every financial finding directly to the exact verbatim contract clause. Section 4.2 is quoted verbatim alongside the step-by-step mathematical proof."

## On-screen Text
`Verbatim Legal Clause Citation & Side-by-Side Proof`

## Transition
Cursor moves to the `GENERATE DISPUTE LETTER` action button.

## IPL Criteria
Commercial Feasibility & Audit Defense.

---

# Scene 10 — 1-Click Automated Dispute Letter

## Time
02:22–02:37

## Duration
15 seconds

## Screen
Dispute Letter modal showing tone calibration buttons (Collaborative, Formal Notice, Strict Demand) and full PDF layout mockup.

## Playwright Action
`recording.spec.js` clicks `GENERATE DISPUTE LETTER`, submits form, displays preview (`scene10_dispute_letter.png`), and closes modal smoothly.

## Voice-over
"With one click, ProcureAI drafts an official vendor dispute letter. Users can calibrate the tone from formal notice to strict legal demand, and export a ready-to-send PDF complete with legal references."

## On-screen Text
`1-Click Dispute Generation | Tone Calibration & PDF Export`

## Transition
Modal closes smoothly; cursor navigates to `Scorecard` on sidebar.

## IPL Criteria
Productivity Gain & End-to-End Automation.

---

# Scene 11 — Supplier Risk Scorecard & Portfolio Leaderboard

## Time
02:37–02:50

## Duration
13 seconds

## Screen
Supplier Risk Scorecard page featuring vendor risk bands (Red/Amber/Green), average compliance ratings, and aggregate vendor leakage.

## Playwright Action
`recording.spec.js` navigates to Scorecard view (`scene11_supplier_scorecard.png`), displaying Apex Logistics Ltd in High Risk status.

## Voice-over
"Across the enterprise, ProcureAI aggregates audit data into a Supplier Risk Scorecard—ranking vendors by risk band and tracking historical compliance trends."

## On-screen Text
`Supplier Risk Leaderboard & Portfolio Banding`

## Transition
Cursor clicks `Analytics` on sidebar.

## IPL Criteria
Enterprise Scalability & Supplier Intelligence.

---

# Scene 12 — Procurement Intelligence & Heatmap Analytics

## Time
02:50–03:03

## Duration
13 seconds

## Screen
Procurement Leakage Analytics page showing monthly financial trend charts, category attribution donuts, and the Clause Violation Heatmap.

## Playwright Action
`recording.spec.js` navigates to Analytics view (`scene12_analytics_dashboard.png`), displaying monthly trend charts and heatmap grid.

## Voice-over
"The Analytics Dashboard provides executive visibility into leakage trends by month, discrepancy category, and a clause violation heatmap—pinpointing systemic supplier errors."

## On-screen Text
`Clause Violation Heatmap & Executive Risk Analytics`

## Transition
Screen holds on executive analytics dashboard as closing voiceover begins.

## IPL Criteria
Strategic Business Value & Analytics.

---

# Scene 13 — Executive Summary & Closing

## Time
03:03–03:15

## Duration
12 seconds

## Screen
Executive analytics dashboard hold with ProcureAI and Prodapt IPL 2026 closing branding overlay.

## Playwright Action
`recording.spec.js` holds final state (`scene13_end_impact_screen.png`); clean end frame.

## Voice-over
"ProcureAI transforms static legal contracts into continuous financial intelligence—stopping procurement leakage before invoices are paid."

## On-screen Text
**ProcureAI**  
*Continuous Financial Intelligence for Enterprise Procurement*  
`Prodapt Innovation Premier League 2026`

## Transition
Fade to black.

## IPL Criteria
Overall Impact & Presentation Excellence.

---

## ElevenLabs Production Notes

To achieve a professional, authoritative, and enterprise-grade narration track:

1. **Recommended Voice Characteristics**:
   - **Gender/Age**: Male or Female, 30–45 age range.
   - **Tone**: Professional, confident, articulate, executive (e.g., ElevenLabs "Adam", "Marcus", or "Rachel").
   - **Stability**: `0.55` (prevents emotional over-dramatization).
   - **Clarity / Similarity**: `0.80` (ensures crisp articulation of financial and technical terms).
   - **Style Exaggeration**: `0.00` (maintains corporate presentation tone).

2. **Pacing Instructions**:
   - Speak at a steady, moderate pace (~145 words per minute).
   - Insert brief 300ms natural pauses at commas and 600ms pauses at periods.
   - Do NOT rush numbers: pronounce "$4,340.00" as *"four thousand three hundred and forty dollars"* or *"forty-three hundred dollars"*.

3. **Key Emphasis Points**:
   - **Scene 01**: Emphasize *"6 to 12 percent"*.
   - **Scene 05**: Emphasize *"Seven autonomous AI agents"* and *"deterministic Python engines"*.
   - **Scene 07 (WOW Moment)**: Emphasize *"4,340 dollars"* and *"25.3 percent"*.
   - **Scene 09**: Emphasize *"verbatim contract clause"*.
   - **Scene 13**: Emphasize *"continuous financial intelligence"*.

4. **Audio File Organization**:
   - Generate audio as separate MP3 files corresponding to each scene (`scene01_narration.mp3` through `scene13_narration.mp3`) for precise timeline matching in CapCut.

---

## CapCut Synchronization Notes

1. **Video Import**:
   - Import the raw webm recording file from `demo/recordings/raw/` into CapCut.
   - Set project canvas aspect ratio to **16:9** at **1920x1080 resolution, 60fps**.

2. **Audio Track Alignment**:
   - Align `scene01_narration.mp3` to start at `00:00.00`.
   - Use the visual screen transitions in the Playwright footage as cue points for each scene narration block.
   - Match the **$4,340.00** leakage voiceover (`scene07_narration.mp3`) exactly when Playwright scrolls to the Summary Card at `01:34`.

3. **Text Overlays & Callouts**:
   - Add sleek, semi-transparent lower-third text callouts matching the `On-screen Text` entries defined in this script.
   - Use clean typography (Inter, Roboto, or Montserrat) with subtle entry animations (Fade In 0.3s).

4. **Background Music**:
   - Add a subtle, low-volume corporate tech background track (e.g., ambient synth/minimal tech heartbeat) at **-24dB** volume under the narration track (**0dB**).

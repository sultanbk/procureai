# ProcureAI — Layer 2 Implementation Prompts
# Feature: Automate the Workflow
# Three prompts — paste each into a fresh AI session independently.
# Build in order: Prompt 1 → Prompt 2 → Prompt 3
# Layer 1 (Supplier Risk Scorecard, Leakage Trend Analytics,
#           Clause Violation Heatmap) must be complete before starting Layer 2.

---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 1 OF 3
# FEATURE: Dispute Letter Generator
# WHAT IT BUILDS: A one-click AI-generated formal dispute letter
#                 from any completed audit report. Editable fields,
#                 PDF export, and copy-to-clipboard.
# EFFORT: 1–2 days | One structured LLM call + React form + PDF export
# WHY FIRST: Closes the detection→action loop. Most impactful demo feature.
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building ProcureAI — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. The core 4-agent
pipeline is working. Layer 1 features (Supplier Risk Scorecard, Leakage
Trend Analytics, Clause Violation Heatmap) are complete.

I am now adding the Dispute Letter Generator.

## WHAT THIS FEATURE DOES

From any completed audit report page, the user clicks "Generate Dispute Letter".
A modal opens with an editable, AI-generated formal dispute letter that:

- Addresses the supplier formally with their name and contact details
- Lists every DISPUTE-recommended finding with clause citations
- Shows a formatted table: Line Item | Clause | Charged | Expected | Delta
- States the total amount in dispute
- Requests a credit note or corrected invoice by a specific deadline
- Is signed by the user's company name and signatory

The user can edit any field in the modal before generating the final output.
The final letter can be:
- Copied to clipboard as plain text
- Downloaded as a PDF
- (Optional) Opened in the user's default email client via mailto:

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2 + Gemini (Vertex AI)
Frontend: React + Vite + Tailwind CSS
The AuditReport JSON is already stored in the audits table (audit_report column).
The Discrepancy objects already have: finding_id, discrepancy_type, clause_reference,
clause_text, unit_price_charged, unit_price_expected, delta, severity, recommendation.
Gemini client singleton already exists at backend/core/llm_client.py.
All monetary values use Python Decimal. All LLM calls use structured JSON output mode.

## WHAT TO BUILD — BACKEND

### New endpoint: backend/api/routes/disputes.py

```
POST /api/disputes/generate

Request body (DisputeLetterRequest):
{
  "audit_id":         str,           -- loads AuditReport from DB
  "company_name":     str,           -- sender's company name
  "signatory_name":   str,           -- person signing the letter
  "signatory_title":  str,           -- e.g. "Head of Procurement"
  "supplier_contact": str,           -- supplier contact person name
  "supplier_email":   Optional[str], -- for mailto link
  "due_date":         str,           -- ISO date, deadline for supplier response
  "reference_number": Optional[str]  -- internal dispute reference
}

Response body (DisputeLetterResponse):
{
  "letter_text":      str,    -- full formatted letter as plain text
  "letter_html":      str,    -- HTML version for PDF rendering
  "findings_count":   int,    -- number of findings included
  "total_disputed":   str,    -- total delta as formatted $ string
  "supplier_email":   str | null
}
```

### Pydantic models

```python
class DisputeLetterRequest(BaseModel):
    audit_id:         str
    company_name:     str
    signatory_name:   str
    signatory_title:  str
    supplier_contact: str
    supplier_email:   Optional[str] = None
    due_date:         str
    reference_number: Optional[str] = None

class DisputeLetterResponse(BaseModel):
    letter_text:    str
    letter_html:    str
    findings_count: int
    total_disputed: str
    supplier_email: Optional[str]
```

### Letter generation logic (backend/services/dispute_generator.py)

```python
async def generate_dispute_letter(
    request: DisputeLetterRequest,
    audit_report: AuditReport,
    db: Session
) -> DisputeLetterResponse:

    # Step 1: Filter to only DISPUTE-recommended findings
    dispute_findings = [
        f for f in audit_report.discrepancies
        if f.recommendation == "DISPUTE"
    ]

    if not dispute_findings:
        raise ValueError("No DISPUTE-recommended findings in this audit report.")

    # Step 2: Compute total disputed amount
    total_disputed = sum(abs(f.delta) for f in dispute_findings)

    # Step 3: Build structured findings summary for LLM
    findings_summary = []
    for f in dispute_findings:
        findings_summary.append({
            "finding_id":         f.finding_id,
            "description":        f.description,
            "clause_reference":   f.clause_reference,
            "clause_text":        f.clause_text,
            "unit_price_charged": str(f.unit_price_charged),
            "unit_price_expected":str(f.unit_price_expected),
            "quantity":           str(f.quantity),
            "charged":            str(f.line_total_charged),
            "expected":           str(f.line_total_expected),
            "delta":              str(abs(f.delta)),
            "discrepancy_type":   f.discrepancy_type
        })

    # Step 4: LLM call — generate the letter body
    # Use structured output: {"letter_text": str, "letter_html": str}
    # The LLM writes the narrative paragraphs and formats the findings table
    # Pass all request fields + findings_summary to the prompt

    prompt = load_prompt("dispute_generator")
    # Inject: company_name, signatory_name, signatory_title,
    #         supplier_name (from audit_report.summary.supplier_name),
    #         supplier_contact, due_date, reference_number,
    #         audit_date (from audit_report.summary.audit_date),
    #         billing_period (from audit_report.summary.billing_period),
    #         contract_id (from audit_report.summary.contract_id),
    #         findings_summary (list), total_disputed

    # Step 5: Return validated response
```

### Prompt file: backend/agents/dispute_generator/prompt.txt

Write a prompt with these instructions:
```
[ROLE]
You are a professional procurement legal correspondent writing a formal
contract dispute letter on behalf of a company to one of their suppliers.

[TASK]
Generate a formal, professional dispute letter based on the audit findings
provided. The letter must be firm but not aggressive, legally precise but
readable, and must cite every specific contract clause for every finding.

[LETTER STRUCTURE — follow exactly]
1. Date and reference line
2. Supplier contact name and company
3. Subject line: "Formal Dispute — Invoice Audit Findings | [Contract ID] | [Billing Period]"
4. Opening paragraph: state purpose, reference the contract, state audit date
5. Summary paragraph: state total amount in dispute, number of findings
6. Findings section:
   - One paragraph per finding explaining the discrepancy in plain English
   - Exact contract clause quoted in quotation marks
   - Charged amount vs. expected amount clearly stated
7. Formatted findings table (in HTML version):
   | Finding | Description | Clause | Charged | Expected | Overcharge |
8. Request paragraph: request credit note or corrected invoice by due_date
9. Consequence paragraph: state that unresolved disputes will be escalated
10. Closing: signatory name, title, company

[OUTPUT FORMAT]
Return ONLY valid JSON with two fields:
- "letter_text": the full letter as plain text with \n line breaks
- "letter_html": the full letter as HTML using only <p>, <table>, <tr>,
  <td>, <th>, <strong>, <br> tags. No CSS. No external classes.

[RULES]
- Never invent clause text — only use the exact clause_text provided
- Never invent financial figures — only use the numbers provided
- All amounts in INR with $ symbol
- Professional tone throughout — this is a legal document
- Due date must appear in the request paragraph
- Reference number (if provided) must appear in the subject line
```

## WHAT TO BUILD — FRONTEND

### Add "Generate Dispute Letter" button to AuditReport.jsx

Position: In the AuditSummaryCard component, below the total leakage amount.
Only show if at least one finding has recommendation === "DISPUTE".

Button click → open DisputeLetterModal.

### Build DisputeLetterModal.jsx (new component)

```
Modal layout (full-screen overlay, centered card, max-width 720px):

Step 1 — Fill in details form (shown first):
  Fields (all pre-filled with sensible defaults, all editable):
    Your Company Name:    [text input]
    Signatory Name:       [text input]
    Signatory Title:      [text input, default "Head of Procurement"]
    Supplier Contact:     [text input]
    Supplier Email:       [email input, optional]
    Response Due Date:    [date picker, default = today + 14 days]
    Internal Reference #: [text input, optional]

  Button: "Generate Letter →"
  → POST /api/disputes/generate with form values + audit_id
  → Show loading spinner: "Drafting your dispute letter..."

Step 2 — Letter preview (shown after generation):
  - Render letter_text in a scrollable <pre> or <div> with monospace font
  - The letter text is EDITABLE (use contentEditable or textarea)
  - Action buttons row:
      [Copy to Clipboard]  [Download PDF]  [← Edit Details]  [✕ Close]

Copy to Clipboard:
  navigator.clipboard.writeText(editedLetterText)
  Show "Copied!" confirmation for 2 seconds

Download PDF:
  Use jsPDF (already in project or add it):
    const doc = new jsPDF()
    doc.setFont("helvetica", "normal")
    doc.setFontSize(11)
    // Split letter_text into lines, add to PDF
    const lines = doc.splitTextToSize(letterText, 180)
    doc.text(lines, 15, 20)
    doc.save(`Dispute_${supplierName}_${auditId}.pdf`)
```

### Frontend API call (add to frontend/src/api/audit.js)

```javascript
export async function generateDisputeLetter(payload) {
  const res = await fetch(`${BASE}/api/disputes/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
```

## IMPLEMENTATION ORDER

1. backend/agents/dispute_generator/prompt.txt — write the prompt
2. backend/services/dispute_generator.py — generate_dispute_letter()
3. backend/api/routes/disputes.py — POST /api/disputes/generate
4. Register disputes router in main.py
5. frontend/src/api/audit.js — add generateDisputeLetter()
6. frontend/src/components/DisputeLetterModal.jsx — full modal
7. Wire "Generate Dispute Letter" button into AuditReport.jsx

## DONE WHEN

- POST /api/disputes/generate returns a well-structured formal letter
  with correct clause citations for every DISPUTE finding
- Letter contains an accurate findings table with correct $ amounts
- Letter text is fully editable in the modal before download
- "Copy to Clipboard" copies the current (possibly edited) text
- "Download PDF" downloads a readable PDF with correct filename
- Button does NOT appear on audits with zero DISPUTE findings
- Letter does not invent any clause text or financial figures
- If audit has no DISPUTE findings, API returns clear 400 error

---
END OF PROMPT 1
---


---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 2 OF 3
# FEATURE: Alert & Notification Engine
# WHAT IT BUILDS: Push alerts to Slack and/or email when a CRITICAL
#                 finding is detected after any audit completes.
#                 Configurable thresholds. Settings UI page.
# EFFORT: 1–2 days | Slack webhook + SMTP/SendGrid + settings page
# WHY SECOND: Lowest complexity in Layer 2. Brings signal to where
#             teams already are. Doesn't require Gmail OAuth.
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building ProcureAI — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. The core pipeline,
Layer 1 features, and Dispute Letter Generator (Layer 2, Prompt 1) are
all complete.

I am now adding the Alert & Notification Engine.

## WHAT THIS FEATURE DOES

After every audit pipeline completes, if the findings meet configurable
alert conditions, the system automatically sends notifications to:
- A Slack channel (via Incoming Webhook URL)
- An email address (via SMTP)

Both channels are optional and independently configurable.

Alert conditions (all configurable in Settings UI):
- CRITICAL finding detected (always alert by default)
- Total leakage exceeds a threshold (e.g. $10,000)
- Any finding detected (can be turned off to reduce noise)

Notification content:
```
[Slack message example]
🚨 *ProcureAI Alert — CRITICAL Finding*
Supplier: Apex Logistics Ltd
Invoice Period: October 2024
Total Leakage: $36,600
Findings: 3 (1 CRITICAL, 1 HIGH, 1 MEDIUM)
Top Finding: Unapplied SLA penalty — $22,760 (Section 8.1)
→ View Report: http://localhost:5173/audit/aud_20241115_abc123
```

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2
The audit pipeline completes inside backend/agents/report_generator/agent.py
after writing the AuditReport to the DB and setting status = COMPLETE.
The notification trigger must be added at the END of that function,
after the DB write, as a fire-and-forget background task.

Environment variables are loaded from backend/.env via python-dotenv.

## WHAT TO BUILD — BACKEND

### Step 1: notification_settings table

```sql
CREATE TABLE notification_settings (
    id                  INTEGER PRIMARY KEY DEFAULT 1,
    slack_enabled       INTEGER DEFAULT 0,        -- 0 or 1
    slack_webhook_url   TEXT,
    email_enabled       INTEGER DEFAULT 0,
    email_to            TEXT,                     -- comma-separated addresses
    email_from          TEXT,
    smtp_host           TEXT,
    smtp_port           INTEGER DEFAULT 587,
    smtp_user           TEXT,
    smtp_password       TEXT,                     -- store as-is for MVP
    alert_on_critical   INTEGER DEFAULT 1,
    alert_on_high       INTEGER DEFAULT 0,
    alert_threshold_inr REAL DEFAULT 10000.0,     -- alert if leakage exceeds this
    alert_on_any_finding INTEGER DEFAULT 0
);

-- Insert default row on first run
INSERT OR IGNORE INTO notification_settings (id) VALUES (1);
```

### Step 2: backend/services/notifier.py

```python
import httpx
import smtplib
from email.mime.text import MIMEText
from decimal import Decimal

async def send_notifications(
    audit_report: AuditReport,
    settings: NotificationSettings
) -> None:
    """
    Fire-and-forget. Called after audit completes.
    Checks conditions, sends Slack + email if configured.
    Never raises — logs errors silently.
    """

    # Check if any condition is met
    should_alert = False
    critical_count = audit_report.summary.critical_count
    total_leakage = audit_report.summary.total_leakage

    if settings.alert_on_critical and critical_count > 0:
        should_alert = True
    if settings.alert_on_high and audit_report.summary.high_count > 0:
        should_alert = True
    if total_leakage >= Decimal(str(settings.alert_threshold_inr)):
        should_alert = True
    if settings.alert_on_any_finding and audit_report.summary.discrepancy_count > 0:
        should_alert = True

    if not should_alert:
        return

    # Build message content
    top_finding = audit_report.discrepancies[0] if audit_report.discrepancies else None
    message = build_message(audit_report, top_finding)

    # Send Slack
    if settings.slack_enabled and settings.slack_webhook_url:
        await send_slack(settings.slack_webhook_url, message)

    # Send email
    if settings.email_enabled and settings.email_to and settings.smtp_host:
        send_email(settings, audit_report, message)


def build_message(report: AuditReport, top_finding) -> dict:
    severity_emoji = "🚨" if report.summary.critical_count > 0 else "⚠️"
    top_finding_text = ""
    if top_finding:
        top_finding_text = (
            f"{top_finding.discrepancy_type.replace('_',' ').title()} — "
            f"${abs(top_finding.delta):,.2f} ({top_finding.clause_reference})"
        )
    return {
        "severity_emoji":    severity_emoji,
        "supplier_name":     report.summary.supplier_name,
        "billing_period":    report.summary.billing_period,
        "total_leakage":     f"${report.summary.total_leakage:,.2f}",
        "discrepancy_count": report.summary.discrepancy_count,
        "critical_count":    report.summary.critical_count,
        "high_count":        report.summary.high_count,
        "medium_count":      report.summary.medium_count,
        "top_finding":       top_finding_text,
        "audit_id":          report.audit_id,
        "report_url":        f"http://localhost:5173/audit/{report.audit_id}"
    }


async def send_slack(webhook_url: str, message: dict) -> None:
    payload = {
        "text": (
            f"{message['severity_emoji']} *ProcureAI Alert*\n"
            f"*Supplier:* {message['supplier_name']}\n"
            f"*Period:* {message['billing_period']}\n"
            f"*Total Leakage:* {message['total_leakage']}\n"
            f"*Findings:* {message['discrepancy_count']} "
            f"({message['critical_count']} CRITICAL, "
            f"{message['high_count']} HIGH, "
            f"{message['medium_count']} MEDIUM)\n"
            f"*Top Finding:* {message['top_finding']}\n"
            f"→ <{message['report_url']}|View Full Report>"
        )
    }
    async with httpx.AsyncClient() as client:
        try:
            await client.post(webhook_url, json=payload, timeout=5.0)
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")


def send_email(settings, report: AuditReport, message: dict) -> None:
    subject = (
        f"[ProcureAI] {message['severity_emoji']} "
        f"{message['supplier_name']} — ${report.summary.total_leakage:,.2f} leakage detected"
    )
    body = f"""
ProcureAI Audit Alert

Supplier:      {message['supplier_name']}
Period:        {message['billing_period']}
Total Leakage: {message['total_leakage']}
Findings:      {message['discrepancy_count']} total
               {message['critical_count']} CRITICAL
               {message['high_count']} HIGH
               {message['medium_count']} MEDIUM

Top Finding:   {message['top_finding']}

View full report: {message['report_url']}

---
This alert was sent automatically by ProcureAI.
    """.strip()

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = settings.email_to

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
    except Exception as e:
        logger.error(f"Email notification failed: {e}")
```

### Step 3: Wire into report_generator/agent.py

At the very end of `run_report_generator`, after writing to DB:
```python
# Fire-and-forget — don't await, don't block the pipeline
settings = db.query(NotificationSettings).first()
if settings:
    asyncio.create_task(
        send_notifications(audit_report, settings)
    )
```

### Step 4: Settings API (backend/api/routes/settings.py)

```
GET  /api/settings/notifications
     → returns current NotificationSettings row

PUT  /api/settings/notifications
     → updates the single settings row
     → request body: all configurable fields (all Optional)

POST /api/settings/notifications/test-slack
     → sends a test Slack message using saved webhook URL
     → returns {success: bool, error: str | null}

POST /api/settings/notifications/test-email
     → sends a test email using saved SMTP settings
     → returns {success: bool, error: str | null}
```

### Pydantic model

```python
class NotificationSettingsUpdate(BaseModel):
    slack_enabled:        Optional[bool] = None
    slack_webhook_url:    Optional[str] = None
    email_enabled:        Optional[bool] = None
    email_to:             Optional[str] = None
    email_from:           Optional[str] = None
    smtp_host:            Optional[str] = None
    smtp_port:            Optional[int] = None
    smtp_user:            Optional[str] = None
    smtp_password:        Optional[str] = None
    alert_on_critical:    Optional[bool] = None
    alert_on_high:        Optional[bool] = None
    alert_threshold_inr:  Optional[float] = None
    alert_on_any_finding: Optional[bool] = None
```

## WHAT TO BUILD — FRONTEND

### Build frontend/src/pages/Settings.jsx

Layout — two collapsible sections:

**Section 1 — Slack Notifications**
```
Toggle: Enable Slack Notifications [on/off switch]
  When ON, show:
    Webhook URL: [text input, type=url]
    [Test Connection] button
      → POST /api/settings/notifications/test-slack
      → Show "✓ Test message sent!" or "✗ Failed: [error]"
```

**Section 2 — Email Notifications**
```
Toggle: Enable Email Notifications [on/off switch]
  When ON, show:
    Send to:       [text input — comma-separated emails]
    From address:  [text input]
    SMTP Host:     [text input]
    SMTP Port:     [number input, default 587]
    SMTP Username: [text input]
    SMTP Password: [password input]
    [Test Email] button
      → POST /api/settings/notifications/test-email
      → Show result
```

**Section 3 — Alert Conditions**
```
Checkboxes (independent):
  ☑ Alert when CRITICAL finding detected (default on)
  ☐ Alert when HIGH finding detected
  ☐ Alert on any finding

Threshold input:
  Alert when total leakage exceeds: $ [number input, default 10000]
```

**Save button:**
```
[Save Settings] → PUT /api/settings/notifications
→ Show "Settings saved ✓" toast for 2 seconds
```

Add /settings route to App.jsx router.
Add "Settings ⚙" link to Navbar (right side).

## IMPLEMENTATION ORDER

1. DB migration — add notification_settings table, insert default row
2. backend/services/notifier.py — full notification service
3. Wire asyncio.create_task into report_generator/agent.py
4. backend/api/routes/settings.py — GET/PUT settings + test endpoints
5. Register settings router in main.py
6. frontend/src/api/audit.js — getNotificationSettings(), updateNotificationSettings(),
   testSlack(), testEmail()
7. frontend/src/pages/Settings.jsx — full settings page
8. Add /settings route + Navbar link

## DONE WHEN

- After running an audit with CRITICAL findings, Slack message appears
  in the configured channel within 5 seconds
- Email arrives at configured address with correct supplier name and leakage amount
- Test buttons correctly validate Slack webhook and SMTP credentials
  before the first real audit runs
- Settings persist across server restarts (stored in DB, not memory)
- Toggling Slack OFF stops messages even when CRITICAL findings exist
- Threshold works: setting $50,000 threshold suppresses alerts for
  audits with total_leakage < $50,000
- Notification failure never crashes the audit pipeline (fire-and-forget)

Do not implement Teams, WhatsApp, or SMS yet.
Do not store SMTP password encrypted yet (MVP — document as known limitation).

---
END OF PROMPT 2
---


---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 3 OF 3
# FEATURE: Scheduled Auto-Audit
# WHAT IT BUILDS: Watch a designated local folder for new invoice
#                 PDFs. Auto-match to the right contract from the
#                 Contract Library. Trigger the audit pipeline
#                 automatically. No manual upload required.
# EFFORT: 3–4 days | File watcher + Contract Library + auto-matching
# PREREQUISITE: Contract Library must be built first (Layer 4, Prompt 3)
#               OR build a simplified version of Contract Library inline here.
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building ProcureAI — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. The core pipeline,
Layer 1 features, Dispute Letter Generator, and Alert Engine are all complete.

I am now adding Scheduled Auto-Audit — the most complex Layer 2 feature.

## WHAT THIS FEATURE DOES

A background file watcher monitors a designated local folder:
  suppliergaurd/watched_invoices/

When a new PDF file appears in that folder, the system:
1. Reads the PDF and extracts the supplier name from it
2. Looks up the matching contract from the Contract Library
3. If a match is found → automatically triggers the full audit pipeline
4. Sends a notification (via the Alert Engine) when complete
5. Moves the processed file to watched_invoices/processed/
6. If no contract match found → moves to watched_invoices/unmatched/ with a log entry

The Auto-Audit status page shows:
- Watch status (watching / paused)
- Last file processed + result
- Queue of files being processed
- History of auto-triggered audits

## IMPORTANT DESIGN DECISION

This feature requires a Contract Library — a DB table that stores uploaded
contracts with supplier metadata so new invoices can be matched automatically.
Build a minimal Contract Library as part of this prompt:
- Contracts table in DB (supplier_name, contract_file_path, parsed_rulebook_id)
- Simple upload UI to add contracts to the library
- Supplier name matching for auto-matching (exact match first, fuzzy fallback)

This is intentionally simpler than the full Layer 4 Contract Library.
The full version will add contract versioning, expiry dates, and search.

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2 + LangGraph
Frontend: React + Vite + Tailwind CSS
The audit pipeline already runs via POST /api/audit/run with file_ids.
The PDF upload already works via POST /api/upload/contract and /api/upload/invoice.
Notifications are handled by backend/services/notifier.py (already built).

## WHAT TO BUILD — BACKEND

### Step 1: contracts table (minimal Contract Library)

```sql
CREATE TABLE contracts (
    id              TEXT PRIMARY KEY,   -- "ctr_apex_logistics_001"
    supplier_name   TEXT NOT NULL,
    supplier_aliases TEXT,              -- JSON array of alternative names
                                       -- ["Apex", "Apex Ltd", "APEX LOGISTICS"]
    contract_file_path TEXT NOT NULL,
    original_filename  TEXT,
    uploaded_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active       INTEGER DEFAULT 1  -- 0 = archived
);
```

### Step 2: watched_files table

```sql
CREATE TABLE watched_files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    filename        TEXT NOT NULL,
    detected_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    status          TEXT DEFAULT 'PENDING',
    -- PENDING | MATCHING | MATCHED | UNMATCHED | PROCESSING | COMPLETE | FAILED
    matched_contract_id TEXT,
    audit_id        TEXT,
    supplier_name_extracted TEXT,
    error_detail    TEXT,
    processed_at    DATETIME
);
```

### Step 3: File watcher service (backend/services/file_watcher.py)

Use Python watchdog library:
```python
# Add to requirements.txt: watchdog==4.0.0

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio, shutil, time
from pathlib import Path

WATCH_DIR = Path("watched_invoices")
PROCESSED_DIR = WATCH_DIR / "processed"
UNMATCHED_DIR = WATCH_DIR / "unmatched"

class InvoiceFileHandler(FileSystemEventHandler):
    def __init__(self, db_session_factory, pipeline_runner):
        self.db_factory = db_session_factory
        self.pipeline_runner = pipeline_runner

    def on_created(self, event):
        if event.is_directory: return
        path = Path(event.src_path)
        if path.suffix.lower() != ".pdf": return
        if path.parent.name in ("processed", "unmatched"): return

        # Wait 500ms for file to finish writing
        time.sleep(0.5)
        asyncio.run(self.process_new_invoice(path))

    async def process_new_invoice(self, invoice_path: Path):
        db = self.db_factory()
        try:
            # 1. Log file detection
            watched = WatchedFile(filename=invoice_path.name, status="MATCHING")
            db.add(watched); db.commit()

            # 2. Extract supplier name from PDF
            supplier_name = await extract_supplier_from_invoice(invoice_path)
            watched.supplier_name_extracted = supplier_name

            # 3. Match to contract
            contract = find_matching_contract(supplier_name, db)

            if not contract:
                watched.status = "UNMATCHED"
                shutil.move(str(invoice_path), str(UNMATCHED_DIR / invoice_path.name))
                logger.warning(f"No contract match for: {supplier_name}")
                db.commit()
                return

            watched.matched_contract_id = contract.id
            watched.status = "PROCESSING"
            db.commit()

            # 4. Copy files to upload directory
            invoice_file_id = await copy_to_upload_dir(invoice_path)
            contract_file_id = contract.id

            # 5. Trigger audit pipeline (same as manual POST /api/audit/run)
            audit_id = await trigger_audit_pipeline(
                contract_file_id=contract_file_id,
                invoice_file_ids=[invoice_file_id],
                db=db
            )
            watched.audit_id = audit_id
            watched.status = "COMPLETE"
            watched.processed_at = datetime.utcnow()

            # 6. Move to processed
            shutil.move(
                str(invoice_path),
                str(PROCESSED_DIR / f"{audit_id}_{invoice_path.name}")
            )
            db.commit()

        except Exception as e:
            watched.status = "FAILED"
            watched.error_detail = str(e)
            db.commit()
            logger.error(f"Auto-audit failed for {invoice_path.name}: {e}")
        finally:
            db.close()


async def extract_supplier_from_invoice(path: Path) -> str:
    """
    Extract supplier name from the first page of the invoice PDF.
    Use Gemini with a short focused prompt — not the full Invoice Extractor agent.
    Prompt: "Read this invoice text and return ONLY the supplier/vendor company name.
             Return just the name, nothing else."
    """
    text = extract_pdf_text(path)[:2000]  # first 2000 chars only
    # One LLM call → plain string response
    ...


def find_matching_contract(supplier_name: str, db: Session) -> Optional[Contract]:
    """
    Step 1: Exact match on contracts.supplier_name (case-insensitive)
    Step 2: Check contracts.supplier_aliases JSON array
    Step 3: Partial match — supplier_name contains or is contained by contract name
    Returns None if no match.
    """
    # Exact
    contract = db.query(Contract).filter(
        func.lower(Contract.supplier_name) == supplier_name.lower(),
        Contract.is_active == 1
    ).first()
    if contract: return contract

    # Alias check
    all_contracts = db.query(Contract).filter(Contract.is_active == 1).all()
    for c in all_contracts:
        aliases = json.loads(c.supplier_aliases or "[]")
        if any(a.lower() == supplier_name.lower() for a in aliases):
            return c

    # Partial match
    for c in all_contracts:
        if (supplier_name.lower() in c.supplier_name.lower() or
            c.supplier_name.lower() in supplier_name.lower()):
            return c

    return None


def start_file_watcher(db_session_factory, pipeline_runner) -> Observer:
    """Call this from FastAPI startup event."""
    WATCH_DIR.mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)
    UNMATCHED_DIR.mkdir(exist_ok=True)

    handler = InvoiceFileHandler(db_session_factory, pipeline_runner)
    observer = Observer()
    observer.schedule(handler, str(WATCH_DIR), recursive=False)
    observer.start()
    logger.info(f"File watcher started on {WATCH_DIR.resolve()}")
    return observer
```

### Step 4: Wire into FastAPI startup/shutdown

```python
# backend/main.py
_observer = None

@app.on_event("startup")
async def startup():
    global _observer
    _observer = start_file_watcher(get_db, run_audit_pipeline)

@app.on_event("shutdown")
async def shutdown():
    if _observer:
        _observer.stop()
        _observer.join()
```

### Step 5: New API endpoints

```
# Contract Library (minimal)
POST   /api/contracts                 Upload + register a contract
GET    /api/contracts                 List all contracts in library
DELETE /api/contracts/{id}            Remove from library
PATCH  /api/contracts/{id}/aliases    Add supplier aliases

# Auto-Audit monitoring
GET    /api/watcher/status            {watching: bool, watch_dir: str, queue_count: int}
POST   /api/watcher/pause            Pause the file watcher
POST   /api/watcher/resume           Resume the file watcher
GET    /api/watcher/history          List recent watched_files records
GET    /api/watcher/unmatched        List files in unmatched/ folder
POST   /api/watcher/retry/{filename} Manually retry an unmatched file with a contract_id
```

## WHAT TO BUILD — FRONTEND

### Page 1: frontend/src/pages/ContractLibrary.jsx (/library)

```
Header: "Contract Library" + "Add Contract" button

Add Contract modal:
  - Drag-drop PDF upload zone
  - Supplier Name field (text input)
  - Supplier Aliases field (comma-separated, e.g. "Apex, Apex Ltd, APEX")
  - [Upload & Register] button
  → POST /api/contracts

Contract list table:
  Columns: Supplier Name | Aliases | Uploaded | Status | Actions
  Actions: [Add Alias] [Archive] [View Audits]
```

### Page 2: frontend/src/pages/AutoAudit.jsx (/auto-audit)

```
Section 1 — Watcher Status card:
  Large status indicator: 👁 Watching / ⏸ Paused
  Watch folder path: ./watched_invoices/
  [Pause Watcher] / [Resume Watcher] button
  Refresh every 5 seconds

Section 2 — Processing Queue:
  List of files currently being processed (status = MATCHING or PROCESSING)
  Show: filename, detected time, current status, matched supplier

Section 3 — Recent History table:
  Columns: File | Detected | Supplier Found | Contract Matched | Status | Audit
  Status badges: COMPLETE (green) | FAILED (red) | UNMATCHED (amber)
  Audit column: link to full audit report if status = COMPLETE

Section 4 — Unmatched Files:
  List of files in unmatched/ folder
  For each: filename, detected_at, supplier_name_extracted
  [Manually Match] button → dropdown of all contracts in library
    → POST /api/watcher/retry/{filename} with selected contract_id

Section 5 — Setup instructions card (shown when library is empty):
  Step 1: Add your supplier contracts to the Contract Library
  Step 2: Drop invoice PDFs into: [path to watched_invoices folder]
  Step 3: ProcureAI detects and audits them automatically
```

Add /library and /auto-audit routes to App.jsx.
Add "Library" and "Auto-Audit" links to Navbar.

## IMPLEMENTATION ORDER

1. DB migration — add contracts table + watched_files table
2. Create watched_invoices/ + processed/ + unmatched/ folders
3. backend/services/file_watcher.py — full watcher service
4. Wire startup/shutdown in main.py
5. backend/api/routes/contracts.py — minimal Contract Library endpoints
6. backend/api/routes/watcher.py — watcher status + history endpoints
7. Register both routers in main.py
8. frontend/src/pages/ContractLibrary.jsx
9. frontend/src/pages/AutoAudit.jsx
10. Add routes + Navbar links

## DONE WHEN

- Drop a PDF into watched_invoices/ → audit triggers automatically within 3 seconds
- File correctly matched when supplier name in invoice matches contract library
  (exact match AND partial match both work)
- COMPLETE files appear in processed/ with audit_id prefix
- UNMATCHED files appear in unmatched/ folder with log entry in DB
- Manually retrying an unmatched file with a selected contract triggers the audit
- Pausing the watcher stops new files from being processed
- Resuming picks up any files added while paused
- Contract Library correctly lists all uploaded contracts with aliases
- Auto-Audit history page shows all past automatic audit runs

Do not implement email inbox watching (IMAP) yet — folder watching only.
Do not implement multi-user contract ownership yet.
Do not implement contract expiry date handling yet.

---
END OF PROMPT 3
---

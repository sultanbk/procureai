# SupplierGuard — Layer 4 Implementation Prompts
# Feature: Make it a Platform
# Five prompts — paste each into a fresh AI session independently.
# Build in order: Prompt 1 → Prompt 2 → Prompt 3 → Prompt 4 → Prompt 5
# Layers 1, 2, and 3 must be complete before starting Layer 4.
# NOTE: A minimal Contract Library was already built in Layer 2 Prompt 3.
#       Prompt 3 in this layer expands it into the full version.

---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 1 OF 5
# FEATURE: Recovery Tracker
# WHAT IT BUILDS: A kanban-style dispute lifecycle tracker per
#                 finding. Tracks: Identified → Disputed → Acknowledged
#                 → Credit Received → Closed. Shows actual ₹ recovered
#                 vs. identified leakage. The ROI proof of SupplierGuard.
# EFFORT: 2 days | DB extension + kanban UI + recovery KPI dashboard
# WHY FIRST: Highest demo impact. "We identified ₹2.3M and recovered
#            ₹1.8M (78%)" is the sentence that justifies this entire system.
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building SupplierGuard — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. Layers 1, 2, and 3
are all complete. I am now adding the Recovery Tracker — Layer 4, Prompt 1.

## WHAT THIS FEATURE DOES

Every Discrepancy finding in every audit report has a lifecycle after it
is identified. Right now that lifecycle exists only in email threads and
spreadsheets. The Recovery Tracker brings it into SupplierGuard.

Per finding, the user can track:
  IDENTIFIED → DISPUTED → ACKNOWLEDGED → CREDIT_RECEIVED → CLOSED

Additional states:
  REJECTED   — supplier refused the dispute
  ACCEPTED   — company decided to accept (waive) the finding

The Recovery Dashboard shows across all audits:
- Total leakage identified (all findings, all time)
- Total amount disputed (findings where dispute was raised)
- Total amount recovered (credit_received_amount, all CREDIT_RECEIVED findings)
- Recovery rate: (recovered / identified) × 100
- Supplier-level recovery breakdown

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2
Frontend: React + Vite + Tailwind CSS
The audits table stores discrepancies as JSON. Each Discrepancy has:
  finding_id, invoice_id, line_id, rule_id, discrepancy_type,
  delta (negative = overcharge), severity, recommendation.
The dispute letter generator (Layer 2 Prompt 1) already exists.

## WHAT TO BUILD — BACKEND

### Step 1: finding_recovery table

```sql
CREATE TABLE finding_recovery (
    id                    TEXT PRIMARY KEY,  -- "rec_{finding_id}"
    audit_id              TEXT NOT NULL,
    finding_id            TEXT NOT NULL,     -- matches Discrepancy.finding_id
    supplier_name         TEXT NOT NULL,
    discrepancy_type      TEXT NOT NULL,
    identified_amount     REAL NOT NULL,     -- abs(delta) at audit time
    disputed_amount       REAL,              -- amount formally disputed
    credit_received_amount REAL DEFAULT 0,  -- actual amount recovered
    status                TEXT DEFAULT 'IDENTIFIED',
    -- IDENTIFIED | DISPUTED | ACKNOWLEDGED | CREDIT_RECEIVED | CLOSED
    -- | REJECTED | ACCEPTED
    dispute_letter_sent   INTEGER DEFAULT 0, -- 0 or 1
    dispute_sent_at       DATETIME,
    supplier_response     TEXT,              -- free text notes
    credit_note_reference TEXT,              -- supplier's credit note number
    resolution_notes      TEXT,
    created_at            DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audit_id) REFERENCES audits(id)
);
```

### Step 2: Auto-populate on audit completion

After Agent 4 (Report Generator) writes the AuditReport to DB,
automatically create one finding_recovery row per Discrepancy
with recommendation == "DISPUTE" or "ESCALATE".
Status starts as IDENTIFIED. identified_amount = abs(finding.delta).

```python
# backend/services/recovery_tracker.py

def initialise_recovery_records(
    audit_id: str,
    audit_report: AuditReport,
    db: Session
) -> None:
    """
    Called after each audit completes.
    Creates finding_recovery rows for actionable findings.
    Skips findings with recommendation == "MONITOR" or "ACCEPT".
    """
    for finding in audit_report.discrepancies:
        if finding.recommendation not in ("DISPUTE", "ESCALATE"):
            continue

        record_id = f"rec_{finding.finding_id}"
        existing = db.query(FindingRecovery).filter_by(id=record_id).first()
        if existing:
            continue  # already exists from a previous run

        db.add(FindingRecovery(
            id=record_id,
            audit_id=audit_id,
            finding_id=finding.finding_id,
            supplier_name=audit_report.summary.supplier_name,
            discrepancy_type=finding.discrepancy_type,
            identified_amount=float(abs(finding.delta)),
            status="IDENTIFIED"
        ))
    db.commit()
```

### Step 3: Recovery aggregation service

```python
def get_recovery_summary(db: Session) -> RecoverySummary:
    records = db.query(FindingRecovery).all()

    total_identified  = sum(r.identified_amount for r in records)
    total_disputed    = sum(r.disputed_amount or r.identified_amount
                            for r in records if r.status != "IDENTIFIED")
    total_recovered   = sum(r.credit_received_amount or 0
                            for r in records
                            if r.status in ("CREDIT_RECEIVED", "CLOSED"))
    recovery_rate     = (
        (total_recovered / total_identified * 100)
        if total_identified > 0 else 0.0
    )

    by_status = defaultdict(lambda: {"count": 0, "amount": 0.0})
    for r in records:
        by_status[r.status]["count"]  += 1
        by_status[r.status]["amount"] += r.identified_amount

    by_supplier = defaultdict(lambda: {"identified": 0.0, "recovered": 0.0})
    for r in records:
        by_supplier[r.supplier_name]["identified"] += r.identified_amount
        by_supplier[r.supplier_name]["recovered"]  += (
            r.credit_received_amount or 0.0
        )

    return RecoverySummary(
        total_identified=Decimal(str(round(total_identified, 2))),
        total_disputed=Decimal(str(round(total_disputed, 2))),
        total_recovered=Decimal(str(round(total_recovered, 2))),
        recovery_rate=round(recovery_rate, 1),
        by_status=dict(by_status),
        by_supplier=dict(by_supplier),
        total_findings=len(records)
    )
```

### Step 4: API endpoints (backend/api/routes/recovery.py)

```
GET  /api/recovery/summary
     Returns RecoverySummary (KPI dashboard data)

GET  /api/recovery/findings
     Query params: status, supplier_name, audit_id
     Returns paginated list of FindingRecovery records
     with full Discrepancy detail (joined from audit discrepancies JSON)

PATCH /api/recovery/{record_id}/status
     Request: {
       status:                str,   -- new status value
       disputed_amount:       float | null,
       credit_received_amount:float | null,
       supplier_response:     str | null,
       credit_note_reference: str | null,
       resolution_notes:      str | null
     }
     Updates status + any provided fields.
     Sets updated_at = now().
     Validates status transitions:
       IDENTIFIED → DISPUTED only
       DISPUTED → ACKNOWLEDGED | REJECTED
       ACKNOWLEDGED → CREDIT_RECEIVED | REJECTED
       CREDIT_RECEIVED → CLOSED
       REJECTED → DISPUTED (allow re-dispute)
       ACCEPTED → CLOSED

PATCH /api/recovery/{record_id}/mark-disputed
     Shortcut: sets status=DISPUTED, dispute_letter_sent=1,
               dispute_sent_at=now()
     Called when user sends a dispute letter

GET  /api/recovery/audit/{audit_id}
     All recovery records for a specific audit
     (shown on AuditReport page)
```

### Step 5: Pydantic models

```python
class FindingRecoveryRecord(BaseModel):
    id:                     str
    audit_id:               str
    finding_id:             str
    supplier_name:          str
    discrepancy_type:       str
    identified_amount:      Decimal
    disputed_amount:        Optional[Decimal]
    credit_received_amount: Decimal
    status:                 Literal[
                              "IDENTIFIED","DISPUTED","ACKNOWLEDGED",
                              "CREDIT_RECEIVED","CLOSED","REJECTED","ACCEPTED"
                            ]
    dispute_letter_sent:    bool
    dispute_sent_at:        Optional[str]
    supplier_response:      Optional[str]
    credit_note_reference:  Optional[str]
    resolution_notes:       Optional[str]
    created_at:             str
    updated_at:             str

class RecoverySummary(BaseModel):
    total_identified:  Decimal
    total_disputed:    Decimal
    total_recovered:   Decimal
    recovery_rate:     float        # percentage 0–100
    total_findings:    int
    by_status:         dict         # {status: {count, amount}}
    by_supplier:       dict         # {supplier: {identified, recovered}}
```

## WHAT TO BUILD — FRONTEND

### Page: frontend/src/pages/Recovery.jsx (/recovery)

**Section 1 — KPI Cards (4 cards)**
```
Card 1: Total Leakage Identified
  Large ₹ number in red. Subtitle: "across X findings"

Card 2: Total Disputed
  ₹ number in amber. Subtitle: "X findings disputed"

Card 3: Total Recovered
  ₹ number in green. Subtitle: "X findings resolved"

Card 4: Recovery Rate
  Large % number. Color: green ≥70%, amber 40–69%, red <40%
  Subtitle: "of identified leakage recovered"
```

**Section 2 — Status Pipeline (visual funnel)**
```
Show counts at each stage as a horizontal flow:
IDENTIFIED → DISPUTED → ACKNOWLEDGED → CREDIT_RECEIVED → CLOSED
  [12]           [8]          [5]            [3]            [2]
Plus: REJECTED [1]  ACCEPTED [1] shown below as side branches.
Use a simple horizontal bar with counts — not a true funnel chart.
Color each stage consistently across the app.
```

**Section 3 — Findings Table (filterable)**
```
Filters: By Supplier | By Status | By Discrepancy Type

Columns:
  Supplier | Finding | Type | Identified ₹ | Recovered ₹ | Status | Actions

Status badge colors:
  IDENTIFIED:      gray
  DISPUTED:        blue
  ACKNOWLEDGED:    amber
  CREDIT_RECEIVED: green
  CLOSED:          dark green
  REJECTED:        red
  ACCEPTED:        purple

Actions per row (dropdown):
  → Mark as Disputed     (IDENTIFIED only)
  → Mark Acknowledged    (DISPUTED only)
  → Enter Credit Amount  (ACKNOWLEDGED only) — opens inline form
  → Mark Closed          (CREDIT_RECEIVED only)
  → Mark Rejected        (DISPUTED or ACKNOWLEDGED)
  → Accept Finding       (any non-terminal status)
  → Add Notes            (any status)
```

**"Enter Credit Amount" inline form:**
```
Appears inline below the row when clicked.
Fields:
  Credit Amount Received: ₹ [number input]
  Credit Note Reference:  [text input]
  Notes:                  [textarea]
[Save] → PATCH /api/recovery/{id}/status with status=CREDIT_RECEIVED
```

**Section 4 — Recovery by Supplier table**
```
Columns: Supplier | Identified ₹ | Disputed ₹ | Recovered ₹ | Recovery Rate %
Sorted by identified amount descending.
Recovery rate bar: thin colored progress bar in the cell.
```

### Also add to AuditReport.jsx:

Below the DiscrepancyTable, add a "Recovery Status" section:
```
For each DISPUTE/ESCALATE finding: show its current recovery status
as an inline badge with a [Update Status] dropdown.
This lets users update status directly from the audit report page.
```

### Also: wire dispute letter into recovery tracker

When user clicks "Generate Dispute Letter" and downloads it,
call PATCH /api/recovery/{record_id}/mark-disputed for each
included finding. This auto-advances those findings to DISPUTED.

## IMPLEMENTATION ORDER

1. DB migration — add finding_recovery table
2. backend/services/recovery_tracker.py — initialise_recovery_records() +
   get_recovery_summary()
3. Wire initialise_recovery_records() into report_generator agent completion
4. backend/api/routes/recovery.py — all endpoints
5. Register recovery router in main.py
6. frontend/src/api/audit.js — getRecoverySummary(), getFindings(),
   updateFindingStatus(), markDisputed()
7. frontend/src/pages/Recovery.jsx — full page
8. Update AuditReport.jsx — add recovery status section
9. Wire dispute letter → mark-disputed call

## DONE WHEN

- Running a new audit with DISPUTE findings → finding_recovery rows auto-created
- Manual status update (IDENTIFIED → DISPUTED) persists correctly
- Entering ₹8,500 credit received → total_recovered increases by ₹8,500
- Recovery rate recalculates correctly after each status update
- Recovery Rate card shows correct percentage (recovered / identified × 100)
- Invalid status transitions are rejected (e.g. IDENTIFIED → CREDIT_RECEIVED)
- Supplier breakdown table shows correct per-supplier identified vs recovered
- AuditReport page shows recovery badges matching the recovery table data

Do not build automated credit note parsing yet.
Do not build email threading for supplier responses yet.

---
END OF PROMPT 1
---


---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 2 OF 5
# FEATURE: Role-Based Access Control (RBAC)
# WHAT IT BUILDS: User authentication with JWT. Four roles: Admin,
#                 Auditor, Approver, Viewer. Approval workflow before
#                 dispute letters are sent. Route guards in React.
# EFFORT: 3–4 days | JWT auth + role middleware + approval workflow
# WHY SECOND: All platform features need auth. Build this before
#             Supplier Portal (Prompt 4) which adds external users.
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building SupplierGuard — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. Layers 1, 2, 3,
and Recovery Tracker (Layer 4 Prompt 1) are all complete.

I am now adding Role-Based Access Control — Layer 4, Prompt 2.

## WHAT THIS FEATURE DOES

Currently SupplierGuard is single-user with no authentication. This adds:

Four roles:
  ADMIN    — full access, manage users, configure system
  AUDITOR  — run audits, view reports, generate dispute letters
  APPROVER — review and approve disputes before they are sent
  VIEWER   — read-only access to reports and dashboards

Approval workflow:
  Auditor generates a dispute letter
  → Status changes to "PENDING_APPROVAL" not "DISPUTED"
  → Approver reviews the letter and findings
  → Approver clicks "Approve" → status advances to "DISPUTED"
  → OR Approver clicks "Reject" → letter goes back to Auditor with notes

JWT auth:
  POST /api/auth/login → returns {access_token, token_type, user}
  All protected routes require: Authorization: Bearer {token}
  Token expiry: 8 hours
  No refresh tokens in MVP

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2
Frontend: React + Vite + Tailwind CSS
python-jose and passlib are available (add to requirements.txt if missing).
All existing routes are currently unprotected — add protection in this prompt.

## WHAT TO BUILD — BACKEND

### Step 1: users table

```sql
CREATE TABLE users (
    id              TEXT PRIMARY KEY,   -- "usr_abc123"
    email           TEXT UNIQUE NOT NULL,
    full_name       TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'VIEWER',
    -- ADMIN | AUDITOR | APPROVER | VIEWER
    is_active       INTEGER DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login      DATETIME
);

-- Seed one admin user on first run:
-- email: admin@suppliergaurd.com
-- password: admin123 (hashed)
-- role: ADMIN
```

### Step 2: approval_requests table

```sql
CREATE TABLE approval_requests (
    id                  TEXT PRIMARY KEY,   -- "apr_abc123"
    audit_id            TEXT NOT NULL,
    dispute_letter_text TEXT NOT NULL,
    finding_ids         TEXT NOT NULL,      -- JSON array of finding_ids
    total_disputed      REAL NOT NULL,
    requested_by        TEXT NOT NULL,      -- user_id
    status              TEXT DEFAULT 'PENDING',
    -- PENDING | APPROVED | REJECTED
    reviewed_by         TEXT,               -- user_id of approver
    review_notes        TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at         DATETIME,
    FOREIGN KEY (audit_id) REFERENCES audits(id)
);
```

### Step 3: Auth service (backend/services/auth_service.py)

```python
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM  = "HS256"
TOKEN_EXPIRE_HOURS = 8

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": user_id, "role": role, "exp": expire},
        SECRET_KEY, algorithm=ALGORITHM
    )

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

### Step 4: FastAPI dependencies (backend/api/dependencies.py)

```python
from fastapi import Depends, HTTPException, Header
from backend.services.auth_service import decode_token

async def get_current_user(authorization: str = Header(...)) -> dict:
    """Extract and validate JWT from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    return {"user_id": payload["sub"], "role": payload["role"]}

def require_role(*allowed_roles: str):
    """Factory: returns a dependency that checks role."""
    async def checker(user=Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                403,
                f"Role '{user['role']}' cannot access this endpoint. "
                f"Required: {allowed_roles}"
            )
        return user
    return checker

# Convenience dependencies
require_admin    = require_role("ADMIN")
require_auditor  = require_role("ADMIN", "AUDITOR")
require_approver = require_role("ADMIN", "APPROVER")
require_viewer   = require_role("ADMIN", "AUDITOR", "APPROVER", "VIEWER")
```

### Step 5: Auth endpoints (backend/api/routes/auth.py)

```
POST /api/auth/login
  Request: {email: str, password: str}
  Response: {access_token: str, token_type: "bearer",
             user: {id, email, full_name, role}}
  Sets last_login on user record.

GET  /api/auth/me
  Protected. Returns current user profile.

POST /api/auth/users            [ADMIN only]
  Create a new user.
  Request: {email, full_name, password, role}

GET  /api/auth/users            [ADMIN only]
  List all users.

PATCH /api/auth/users/{user_id} [ADMIN only]
  Update role or active status.

PATCH /api/auth/me/password
  Change own password.
  Request: {current_password, new_password}
```

### Step 6: Protect all existing routes

Apply dependencies to existing routers:

```python
# audit routes
@router.post("/run", dependencies=[Depends(require_auditor)])
@router.get("/{audit_id}", dependencies=[Depends(require_viewer)])
@router.delete("/{audit_id}", dependencies=[Depends(require_admin)])

# recovery routes
@router.patch("/{record_id}/status", dependencies=[Depends(require_auditor)])

# dispute routes
@router.post("/generate", dependencies=[Depends(require_auditor)])

# analytics routes — viewer and above
@router.get("/overview", dependencies=[Depends(require_viewer)])

# settings routes — admin only
@router.get("/notifications", dependencies=[Depends(require_admin)])
@router.put("/notifications", dependencies=[Depends(require_admin)])
```

### Step 7: Approval workflow endpoints (backend/api/routes/approvals.py)

```
POST /api/approvals
  [AUDITOR] Submit a dispute letter for approval.
  Request: {audit_id, dispute_letter_text, finding_ids, total_disputed}
  Creates approval_request record with status=PENDING.
  Sends notification to all APPROVER users (via notifier.py).
  Returns: {approval_id, status: "PENDING"}

GET  /api/approvals
  [APPROVER, ADMIN] List all pending approval requests.

GET  /api/approvals/{approval_id}
  Full approval request with letter text and findings.

POST /api/approvals/{approval_id}/approve
  [APPROVER, ADMIN] Approve the dispute letter.
  Sets status=APPROVED, reviewed_by, reviewed_at.
  Calls mark-disputed on all finding_ids in the request.
  Returns: {status: "APPROVED"}

POST /api/approvals/{approval_id}/reject
  [APPROVER, ADMIN] Reject with notes.
  Request: {review_notes: str}
  Sets status=REJECTED.
  Sends notification back to requesting AUDITOR.
```

## WHAT TO BUILD — FRONTEND

### Login page (frontend/src/pages/Login.jsx)

```
Centered card:
  SupplierGuard logo/name
  Email input
  Password input
  [Sign In] button
  Error message if login fails

On success:
  Store {access_token, user} in localStorage
  Redirect to /
```

### Auth context (frontend/src/context/AuthContext.jsx)

```javascript
const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() =>
    JSON.parse(localStorage.getItem("sg_user") || "null")
  )
  const [token, setToken] = useState(() =>
    localStorage.getItem("sg_token") || null
  )

  const login = (tokenData) => {
    localStorage.setItem("sg_token", tokenData.access_token)
    localStorage.setItem("sg_user", JSON.stringify(tokenData.user))
    setToken(tokenData.access_token)
    setUser(tokenData.user)
  }

  const logout = () => {
    localStorage.removeItem("sg_token")
    localStorage.removeItem("sg_user")
    setToken(null); setUser(null)
  }

  // Add token to all API calls
  const authFetch = async (url, options = {}) => {
    return fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
        ...options.headers
      }
    })
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, authFetch }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
```

### Route guards

```jsx
// frontend/src/components/ProtectedRoute.jsx
export function ProtectedRoute({ children, allowedRoles }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" />
  if (allowedRoles && !allowedRoles.includes(user.role))
    return <Navigate to="/unauthorized" />
  return children
}

// In App.jsx:
<Route path="/settings" element={
  <ProtectedRoute allowedRoles={["ADMIN"]}>
    <Settings />
  </ProtectedRoute>
} />
```

### Navbar changes

Show user name + role badge in top right.
[Logout] button clears auth context + redirects to /login.
Hide menu items the current role cannot access:
  Settings: ADMIN only
  User Management: ADMIN only
  Approve Disputes: APPROVER and ADMIN only

### Approvals page (frontend/src/pages/Approvals.jsx) [APPROVER/ADMIN]

```
List of pending approval requests:
  Each card shows: Audit | Supplier | Total Disputed | Requested By | Date

On click → expand full letter text in a modal:
  Full dispute letter text (read-only)
  Findings table (clause, charged, expected, delta)
  [Approve ✓] [Reject ✗] buttons
  Reject requires notes input before confirming.
```

### Dispute Letter Generator update

Replace "Download PDF" button with:
  [Submit for Approval →]  (AUDITOR sees this)
  [Approve & Download →]   (APPROVER/ADMIN sees this — skip approval workflow)

## IMPLEMENTATION ORDER

1. DB migration — add users table + approval_requests table + seed admin user
2. backend/services/auth_service.py — passwords + JWT
3. backend/api/dependencies.py — get_current_user + require_role
4. backend/api/routes/auth.py — login + user management endpoints
5. Apply dependencies to ALL existing routes
6. backend/api/routes/approvals.py — approval workflow endpoints
7. Register auth + approvals routers in main.py
8. frontend/src/context/AuthContext.jsx — auth context + authFetch
9. Update ALL frontend API calls to use authFetch (not raw fetch)
10. frontend/src/pages/Login.jsx
11. frontend/src/components/ProtectedRoute.jsx
12. Update App.jsx — wrap routes with ProtectedRoute
13. Update Navbar — user display + logout
14. frontend/src/pages/Approvals.jsx
15. Update DisputeLetterModal.jsx — submit for approval flow

## DONE WHEN

- /api/audit/run returns 401 without a valid Bearer token
- Admin user can login with seeded credentials
- Admin can create AUDITOR, APPROVER, VIEWER users via /api/auth/users
- VIEWER cannot access /api/settings/notifications (returns 403)
- AUDITOR submitting a dispute letter creates an approval_request (PENDING)
- APPROVER sees the request, reviews letter, clicks Approve → findings marked DISPUTED
- APPROVER rejects with notes → Auditor sees rejection reason
- React routes redirect to /login if not authenticated
- /settings page shows 403 redirect for non-ADMIN roles
- Logout clears localStorage and redirects to /login

Do not implement OAuth (Google/GitHub) yet.
Do not implement refresh tokens yet.
Do not implement password reset via email yet.

---
END OF PROMPT 2
---


---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 3 OF 5
# FEATURE: Full Contract Library
# WHAT IT BUILDS: Expands the minimal Contract Library (built in
#                 Layer 2 Prompt 3) into the full version with contract
#                 versioning, expiry tracking, renewal alerts,
#                 full-text search, and audit history per contract.
# EFFORT: 2–3 days | DB expansion + versioning + expiry alerts + search
# PREREQUISITE: Minimal Contract Library from Layer 2 Prompt 3 must exist.
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building SupplierGuard — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. Layers 1, 2, 3,
Recovery Tracker, and RBAC are all complete.

In Layer 2 Prompt 3 (Scheduled Auto-Audit), I built a minimal Contract Library
with this schema:
```sql
CREATE TABLE contracts (
    id                TEXT PRIMARY KEY,
    supplier_name     TEXT NOT NULL,
    supplier_aliases  TEXT,            -- JSON array
    contract_file_path TEXT NOT NULL,
    original_filename  TEXT,
    uploaded_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active         INTEGER DEFAULT 1
);
```

I am now expanding this into the Full Contract Library — Layer 4, Prompt 3.

## WHAT THIS FEATURE DOES

The full Contract Library is the central repository for all supplier contracts.
It adds on top of the minimal version:

1. Contract versioning — multiple versions per supplier, one marked ACTIVE
2. Expiry tracking — contract end dates with renewal alert system
3. Key terms summary — AI-extracted summary card per contract
4. Full-text search — search across all contracts by clause content
5. Audit history per contract — all audits run against this contract
6. Contract health score — how compliant has this contract been?

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2 + Gemini
Frontend: React + Vite + Tailwind CSS
Auth: JWT (built in Layer 4 Prompt 2). All routes need auth dependencies.
The contracts table already exists (minimal version).
The contract_chunks table exists (built in Layer 3 Prompt 1 — Contract Q&A).
BM25 retrieval over contract_chunks already implemented.

## WHAT TO BUILD — BACKEND

### Step 1: Alter contracts table (add new columns via migration)

```sql
ALTER TABLE contracts ADD COLUMN contract_start_date TEXT;
ALTER TABLE contracts ADD COLUMN contract_end_date   TEXT;  -- ISO date
ALTER TABLE contracts ADD COLUMN contract_value       REAL;  -- total contract value INR
ALTER TABLE contracts ADD COLUMN version_number       TEXT DEFAULT '1.0';
ALTER TABLE contracts ADD COLUMN version_notes        TEXT;
ALTER TABLE contracts ADD COLUMN is_current_version   INTEGER DEFAULT 1;
ALTER TABLE contracts ADD COLUMN parent_contract_id   TEXT;  -- for version chain
ALTER TABLE contracts ADD COLUMN key_terms_summary    TEXT;  -- JSON (KeyTermsSummary)
ALTER TABLE contracts ADD COLUMN renewal_alert_days   INTEGER DEFAULT 30;
    -- alert X days before expiry
ALTER TABLE contracts ADD COLUMN renewal_alert_sent   INTEGER DEFAULT 0;
ALTER TABLE contracts ADD COLUMN uploaded_by          TEXT;  -- user_id
```

### Step 2: Key Terms Summary extraction

After uploading a new contract and running Agent 1 (Contract Parser),
extract a key terms summary using one focused LLM call:

```python
# backend/services/contract_library_service.py

async def extract_key_terms_summary(
    rulebook: ContractRulebook,
    contract_text: str
) -> KeyTermsSummary:
    """
    One LLM call. Returns structured summary of the most important
    contract terms for quick at-a-glance review.
    """
    # Returns:
    # {
    #   "contract_type": str,        -- "Logistics MSA" | "SaaS Subscription" | etc.
    #   "payment_terms": str,        -- "Net-30" | "Net-10 with 2% discount"
    #   "notice_period_days": int,   -- termination notice period
    #   "auto_renewal": bool,
    #   "governing_law": str,        -- jurisdiction
    #   "liability_cap": str,        -- liability cap amount or "Not specified"
    #   "key_obligations": list[str] -- top 3–5 obligations in plain English
    # }

class KeyTermsSummary(BaseModel):
    contract_type:       str
    payment_terms:       str
    notice_period_days:  Optional[int]
    auto_renewal:        bool
    governing_law:       Optional[str]
    liability_cap:       Optional[str]
    key_obligations:     list[str]
```

### Step 3: Expiry alert background job

Run every 24 hours using APScheduler (already installed for file watcher).

```python
# backend/services/expiry_checker.py

def check_contract_expiries(db: Session) -> None:
    """
    Find contracts expiring within renewal_alert_days.
    Send Slack/email alert (via notifier.py) if not already sent.
    """
    today = date.today()
    contracts = db.query(Contract).filter(
        Contract.is_active == 1,
        Contract.contract_end_date.isnot(None),
        Contract.renewal_alert_sent == 0
    ).all()

    for contract in contracts:
        end_date = date.fromisoformat(contract.contract_end_date)
        days_remaining = (end_date - today).days

        if days_remaining <= contract.renewal_alert_days:
            # Send alert
            message = (
                f"⏰ Contract Renewal Alert\n"
                f"Supplier: {contract.supplier_name}\n"
                f"Contract: {contract.original_filename}\n"
                f"Expires: {contract.contract_end_date} "
                f"({days_remaining} days remaining)\n"
                f"Action: Review and initiate renewal process."
            )
            # send via notifier.py Slack/email
            contract.renewal_alert_sent = 1

    db.commit()
```

### Step 4: Full-text search over contracts

```
GET /api/contracts/search?q={query}&supplier={supplier}

Uses BM25 retrieval over contract_chunks table (already built in Layer 3).
Returns: list of matching chunks with contract metadata.
Each result: {contract_id, supplier_name, section_header, chunk_text, score}
```

### Step 5: New and updated API endpoints

```
# Expand existing contracts router:

POST /api/contracts
  [AUDITOR+] Upload + register contract. Now accepts:
  - contract_start_date, contract_end_date, contract_value,
    version_notes, renewal_alert_days
  After upload: runs Agent 1 extraction + key_terms_summary extraction
  Returns full ContractRecord.

POST /api/contracts/{id}/new-version
  [AUDITOR+] Upload a new version of an existing contract.
  - Sets old version is_current_version=0
  - Creates new contract record with parent_contract_id={id}
  - Runs Agent 1 on new version
  - Runs contract comparison (Layer 3 Prompt 2) against previous version
  Returns: {new_contract_id, comparison_id}

GET /api/contracts
  Returns all CURRENT versions. Query params: supplier, expiring_within_days.

GET /api/contracts/{id}
  Full contract detail including key_terms_summary, version history,
  audit history (all audits where contract_file matches), health score.

GET /api/contracts/{id}/versions
  All versions of this contract in chronological order.

GET /api/contracts/{id}/audits
  All audits run using this contract. With total leakage per audit.

GET /api/contracts/expiring
  [VIEWER+] Contracts expiring within 60 days. For dashboard widget.

PATCH /api/contracts/{id}
  [AUDITOR+] Update metadata: end_date, renewal_alert_days, aliases, notes.

DELETE /api/contracts/{id}   (soft delete — sets is_active=0)
  [ADMIN only]

GET /api/contracts/search?q=...
  Full-text search across all contract chunks.
```

### Contract health score

```python
def compute_contract_health(contract_id: str, db: Session) -> float:
    """
    Average compliance score across all audits for this contract.
    Uses supplier_scores table filtered by audits linked to this contract.
    Returns 0–100 float.
    """
```

## WHAT TO BUILD — FRONTEND

### Expand ContractLibrary.jsx (/library)

**Top section — KPI cards:**
```
Total Active Contracts | Expiring Within 30 Days (⚠️ amber) |
Avg Contract Health Score | Total Contract Value (₹)
```

**Expiry Alert Banner:**
If any contracts expiring within 30 days:
```
⏰ 3 contracts expiring soon — [View Expiring Contracts]
```

**Contracts Table (expanded columns):**
```
Supplier | Version | Start Date | End Date | Days Left |
Health Score | Total Leakage | Audits | Actions
```

Days Left: color red (<14), amber (14–30), green (>30).
Health Score: colored badge (same green/amber/red as scorecard).

**Contract Detail Page (/library/{id})**

When clicking a contract row → opens detail page:

```
Section 1 — Header
  Supplier name, contract ID, version badge, active/archived status

Section 2 — Key Terms Summary Card
  contract_type | payment_terms | notice_period | auto_renewal badge
  governing_law | liability_cap
  Key obligations: bulleted list

Section 3 — Pricing Rules (from ContractRulebook)
  Table of all extracted rules: Rule ID | Type | Description | Clause

Section 4 — Contract Q&A Chat panel (reuse from Layer 3 Prompt 1)
  Same chat interface, already built — just embed it here too

Section 5 — Audit History
  Table of all audits for this contract:
  Date | Invoice Period | Leakage | Findings | Status | [View Report]

Section 6 — Version History
  Timeline of all versions with comparison links:
  v1.0 (2024-01-01) | v1.1 (2024-07-01) → [View Changes]

Section 7 — Upload New Version button
  Opens modal with PDF upload + version notes
```

**Full-text search bar** at top of library page:
```
[🔍 Search all contracts...]
→ GET /api/contracts/search?q=...
→ Shows matching clause excerpts with supplier + section context
→ Click result → opens contract detail page
```

## IMPLEMENTATION ORDER

1. DB migration — ALTER TABLE contracts to add new columns
2. backend/services/contract_library_service.py:
   a. extract_key_terms_summary()
   b. compute_contract_health()
3. backend/services/expiry_checker.py — register with APScheduler in main.py
4. backend/api/routes/contracts.py — expand all endpoints
5. frontend/src/api/audit.js — update all contract API calls
6. Update ContractLibrary.jsx — new KPI cards + expiry banner + expanded table
7. frontend/src/pages/ContractDetail.jsx — full detail page
8. Add /library/:id route to App.jsx
9. Wire search bar into library page

## DONE WHEN

- Uploading a contract with end_date = 25 days from now → appears in
  expiring contracts section with amber Days Left badge
- Expiry alert job marks renewal_alert_sent=1 after first alert
- Key terms summary shows correct payment_terms and contract_type
- Version history shows both v1.0 and v1.1 after uploading a new version
- [View Changes] links correctly to the comparison created at upload time
- Full-text search for "SLA" returns relevant clause chunks with context
- Contract health score matches the supplier's historical compliance

---
END OF PROMPT 3
---


---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 4 OF 5
# FEATURE: API + Webhook Export
# WHAT IT BUILDS: A public versioned REST API (/v1/) with API key auth
#                 so external systems can pull audit results. Plus
#                 per-audit webhook delivery so findings flow into
#                 SAP, Oracle, Notion, or any webhook endpoint.
# EFFORT: 1–2 days | API key table + /v1/ router + webhook delivery
# WHY FOURTH: Lowest complexity in Layer 4. Makes SupplierGuard
#             integrable. Enables enterprise adoption.
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building SupplierGuard — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. Layers 1–3, Recovery
Tracker, RBAC, and Full Contract Library are all complete.

I am now adding API + Webhook Export — Layer 4, Prompt 4.

## WHAT THIS FEATURE DOES

Two separate integration mechanisms:

1. PUBLIC REST API (/v1/)
   External systems query SupplierGuard audit data using an API key.
   No JWT — API keys only (simpler for server-to-server integration).
   Rate limited: 100 requests/hour per API key.

2. WEBHOOK DELIVERY
   After each audit completes, POST the AuditReport JSON to a
   configurable webhook URL. Per-audit webhook override supported.
   Signed with HMAC-SHA256 so receivers can verify authenticity.

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2
Frontend: React + Vite + Tailwind CSS
Auth: JWT (Layer 4 Prompt 2) — API uses separate API key auth.
httpx already installed (for outbound webhook POST).
All monetary Decimal values serialised as strings in JSON.

## WHAT TO BUILD — BACKEND

### Step 1: api_keys table

```sql
CREATE TABLE api_keys (
    id              TEXT PRIMARY KEY,       -- "key_abc123"
    name            TEXT NOT NULL,          -- "SAP Integration"
    key_hash        TEXT NOT NULL,          -- SHA256 hash of actual key
    key_prefix      TEXT NOT NULL,          -- first 8 chars shown in UI: "sg_live_"
    created_by      TEXT NOT NULL,          -- user_id
    is_active       INTEGER DEFAULT 1,
    last_used_at    DATETIME,
    request_count   INTEGER DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

API key format: `sg_live_{random_32_chars}`
Only the first 8 chars (`sg_live_`) stored in DB for display.
Full key shown ONCE at creation — never again.
DB stores SHA256 hash only.

```python
# backend/services/api_key_service.py
import secrets, hashlib

def generate_api_key() -> tuple[str, str]:
    """Returns (full_key, key_hash)"""
    random_part = secrets.token_urlsafe(32)
    full_key = f"sg_live_{random_part}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, key_hash

def verify_api_key(provided_key: str, db: Session) -> Optional[ApiKey]:
    """Verify provided key against stored hashes."""
    key_hash = hashlib.sha256(provided_key.encode()).hexdigest()
    key = db.query(ApiKey).filter_by(
        key_hash=key_hash, is_active=1
    ).first()
    if key:
        key.last_used_at = datetime.utcnow()
        key.request_count += 1
        db.commit()
    return key
```

### Step 2: webhook_configs table

```sql
CREATE TABLE webhook_configs (
    id              TEXT PRIMARY KEY,   -- "wh_abc123"
    name            TEXT NOT NULL,      -- "SAP Webhook"
    url             TEXT NOT NULL,
    secret          TEXT NOT NULL,      -- HMAC signing secret
    events          TEXT DEFAULT '["audit.complete"]',  -- JSON array
    -- events: "audit.complete" | "finding.critical" | "dispute.approved"
    is_active       INTEGER DEFAULT 1,
    created_by      TEXT NOT NULL,
    last_triggered  DATETIME,
    success_count   INTEGER DEFAULT 0,
    failure_count   INTEGER DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Step 3: Public API router (/v1/)

```python
# backend/api/routes/v1/__init__.py
# backend/api/routes/v1/audits.py
# backend/api/routes/v1/suppliers.py

from fastapi import APIRouter, Header, HTTPException, Depends
from backend.services.api_key_service import verify_api_key

v1_router = APIRouter(prefix="/v1", tags=["Public API v1"])

async def require_api_key(x_api_key: str = Header(...)) -> ApiKey:
    db = next(get_db())
    key = verify_api_key(x_api_key, db)
    if not key:
        raise HTTPException(401, "Invalid API key")
    return key

# Endpoints:

GET /v1/audits
  Query: supplier_name, status, from_date, to_date, limit (max 100)
  Returns: list of AuditSummary objects (no raw JSON blobs)

GET /v1/audits/{audit_id}
  Returns: full AuditReport JSON
  (same Pydantic model as internal API)

GET /v1/audits/{audit_id}/findings
  Returns: list of Discrepancy objects for this audit

GET /v1/suppliers
  Returns: list of suppliers with latest_score, total_leakage

GET /v1/suppliers/{supplier_name}/audits
  Returns: audit history for one supplier

GET /v1/recovery/summary
  Returns: RecoverySummary (total identified, disputed, recovered)

GET /v1/health
  Public — no API key required
  Returns: {status: "ok", version: "1.0"}
```

All /v1/ responses:
- Paginated with {data: [...], total: int, page: int, per_page: int}
- Decimal values as strings
- Dates as ISO 8601 strings

### Step 4: Webhook delivery service

```python
# backend/services/webhook_delivery.py

import hmac, hashlib, json
import httpx

async def deliver_webhook(
    event_type: str,
    payload: dict,
    db: Session
) -> None:
    """
    Find all active webhooks subscribed to event_type.
    Deliver payload to each. Fire-and-forget. Log success/failure.
    """
    configs = db.query(WebhookConfig).filter(
        WebhookConfig.is_active == 1
    ).all()

    for config in configs:
        events = json.loads(config.events)
        if event_type not in events:
            continue

        await _post_webhook(config, event_type, payload, db)


async def _post_webhook(
    config: WebhookConfig,
    event_type: str,
    payload: dict,
    db: Session
) -> None:
    body = json.dumps({
        "event":      event_type,
        "timestamp":  datetime.utcnow().isoformat(),
        "payload":    payload
    })

    # HMAC-SHA256 signature
    signature = hmac.new(
        config.secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type":         "application/json",
        "X-SupplierGuard-Event": event_type,
        "X-SupplierGuard-Sig":   f"sha256={signature}"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(config.url, content=body, headers=headers)
            resp.raise_for_status()
            config.success_count += 1
            config.last_triggered = datetime.utcnow()
    except Exception as e:
        config.failure_count += 1
        logger.error(f"Webhook delivery failed for {config.url}: {e}")

    db.commit()
```

Wire into report_generator agent:
```python
# After audit_report is written to DB:
asyncio.create_task(
    deliver_webhook(
        event_type="audit.complete",
        payload=audit_report.model_dump(),
        db=db
    )
)
```

Wire into approval workflow:
```python
# After approval approved:
asyncio.create_task(
    deliver_webhook("dispute.approved", {...}, db)
)
```

### Step 5: Management endpoints (backend/api/routes/integrations.py)

```
# API Key management [ADMIN only]
POST   /api/integrations/api-keys
  Request: {name: str}
  Returns: {key_id, full_key (shown once), prefix, name}
  -- full_key never stored, only shown at creation

GET    /api/integrations/api-keys
  Returns: list of {id, name, prefix, last_used_at, request_count, is_active}

DELETE /api/integrations/api-keys/{id}
  Deactivates the key (sets is_active=0)

# Webhook management [ADMIN only]
POST   /api/integrations/webhooks
  Request: {name, url, secret, events}
  Validates URL is reachable with a test ping.

GET    /api/integrations/webhooks
  Returns: all webhook configs with success/failure counts

PATCH  /api/integrations/webhooks/{id}
  Update URL, events, active status.

POST   /api/integrations/webhooks/{id}/test
  Sends a test payload to the webhook URL.
  Returns: {success: bool, status_code: int, response_time_ms: int}

DELETE /api/integrations/webhooks/{id}
```

## WHAT TO BUILD — FRONTEND

### Add Integrations section to Settings.jsx

New tab/section in Settings: "Integrations"

**API Keys subsection:**
```
[+ Create API Key] button → modal:
  Name: [text input, e.g. "SAP Integration"]
  [Generate Key] button

After generation — show ONCE screen:
  ⚠️ Copy this key now. It will never be shown again.
  [key value in monospace box] [Copy]

API Keys table:
  Name | Prefix | Last Used | Requests | Created | [Revoke]
```

**Webhooks subsection:**
```
[+ Add Webhook] button → form:
  Name:    [text input]
  URL:     [text input, type=url]
  Secret:  [text input — user provides their own]
  Events:  [checkboxes: ☑ audit.complete  ☐ finding.critical  ☐ dispute.approved]
  [Save & Test] → sends test ping, shows result

Webhooks table:
  Name | URL | Events | Last Triggered | Success | Failures | [Test] [Delete]
```

**API Documentation card:**
```
Collapsible section showing quick reference:
  Base URL: http://localhost:8000/v1
  Auth: X-API-Key: sg_live_...
  Example curl commands for each endpoint
```

## IMPLEMENTATION ORDER

1. DB migration — add api_keys + webhook_configs tables
2. backend/services/api_key_service.py — generate + verify
3. backend/services/webhook_delivery.py — deliver + sign
4. Wire webhook into report_generator + approvals
5. backend/api/routes/v1/ — public API router
6. backend/api/routes/integrations.py — management endpoints
7. Register all routers in main.py
8. Update Settings.jsx — add Integrations tab
9. Add API key creation modal with one-time display
10. Add webhook config form + test button

## DONE WHEN

- GET /v1/audits with valid X-API-Key returns paginated audit list
- GET /v1/audits with invalid key returns 401
- Completing an audit POSTs to all active webhooks within 5 seconds
- Webhook body is signed with HMAC-SHA256 (receiver can verify)
- Failed webhook increments failure_count, does not crash pipeline
- API key created in UI shows full key ONCE with copy button
- Revoking an API key → subsequent /v1/ calls with that key return 401
- Webhook test button shows correct status_code and response_time_ms

Do not implement rate limiting (request count tracked but not enforced in MVP).
Do not implement webhook retry with exponential backoff yet.

---
END OF PROMPT 4
---


---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 5 OF 5
# FEATURE: Supplier Self-Service Portal
# WHAT IT BUILDS: A separate login for suppliers. They see their own
#                 compliance score, view findings raised against them,
#                 respond to disputes, and submit corrected invoices.
#                 Turns SupplierGuard into a two-sided platform.
# EFFORT: 4–5 days | Supplier auth + read-only views + dispute response
# WHY LAST: Depends on all other Layer 4 features (RBAC, recovery
#           tracker, contract library) being in place first.
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building SupplierGuard — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. All previous layers
and Layer 4 Prompts 1–4 are complete (Recovery Tracker, RBAC, Contract Library,
API + Webhook Export).

I am now adding the Supplier Self-Service Portal — the final feature.

## WHAT THIS FEATURE DOES

A completely separate login and portal experience for suppliers. The main
SupplierGuard app is for the buying company (internal users). The Supplier
Portal is for the suppliers themselves.

When a dispute letter is approved and sent, the supplier receives an email
(via the alert engine) with a link to log into their portal. In the portal,
a supplier representative can:

1. View their compliance score and history
2. See all findings raised against them with full evidence
3. Respond to disputes: accept / contest / attach supporting documents
4. Submit a corrected invoice PDF
5. Track the status of each disputed finding
6. See their contract terms (read-only, the active contract from the library)

This is the feature that eliminates the email thread. Everything happens
in one tracked system.

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2 + Gemini
Frontend: React + Vite + Tailwind CSS
Auth: JWT (Layer 4 Prompt 2). Suppliers get a separate role: SUPPLIER.
The users table already exists — add SUPPLIER to the role enum.
The finding_recovery table, contracts table, and supplier_scores table exist.

## WHAT TO BUILD — BACKEND

### Step 1: supplier_users table and invite system

```sql
CREATE TABLE supplier_users (
    id               TEXT PRIMARY KEY,   -- "sup_usr_abc123"
    user_id          TEXT NOT NULL,      -- FK to users table (role=SUPPLIER)
    supplier_name    TEXT NOT NULL,      -- must match contracts.supplier_name
    company_name     TEXT NOT NULL,
    invited_by       TEXT NOT NULL,      -- internal user_id
    invite_token     TEXT,               -- for email invite link (expires 48h)
    invite_expires   DATETIME,
    portal_access    INTEGER DEFAULT 1,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Step 2: supplier_responses table

```sql
CREATE TABLE supplier_responses (
    id                  TEXT PRIMARY KEY,   -- "resp_abc123"
    finding_recovery_id TEXT NOT NULL,
    supplier_user_id    TEXT NOT NULL,
    response_type       TEXT NOT NULL,
        -- "ACCEPT" | "CONTEST" | "SUBMIT_CORRECTION"
    response_notes      TEXT,
    supporting_doc_path TEXT,             -- uploaded corrected invoice path
    submitted_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_by         TEXT,             -- internal user_id who reviewed
    review_status       TEXT DEFAULT 'PENDING',
        -- "PENDING" | "ACCEPTED" | "REJECTED"
    review_notes        TEXT,
    reviewed_at         DATETIME
);
```

### Step 3: Supplier-scoped JWT

Suppliers log in via the same POST /api/auth/login endpoint.
Their JWT payload includes role="SUPPLIER" AND supplier_name.
All supplier API routes extract supplier_name from the token and
scope all queries to that supplier ONLY. Suppliers cannot see
data from other suppliers under any circumstances.

```python
# backend/api/dependencies.py — add:

async def get_supplier_user(
    authorization: str = Header(...)
) -> dict:
    payload = decode_token(authorization.split(" ")[1])
    if payload.get("role") != "SUPPLIER":
        raise HTTPException(403, "Supplier access only")
    return {
        "user_id":       payload["sub"],
        "role":          "SUPPLIER",
        "supplier_name": payload["supplier_name"]  # always scoped
    }
```

### Step 4: Supplier invite endpoints (internal users only)

```
POST /api/supplier-portal/invite       [ADMIN, APPROVER]
  Request: {
    supplier_name: str,  -- must match a contract in library
    contact_email: str,
    contact_name:  str,
    company_name:  str
  }
  Creates user record (role=SUPPLIER) + supplier_users record.
  Generates invite_token (expires 48h).
  Sends invite email with portal link:
    "You have been invited to view your compliance dashboard on
     SupplierGuard. Click here to set your password: {link}"
  Returns: {invite_sent: true, email: str}

POST /api/supplier-portal/accept-invite
  Public endpoint (no auth required).
  Request: {invite_token: str, password: str}
  Validates token not expired. Sets password. Clears invite_token.
  Returns: {access_token, user}

GET  /api/supplier-portal/users        [ADMIN]
  List all supplier users.

PATCH /api/supplier-portal/users/{id}  [ADMIN]
  Enable/disable portal access.
```

### Step 5: Supplier-facing API endpoints

All routes scoped to the authenticated supplier's supplier_name.

```
GET /api/portal/dashboard
  Returns supplier's own data only:
  {
    supplier_name:        str,
    compliance_score:     float,           -- from supplier_scores
    score_trend:          "improving"|"worsening"|"stable",
    total_leakage_identified: Decimal,
    total_recovered:      Decimal,
    open_disputes:        int,             -- DISPUTED or ACKNOWLEDGED
    recent_audits: [
      {audit_id, billing_period, total_leakage, finding_count, status}
    ]
  }

GET /api/portal/findings
  All findings against this supplier from finding_recovery table.
  Query: status, audit_id
  Returns FindingRecovery records with full Discrepancy detail.
  Excludes: audit_id references, internal notes, reviewed_by details.
  Includes: discrepancy_type, description, clause_text,
            charged, expected, delta, status, supplier_response (if any)

POST /api/portal/findings/{recovery_id}/respond
  Supplier submits response to a finding.
  Request: {
    response_type: "ACCEPT"|"CONTEST"|"SUBMIT_CORRECTION",
    response_notes: str,
    supporting_doc: file (optional PDF)
  }
  Validates: recovery_id belongs to this supplier (check supplier_name).
  Creates supplier_responses record.
  Sends notification to internal APPROVER users.
  Updates finding_recovery.status to "ACKNOWLEDGED" if ACCEPT.
  Returns: {response_id, status: "submitted"}

GET /api/portal/contract
  Returns the active contract for this supplier (read-only).
  Includes: key_terms_summary, rules list, expiry date.
  Excludes: internal notes, pricing strategy annotations.

GET /api/portal/audits
  List of all audits run against this supplier.
  Each audit: billing_period, total_leakage, finding_count, status.
  NOT included: full discrepancies JSON — use /portal/findings instead.
```

### Step 6: Security rules (non-negotiable)

```python
# Every supplier endpoint MUST validate ownership:

def assert_supplier_owns_finding(
    recovery_id: str,
    supplier_name: str,
    db: Session
) -> FindingRecovery:
    record = db.query(FindingRecovery).filter_by(id=recovery_id).first()
    if not record:
        raise HTTPException(404, "Finding not found")
    if record.supplier_name != supplier_name:
        raise HTTPException(403, "Access denied")
    return record

# Apply to every route that takes a finding/audit ID as input.
# Never trust the client. Always re-validate from DB.
```

## WHAT TO BUILD — FRONTEND

### Separate React entry point or subdomain

The supplier portal is a separate UI from the main app.
Two options — choose Option A (simpler):

Option A: Same React app, separate route prefix /portal/*
  - /portal/login    — supplier login page
  - /portal/dashboard
  - /portal/findings
  - /portal/contract
  - Route guard: if role == SUPPLIER → redirect to /portal/dashboard
  - Route guard: if on /portal/* and role != SUPPLIER → redirect to /

Option B: Separate Vite app (too complex for MVP — skip)

### Supplier Login (/portal/login)

```
Same JWT login flow as internal login.
Different branding: "Supplier Compliance Portal"
Separate from main /login page.
After login: redirect to /portal/dashboard
```

### Supplier Dashboard (/portal/dashboard)

```
Header: "Welcome, [company_name]" + [Logout]
No Navbar with internal links — completely separate UI.

KPI cards (4):
  Your Compliance Score (large, colored badge)
  Open Disputes (number, amber if > 0)
  Total Identified (₹)
  Total Resolved (₹)

Score trend chart (simple — last 6 audits, line chart via Recharts)

Recent Audit Invoices table:
  Period | Findings | Leakage | Status
  [View Findings →] link per row
```

### Findings Page (/portal/findings)

```
Filter by: Status | Audit Period

Finding cards (NOT a dense table — designed for supplier readability):
  Each card shows:
    Invoice Period | Discrepancy Type label
    Plain English description
    What was charged: ₹X | What should have been: ₹Y | Difference: ₹Z
    Contract clause: [Section 4.2 — quoted text]
    Current Status badge

  Action buttons (shown based on current status):
    If status DISPUTED or ACKNOWLEDGED and no response yet:
      [Accept this finding]   → opens Accept modal
      [Contest this finding]  → opens Contest modal
      [Submit Corrected Invoice] → opens upload modal

    If response already submitted:
      Show: "Response submitted on [date]: ACCEPT / CONTEST"
      Show: review_status badge (PENDING/ACCEPTED/REJECTED)

Accept modal:
  "By accepting this finding, you confirm the overcharge of ₹X.
   A credit note will be arranged separately."
  [Confirm Accept]

Contest modal:
  "Explain why you believe this finding is incorrect:"
  [textarea — required]
  [Upload supporting document] (optional PDF)
  [Submit Contest]

Corrected Invoice modal:
  [Upload corrected invoice PDF]
  Notes: [textarea]
  [Submit]
```

### Contract Page (/portal/contract)

```
Read-only view of supplier's active contract:
  Key Terms Summary card (same as internal ContractDetail view)
  Pricing Rules table (all extracted rules with clause references)
  No edit options. No version history. No internal audit data.
```

### Internal UI additions (main app)

**In Approvals.jsx — add supplier response column:**
```
If a supplier has responded to a finding:
  Show response_type badge + truncated notes
  [View Full Response] button → modal with full supplier response
  [Accept Response] / [Reject Response] buttons for APPROVER
```

**In Settings.jsx — add Supplier Portal tab:**
```
Invite Supplier form:
  Supplier Name (dropdown from contract library)
  Contact Name, Contact Email, Company Name
  [Send Invite] button

Active Supplier Users table:
  Company | Contact Email | Supplier Name | Last Login | [Disable Access]
```

## IMPLEMENTATION ORDER

1. DB migration — add supplier_users + supplier_responses tables
2. Add SUPPLIER to role enum, update token payload to include supplier_name
3. backend/api/dependencies.py — get_supplier_user()
4. backend/api/routes/supplier_portal.py — invite endpoints
5. backend/api/routes/portal.py — all /api/portal/* endpoints
6. assert_supplier_owns_finding() security validation on all routes
7. Register both routers in main.py
8. frontend/src/pages/portal/PortalLogin.jsx
9. frontend/src/pages/portal/PortalDashboard.jsx
10. frontend/src/pages/portal/PortalFindings.jsx
11. frontend/src/pages/portal/PortalContract.jsx
12. Add /portal/* routes to App.jsx with SUPPLIER role guard
13. Update Approvals.jsx — supplier response column
14. Add Supplier Portal tab to Settings.jsx

## DONE WHEN

- Admin invites supplier → supplier receives email with invite link
- Supplier clicks link → sets password → logs in to portal dashboard
- Supplier can see their own compliance score and findings
- Supplier CANNOT see findings from other suppliers (403 if they try)
- Supplier accepts a finding → finding status updates to ACKNOWLEDGED
- Supplier contests a finding → internal APPROVER receives notification
- Supplier uploads corrected invoice → file stored, APPROVER notified
- Internal Approver can see supplier response in Approvals.jsx
- Approver accepts supplier response → finding moves to CLOSED
- /portal/* routes redirect to /portal/login if not authenticated as SUPPLIER
- Main app routes redirect non-SUPPLIER users away from /portal/*

Do not implement two-factor authentication yet.
Do not implement supplier-to-supplier messaging yet.
Do not implement automatic credit note generation yet.

---
END OF PROMPT 5
---

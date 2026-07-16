# ProcureAI — Layer 1 Implementation Prompts
# Three features, three prompts. Paste each one into a fresh AI session.
# Each prompt is self-contained — no prior context needed beyond your project files.

---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 1 OF 3
# FEATURE: Supplier Risk Scorecard
# WHAT IT BUILDS: A 0–100 compliance score per supplier aggregated
#                 from all past audits. A leaderboard page showing
#                 all suppliers ranked by risk with trend direction.
# EFFORT: 2–3 days | NO new AI needed — pure aggregation + React UI
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building ProcureAI — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. The core 4-agent
pipeline (Contract Parser → Invoice Extractor → Compliance Checker →
Report Generator) is already working. I can generate audits and see
discrepancy reports with clause citations and financial deltas.

I am now adding the Supplier Risk Scorecard feature.

## WHAT THIS FEATURE DOES

Every time an audit completes, a compliance score is computed for that
supplier and stored. Over time, each supplier builds up a score history.
The Supplier Risk Scorecard page shows:
- All suppliers ranked 0–100 (100 = perfect compliance, 0 = worst)
- Trend direction per supplier: improving ↑ / worsening ↓ / stable →
- Color banding: GREEN (80–100) / AMBER (50–79) / RED (0–49)
- Click through to full audit history for any supplier
- Summary KPIs at the top: total suppliers tracked, average score,
  number in red zone, total leakage identified across all suppliers

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + LangGraph + Pydantic v2
Frontend: React + Vite + Tailwind CSS
Database: SQLite — audits table already exists with these relevant columns:
  id, status, supplier_name, discrepancies (JSON), audit_report (JSON),
  total_leakage (REAL), created_at, completed_at

All monetary values use Python Decimal.
All imports are absolute (from backend.models.schemas import ...).
All Pydantic models are v2.

## WHAT TO BUILD — BACKEND

### Step 1: Add supplier_scores table to the database

```sql
CREATE TABLE supplier_scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name   TEXT NOT NULL,
    audit_id        TEXT NOT NULL,
    score           REAL NOT NULL,         -- 0.0 to 100.0
    total_lines     INTEGER NOT NULL,
    compliant_lines INTEGER NOT NULL,
    critical_count  INTEGER DEFAULT 0,
    high_count      INTEGER DEFAULT 0,
    medium_count    INTEGER DEFAULT 0,
    total_leakage   REAL DEFAULT 0.0,
    computed_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audit_id) REFERENCES audits(id)
);
```

### Step 2: Score computation function

Build `backend/services/scoring.py` with this logic:

```
compute_score(audit_report: AuditReport) -> float:

  base_score = (compliant_lines / total_lines_audited) * 100

  penalties:
    each CRITICAL finding: -8 points
    each HIGH finding:     -4 points
    each MEDIUM finding:   -1 point

  score = max(0.0, min(100.0, base_score - total_penalties))
  round to 1 decimal place
  return score
```

After every audit pipeline completes (in report_generator/agent.py,
after writing the audit to DB), call this function and insert a new
row into supplier_scores.

### Step 3: New API endpoints in backend/api/routes/suppliers.py

```
GET /api/suppliers
  Returns list of all unique suppliers with:
    - supplier_name
    - latest_score (most recent supplier_scores row)
    - previous_score (second most recent, for trend)
    - trend: "improving" | "worsening" | "stable" | "new"
      (improving if latest > previous + 2, worsening if latest < previous - 2)
    - audit_count (total audits run for this supplier)
    - total_leakage_identified (sum across all their audits)
    - last_audit_date
    - risk_band: "green" | "amber" | "red"
      (green ≥ 80, amber 50–79, red < 50)

GET /api/suppliers/{supplier_name}/history
  Returns all audit history for one supplier:
    - list of {audit_id, score, total_leakage, created_at, discrepancy_count}
    - score over time (for the trend sparkline on the frontend)

GET /api/suppliers/summary
  Returns aggregate KPIs:
    - total_suppliers_tracked
    - average_score_across_all_suppliers
    - suppliers_in_red_zone (score < 50)
    - total_leakage_identified_all_time (sum of all audit total_leakage)
    - most_at_risk_supplier (lowest latest score)
    - most_improved_supplier (biggest positive score delta)
```

### Step 4: Pydantic response models

```python
class SupplierScoreCard(BaseModel):
    supplier_name:             str
    latest_score:              float
    previous_score:            Optional[float]
    trend:                     Literal["improving","worsening","stable","new"]
    audit_count:               int
    total_leakage_identified:  Decimal
    last_audit_date:           str
    risk_band:                 Literal["green","amber","red"]

class SupplierSummaryKPIs(BaseModel):
    total_suppliers_tracked:      int
    average_score:                float
    suppliers_in_red_zone:        int
    total_leakage_all_time:       Decimal
    most_at_risk_supplier:        Optional[str]
    most_improved_supplier:       Optional[str]
```

## WHAT TO BUILD — FRONTEND

Build `frontend/src/pages/SupplierScorecard.jsx`

### Layout

Top section — KPI cards (4 cards in a row):
  - Total Suppliers Tracked
  - Average Compliance Score (with color based on band)
  - Suppliers in Red Zone
  - Total Leakage Identified (all time, in $)

Middle section — Supplier Leaderboard table:
  Columns: Rank | Supplier Name | Score (with color band) | Trend Arrow
           | Audits Run | Total Leakage | Last Audit | Action
  - Score column: show number + colored badge (green/amber/red)
  - Trend column: ↑ green, ↓ red, → gray, NEW badge for first-timers
  - Sorted by score ascending (riskiest first)
  - Click on any row → navigate to /suppliers/{name}/history

Score history page `frontend/src/pages/SupplierHistory.jsx`:
  - Supplier name + current score badge at top
  - Line chart of score over time (use Recharts LineChart)
  - Table of all past audits: date, score, leakage, discrepancy count
  - Link to open each full audit report

### UI rules
- Use Tailwind CSS only — no additional libraries
- Score badge colors:
    green:  bg-green-100 text-green-800
    amber:  bg-yellow-100 text-yellow-800
    red:    bg-red-100 text-red-800
- Trend arrows: ↑ text-green-600, ↓ text-red-600, → text-gray-400
- Table rows: hover:bg-gray-50, cursor-pointer
- Add /suppliers route to App.jsx router

## IMPLEMENTATION ORDER

1. Database migration — add supplier_scores table
2. backend/services/scoring.py — compute_score() function
3. Wire scoring into report_generator agent (call after DB persist)
4. backend/api/routes/suppliers.py — all 3 endpoints
5. Register suppliers router in main.py
6. frontend/src/api/audit.js — add getSuppliers(), getSupplierHistory(), getSupplierSummary()
7. frontend/src/pages/SupplierScorecard.jsx
8. frontend/src/pages/SupplierHistory.jsx
9. Add routes in App.jsx
10. Add "Suppliers" link to Navbar

## DONE WHEN

- /api/suppliers returns correct scores after running 2+ audits for same supplier
- Score changes correctly when a new audit is run (worse audit → lower score)
- Trend shows "worsening" correctly when score drops by more than 2 points
- Frontend leaderboard renders all suppliers sorted by score
- Clicking a supplier shows their score history page with Recharts line chart
- KPI cards at top match the DB aggregate data

Do not add authentication. Do not add pagination yet. Keep it simple and working.

---
END OF PROMPT 1
---


---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 2 OF 3
# FEATURE: Leakage Trend Analytics
# WHAT IT BUILDS: An executive analytics dashboard with time-series
#                 charts showing leakage over time, by supplier,
#                 by discrepancy type, and total recovery stats.
# EFFORT: 2 days | Pure data aggregation + Recharts — no new AI
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building ProcureAI — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. The core pipeline
is working. I can generate audits and see discrepancy reports. The Supplier
Risk Scorecard feature is also complete (supplier_scores table exists,
/api/suppliers endpoint exists).

I am now adding the Leakage Trend Analytics dashboard.

## WHAT THIS FEATURE DOES

A dedicated analytics page that gives a finance leader a full picture of
procurement leakage over time. It answers these questions at a glance:

- How much total leakage has been identified this month / quarter / year?
- Which supplier is causing the most leakage?
- Is overall leakage trending up or down over time?
- What type of discrepancy is most common (overcharge vs. missed discount vs. SLA)?
- How much of the identified leakage has been disputed and recovered?

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2
Frontend: React + Vite + Tailwind CSS + Recharts (already installed)
Database tables already exist:
  - audits: id, supplier_name, discrepancies (JSON), total_leakage,
            created_at, completed_at, status
  - supplier_scores: supplier_name, score, total_leakage, computed_at
  - findings: (if Recovery Tracker is built — otherwise derive from
               discrepancies JSON in audits table)

All monetary values: Python Decimal backend, number on frontend.
Recharts is available: import { LineChart, BarChart, ... } from "recharts"

## WHAT TO BUILD — BACKEND

### New analytics endpoint: backend/api/routes/analytics.py

```
GET /api/analytics/overview?period=30d|90d|1y|all

Returns a single JSON object with all dashboard data:

{
  "period_label": "Last 30 days",
  "kpis": {
    "total_leakage_identified": Decimal,   -- sum of all audit total_leakage
    "total_audits_run": int,
    "avg_leakage_per_audit": Decimal,
    "total_suppliers_audited": int,
    "leakage_trend_pct": float             -- % change vs previous same period
      (positive = getting worse, negative = improving)
  },
  "leakage_by_month": [
    {"month": "2024-10", "total_leakage": Decimal, "audit_count": int},
    {"month": "2024-11", "total_leakage": Decimal, "audit_count": int},
    ...
  ],
  "leakage_by_supplier": [
    {"supplier_name": str, "total_leakage": Decimal, "audit_count": int},
    ...  -- sorted by total_leakage descending, top 10
  ],
  "leakage_by_type": [
    {"discrepancy_type": str, "count": int, "total_leakage": Decimal},
    ...  -- aggregated across all discrepancies in all audits
  ],
  "severity_breakdown": {
    "CRITICAL": {"count": int, "total_leakage": Decimal},
    "HIGH":     {"count": int, "total_leakage": Decimal},
    "MEDIUM":   {"count": int, "total_leakage": Decimal}
  },
  "top_findings": [
    -- the 5 largest individual discrepancies in the period
    {
      "supplier_name": str,
      "discrepancy_type": str,
      "delta": Decimal,
      "severity": str,
      "audit_date": str,
      "clause_reference": str
    }
  ]
}
```

### Data extraction logic

The `discrepancies` column in the audits table stores the DiscrepancyList
as a JSON string. To compute leakage_by_type and severity_breakdown,
load each audit's discrepancies JSON, parse it, and iterate over the
findings list. Do this in Python — do not use SQL JSON functions.

```python
# backend/services/analytics.py

def compute_analytics(period_days: int, db: Session) -> AnalyticsOverview:
    cutoff = datetime.utcnow() - timedelta(days=period_days)
    audits = db.query(Audit).filter(
        Audit.status == "COMPLETE",
        Audit.completed_at >= cutoff
    ).all()

    leakage_by_type = defaultdict(lambda: {"count": 0, "total": Decimal("0")})
    severity_breakdown = {"CRITICAL": ..., "HIGH": ..., "MEDIUM": ...}
    top_findings = []

    for audit in audits:
        if not audit.discrepancies:
            continue
        disc_data = json.loads(audit.discrepancies)
        for finding in disc_data.get("discrepancies", []):
            dtype = finding["discrepancy_type"]
            delta = abs(Decimal(str(finding["delta"])))
            leakage_by_type[dtype]["count"] += 1
            leakage_by_type[dtype]["total"] += delta
            severity_breakdown[finding["severity"]]["count"] += 1
            severity_breakdown[finding["severity"]]["total_leakage"] += delta
            top_findings.append({...finding details + audit.supplier_name...})

    top_findings.sort(key=lambda x: x["delta"], reverse=True)
    return AnalyticsOverview(...)
```

### Period filter logic

```
period param → days to look back:
  "30d"  → 30 days
  "90d"  → 90 days
  "1y"   → 365 days
  "all"  → no date filter
```

Trend percentage:
```
current_period_leakage = sum of leakage in selected period
previous_period_leakage = sum of leakage in same length period before that
trend_pct = ((current - previous) / previous) * 100
if previous == 0: trend_pct = 0
```

## WHAT TO BUILD — FRONTEND

Build `frontend/src/pages/Analytics.jsx`

### Layout (top to bottom)

**Section 1 — Period selector tabs**
  Buttons: 30 Days | 90 Days | 1 Year | All Time
  On click → refetch /api/analytics/overview?period=...

**Section 2 — KPI cards row (5 cards)**
  - Total Leakage Identified (large $ number, red if > 0)
  - Total Audits Run
  - Avg Leakage Per Audit
  - Suppliers Audited
  - Leakage Trend (↑ +12% worse / ↓ −8% better) with color

**Section 3 — Two charts side by side**

Left: Leakage Over Time (LineChart)
  - X axis: months ("Oct 2024", "Nov 2024", ...)
  - Y axis: total leakage in $
  - One line for total leakage, one line for audit count (secondary axis)
  - Use Recharts LineChart with ComposedChart for dual axis

Right: Leakage by Supplier (BarChart)
  - Horizontal bar chart
  - Y axis: supplier names
  - X axis: total leakage $
  - Top 10 suppliers only
  - Color bars by risk band (red/amber/green based on leakage amount)

**Section 4 — Two more charts side by side**

Left: Leakage by Discrepancy Type (PieChart or DonutChart)
  - Segments: overcharge, missed_discount, unapplied_penalty,
              incorrect_rate, missing_credit, period_mismatch
  - Show $ amount + count per segment in tooltip
  - Use Recharts PieChart with label

Right: Severity Breakdown (BarChart stacked or grouped)
  - X axis: CRITICAL, HIGH, MEDIUM
  - Y axis: count of findings + total leakage
  - Color: red (CRITICAL), orange (HIGH), yellow (MEDIUM)

**Section 5 — Top 5 Largest Findings table**
  Columns: Supplier | Type | Severity | Delta | Clause | Date
  - Sorted by delta descending
  - Severity badge with color
  - Delta in $ bold red

### Recharts usage
```jsx
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
         XAxis, YAxis, CartesianGrid, Tooltip, Legend,
         ResponsiveContainer } from "recharts"

// Always wrap charts in ResponsiveContainer width="100%" height={300}
// Format $ in tooltips: formatter={(value) => `$${value.toLocaleString('en-US')}`}
```

## IMPLEMENTATION ORDER

1. backend/services/analytics.py — compute_analytics() function
2. backend/api/routes/analytics.py — GET /api/analytics/overview
3. Register analytics router in main.py
4. frontend/src/api/audit.js — add getAnalytics(period) function
5. frontend/src/pages/Analytics.jsx — full page with all sections
6. Add /analytics route to App.jsx
7. Add "Analytics" link to Navbar

## DONE WHEN

- /api/analytics/overview?period=30d returns correct aggregated data
  after running 3+ audits with different suppliers
- All 4 charts render with real data from the API (not hardcoded)
- Period selector correctly filters data and rerenders charts
- Trend percentage correctly shows direction vs. previous period
- Top 5 findings table shows real discrepancies with correct amounts
- All $ amounts formatted as Indian locale ($1,24,000 not $124,000)

Do not add export to CSV yet. Do not add drill-down into individual audits
from charts yet. Keep charts simple and accurate.

---
END OF PROMPT 2
---


---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 3 OF 3
# FEATURE: Clause Violation Heatmap
# WHAT IT BUILDS: A heatmap grid showing which contract clause types
#                 are violated most often by which suppliers.
#                 Turns audit data into contract negotiation intelligence.
# EFFORT: 1–2 days | Pure aggregation + custom React heatmap grid
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building ProcureAI — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. The core pipeline,
Supplier Risk Scorecard, and Leakage Trend Analytics are all complete.

I am now adding the Clause Violation Heatmap — the final Layer 1 feature.

## WHAT THIS FEATURE DOES

A visual heatmap grid that answers: "Which contract clause types are
violated most often, and by which suppliers?"

The grid has:
- Rows: each supplier
- Columns: each discrepancy type (overcharge, missed_discount,
           unapplied_penalty, incorrect_rate, missing_credit, period_mismatch)
- Cells: colored by frequency of violation (white → light → dark)
         with a number showing count of violations

Below the heatmap:
- Clause type insight cards — for each column, a card says:
  "Volume tier violations have caused $X in leakage across Y audits.
   This suggests tightening the volume calculation method in future contracts."
- Supplier insight row — for each supplier row, shows their most
  frequently violated clause type

This page is primarily a strategic insight tool for procurement/legal teams.

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2
Frontend: React + Vite + Tailwind CSS
Database: audits table with discrepancies JSON column
The discrepancies column contains a DiscrepancyList JSON object with a
"discrepancies" array. Each finding has: discrepancy_type, supplier_name
(via the audit), delta, severity, clause_reference, rule_id.

## WHAT TO BUILD — BACKEND

### New endpoint: backend/api/routes/analytics.py (add to existing file)

```
GET /api/analytics/heatmap?period=30d|90d|1y|all

Returns:
{
  "suppliers": ["Apex Logistics", "TechSoft Solutions", ...],
  "clause_types": [
    "overcharge",
    "missed_discount",
    "unapplied_penalty",
    "incorrect_rate",
    "missing_credit",
    "period_mismatch"
  ],
  "grid": {
    "Apex Logistics": {
      "overcharge":        {"count": 5, "total_leakage": "18400.00"},
      "missed_discount":   {"count": 2, "total_leakage": "3200.00"},
      "unapplied_penalty": {"count": 3, "total_leakage": "22760.00"},
      "incorrect_rate":    {"count": 0, "total_leakage": "0.00"},
      "missing_credit":    {"count": 1, "total_leakage": "6200.00"},
      "period_mismatch":   {"count": 0, "total_leakage": "0.00"}
    },
    "TechSoft Solutions": { ... }
  },
  "column_totals": {
    "overcharge":        {"count": 12, "total_leakage": "45000.00"},
    "missed_discount":   {"count": 4,  "total_leakage": "8200.00"},
    ...
  },
  "row_totals": {
    "Apex Logistics":     {"count": 11, "total_leakage": "50560.00"},
    "TechSoft Solutions": {"count": 6,  "total_leakage": "21000.00"},
    ...
  },
  "insights": {
    "most_violated_clause_type": "overcharge",
    "most_problematic_supplier": "Apex Logistics",
    "clause_insights": [
      {
        "clause_type": "overcharge",
        "total_count": 12,
        "total_leakage": "45000.00",
        "recommendation": "Add invoice certification requirement for unit pricing in future contracts. Require suppliers to show tier calculation on each invoice line."
      },
      {
        "clause_type": "unapplied_penalty",
        "total_count": 7,
        "total_leakage": "38000.00",
        "recommendation": "Automate SLA data collection. Current manual process misses penalty triggers. Add contractual obligation for suppliers to self-report SLA breaches."
      },
      ...
    ]
  }
}
```

### Data extraction logic (add to backend/services/analytics.py)

```python
def compute_heatmap(period_days: int, db: Session) -> HeatmapData:
    audits = get_audits_in_period(period_days, db)

    # Build the grid: {supplier_name: {discrepancy_type: {count, total}}}
    grid = defaultdict(lambda: defaultdict(lambda: {"count": 0, "total": Decimal("0")}))
    column_totals = defaultdict(lambda: {"count": 0, "total": Decimal("0")})
    row_totals = defaultdict(lambda: {"count": 0, "total": Decimal("0")})

    for audit in audits:
        if not audit.discrepancies: continue
        disc_data = json.loads(audit.discrepancies)
        for finding in disc_data.get("discrepancies", []):
            dtype = finding["discrepancy_type"]
            delta = abs(Decimal(str(finding["delta"])))
            supplier = audit.supplier_name

            grid[supplier][dtype]["count"] += 1
            grid[supplier][dtype]["total"] += delta
            column_totals[dtype]["count"] += 1
            column_totals[dtype]["total"] += delta
            row_totals[supplier]["count"] += 1
            row_totals[supplier]["total"] += delta

    return HeatmapData(grid=grid, column_totals=column_totals,
                       row_totals=row_totals, insights=generate_insights(grid))
```

### Insights generation (LLM — one call at the end, not per cell)

```python
def generate_insights(column_totals: dict) -> list[ClauseInsight]:
    # Sort clause types by total_leakage descending
    # For each of the top 3, generate a procurement recommendation
    # Use one LLM call with all clause data → structured JSON output
    # Return list[ClauseInsight] validated by Pydantic

    prompt = f"""
    You are a procurement contract expert. Based on these clause violation
    patterns from supplier invoice audits, generate a specific, actionable
    contract negotiation recommendation for each clause type.

    Violation data: {json.dumps(column_totals)}

    Return JSON array: [{{"clause_type": str, "recommendation": str}}]
    Recommendations must be concrete (max 2 sentences each).
    Focus on what to add or change in future contract drafts.
    """
    # Use Gemini structured output → validate against ClauseInsight schema
```

### Pydantic models

```python
class HeatmapCell(BaseModel):
    count:         int
    total_leakage: Decimal

class ClauseInsight(BaseModel):
    clause_type:      str
    total_count:      int
    total_leakage:    Decimal
    recommendation:   str

class HeatmapData(BaseModel):
    suppliers:              list[str]
    clause_types:           list[str]
    grid:                   dict[str, dict[str, HeatmapCell]]
    column_totals:          dict[str, HeatmapCell]
    row_totals:             dict[str, HeatmapCell]
    insights:               dict        # most_violated, most_problematic, clause_insights
```

## WHAT TO BUILD — FRONTEND

Build as a new section inside `frontend/src/pages/Analytics.jsx`
(add below the existing charts — do not create a new page).

### Section: Clause Violation Heatmap

**Subsection 1 — Heatmap Grid**

Build as a custom HTML table with Tailwind classes.
Do NOT use a third-party heatmap library — build it in pure React/Tailwind.

```
Layout:
  Top-left corner: empty cell
  Top row: clause type headers (6 columns)
    Display names:
      overcharge       → "Overcharge"
      missed_discount  → "Missed Discount"
      unapplied_penalty→ "SLA / Penalty"
      incorrect_rate   → "Wrong Rate"
      missing_credit   → "Missing Credit"
      period_mismatch  → "Period Error"
  Left column: supplier names (one row per supplier)
  Each cell: shows count (large) + $ amount (small, below count)
  Right column: row total (count + leakage for that supplier)
  Bottom row: column total (count + leakage for that clause type)
```

Cell color intensity (Tailwind bg classes based on count):
```javascript
function getCellColor(count, maxCount) {
  if (count === 0) return "bg-gray-50 text-gray-300"
  const intensity = count / maxCount  // 0.0 to 1.0
  if (intensity < 0.25) return "bg-red-100 text-red-700"
  if (intensity < 0.50) return "bg-red-200 text-red-800"
  if (intensity < 0.75) return "bg-red-400 text-white"
  return "bg-red-600 text-white"
}
// maxCount = the highest count value in the entire grid
```

Cell hover tooltip (use title attribute):
```
"Apex Logistics | Overcharge | 5 violations | $18,400 leakage"
```

**Subsection 2 — Clause Insight Cards**

Below the heatmap, render one card per clause type that has violations:
```
Card layout:
  Icon + clause type name (bold)
  Total violations: X times across Y suppliers
  Total leakage: $X
  Recommendation: [LLM-generated text from insights.clause_insights]
  Color: border-left matching severity (most violations = red border)
```

Only show cards for clause types with count > 0.
Sort cards by total_leakage descending.

**Subsection 3 — Period selector**
Reuse the same period selector from the analytics page (30d/90d/1y/All)
to filter heatmap data.

## IMPLEMENTATION ORDER

1. Add compute_heatmap() to backend/services/analytics.py
2. Add GET /api/analytics/heatmap endpoint to analytics.py routes
3. Add generate_insights() with one LLM call (use existing Gemini client)
4. frontend/src/api/audit.js — add getHeatmap(period) function
5. Add HeatmapGrid component inline in Analytics.jsx
6. Add ClauseInsightCards component inline in Analytics.jsx
7. Wire up to existing period selector state

## DONE WHEN

- /api/analytics/heatmap returns correct grid data after 3+ audits
- Grid cells are colored correctly (darker = more violations)
- Zero-count cells show as light gray (visually distinct from violated)
- Column totals and row totals are mathematically correct
- Clause insight cards render with LLM-generated recommendations
- Hovering any cell shows the tooltip with supplier + type + count + leakage
- Period filter correctly changes the heatmap data
- Recommendations make procurement sense (not generic AI filler)

Do not add click-through to individual audits from heatmap cells yet.
Do not add export functionality yet. Focus on accuracy and clarity.

---
END OF PROMPT 3
---

# ProcureAI — Layer 3 Implementation Prompts
# Feature: Expand the Intelligence
# Four prompts — paste each into a fresh AI session independently.
# Build in order: Prompt 1 → Prompt 2 → Prompt 3 → Prompt 4
# Layers 1 and 2 must be complete before starting Layer 3.

---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 1 OF 4
# FEATURE: Contract Q&A Chat
# WHAT IT BUILDS: A RAG-powered chat interface on the audit report
#                 page. Users ask plain-English questions about their
#                 contract terms. Answers are grounded in the parsed
#                 ContractRulebook with exact clause citations.
# EFFORT: 2–3 days | RAG over structured JSON + streaming chat UI
# WHY FIRST: Reuses ContractRulebook already produced by Agent 1.
#            Zero new infrastructure — just a RAG layer on top.
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building ProcureAI — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. The core 4-agent
pipeline is working. Layers 1 and 2 are complete.

I am now adding Contract Q&A Chat — a RAG-powered conversational interface
that lets users ask plain-English questions about any parsed contract.

## WHAT THIS FEATURE DOES

On every completed audit report page, a collapsible side panel opens titled
"Ask About This Contract". The user types questions like:

  "What's our unit price if we ship 3,000 units?"
  "When does the SLA penalty kick in?"
  "What's the early payment discount window?"
  "Does the contract allow for price renegotiation?"
  "What services are covered under this agreement?"

The AI answers using ONLY information extracted from the contract's
ContractRulebook JSON + the original contract text chunks. Every answer
cites the specific clause it used. If the answer is not in the contract,
it says so explicitly — it never halluccinates.

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2 + Gemini (Vertex AI)
Frontend: React + Vite + Tailwind CSS
The ContractRulebook JSON is stored in the audits table (rulebook column).
The original contract PDF text is available from the uploaded file path
(contract_file column in audits table).
Gemini client singleton exists at backend/core/llm_client.py.
All LLM calls use structured output mode (response_mime_type="application/json").
Exception: chat responses are plain text — do NOT use JSON mode for chat answers.

## WHAT TO BUILD — BACKEND

### Step 1: contract_chunks table (for RAG retrieval)

```sql
CREATE TABLE contract_chunks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id        TEXT NOT NULL,
    chunk_index     INTEGER NOT NULL,
    chunk_text      TEXT NOT NULL,
    section_header  TEXT,           -- e.g. "Section 4.2 — Pricing"
    embedding       TEXT,           -- JSON array of floats (optional — see below)
    FOREIGN KEY (audit_id) REFERENCES audits(id)
);
```

NOTE on embeddings: For MVP, do NOT use vector embeddings or a vector DB.
Use keyword + BM25-style retrieval over chunk_text instead.
Add the `rank-bm25` package (pip install rank-bm25).
This avoids Pinecone/Weaviate setup complexity while keeping retrieval quality
good enough for contract text (which is already structured and precise).
Embeddings can be added later as an upgrade.

### Step 2: Contract chunking on audit completion

After Agent 1 (Contract Parser) writes the rulebook to state, also chunk
the contract_text and store chunks in contract_chunks table.

Add to backend/services/contract_chunker.py:

```python
from rank_bm25 import BM25Okapi
import re, json

def chunk_contract(contract_text: str, audit_id: str, db: Session) -> None:
    """
    Split contract text into overlapping chunks by section.
    Store each chunk in contract_chunks table.
    Called once after Agent 1 completes.
    """
    # Strategy: split on section headers first, then by max 500 chars
    # Section headers: lines matching "Section X", "Clause X", "Schedule X",
    #                  lines ending with ":" that are short (< 60 chars)

    sections = split_by_sections(contract_text)

    chunks = []
    for section_header, section_text in sections:
        # If section > 500 chars, split further with 50-char overlap
        sub_chunks = split_with_overlap(section_text, max_chars=500, overlap=50)
        for i, chunk in enumerate(sub_chunks):
            chunks.append({
                "audit_id":      audit_id,
                "chunk_index":   len(chunks),
                "chunk_text":    chunk.strip(),
                "section_header": section_header
            })

    # Bulk insert
    db.bulk_insert_mappings(ContractChunk, chunks)
    db.commit()


def retrieve_relevant_chunks(
    query: str,
    audit_id: str,
    db: Session,
    top_k: int = 5
) -> list[dict]:
    """
    BM25 retrieval over chunks for this audit's contract.
    Returns top_k most relevant chunks with their section headers.
    """
    chunks = db.query(ContractChunk).filter(
        ContractChunk.audit_id == audit_id
    ).all()

    if not chunks:
        return []

    # BM25 over tokenised chunk text
    tokenised = [c.chunk_text.lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenised)
    query_tokens = query.lower().split()
    scores = bm25.get_scores(query_tokens)

    # Get top_k indices
    top_indices = sorted(
        range(len(scores)), key=lambda i: scores[i], reverse=True
    )[:top_k]

    return [
        {
            "chunk_text":     chunks[i].chunk_text,
            "section_header": chunks[i].section_header,
            "relevance_score": float(scores[i])
        }
        for i in top_indices
        if scores[i] > 0.0  # skip zero-score chunks
    ]
```

### Step 3: Also include ContractRulebook rules in retrieval

Before BM25 retrieval, always inject the full ContractRulebook rules JSON
as additional context. Rules are already structured and precise — always
relevant for pricing questions.

```python
def build_rag_context(
    query: str,
    audit_id: str,
    rulebook: ContractRulebook,
    db: Session
) -> str:
    # Always include all rules (they are short and structured)
    rules_context = "CONTRACT PRICING RULES (structured):\n"
    for rule in rulebook.rules:
        rules_context += (
            f"\n[{rule.rule_id}] {rule.description}\n"
            f"Clause: {rule.clause_reference}\n"
            f"Text: {rule.clause_text}\n"
        )
        if rule.tiers:
            rules_context += "Tiers: " + json.dumps(
                [t.model_dump() for t in rule.tiers]
            ) + "\n"

    # BM25 retrieval for broader contract context
    chunks = retrieve_relevant_chunks(query, audit_id, db, top_k=4)
    chunks_context = "\nRELEVANT CONTRACT SECTIONS:\n"
    for c in chunks:
        chunks_context += (
            f"\n[{c['section_header']}]\n{c['chunk_text']}\n"
        )

    return rules_context + chunks_context
```

### Step 4: Chat endpoint

```
POST /api/contracts/{audit_id}/chat

Request:
{
  "message":  str,           -- user's question
  "history":  list[dict]     -- [{"role": "user"|"assistant", "content": str}]
                             -- last 6 turns maximum
}

Response (streaming — use StreamingResponse):
{
  "answer":   str,           -- the answer text
  "citations": [             -- clauses used to answer
    {
      "clause_reference": str,
      "clause_text":      str,
      "rule_id":          str | null
    }
  ],
  "confidence": "high" | "medium" | "not_found"
}
```

NOTE: Stream the answer token by token using FastAPI StreamingResponse
for a better chat UX. Citations are returned at the end of the stream
as a JSON suffix after a delimiter: `\n\n---CITATIONS---\n{json}`.

### Step 5: Chat system prompt (backend/agents/contract_qa/prompt.txt)

```
[ROLE]
You are a contract intelligence assistant for ProcureAI.
You answer questions about a specific supplier contract based ONLY on
the contract text and pricing rules provided to you as context.

[RULES — STRICTLY FOLLOW]
1. Answer ONLY from the provided context. Never use general knowledge
   about what contracts "usually" say.
2. If the answer is not in the context, say exactly:
   "I could not find this information in the contract. The contract may
   not address this, or it may be in a section that was not extracted."
3. Always cite the specific clause reference for every claim you make.
   Format citations as: (Section X.Y) or (Schedule B).
4. For pricing questions, show the exact calculation:
   "For 3,000 units: Tier 3 applies (≥2,000 units) → 3,000 × $9.80 = $29,400"
5. Keep answers concise — 3–6 sentences maximum unless a calculation
   requires more lines.
6. Never say "based on what you told me" or "according to you" —
   the context comes from the contract itself.

[CONFIDENCE LEVELS — include at end of answer]
Return one of:
  HIGH: answer is directly and explicitly stated in a clause
  MEDIUM: answer requires reasonable inference from stated clauses
  NOT_FOUND: answer is not in the provided context

[FORMAT]
Answer in plain text. No markdown. No bullet points unless listing tiers.
End with: [CONFIDENCE: HIGH|MEDIUM|NOT_FOUND]
Citations will be extracted programmatically — do not format them separately.
```

### Step 6: Answer + citation parsing

After the LLM response, extract citations by:
1. Finding all clause references in the answer text using regex:
   `r"Section\s+[\d\.]+|Schedule\s+[A-Z\d]+|Clause\s+[\d\.]+"`
2. Looking up each reference in the rulebook to get the full clause_text
3. Building the citations list

## WHAT TO BUILD — FRONTEND

### Chat panel in AuditReport.jsx

Add a collapsible right panel (drawer) that opens when user clicks
"Ask About This Contract 💬" button in the report header.

Panel width: 380px, fixed right side, scrollable.
Panel header: "Contract Q&A" + supplier name + [✕] close button.

Message input at bottom (sticky):
```jsx
<textarea
  placeholder='Ask anything... "What's our volume discount threshold?"'
  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
  rows={2}
/>
Send →
```

Message display (scrollable list, newest at bottom):
```
User message:   right-aligned, blue bubble
Assistant reply: left-aligned, white bubble with border

Each assistant reply shows:
  - Answer text
  - Citations block (if any): small gray text below answer
    "📄 Section 4.2, Schedule B"
  - Confidence badge:
      HIGH:      green dot "High confidence"
      MEDIUM:    amber dot "Inferred from contract"
      NOT_FOUND: gray dot "Not found in contract"
```

Loading state: Animated "..." dots while waiting for response.

Suggested questions (shown on first open, before any message):
```
Quick questions:
  [What's our unit price for 1,000 units?]
  [When does the SLA penalty apply?]
  [Is there an early payment discount?]
  [What's the contract period?]
```
Clicking a suggestion sends it as a message immediately.

### Frontend API call

```javascript
// frontend/src/api/audit.js
export async function chatWithContract(auditId, message, history) {
  const res = await fetch(`${BASE}/api/contracts/${auditId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history: history.slice(-6) })
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
```

## IMPLEMENTATION ORDER

1. DB migration — add contract_chunks table
2. backend/services/contract_chunker.py — chunk_contract() + retrieve_relevant_chunks()
3. Wire chunk_contract() into Agent 1 completion (after rulebook written to DB)
4. backend/agents/contract_qa/prompt.txt — write the prompt
5. backend/api/routes/contracts.py — POST /api/contracts/{audit_id}/chat
6. Register route in main.py
7. frontend/src/api/audit.js — add chatWithContract()
8. Add chat drawer panel to AuditReport.jsx
9. Add suggested questions component

## DONE WHEN

- "What's our unit price for 1,000 units?" returns the correct tier price
  with clause citation and calculation shown
- "Does the contract allow early termination?" returns NOT_FOUND with the
  correct message when that clause doesn't exist in the contract
- Citations always reference real clause numbers that exist in the rulebook
- Chat history is maintained within the session (last 6 turns sent)
- Suggested questions render on first open and send correctly on click
- LLM never invents a price or clause that isn't in the contract

Do not implement embeddings or vector DB yet — BM25 only for MVP.
Do not implement conversation persistence across page reloads yet.

---
END OF PROMPT 1
---


---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 2 OF 4
# FEATURE: Contract Version Comparator
# WHAT IT BUILDS: Upload two versions of the same supplier contract.
#                 AI diffs the pricing rules, surfaces what changed,
#                 what got worse, what improved — with a side-by-side
#                 comparison table and negotiation flags.
# EFFORT: 2–3 days | Run Agent 1 twice + structured diff + React UI
# WHY SECOND: Reuses Agent 1 (Contract Parser) directly — no new AI.
#             The diff is pure Python. Very high value for procurement.
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building ProcureAI — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. The core pipeline,
Layers 1 and 2, and Contract Q&A Chat are all complete.

I am now adding the Contract Version Comparator.

## WHAT THIS FEATURE DOES

A standalone comparison tool (separate from the audit flow). The user
uploads two PDFs — old contract version and new contract version from
the same supplier.

The system:
1. Runs Agent 1 (Contract Parser) on both contracts → two ContractRulebooks
2. Diffs the rulebooks at the rule level
3. Classifies each change: BETTER / WORSE / NEUTRAL / NEW / REMOVED
4. Generates a plain-English change summary
5. Flags the top negotiation points ("push back on this")

Output is a side-by-side comparison page showing every changed pricing
term with its business impact.

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2 + Gemini (Vertex AI)
Frontend: React + Vite + Tailwind CSS
Agent 1 (Contract Parser) already exists at backend/agents/contract_parser/agent.py.
It takes contract_text as input and returns ContractRulebook (Pydantic validated).
All monetary values use Decimal.

## WHAT TO BUILD — BACKEND

### Step 1: comparisons table

```sql
CREATE TABLE comparisons (
    id              TEXT PRIMARY KEY,   -- "cmp_20241115_abc123"
    supplier_name   TEXT,
    old_contract_file TEXT,
    new_contract_file TEXT,
    old_rulebook    TEXT,               -- JSON (ContractRulebook)
    new_rulebook    TEXT,               -- JSON (ContractRulebook)
    diff_result     TEXT,               -- JSON (ComparisonResult)
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    status          TEXT DEFAULT "PENDING"
);
```

### Step 2: Comparison pipeline (backend/services/contract_comparator.py)

```python
async def run_comparison(
    old_contract_text: str,
    new_contract_text: str,
    comparison_id: str,
    db: Session
) -> ComparisonResult:

    # Step 1: Parse both contracts using Agent 1 logic directly
    # (call the same extraction function used inside Agent 1,
    #  not the full LangGraph pipeline — just the LLM extraction part)
    old_rulebook = await extract_rulebook(old_contract_text)
    new_rulebook = await extract_rulebook(new_contract_text)

    # Step 2: Diff the rulebooks
    diff = diff_rulebooks(old_rulebook, new_rulebook)

    # Step 3: LLM generates change summary + negotiation flags
    summary = await generate_comparison_summary(diff, old_rulebook, new_rulebook)

    result = ComparisonResult(
        comparison_id=comparison_id,
        supplier_name=new_rulebook.supplier_name,
        old_contract_id=old_rulebook.contract_id,
        new_contract_id=new_rulebook.contract_id,
        changes=diff.changes,
        summary=summary.executive_summary,
        negotiation_flags=summary.negotiation_flags,
        overall_impact=summary.overall_impact
    )

    # Persist
    db.query(Comparison).filter_by(id=comparison_id).update({
        "old_rulebook": old_rulebook.model_dump_json(),
        "new_rulebook": new_rulebook.model_dump_json(),
        "diff_result":  result.model_dump_json(),
        "status":       "COMPLETE"
    })
    db.commit()
    return result
```

### Step 3: Rulebook diff logic (pure Python — no LLM)

```python
def diff_rulebooks(
    old: ContractRulebook,
    new: ContractRulebook
) -> RulebookDiff:
    """
    Match rules between old and new by rule_type + applies_to.
    Rules are matched on semantic similarity of applies_to + rule_type,
    NOT on rule_id (IDs change between contract versions).
    """
    changes = []

    old_rules = {(r.rule_type, r.applies_to): r for r in old.rules}
    new_rules = {(r.rule_type, r.applies_to): r for r in new.rules}

    all_keys = set(old_rules.keys()) | set(new_rules.keys())

    for key in all_keys:
        old_rule = old_rules.get(key)
        new_rule = new_rules.get(key)

        if old_rule and not new_rule:
            changes.append(RuleChange(
                change_type="REMOVED",
                rule_type=key[0],
                applies_to=key[1],
                old_rule=old_rule,
                new_rule=None,
                impact="NEUTRAL",    # removal could be good or bad — LLM assesses
                description=f"Rule removed: {old_rule.description}"
            ))

        elif new_rule and not old_rule:
            changes.append(RuleChange(
                change_type="ADDED",
                rule_type=key[0],
                applies_to=key[1],
                old_rule=None,
                new_rule=new_rule,
                impact="NEUTRAL",
                description=f"New rule added: {new_rule.description}"
            ))

        else:
            # Both exist — compare the values
            change = compare_rules(old_rule, new_rule)
            if change:
                changes.append(change)

    return RulebookDiff(changes=changes)


def compare_rules(old: PricingRule, new: PricingRule) -> Optional[RuleChange]:
    """Compare two matched rules and determine if anything changed."""
    differences = []
    impact = "NEUTRAL"

    # Compare tiers (volume pricing)
    if old.tiers and new.tiers:
        for old_tier in old.tiers:
            matching_new = next(
                (t for t in new.tiers if t.min_units == old_tier.min_units), None
            )
            if matching_new and matching_new.unit_price != old_tier.unit_price:
                delta = matching_new.unit_price - old_tier.unit_price
                impact = "WORSE" if delta > 0 else "BETTER"
                differences.append(
                    f"Tier {old_tier.min_units}+ units: "
                    f"${old_tier.unit_price} → ${matching_new.unit_price} "
                    f"({'↑ you pay more' if delta > 0 else '↓ you pay less'})"
                )

    # Compare flat rates
    if old.flat_unit_price and new.flat_unit_price:
        if old.flat_unit_price != new.flat_unit_price:
            delta = new.flat_unit_price - old.flat_unit_price
            impact = "WORSE" if delta > 0 else "BETTER"
            differences.append(
                f"Unit price: ${old.flat_unit_price} → ${new.flat_unit_price}"
            )

    # Compare SLA threshold (lower threshold = better for you)
    if old.sla_threshold_pct is not None and new.sla_threshold_pct is not None:
        if old.sla_threshold_pct != new.sla_threshold_pct:
            impact = "WORSE" if new.sla_threshold_pct > old.sla_threshold_pct else "BETTER"
            differences.append(
                f"SLA threshold: {old.sla_threshold_pct*100}% → {new.sla_threshold_pct*100}%"
            )

    # Compare penalty (higher penalty = better for you — more leverage)
    if old.penalty_pct is not None and new.penalty_pct is not None:
        if old.penalty_pct != new.penalty_pct:
            impact = "BETTER" if new.penalty_pct > old.penalty_pct else "WORSE"
            differences.append(
                f"Penalty: {old.penalty_pct*100}% → {new.penalty_pct*100}%"
            )

    # Compare early payment discount
    if old.discount_pct is not None and new.discount_pct is not None:
        if old.discount_pct != new.discount_pct:
            impact = "BETTER" if new.discount_pct > old.discount_pct else "WORSE"
            differences.append(
                f"Discount: {old.discount_pct*100}% → {new.discount_pct*100}%"
            )

    if not differences:
        return None  # No meaningful change

    return RuleChange(
        change_type="MODIFIED",
        rule_type=old.rule_type,
        applies_to=old.applies_to,
        old_clause=old.clause_reference,
        new_clause=new.clause_reference,
        old_rule=old,
        new_rule=new,
        impact=impact,
        differences=differences,
        description="; ".join(differences)
    )
```

### Step 4: LLM summary generation

One LLM call after the diff is complete:

```python
async def generate_comparison_summary(
    diff: RulebookDiff,
    old: ContractRulebook,
    new: ContractRulebook
) -> ComparisonSummary:
    """
    Prompt: Given these rule changes between two contract versions,
    generate:
    1. executive_summary: 3-sentence plain English summary for a CFO
       (overall impact: did the new contract get better or worse?)
    2. negotiation_flags: list of specific things to push back on
       (only WORSE changes — max 5 items)
    3. overall_impact: "BETTER" | "WORSE" | "MIXED" | "UNCHANGED"

    Return structured JSON: {executive_summary, negotiation_flags, overall_impact}
    """
```

### Step 5: Pydantic models

```python
class RuleChange(BaseModel):
    change_type:   Literal["MODIFIED","ADDED","REMOVED"]
    rule_type:     str
    applies_to:    str
    old_clause:    Optional[str]
    new_clause:    Optional[str]
    old_rule:      Optional[PricingRule]
    new_rule:      Optional[PricingRule]
    impact:        Literal["BETTER","WORSE","NEUTRAL"]
    differences:   list[str] = []
    description:   str

class ComparisonSummary(BaseModel):
    executive_summary:   str
    negotiation_flags:   list[str]     # "Push back on: volume tier increase..."
    overall_impact:      Literal["BETTER","WORSE","MIXED","UNCHANGED"]

class ComparisonResult(BaseModel):
    comparison_id:       str
    supplier_name:       str
    old_contract_id:     str
    new_contract_id:     str
    changes:             list[RuleChange]
    summary:             str
    negotiation_flags:   list[str]
    overall_impact:      Literal["BETTER","WORSE","MIXED","UNCHANGED"]
    worse_count:         int = 0
    better_count:        int = 0
    neutral_count:       int = 0
```

### Step 6: API endpoints (add to backend/api/routes/contracts.py)

```
POST /api/compare/upload
  Accepts: old_contract (file), new_contract (file)
  Returns: {comparison_id, status: "processing"}
  Background task: run_comparison(...)

GET /api/compare/{comparison_id}
  Returns: ComparisonResult or {status: "processing"}

GET /api/compare
  Returns: list of all past comparisons
```

## WHAT TO BUILD — FRONTEND

### Build frontend/src/pages/Compare.jsx (/compare)

**Upload Section:**
```
Two side-by-side upload zones:
  Left:  "Old Contract Version"  [drag-drop PDF]
  Right: "New Contract Version"  [drag-drop PDF]

[Compare Contracts →] button (disabled until both files uploaded)
→ POST /api/compare/upload (multipart, both files)
→ Poll GET /api/compare/{id} every 2s while processing
→ Show progress: "Parsing old contract... Parsing new contract... Comparing..."
```

**Results Section (shown after COMPLETE):**

Header banner:
```
Overall Impact badge: WORSE (red) / BETTER (green) / MIXED (amber) / UNCHANGED (gray)
Executive summary text (3 sentences)
Stats row: X changes worse | Y changes better | Z neutral | W new/removed
```

Negotiation flags card (if any WORSE changes):
```
🚩 Negotiation Points:
  • Push back on volume tier pricing increase — Tier 1 rose from $11.50 to $14.00
  • SLA threshold raised from 97% to 99% — harder to avoid penalty
  • Early payment window shortened from 15 to 10 days
```

Side-by-side changes table:
```
Columns: Change | Rule Type | Old Term | New Term | Impact

Row colors:
  WORSE:   bg-red-50   left border red
  BETTER:  bg-green-50 left border green
  NEUTRAL: bg-gray-50  left border gray
  ADDED:   bg-blue-50  left border blue
  REMOVED: bg-yellow-50 left border yellow

Impact badge per row:
  WORSE:   "↑ You pay more"   red
  BETTER:  "↓ You pay less"   green
  NEUTRAL: "No financial change" gray
  ADDED:   "New term"          blue
  REMOVED: "Term removed"      yellow
```

Add /compare route to App.jsx.
Add "Compare" link to Navbar.

## IMPLEMENTATION ORDER

1. DB migration — add comparisons table
2. backend/services/contract_comparator.py:
   a. extract_rulebook() — standalone Agent 1 extraction (no LangGraph)
   b. diff_rulebooks() + compare_rules() — pure Python diff
   c. generate_comparison_summary() — one LLM call
   d. run_comparison() — orchestrator
3. backend/api/routes/contracts.py — add compare endpoints
4. Register in main.py
5. frontend/src/api/audit.js — uploadForComparison(), pollComparison()
6. frontend/src/pages/Compare.jsx — full page
7. Add route + Navbar link

## DONE WHEN

- Uploading same contract twice → shows "UNCHANGED" with zero changes
- Uploading a contract where Tier 1 price increased → shows WORSE for that tier
- Uploading a contract where SLA penalty increased → shows BETTER (more leverage)
- Negotiation flags only appear for WORSE changes
- Executive summary correctly characterises the overall direction of change
- Side-by-side table shows old clause reference vs. new clause reference per row
- Comparison history page lists all past comparisons

Do not implement three-way merge (comparing 3 versions) yet.
Do not implement automated contract improvement suggestions yet (that is Prompt 3).

---
END OF PROMPT 2
---


---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 3 OF 4
# FEATURE: Negotiation Intelligence Report
# WHAT IT BUILDS: A data-backed negotiation brief generated from a
#                 supplier's full audit violation history. Tells
#                 procurement exactly what to push for in the next
#                 contract renewal — with evidence from past audits.
# EFFORT: 2 days | Aggregation + one structured LLM call + report UI
# WHY THIRD: The data already exists in the audit DB.
#            Pure synthesis layer — no new AI infrastructure.
#            The highest-value feature for strategic procurement teams.
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building ProcureAI — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. The core pipeline,
Layers 1 and 2, Contract Q&A Chat, and Contract Version Comparator are
all complete.

I am now adding the Negotiation Intelligence Report.

## WHAT THIS FEATURE DOES

For any supplier with 2+ completed audits in the system, a one-click
"Generate Negotiation Brief" button appears on their Supplier Scorecard page.

The system:
1. Loads ALL past audit findings for this supplier from the DB
2. Aggregates violation patterns: which clauses, how often, how much leakage
3. Runs one LLM call to generate a structured negotiation brief
4. Produces a downloadable report telling procurement exactly what to
   demand in the next contract renewal based on evidence

The brief contains:
- Executive summary: 3 sentences on how this supplier has been performing
- Violation pattern analysis: which clause types were violated, how often
- Specific negotiation demands with evidence:
  "Demand automatic invoice certification for volume tier pricing.
   This clause was violated 4 times causing $18,400 in overcharges."
- Clauses to add: new protective clauses they should insist on
- Clauses to tighten: existing clauses that need stronger language
- Risk rating for the upcoming renewal: LOW / MEDIUM / HIGH
- Recommended negotiation stance: AGGRESSIVE / FIRM / COLLABORATIVE

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2 + Gemini (Vertex AI)
Frontend: React + Vite + Tailwind CSS
Existing DB tables: audits (with discrepancies JSON), supplier_scores.
All violation data is in the discrepancies column of completed audits.
Gemini client at backend/core/llm_client.py.
All LLM calls use structured output (response_mime_type="application/json").

## WHAT TO BUILD — BACKEND

### Step 1: negotiation_briefs table

```sql
CREATE TABLE negotiation_briefs (
    id                  TEXT PRIMARY KEY,
    supplier_name       TEXT NOT NULL,
    generated_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    audits_analysed     INTEGER,
    total_leakage_basis Decimal,
    brief_json          TEXT,      -- JSON (NegotiationBrief)
    status              TEXT DEFAULT "COMPLETE"
);
```

### Step 2: Data aggregation (backend/services/negotiation_analyzer.py)

```python
def aggregate_supplier_violations(
    supplier_name: str,
    db: Session
) -> SupplierViolationSummary:
    """
    Pull all COMPLETE audits for this supplier.
    Aggregate violations across all findings in all audits.
    """
    audits = db.query(Audit).filter(
        Audit.supplier_name == supplier_name,
        Audit.status == "COMPLETE"
    ).order_by(Audit.completed_at.asc()).all()

    if len(audits) < 2:
        raise ValueError(
            f"Need at least 2 completed audits for {supplier_name}. "
            f"Found: {len(audits)}"
        )

    # Aggregate all findings
    clause_violations = defaultdict(lambda: {
        "count": 0,
        "total_leakage": Decimal("0"),
        "invoices_affected": set(),
        "clause_references": set(),
        "example_finding": None
    })

    total_leakage = Decimal("0")
    total_findings = 0
    monthly_leakage = {}  # {month_str: Decimal}

    for audit in audits:
        if not audit.discrepancies:
            continue
        disc_data = json.loads(audit.discrepancies)
        month = audit.completed_at.strftime("%Y-%m")

        for finding in disc_data.get("discrepancies", []):
            dtype = finding["discrepancy_type"]
            delta = abs(Decimal(str(finding["delta"])))

            clause_violations[dtype]["count"] += 1
            clause_violations[dtype]["total_leakage"] += delta
            clause_violations[dtype]["invoices_affected"].add(audit.id)
            clause_violations[dtype]["clause_references"].add(
                finding["clause_reference"]
            )
            if not clause_violations[dtype]["example_finding"]:
                clause_violations[dtype]["example_finding"] = {
                    "description": finding["description"],
                    "clause_text": finding["clause_text"],
                    "delta": str(delta)
                }

            total_leakage += delta
            total_findings += 1
            monthly_leakage[month] = monthly_leakage.get(month, Decimal("0")) + delta

    # Compute trend
    monthly_values = [float(v) for v in monthly_leakage.values()]
    trend = "improving" if (
        len(monthly_values) >= 2 and
        monthly_values[-1] < monthly_values[0]
    ) else "worsening"

    return SupplierViolationSummary(
        supplier_name=supplier_name,
        audits_analysed=len(audits),
        audit_period_start=audits[0].completed_at.isoformat(),
        audit_period_end=audits[-1].completed_at.isoformat(),
        total_leakage=total_leakage,
        total_findings=total_findings,
        clause_violations={
            k: {**v, "invoices_affected": len(v["invoices_affected"]),
                "clause_references": list(v["clause_references"])}
            for k, v in clause_violations.items()
        },
        leakage_trend=trend,
        monthly_leakage={k: str(v) for k, v in monthly_leakage.items()}
    )
```

### Step 3: LLM negotiation brief generation

ONE structured LLM call using the full violation summary:

```python
async def generate_negotiation_brief(
    summary: SupplierViolationSummary
) -> NegotiationBrief:

    prompt = load_prompt("negotiation_analyzer")
    # Inject full summary JSON into prompt

    # LLM returns structured JSON:
    # {
    #   "executive_summary": str,
    #   "violation_analysis": [
    #     {
    #       "clause_type": str,
    #       "pattern": str,          -- "Systematic overcharge on volume pricing"
    #       "evidence": str,         -- "4 violations across 6 audits, $18,400 total"
    #       "severity": "HIGH"|"MEDIUM"|"LOW"
    #     }
    #   ],
    #   "demands": [
    #     {
    #       "demand": str,           -- specific, actionable demand
    #       "justification": str,    -- evidence from audit history
    #       "type": "ADD_CLAUSE"|"TIGHTEN_CLAUSE"|"INCREASE_PENALTY"|"REQUIRE_CERTIFICATION"
    #       "priority": "MUST_HAVE"|"NICE_TO_HAVE"
    #     }
    #   ],
    #   "risk_rating": "LOW"|"MEDIUM"|"HIGH",
    #   "recommended_stance": "AGGRESSIVE"|"FIRM"|"COLLABORATIVE",
    #   "stance_rationale": str
    # }
```

### Step 4: Negotiation Analyzer prompt (backend/agents/negotiation_analyzer/prompt.txt)

```
[ROLE]
You are a senior procurement strategist and contract negotiation expert.
You analyse supplier audit history and produce evidence-based negotiation briefs.

[TASK]
Given the supplier violation summary below, generate a precise negotiation brief
that tells a procurement team exactly what to demand in their next contract renewal.

[INPUT]
Supplier name, audit period, total leakage, and a breakdown of violations by
clause type with counts, amounts, and example findings.

[OUTPUT RULES]
1. Every demand must be specific and actionable — not generic advice.
   BAD: "Strengthen pricing clauses"
   GOOD: "Add a mandatory invoice line showing the volume tier calculation
          (quantity, applicable tier, unit price) for each shipment line."

2. Every demand must cite evidence from the audit history.
   BAD: "The supplier has overcharged on volume pricing."
   GOOD: "Volume tier violations occurred in 4 of 6 audits, causing $18,400
          in overcharges. Systematic pattern suggests supplier billing system
          does not apply tier breaks automatically."

3. Risk rating:
   HIGH:   Total leakage > $50,000 OR same violation type in >50% of audits
   MEDIUM: Total leakage $10,000–$50,000 OR recurring violations
   LOW:    Total leakage < $10,000 AND violations appear non-systematic

4. Stance:
   AGGRESSIVE:    Risk HIGH + worsening trend
   FIRM:          Risk MEDIUM OR improving trend
   COLLABORATIVE: Risk LOW AND improving trend

5. Generate 3–6 demands, sorted by MUST_HAVE first.

[CONSTRAINTS]
- Base ALL recommendations ONLY on the provided violation data
- Do not recommend clauses for violation types that have never occurred
- Keep each demand under 3 sentences
```

### Step 5: Pydantic models

```python
class ViolationPattern(BaseModel):
    clause_type:  str
    pattern:      str
    evidence:     str
    severity:     Literal["HIGH","MEDIUM","LOW"]

class NegotiationDemand(BaseModel):
    demand:        str
    justification: str
    demand_type:   Literal["ADD_CLAUSE","TIGHTEN_CLAUSE",
                            "INCREASE_PENALTY","REQUIRE_CERTIFICATION"]
    priority:      Literal["MUST_HAVE","NICE_TO_HAVE"]

class NegotiationBrief(BaseModel):
    brief_id:             str
    supplier_name:        str
    generated_at:         str
    audits_analysed:      int
    audit_period:         str
    total_leakage_basis:  Decimal
    executive_summary:    str
    violation_analysis:   list[ViolationPattern]
    demands:              list[NegotiationDemand]
    risk_rating:          Literal["LOW","MEDIUM","HIGH"]
    recommended_stance:   Literal["AGGRESSIVE","FIRM","COLLABORATIVE"]
    stance_rationale:     str
```

### Step 6: API endpoints (add to backend/api/routes/suppliers.py)

```
POST /api/suppliers/{supplier_name}/negotiation-brief
  Generates a new brief — runs aggregation + LLM call
  Returns: NegotiationBrief

GET  /api/suppliers/{supplier_name}/negotiation-briefs
  Lists all past briefs for this supplier

GET  /api/suppliers/{supplier_name}/negotiation-briefs/{brief_id}
  Returns a specific brief
```

## WHAT TO BUILD — FRONTEND

### Add to SupplierHistory.jsx page

Below the audit history table, add a "Negotiation Intelligence" section.

Show this section only if audit_count >= 2.

```
Section header: "Negotiation Intelligence" + info tooltip
  "Based on X audits covering [period]"

[Generate Negotiation Brief] button (primary, large)
→ POST /api/suppliers/{name}/negotiation-brief
→ Loading: "Analysing X audits... Generating brief..."
→ On complete: render NegotiationBriefCard inline
```

### NegotiationBriefCard component

```
Card 1 — Header
  Risk Rating badge: HIGH (red) / MEDIUM (amber) / LOW (green)
  Stance badge: AGGRESSIVE / FIRM / COLLABORATIVE (with color)
  Executive summary text

Card 2 — Violation Patterns
  List each ViolationPattern as a row:
    [Severity badge] [clause_type label] [pattern description]
    Evidence text (italicised, smaller)

Card 3 — Negotiation Demands (most important card)
  Sorted: MUST_HAVE first
  Each demand as a card with left border color:
    MUST_HAVE:    red left border
    NICE_TO_HAVE: gray left border

  Each demand card shows:
    Top: [type badge] [priority badge]
    Middle: demand text (bold, readable)
    Bottom: justification text (gray, smaller)

Card 4 — Action buttons
  [Download as PDF]  [Copy All Demands]
```

PDF download: jsPDF — same pattern as Dispute Letter Generator.

Add "Generate Brief" button also to SupplierScorecard.jsx supplier rows
(only shown if audit_count >= 2).

## IMPLEMENTATION ORDER

1. DB migration — add negotiation_briefs table
2. backend/agents/negotiation_analyzer/prompt.txt — write the prompt
3. backend/services/negotiation_analyzer.py:
   a. aggregate_supplier_violations()
   b. generate_negotiation_brief()
4. backend/api/routes/suppliers.py — add brief endpoints
5. frontend/src/api/audit.js — generateNegotiationBrief(), getBriefs()
6. frontend/src/components/NegotiationBriefCard.jsx
7. Wire into SupplierHistory.jsx
8. Add trigger button to SupplierScorecard.jsx rows

## DONE WHEN

- Brief generates correctly for a supplier with 2+ audits
- Every demand cites specific evidence (not generic advice)
- Supplier with only overcharge violations does NOT get SLA penalty demands
- Risk rating is HIGH when total_leakage > $50,000
- AGGRESSIVE stance appears when risk is HIGH and trend is worsening
- PDF download produces readable brief with all demands
- "Generate Brief" button hidden for suppliers with < 2 audits
- Second brief generation for same supplier creates a new record
  (briefs are historical snapshots — not overwritten)

---
END OF PROMPT 3
---


---
---

# ═══════════════════════════════════════════════════════════════
# PROMPT 4 OF 4
# FEATURE: Overcharge Prediction
# WHAT IT BUILDS: A risk score (LOW / MEDIUM / HIGH) shown on the
#                 invoice upload step, before the full audit runs.
#                 Tells users which invoices to prioritise for deep
#                 review based on that supplier's past pattern.
# EFFORT: 1–2 days | Heuristic scoring + upload UI badge
# WHY LAST: Lowest complexity in Layer 3. Pure heuristics — no ML,
#           no new LLM calls. Depends on supplier history existing.
# ═══════════════════════════════════════════════════════════════

---
PASTE THIS ENTIRE BLOCK INTO YOUR AI ASSISTANT
---

I am building ProcureAI — a multi-agent AI system that audits supplier
contracts against invoices and finds financial leakage. The core pipeline,
Layers 1, 2, Contract Q&A Chat, Contract Version Comparator, and
Negotiation Intelligence Report are all complete.

I am now adding Overcharge Prediction — the final Layer 3 feature.

## WHAT THIS FEATURE DOES

On the Upload page, after the user selects their invoice PDF(s) and
before they click "Run Audit", the system shows a risk prediction badge
per invoice file:

  🔴 HIGH RISK — Apex Logistics has overcharged on 4 of 6 past audits.
                 $22,000 avg leakage. Recommend thorough review.

  🟡 MEDIUM RISK — TechSoft Solutions has 2 known violations.
                   $4,200 avg leakage. Check volume pricing lines.

  🟢 LOW RISK — MediSupply Corp has no prior violations in 3 audits.

  ⚪ NEW SUPPLIER — No audit history for BuildRight Contractors.

The risk score is computed entirely from the existing audit DB using
deterministic heuristics — no LLM call, no ML model.

The score also appears:
- As a column in the auto-audit history table (AutoAudit.jsx)
- As a badge in the supplier list (SupplierScorecard.jsx)
- In the audit detail header after the audit completes

## MY EXISTING TECH STACK

Backend: FastAPI + Python + SQLite (SQLAlchemy) + Pydantic v2
Frontend: React + Vite + Tailwind CSS
Existing data: audits table (with discrepancies JSON, total_leakage, supplier_name),
supplier_scores table (score, critical_count, high_count, computed_at).

The supplier name must be extracted from the invoice PDF to compute the
prediction before the full audit runs. Use the same lightweight
extract_supplier_from_invoice() function built in Layer 2 Prompt 3
(Scheduled Auto-Audit). If that feature was not built, implement it here:
a focused one-shot Gemini call on the first 1500 chars of the PDF.

## WHAT TO BUILD — BACKEND

### Step 1: Risk scoring logic (backend/services/risk_scorer.py)

```python
from decimal import Decimal
from dataclasses import dataclass

@dataclass
class RiskScore:
    level:              str       # "HIGH" | "MEDIUM" | "LOW" | "NEW_SUPPLIER"
    score:              float     # 0.0 to 100.0 (100 = highest risk)
    supplier_name:      str
    reason:             str       # one sentence explanation
    focus_areas:        list[str] # specific clause types to watch
    audits_analysed:    int
    avg_leakage:        Decimal
    violation_rate:     float     # violations per audit


def compute_risk_score(supplier_name: str, db: Session) -> RiskScore:
    """
    Deterministic heuristic scorer. No LLM. No ML.
    All math uses Decimal.
    """

    # Load all completed audits for this supplier
    audits = db.query(Audit).filter(
        Audit.supplier_name == supplier_name,
        Audit.status == "COMPLETE"
    ).all()

    # NEW SUPPLIER — no history
    if not audits:
        return RiskScore(
            level="NEW_SUPPLIER",
            score=50.0,
            supplier_name=supplier_name,
            reason="No audit history available for this supplier.",
            focus_areas=[],
            audits_analysed=0,
            avg_leakage=Decimal("0"),
            violation_rate=0.0
        )

    # Aggregate metrics
    total_leakage = sum(
        Decimal(str(a.total_leakage or 0)) for a in audits
    )
    avg_leakage = total_leakage / len(audits)

    audits_with_violations = sum(
        1 for a in audits
        if a.total_leakage and Decimal(str(a.total_leakage)) > 0
    )
    violation_rate = audits_with_violations / len(audits)  # 0.0 to 1.0

    # Count critical and high findings across all audits
    critical_total = 0
    high_total = 0
    clause_type_counts = defaultdict(int)

    for audit in audits:
        if not audit.discrepancies: continue
        data = json.loads(audit.discrepancies)
        for f in data.get("discrepancies", []):
            if f["severity"] == "CRITICAL": critical_total += 1
            if f["severity"] == "HIGH":     high_total += 1
            clause_type_counts[f["discrepancy_type"]] += 1

    # Check recency — did last audit have violations?
    latest_audit = max(audits, key=lambda a: a.completed_at)
    latest_had_violations = (
        latest_audit.total_leakage and
        Decimal(str(latest_audit.total_leakage)) > 100
    )

    # Compute composite score (0–100, higher = riskier)
    score = 0.0
    score += violation_rate * 40          # up to 40 pts: how often they violate
    score += min(float(avg_leakage) / 1000, 30)  # up to 30 pts: avg leakage size
    score += min(critical_total * 5, 20)  # up to 20 pts: critical findings
    score += 10 if latest_had_violations else 0   # 10 pts: recent violation

    score = min(100.0, round(score, 1))

    # Classify
    if score >= 60:      level = "HIGH"
    elif score >= 30:    level = "MEDIUM"
    else:                level = "LOW"

    # Build reason
    if level == "HIGH":
        reason = (
            f"{supplier_name} violated contract terms in "
            f"{audits_with_violations} of {len(audits)} audits "
            f"with ${avg_leakage:,.2f} average leakage."
        )
    elif level == "MEDIUM":
        reason = (
            f"{supplier_name} has {audits_with_violations} violation(s) "
            f"across {len(audits)} audits. "
            f"Average leakage: ${avg_leakage:,.2f}."
        )
    else:
        reason = (
            f"{supplier_name} has a strong compliance record "
            f"across {len(audits)} audits."
        )

    # Focus areas: top 3 most violated clause types
    focus_areas = [
        k.replace("_", " ").title()
        for k, _ in sorted(
            clause_type_counts.items(),
            key=lambda x: x[1], reverse=True
        )[:3]
    ]

    return RiskScore(
        level=level,
        score=score,
        supplier_name=supplier_name,
        reason=reason,
        focus_areas=focus_areas,
        audits_analysed=len(audits),
        avg_leakage=avg_leakage,
        violation_rate=violation_rate
    )
```

### Step 2: API endpoint

```
POST /api/predict/risk
Request:
{
  "supplier_name": str | null,   -- if known (from Contract Library match)
  "invoice_file_id": str | null  -- if supplier name unknown, extract from PDF
}

Response:
{
  "supplier_name":    str,
  "risk_level":       "HIGH" | "MEDIUM" | "LOW" | "NEW_SUPPLIER",
  "risk_score":       float,
  "reason":           str,
  "focus_areas":      list[str],
  "audits_analysed":  int,
  "avg_leakage":      str       -- formatted $ string
}
```

If supplier_name is null, extract it from the PDF using
extract_supplier_from_invoice() before scoring.

Add endpoint to backend/api/routes/audit.py.

## WHAT TO BUILD — FRONTEND

### Update Upload.jsx

After each invoice file is selected (before Run Audit is clicked):

```jsx
// When file is added to invoice list:
// 1. Upload file → get file_id
// 2. POST /api/predict/risk with {invoice_file_id}
// 3. While loading: show spinner next to filename
// 4. When done: show RiskBadge next to filename

function RiskBadge({ risk }) {
  const config = {
    HIGH:         { color: "bg-red-100 text-red-800",    icon: "🔴", label: "High Risk" },
    MEDIUM:       { color: "bg-yellow-100 text-yellow-800", icon: "🟡", label: "Medium Risk" },
    LOW:          { color: "bg-green-100 text-green-800", icon: "🟢", label: "Low Risk" },
    NEW_SUPPLIER: { color: "bg-gray-100 text-gray-600",  icon: "⚪", label: "New Supplier" }
  }[risk.risk_level]

  return (
    
      
        {config.icon} {config.label}
      
      {risk.reason}
      {risk.focus_areas.length > 0 && (
        
          Watch: {risk.focus_areas.join(", ")}
        
      )}
    
  )
}
```

Show risk prediction below each uploaded invoice filename.
The "Run Audit" button is NOT blocked by risk prediction — it is
informational only. User can run the audit regardless of risk level.

### Also update:

**AuditReport.jsx header** — add risk badge next to supplier name
(fetch score on page load using supplier_name from audit_report.summary)

**SupplierScorecard.jsx** — add a "Risk" column to the leaderboard table
showing HIGH/MEDIUM/LOW badge per supplier (computed from existing
supplier_scores data — no new API call needed, derive from score band)

## IMPLEMENTATION ORDER

1. backend/services/risk_scorer.py — compute_risk_score()
2. backend/api/routes/audit.py — POST /api/predict/risk
3. frontend/src/api/audit.js — predictRisk(invoiceFileId)
4. frontend/src/components/RiskBadge.jsx — reusable badge component
5. Update Upload.jsx — call predictRisk after file upload, show badge
6. Update AuditReport.jsx — show risk badge in header
7. Update SupplierScorecard.jsx — add Risk column

## DONE WHEN

- Uploading an invoice from a supplier with 4+ violations → shows HIGH RISK
  with correct reason and focus areas within 3 seconds
- Uploading an invoice from a supplier with no violations → shows LOW RISK
- Uploading an invoice from an unknown supplier → shows NEW SUPPLIER
  (supplier name extraction from PDF works correctly)
- Risk badge appears on Upload page BEFORE Run Audit is clicked
- "Run Audit" button still works normally regardless of risk level
- Focus areas list correct clause types (e.g. "Overcharge, Missed Discount")
- AuditReport header shows risk badge matching the supplier's history

Do not build ML-based prediction yet (this is purely heuristic).
Do not block audit execution based on risk level.
Do not show risk scores for suppliers with < 1 completed audit.

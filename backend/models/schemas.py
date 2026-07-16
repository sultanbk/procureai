"""
FILE CANONICAL IDENTIFIER: backend/models/schemas.py
MODULE ROLE: Defines Pydantic schemas, TypedDict states, and data contracts used across the ProcureAI application.
SYSTEM BOUNDARY: Type definition, serialization, and input validation layer. No database, filesystem, or external API execution boundaries.
STATE DEPENDENCY / DATA CONTRACTS: Exposes data contracts for PipelineState, ContractRulebook, InvoiceData, DiscrepancyList, AuditReport, and HTTP request/response payloads.
CRITICAL LOGIC: Implements custom BeforeValidator (normalize_decimal / CleanDecimal) that utilizes regular expressions to strip currency symbols/formatting and robustly parse numeric inputs into python Decimal objects.
"""

import re
from typing import TypedDict, Optional, List, Dict, Literal, Annotated, NotRequired
from pydantic import BaseModel, Field, BeforeValidator
from decimal import Decimal

import logging as _logging

_decimal_logger = _logging.getLogger("procureai.decimal")


def normalize_decimal(v) -> Decimal:
    """
    Normalizes string/numeric values into a clean Decimal representation.
    Removes currency symbols, commas, and spaces.

    IMPORTANT: Logs a warning (with the original value) whenever the input
    cannot be parsed deterministically.  Never silently returns 0.00 for
    genuinely unparseable monetary values — that would create false
    discrepancies downstream.
    """
    if v is None:
        _decimal_logger.warning(
            "normalize_decimal received None — defaulting to 0.00. "
            "This may indicate a missing value in an invoice or contract."
        )
        return Decimal("0.00")
    if isinstance(v, Decimal):
        return v
    if isinstance(v, (int, float)):
        return Decimal(str(v))
        
    val_str = str(v).strip()
    original_value = val_str  # preserve for diagnostics
    
    # Remove currency symbols and common letters (e.g. INR, USD, Rs, etc.)
    val_str = re.sub(r'[^\d\.\,\-]', '', val_str)
    
    # Handle thousand separators vs decimal separators
    if ',' in val_str and '.' in val_str:
        comma_idx = val_str.find(',')
        dot_idx = val_str.find('.')
        if comma_idx < dot_idx:
            val_str = val_str.replace(',', '')
        else:
            val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        parts = val_str.split(',')
        if len(parts) == 2 and len(parts[1]) == 2:
            val_str = val_str.replace(',', '.')
        else:
            val_str = val_str.replace(',', '')
            
    if not val_str:
        _decimal_logger.warning(
            "normalize_decimal: input '%s' reduced to empty string after "
            "stripping non-numeric characters — defaulting to 0.00. "
            "Review the source document for data quality issues.",
            original_value,
        )
        return Decimal("0.00")
        
    try:
        return Decimal(val_str)
    except Exception:
        match = re.search(r'[-+]?\d*\.\d+|\d+', val_str)
        if match:
            _decimal_logger.warning(
                "normalize_decimal: partial parse of '%s' — extracted '%s'. "
                "The full value could not be parsed as a Decimal.",
                original_value, match.group(),
            )
            return Decimal(match.group())
        _decimal_logger.error(
            "normalize_decimal: FAILED to parse '%s' as any numeric value. "
            "Returning 0.00 — THIS WILL LIKELY CAUSE A FALSE DISCREPANCY. "
            "Investigate the source document immediately.",
            original_value,
        )
        return Decimal("0.00")

CleanDecimal = Annotated[Decimal, BeforeValidator(normalize_decimal)]

# --- PIPELINE STATE ---

class PipelineState(TypedDict):
    audit_id: str
    contract_path: str
    invoice_paths: List[str]
    contract_text: str
    invoice_texts: List[str]
    rulebook: NotRequired[Optional[Dict]]
    invoice_data: NotRequired[Optional[List[Dict]]]
    # v3 Node 3 outputs
    cross_validation: NotRequired[Optional[Dict]]
    candidate_map: NotRequired[Optional[Dict]]
    # Node 4 outputs
    discrepancies: NotRequired[Optional[List[Dict]]]
    data_required_flags: NotRequired[Optional[List[Dict]]]
    review_flags: NotRequired[Optional[List[Dict]]]
    audit_report: NotRequired[Optional[Dict]]
    errors: NotRequired[List[Dict]]
    current_agent: str
    halt: NotRequired[bool]
    # v4 additions
    unit_conversions: NotRequired[Optional[Dict]]       # {line_id: {rule_id: conversion_info}}
    reverse_sweep: NotRequired[Optional[Dict]]          # ReverseSweepResult
    cross_invoice: NotRequired[Optional[Dict]]          # CrossInvoiceResult

# --- AGENT ERROR SCHEMA ---

class AgentError(BaseModel):
    agent: str       # "contract_parser" | "invoice_extractor" | etc.
    error_type: Literal[
        "pdf_extraction_failed",
        "llm_call_failed",
        "validation_failed",
        "rule_application_failed",
        "no_rules_found",
        "no_line_items_found",
        "hallucinated_clause",
        "timeout"
    ]
    message: str       # Human-readable explanation
    recoverable: bool  # True = pipeline can continue, False = must halt
    partial_data: Optional[Dict] = None  # Any partial output before failure

# --- AGENT 1 OUTPUT — ContractRulebook ---

class VolumeTier(BaseModel):
    min_units: int
    max_units: Optional[int] = None   # None means "and above"
    unit_price: CleanDecimal

class PricingRule(BaseModel):
    rule_id: str            # "R001", "R002" ...
    rule_type: Literal["volume_tier", "flat_rate", "sla_penalty", "early_payment_discount", "bundle_discount", "cap_rate", "annual_adjustment", "milestone_penalty", "unknown"]
    description: str            # Human-readable description of this rule
    clause_reference: str            # e.g. "Section 4.2, Schedule B"
    clause_text: str            # Exact quoted text from contract
    applies_to: str            # Which line item / service this rule governs
    effective_from: Optional[str] = None  # ISO date string or None
    effective_until: Optional[str] = None  # ISO date string or None
    expected_cost_formula: Optional[str] = None  # Code as Data: Python expression

    # Type-specific fields — only one group populated per rule
    # volume_tier
    tiers: Optional[List[VolumeTier]] = None

    # flat_rate
    flat_unit_price: Optional[CleanDecimal] = None
    standard_unit_price: Optional[CleanDecimal] = None

    # sla_penalty
    sla_threshold_pct: Optional[float] = None   # e.g. 0.99 = 99%
    penalty_pct: Optional[float] = None   # e.g. 0.12 = 12% of invoice

    # early_payment_discount
    payment_window_days: Optional[int] = None   # e.g. 10 = Net-10
    discount_pct: Optional[float] = None

    # bundle_discount
    bundle_threshold: Optional[int] = None   # units/hours to trigger bundle
    bundle_price: Optional[CleanDecimal] = None   # discounted price after threshold

    # cap_rate
    cap_amount: Optional[CleanDecimal] = None   # maximum chargeable amount
    cap_applies_to: Optional[str] = None   # what the cap governs

    extraction_confidence: float        # 0.0 – 1.0, agent's confidence in extraction

    # v4: Clause byte anchoring — character offsets in the original contract_text
    clause_start_offset: Optional[int] = None   # char position where clause_text begins
    clause_end_offset: Optional[int] = None     # char position where clause_text ends

    # v4: Self-consistency metadata
    vote_agreement: Optional[str] = None   # "3/3", "2/3", "1/3" — how many passes agreed

class ContractRulebook(BaseModel):
    supplier_name: str
    contract_id: str
    contract_date: Optional[str] = None        # ISO date
    contract_currency: str = "INR"
    rules: List[PricingRule]    # All extracted rules
    unextracted_sections: List[str] = Field(default_factory=list)   # Sections agent could not parse
    extraction_notes: str = ""            # Any caveats the agent wants to flag

# --- AGENT 2 OUTPUT — InvoiceData ---

class LineItem(BaseModel):
    line_id: str          # "L001", "L002" ...
    raw_description: str          # Exact text from invoice
    mapped_contract_item: str          # Matched contract service/product name
    mapping_confidence: float        # 0.0 – 1.0
    quantity: CleanDecimal
    unit_price_charged: CleanDecimal
    line_total_charged: CleanDecimal
    billing_period: Optional[str] = None  # "October 2024"
    # v3 conditional rule support data
    sla_actual_pct: Optional[float] = None
    milestone_date: Optional[str] = None
    milestone_status: Optional[str] = None
    extraction_confidence: float = 1.0
    arithmetic_valid: bool = True
    notes: str = ""

class InvoiceValidation(BaseModel):
    totals_match: bool
    all_lines_mapped: bool
    arithmetic_errors: List[str]   # Empty if all line arithmetic correct
    unmapped_lines: List[str]   # line_ids that could not be mapped

class InvoiceData(BaseModel):
    invoice_id: str
    invoice_date: str         # ISO date
    billing_period: str         # "October 2024"
    supplier_name: str
    invoice_total: CleanDecimal
    line_items: List[LineItem]
    validation: InvoiceValidation
    # v3 fields
    notes: str = ""
    milestone_statements: List[str] = Field(default_factory=list)
    penalties_applied: Optional[float] = None
    invoice_arithmetic_valid: bool = True

# --- AGENT 3 OUTPUT (V3) — Cross Validation ---

class CrossValidationResult(BaseModel):
    candidate_map: Dict[str, List[str]]
    unmapped_lines: List[str]
    rules_without_data: List[Dict]
    rules_never_billed: List[str]

class DataRequiredFlag(BaseModel):
    rule_id: str
    clause_section: str
    reason: str

class ReviewFlag(BaseModel):
    line_id: Optional[str] = None
    rule_id: Optional[str] = None
    reason: str
    critic_reasoning: Optional[str] = None
    clause_text: Optional[str] = None

# --- AGENT 4 OUTPUT — Discrepancy + DiscrepancyList ---

class Discrepancy(BaseModel):
    finding_id: str          # "F001", "F002" ...
    invoice_id: str
    line_id: str          # References LineItem.line_id
    rule_id: str          # References PricingRule.rule_id
    discrepancy_type: Literal[
        "overcharge",
        "missed_discount",
        "unapplied_penalty",
        "incorrect_rate",
        "missing_credit",
        "period_mismatch"
    ]
    description: str          # Plain English explanation
    clause_reference: str          # e.g. "Section 4.2, Schedule B"
    clause_text: str            # Exact quoted contract text
    quantity: CleanDecimal
    unit_price_charged: CleanDecimal
    unit_price_expected: CleanDecimal
    line_total_charged: CleanDecimal
    line_total_expected: CleanDecimal
    delta: CleanDecimal      # expected - charged (negative = overcharge)
    severity: Literal["CRITICAL", "HIGH", "MEDIUM"]
    recommendation: Literal["DISPUTE", "ESCALATE", "MONITOR", "REVIEW"]
    confidence: float        # 0.0 – 1.0
    critic_status: Literal["CONFIRMED", "NEEDS_HUMAN_REVIEW"]
    critic_reasoning: Optional[str] = None
    narrative: Optional[str] = None

class CompliantLine(BaseModel):
    line_id: str
    rule_id: str
    description: str = "Line item complies with contract terms"

class DiscrepancyList(BaseModel):
    audit_id: str
    discrepancies: List[Discrepancy]
    compliant_lines: List[CompliantLine]
    skipped_lines: List[str]          # line_ids skipped due to low confidence
    total_delta: CleanDecimal            # Sum of all discrepancy deltas
    checker_notes: str = ""

# --- AGENT 4 OUTPUT — AuditReport ---

class AuditSummary(BaseModel):
    supplier_name: str
    contract_id: str
    audit_date: str          # ISO datetime
    billing_period: str
    total_leakage: CleanDecimal      # Absolute value, always positive
    total_lines_audited: int
    compliant_lines: int
    compliance_score: float          # (compliant_lines / total_lines) * 100
    discrepancy_count: int
    critical_count: int
    high_count: int
    medium_count: int
    executive_summary: str          # 2–3 sentences for CFO

class AuditReport(BaseModel):
    audit_id: str
    summary: AuditSummary
    discrepancies: List[Discrepancy]  # Sorted: CRITICAL → HIGH → MEDIUM
    compliant_lines: List[CompliantLine]
    recommendations: List[str]    # Ordered action items
    report_generated_at: str          # ISO datetime
    # v3 fields
    data_required_flags: List[DataRequiredFlag] = Field(default_factory=list)
    review_flags: List[ReviewFlag] = Field(default_factory=list)
    rules_never_billed: List[str] = Field(default_factory=list)
    # v4 fields
    missing_credits: List[Dict] = Field(default_factory=list)    # From reverse_sweep
    price_drifts: List[Dict] = Field(default_factory=list)       # From cross_invoice_analyzer

# --- API REQUEST / RESPONSE SCHEMAS ---

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    size_bytes: int
    file_type: Literal["contract", "invoice"]

class AuditRequest(BaseModel):
    contract_file_id: str
    invoice_file_ids: List[str]     # min 1, max 10
    supplier_name: Optional[str] = None # if provided, overrides extracted name
    force: bool = False             # if true, bypasses duplicate check

class AuditStatusResponse(BaseModel):
    audit_id: str
    status: Literal[
        "PENDING",
        "EXTRACTING_PDF",
        "PARSING_CONTRACT",
        "EXTRACTING_INVOICES",
        "CROSS_VALIDATING",
        "CHECKING_COMPLIANCE",
        "GENERATING_REPORT",
        "COMPLETE",
        "FAILED"
    ]
    current_agent: Optional[str] = None
    progress_pct: int           # 0 – 100
    agents_completed: List[str] = Field(default_factory=list)
    partial_results: Optional[Dict] = None
    audit_report: Optional[AuditReport] = None
    error_detail: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    supplier_name: Optional[str] = None
    contract_file: Optional[str] = None
    invoice_files: Optional[List[str]] = None

class AuditListItem(BaseModel):
    audit_id: str
    supplier_name: str
    status: str
    total_leakage: Optional[CleanDecimal] = None
    created_at: str

class SupplierScoreCard(BaseModel):
    supplier_name:             str
    latest_score:              float
    previous_score:            Optional[float] = None
    trend:                     Literal["improving", "worsening", "stable", "new"]
    audit_count:               int
    total_leakage_identified:  Decimal
    last_audit_date:           str
    risk_band:                 Literal["green", "amber", "red"]

class SupplierSummaryKPIs(BaseModel):
    total_suppliers_tracked:      int
    average_score:                float
    suppliers_in_red_zone:        int
    total_leakage_all_time:       Decimal
    most_at_risk_supplier:        Optional[str] = None
    most_improved_supplier:       Optional[str] = None

class HeatmapCell(BaseModel):
    count:         int
    total_leakage: Decimal

class ClauseInsight(BaseModel):
    clause_type:      str
    total_count:      int
    total_leakage:    Decimal
    recommendation:   str

class HeatmapInsights(BaseModel):
    most_violated_clause_type: Optional[str] = None
    most_problematic_supplier: Optional[str] = None
    clause_insights:           List[ClauseInsight]

class HeatmapData(BaseModel):
    suppliers:              List[str]
    clause_types:           List[str]
    grid:                   Dict[str, Dict[str, HeatmapCell]]
    column_totals:          Dict[str, HeatmapCell]
    row_totals:             Dict[str, HeatmapCell]
    insights:               HeatmapInsights


class DisputeLetterRequest(BaseModel):
    audit_id:         str
    company_name:     str
    signatory_name:   str
    signatory_title:  str
    supplier_contact: str
    supplier_email:   Optional[str] = None
    due_date:         str
    reference_number: Optional[str] = None


class DisputeLetterRevisionRequest(BaseModel):
    audit_id: str
    current_letter_text: str
    change_request: str


class DisputeLetterResponse(BaseModel):
    letter_text:    str
    letter_html:    str
    findings_count: int
    total_disputed: str
    supplier_email: Optional[str] = None

class ChatMessage(BaseModel):
    role: Literal["user", "model", "assistant"]
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = Field(default_factory=list)

class AliasUpdate(BaseModel):
    aliases: List[str]


class RuleChange(BaseModel):
    change_type:   Literal["MODIFIED", "ADDED", "REMOVED"]
    rule_type:     str
    applies_to:    str
    old_clause:    Optional[str] = None
    new_clause:    Optional[str] = None
    old_rule:      Optional[PricingRule] = None
    new_rule:      Optional[PricingRule] = None
    impact:        Literal["BETTER", "WORSE", "NEUTRAL"]
    differences:   List[str] = Field(default_factory=list)
    description:   str


class ComparisonSummary(BaseModel):
    executive_summary:   str
    negotiation_flags:   List[str]
    overall_impact:      Literal["BETTER", "WORSE", "MIXED", "UNCHANGED"]


class ComparisonResult(BaseModel):
    comparison_id:       str
    supplier_name:       str
    old_contract_id:     str
    new_contract_id:     str
    changes:             List[RuleChange]
    summary:             str
    negotiation_flags:   List[str]
    overall_impact:      Literal["BETTER", "WORSE", "MIXED", "UNCHANGED"]
    worse_count:         int = 0
    better_count:        int = 0
    neutral_count:       int = 0


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

class SupplierViolationSummary(BaseModel):
    supplier_name: str
    audits_analysed: int
    audit_period_start: str
    audit_period_end: str
    total_leakage: Decimal
    total_findings: int
    clause_violations: dict
    leakage_trend: str
    monthly_leakage: dict

class NegotiationBrief(BaseModel):
    brief_id:             str
    supplier_name:        str
    generated_at:         str
    audits_analysed:      int
    audit_period:         str
    total_leakage_basis:  Decimal
    executive_summary:    str
    violation_analysis:   List[ViolationPattern]
    demands:              List[NegotiationDemand]
    risk_rating:          Literal["LOW","MEDIUM","HIGH"]
    recommended_stance:   Literal["AGGRESSIVE","FIRM","COLLABORATIVE"]
    stance_rationale:     str

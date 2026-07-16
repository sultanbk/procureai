"""
ProcureAI - File Summary

What it does:
Defines declarative SQLAlchemy ORM models representing the database schema.

What it means:
The definitive relational database structure mappings (e.g. Audit, Discrepancies, WatchedFiles).

Importance in Project:
Critical. Core database representation shared by all backend services and API routes.
"""

from sqlalchemy import Column, String, Float, DateTime, Text, Integer, ForeignKey, Numeric
from backend.core.db import Base
from backend.core.time import utc_now

class Audit(Base):
    __tablename__ = "audits"
    
    id = Column(String, primary_key=True, index=True) # e.g. "aud_20241115_abc123"
    status = Column(String, nullable=False)           # PENDING | EXTRACTING_PDF | ... | COMPLETE | FAILED
    supplier_name = Column(String, nullable=True)
    contract_file = Column(String, nullable=True)      # stored file path
    invoice_files = Column(String, nullable=True)      # JSON array of file paths
    rulebook = Column(Text, nullable=True)             # JSON (ContractRulebook)
    invoice_data = Column(Text, nullable=True)         # JSON (InvoiceData[])
    discrepancies = Column(Text, nullable=True)        # JSON (DiscrepancyList)
    audit_report = Column(Text, nullable=True)         # JSON (AuditReport)
    total_leakage = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)
    error_detail = Column(Text, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    level = Column(String, nullable=False)
    agent = Column(String, nullable=True)
    message = Column(Text, nullable=False)


class DisputeLetter(Base):
    __tablename__ = "dispute_letters"

    audit_id = Column(String, ForeignKey("audits.id"), primary_key=True)
    letter_text = Column(Text, nullable=False)
    letter_html = Column(Text, nullable=False)
    request_payload = Column(Text, nullable=True)
    findings_count = Column(Integer, default=0, nullable=False)
    total_disputed = Column(String, nullable=True)
    supplier_email = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, nullable=False)

class SupplierScore(Base):
    __tablename__ = "supplier_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_name = Column(String, nullable=False, index=True)
    audit_id = Column(String, ForeignKey("audits.id"), nullable=False)
    score = Column(Float, nullable=False)
    total_lines = Column(Integer, nullable=False)
    compliant_lines = Column(Integer, nullable=False)
    critical_count = Column(Integer, default=0, nullable=False)
    high_count = Column(Integer, default=0, nullable=False)
    medium_count = Column(Integer, default=0, nullable=False)
    total_leakage = Column(Float, default=0.0, nullable=False)
    computed_at = Column(DateTime, default=utc_now, nullable=False)

class NotificationSettings(Base):
    __tablename__ = "notification_settings"
    
    id = Column(Integer, primary_key=True, default=1)
    slack_enabled = Column(Integer, default=0)        # 0 or 1
    slack_webhook_url = Column(Text, nullable=True)
    email_enabled = Column(Integer, default=0)        # 0 or 1
    email_to = Column(Text, nullable=True)             # comma-separated addresses
    email_from = Column(Text, nullable=True)
    smtp_host = Column(Text, nullable=True)
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(Text, nullable=True)
    smtp_password = Column(Text, nullable=True)        # store as-is for MVP
    alert_on_critical = Column(Integer, default=1)     # 0 or 1
    alert_on_high = Column(Integer, default=0)         # 0 or 1
    alert_threshold_inr = Column(Float, default=10000.0) # alert if leakage exceeds this
    alert_on_any_finding = Column(Integer, default=0)  # 0 or 1

class ContractChunk(Base):
    __tablename__ = "contract_chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String, ForeignKey("audits.id"), index=True, nullable=True)
    contract_id = Column(String, ForeignKey("contracts.id"), index=True, nullable=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    section_header = Column(String, nullable=True)
    embedding = Column(Text, nullable=True)

class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(String, primary_key=True)
    supplier_name = Column(String, nullable=False)
    supplier_aliases = Column(Text, nullable=True)  # JSON array
    contract_file_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=utc_now)
    is_active = Column(Integer, default=1)
    file_hash = Column(String, unique=True, index=True, nullable=True)
    version = Column(Integer, default=1, nullable=True)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    rulebook = Column(Text, nullable=True)               # JSON (ContractRulebook)

class WatchedFile(Base):
    __tablename__ = "watched_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)
    detected_at = Column(DateTime, default=utc_now)
    status = Column(String, default="PENDING")
    matched_contract_id = Column(String, nullable=True)
    audit_id = Column(String, nullable=True)
    supplier_name_extracted = Column(String, nullable=True)
    error_detail = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)


class Comparison(Base):
    __tablename__ = "comparisons"
    
    id = Column(String, primary_key=True)
    supplier_name = Column(String, nullable=True)
    old_contract_file = Column(String, nullable=True)
    new_contract_file = Column(String, nullable=True)
    old_rulebook = Column(Text, nullable=True)               # JSON (ContractRulebook)
    new_rulebook = Column(Text, nullable=True)               # JSON (ContractRulebook)
    diff_result = Column(Text, nullable=True)                # JSON (ComparisonResult)
    created_at = Column(DateTime, default=utc_now)
    status = Column(String, default="PENDING")

class NegotiationBrief(Base):
    __tablename__ = "negotiation_briefs"
    
    id = Column(String, primary_key=True)
    supplier_name = Column(String, nullable=False, index=True)
    generated_at = Column(DateTime, default=utc_now)
    audits_analysed = Column(Integer, nullable=True)
    total_leakage_basis = Column(Numeric, nullable=True)
    brief_json = Column(Text, nullable=True)               # JSON (NegotiationBrief schema)
    status = Column(String, default="COMPLETE")

class FindingFeedback(Base):
    __tablename__ = "finding_feedback"

    id = Column(String, primary_key=True)
    audit_id = Column(String, ForeignKey("audits.id"), index=True)
    finding_id = Column(String, nullable=False)           # F001, MC001, PD001, etc.
    supplier_name = Column(String, nullable=True)
    rule_id = Column(String, nullable=True)
    rule_type = Column(String, nullable=True)
    applies_to = Column(String, nullable=True)
    human_verdict = Column(String, nullable=False)        # CORRECT | FALSE_POSITIVE | FALSE_NEGATIVE | ADJUSTED
    adjusted_delta = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, default=utc_now)


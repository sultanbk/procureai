"""
FILE CANONICAL IDENTIFIER: scripts/run_cloudscale_deep_dive.py
PURPOSE: Runs an end-to-end deep dive compliance audit trace on CloudScale Technologies (SEC EDGAR Exhibit 10) across a 3-month invoice series.
"""

import os
import sys
import json
import asyncio
import time
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, delete
from backend.core import config
from backend.core.db import AsyncSessionLocal, engine, Base
from backend.models.audit import Audit, AuditLog, SupplierScore, ContractChunk, DisputeLetter
from backend.core.pdf_extractor import extract_pdf_text
from backend.agents.pipeline import build_pipeline

async def run_deep_dive():
    print("=" * 70)
    print("      PROCUREAI — STEP 2: CLOUDSCALE DEEP-DIVE AUDIT TRACE")
    print("=" * 70)

    # 1. Setup paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    contract_path = os.path.join(base_dir, "data", "synthetic", "contracts", "c009_cloudscale_technologies_edgar.pdf")
    invoice_paths = [
        os.path.join(base_dir, "data", "synthetic", "invoices", "c009_invoice_i018.pdf"), # Month 1 (Jan) - Clean Control
        os.path.join(base_dir, "data", "synthetic", "invoices", "c009_invoice_i019.pdf"), # Month 2 (Feb) - Egress Tier + Support Cap + SLA Breach
        os.path.join(base_dir, "data", "synthetic", "invoices", "c009_invoice_i020.pdf")  # Month 3 (Mar) - Early Payment Discount
    ]

    print(f"\n[1] Contract PDF: {os.path.basename(contract_path)}")
    for i, p in enumerate(invoice_paths, 1):
        print(f"    Invoice {i}: {os.path.basename(p)}")

    # 2. Prepare DB record
    audit_id = "trace_cloudscale_edgar"
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Delete prior audit records
        await session.execute(delete(AuditLog).where(AuditLog.audit_id == audit_id))
        await session.execute(delete(SupplierScore).where(SupplierScore.audit_id == audit_id))
        await session.execute(delete(ContractChunk).where(ContractChunk.audit_id == audit_id))
        await session.execute(delete(DisputeLetter).where(DisputeLetter.audit_id == audit_id))
        await session.execute(delete(Audit).where(Audit.id == audit_id))
        await session.commit()

        new_audit = Audit(
            id=audit_id,
            status="PENDING",
            contract_file=contract_path,
            invoice_files=json.dumps(invoice_paths)
        )
        session.add(new_audit)
        await session.commit()

    # 3. Extract text from PDFs
    print("\n[2] Extracting PDF Text...")
    contract_text = extract_pdf_text(contract_path)
    invoice_texts = [extract_pdf_text(p) for p in invoice_paths]
    print(f"    Contract Text Length: {len(contract_text)} chars")
    for idx, txt in enumerate(invoice_texts, 1):
        print(f"    Invoice {idx} Text Length: {len(txt)} chars")

    initial_state = {
        "audit_id": audit_id,
        "contract_path": contract_path,
        "invoice_paths": invoice_paths,
        "contract_text": contract_text,
        "invoice_texts": invoice_texts,
        "rulebook": None,
        "invoice_data": None,
        "discrepancies": None,
        "audit_report": None,
        "errors": [],
        "current_agent": "init",
        "halt": False
    }

    # 4. Run the Pipeline
    print("\n[3] Executing LangGraph Multi-Agent Pipeline...")
    start_time = time.time()
    graph = build_pipeline()
    final_state = await graph.ainvoke(initial_state)
    elapsed = time.time() - start_time
    print(f"    Pipeline completed in {elapsed:.2f}s!")

    # 5. Display Structured Agent Outputs
    print("\n" + "=" * 70)
    print("                    PIPELINE AUDIT FINDINGS")
    print("=" * 70)

    # Rulebook
    rulebook = final_state.get("rulebook") or {}
    rules = rulebook.get("rules", [])
    print(f"\n--- [AGENT 1 & 2] EXTRACTED CONTRACT RULES ({len(rules)} Rules Found) ---")
    for r in rules:
        print(f"  • [{r.get('rule_id')}] Type: {r.get('rule_type')} | Applies To: {r.get('applies_to')}")
        print(f"    Clause: \"{r.get('clause_text')}\"")
        if r.get('tiers'):
            print(f"    Tiers: {r.get('tiers')}")
        if r.get('cap_amount'):
            print(f"    Cap Limit: ${r.get('cap_amount')}")
        if r.get('discount_pct'):
            print(f"    Discount: {r.get('discount_pct')}% (Window: {r.get('payment_window_days')} days)")
        if r.get('sla_threshold_pct'):
            print(f"    SLA Threshold: {r.get('sla_threshold_pct')}% | Penalty: {r.get('penalty_pct')}%")

    # Invoices Extracted
    invoice_data = final_state.get("invoice_data") or []
    print(f"\n--- EXTRACTED INVOICE DATA ({len(invoice_data)} Invoices Parsed) ---")
    for inv in invoice_data:
        print(f"  • Inv #{inv.get('invoice_number')} ({inv.get('billing_period')}) | Total: ${float(inv.get('invoice_total', 0)):,.2f} | Items: {len(inv.get('line_items', []))}")
        if inv.get('notes'):
            print(f"    Notes: {inv.get('notes')}")

    # Compliance Checker Discrepancies
    discrepancies_state = final_state.get("discrepancies") or {}
    discrepancies = discrepancies_state.get("discrepancies", [])
    print(f"\n--- [AGENT 4] COMPLIANCE DISCREPANCIES ({len(discrepancies)} Overcharges Detected) ---")
    for d in discrepancies:
        print(f"  [FLAG - {d.get('severity')}] Line: {d.get('line_id')} ({d.get('description')})")
        print(f"    Charged: ${float(d.get('charged_amount', 0)):,.2f} | Expected: ${float(d.get('expected_amount', 0)):,.2f} | Delta: ${float(d.get('delta', 0)):,.2f}")
        print(f"    Violated Rule: {d.get('rule_id')}")
        if d.get('reasoning'):
            print(f"    Reasoning: {d.get('reasoning')}")

    # Reverse Sweep Missing Credits
    reverse_sweep_state = final_state.get("reverse_sweep") or {}
    missing_credits = reverse_sweep_state.get("missing_credits", [])
    print(f"\n--- [AGENT 5] REVERSE SWEEP ({len(missing_credits)} Missing Credits Claimed) ---")
    for mc in missing_credits:
        print(f"  [CREDIT CLAIM] Rule Type: {mc.get('rule_type')} | Expected Credit: ${float(mc.get('expected_credit', 0)):,.2f}")
        print(f"    Trigger Clause: \"{mc.get('trigger_clause')}\"")
        print(f"    Evidence: {mc.get('invoice_evidence')}")

    # Cross Invoice Price Drift
    cross_invoice_state = final_state.get("cross_invoice") or {}
    drifts = cross_invoice_state.get("price_drift_findings", [])
    print(f"\n--- [AGENT 6] CROSS-INVOICE PRICE DRIFT ({len(drifts)} Drifts Flagged) ---")
    for df in drifts:
        print(f"  [PRICE DRIFT] Item: {df.get('description')} | Base: ${df.get('base_unit_price')} -> Current: ${df.get('current_unit_price')} (Change: {df.get('pct_change')}%)")

    # Final Report Summary
    audit_report = final_state.get("audit_report") or {}
    summary = audit_report.get("summary") or {}
    print(f"\n--- [AGENT 7] FINAL AUDIT EXECUTIVE SUMMARY ---")
    print(f"  Total Invoiced Spend:    ${float(summary.get('total_invoiced', 0)):,.2f}")
    print(f"  Total Financial Leakage: ${float(summary.get('total_leakage', 0)):,.2f}")
    print(f"  Potential Recovery ROI:  ${float(summary.get('potential_recovery', 0)):,.2f}")
    print(f"  Compliance Health Score: {summary.get('compliance_score')}/100")
    if audit_report.get("executive_summary"):
        print(f"\n  Executive Narrative:\n  {audit_report.get('executive_summary')}")

    print("\n" + "=" * 70)
    print("                    TRACE COMPLETED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_deep_dive())

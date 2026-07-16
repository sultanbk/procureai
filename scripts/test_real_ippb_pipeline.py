import asyncio
import json
import os
from sqlalchemy import select

from backend.core.db import AsyncSessionLocal
from backend.models.audit import Audit
from backend.core.pdf_extractor import extract_pdf_text
from backend.agents.pipeline import build_pipeline
from backend.models.schemas import PipelineState
from backend.core.logging_config import setup_logging
from dotenv import load_dotenv

load_dotenv()
setup_logging(os.getenv("LOG_LEVEL", "INFO"), os.getenv("LOG_FORMAT", "CONSOLE"))

async def test_end_to_end_pipeline():
    audit_id = "aud_ippb_real_pipeline"
    contract_path = "MSA_3c7d18f7-25f8-466b-adf61694603255182_managerprocurement1.pdf"
    invoice_paths = [
        "data/synthetic/invoices/ippb_invoice.pdf"
    ]
    
    # 1. Prepare DB record
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            await session.delete(existing)
            await session.commit()
            
        new_audit = Audit(
            id=audit_id,
            status="PENDING",
            contract_file=contract_path,
            invoice_files=json.dumps(invoice_paths)
        )
        session.add(new_audit)
        await session.commit()
        print(f"Prepared DB record for audit {audit_id}.")

    # 2. Extract texts
    print("Extracting contract text...")
    contract_text = extract_pdf_text(contract_path)
    
    invoice_texts = []
    for ip in invoice_paths:
        print(f"Extracting invoice text from {ip}...")
        invoice_texts.append(extract_pdf_text(ip))

    # 3. Create initial PipelineState dict
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

    # Use the real model
    os.environ["MOCK_LLM"] = "false"

    # 4. Build and run the compiled LangGraph pipeline
    print("\n--- Compiling and Running LangGraph Pipeline with MOCK_LLM=false ---")
    graph = build_pipeline()
    
    # Run the graph
    final_state = await graph.ainvoke(initial_state)
    
    print("\n--- Pipeline Execution Finished ---")
    print(f"Final Agent: {final_state.get('current_agent')}")
    print(f"Halt Status: {final_state.get('halt')}")
    print(f"Errors list: {final_state.get('errors')}")

    # 5. Verify the Audit Report in State
    report = final_state.get("audit_report")
    if report:
        summary = report.get("summary", {})
        print("\n--- Final Audit Report Summary ---")
        print(f"Supplier Name:       {summary.get('supplier_name')}")
        print(f"Contract ID:         {summary.get('contract_id')}")
        print(f"Total Leakage Found: INR {summary.get('total_leakage')}")
        print(f"Lines Audited:       {summary.get('total_lines_audited')}")
        print(f"Compliant Lines:     {summary.get('compliant_lines')}")
        print(f"Discrepancies Count: {summary.get('discrepancy_count')}")
        print(f"Executive Summary:\n{summary.get('executive_summary')}")
        
        print("\nRecommendations:")
        for idx, rec in enumerate(report.get("recommendations", []), 1):
            print(f"  {idx}. {rec}")
            
        print("\nDiscrepancies Detail:")
        for idx, d in enumerate(report.get("discrepancies", []), 1):
            print(f"  Finding #{idx} ({d.get('finding_id')}): Rule {d.get('rule_id')} ({d.get('discrepancy_type')}) - Delta: INR {d.get('delta')}")
            print(f"    Description: {d.get('description')}")
    else:
        print("ERROR: No audit report returned in state.")

    # 6. Check database record
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        db_audit = result.scalar_one_or_none()
        if db_audit:
            print("\n--- Database Record After Pipeline Run ---")
            print(f"Status in DB:       {db_audit.status}")
            print(f"Leakage in DB:      {db_audit.total_leakage}")
            print(f"Has Audit Report:   {db_audit.audit_report is not None}")
            print(f"Completed At:       {db_audit.completed_at}")
            if db_audit.status == "FAILED":
                print(f"Error Detail:       {db_audit.error_detail}")
        else:
            print("ERROR: DB record not found.")

if __name__ == "__main__":
    asyncio.run(test_end_to_end_pipeline())

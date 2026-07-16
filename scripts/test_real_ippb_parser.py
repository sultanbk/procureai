import asyncio
import json
import os
from sqlalchemy import select

from backend.core.db import AsyncSessionLocal
from backend.models.audit import Audit
from backend.core.pdf_extractor import extract_pdf_text
from backend.agents.contract_parser.agent import run_contract_parser
from backend.models.schemas import PipelineState

async def test_agent():
    audit_id = "aud_ippb_test"
    contract_path = "MSA_3c7d18f7-25f8-466b-adf61694603255182_managerprocurement1.pdf"
    
    # 1. Clean up and insert initial Audit record in DB
    async with AsyncSessionLocal() as session:
        # Delete existing if any
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
            invoice_files=json.dumps([])
        )
        session.add(new_audit)
        await session.commit()
        print(f"Inserted audit {audit_id} with status PENDING.")

    # 2. Read or extract text from PDF
    print(f"Extracting text from {contract_path}...")
    contract_text = extract_pdf_text(contract_path)
    print(f"Extracted {len(contract_text)} characters.")

    # 3. Form initial PipelineState
    initial_state = PipelineState(
        audit_id=audit_id,
        contract_path=contract_path,
        invoice_paths=[],
        contract_text=contract_text,
        invoice_texts=[],
        rulebook=None,
        invoice_data=None,
        discrepancies=None,
        audit_report=None,
        errors=[],
        current_agent="init",
        halt=False
    )

    # 4. Set MOCK_LLM=false to use the real Gemini model
    os.environ["MOCK_LLM"] = "false"
    
    # 5. Run agent
    print("Running run_contract_parser with MOCK_LLM=false...")
    final_state = await run_contract_parser(initial_state)
    
    print("\n--- RESULTS ---")
    print(f"Halt status: {final_state.get('halt')}")
    print(f"Errors list: {final_state.get('errors')}")
    
    rulebook = final_state.get("rulebook")
    if rulebook:
        print(f"\nExtracted Rulebook:")
        print(f"Supplier Name: {rulebook.get('supplier_name')}")
        print(f"Contract ID:   {rulebook.get('contract_id')}")
        print(f"Rules count:   {len(rulebook.get('rules', []))}")
        print(json.dumps(rulebook, indent=2, default=str))
    else:
        print("ERROR: No rulebook returned in state.")

if __name__ == "__main__":
    asyncio.run(test_agent())

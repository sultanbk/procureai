"""
ProcureAI - Batch Test Audits Runner
Runs all synthetic test datasets so they appear in Audit History (GET /api/audits),
EXCEPT c008_premium_cold_foods_contract.pdf (Premium Cold Foods) which will be run
live by the user during screen recording.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import asyncio
from datetime import timedelta
from sqlalchemy import select, delete
from backend.core.db import AsyncSessionLocal
from backend.models.audit import Audit, AuditLog, SupplierScore, ContractChunk, DisputeLetter
from backend.api.routes.audit import run_audit_pipeline
from backend.core.time import utc_now

# All test datasets to run.
# NOTE: c008_premium_cold_foods_contract.pdf is EXCLUDED per user instructions.
TEST_DATASETS = [
    {
        "audit_id": "aud_c001_apex",
        "supplier_name": "Apex Logistics Ltd",
        "contract_file": "data/synthetic/contracts/c001_apex_logistics_contract.pdf",
        "invoice_files": [
            "data/synthetic/invoices/c001_invoice_i001.pdf",
            "data/synthetic/invoices/c001_invoice_i002.pdf"
        ]
    },
    {
        "audit_id": "aud_c002_techsoft",
        "supplier_name": "TechSoft Solutions",
        "contract_file": "data/synthetic/contracts/c002_techsoft_solutions_contract.pdf",
        "invoice_files": [
            "data/synthetic/invoices/c002_invoice_i003.pdf",
            "data/synthetic/invoices/c002_invoice_i004.pdf"
        ]
    },
    {
        "audit_id": "aud_c003_buildright",
        "supplier_name": "BuildRight Contractors",
        "contract_file": "data/synthetic/contracts/c003_buildright_contractors_contract.pdf",
        "invoice_files": [
            "data/synthetic/invoices/c003_invoice_i005.pdf",
            "data/synthetic/invoices/c003_invoice_i006.pdf"
        ]
    },
    {
        "audit_id": "aud_c004_medisupply",
        "supplier_name": "MediSupply Corp",
        "contract_file": "data/synthetic/contracts/c004_medisupply_contract.pdf",
        "invoice_files": [
            "data/synthetic/invoices/c004_invoice_i007.pdf",
            "data/synthetic/invoices/c004_invoice_i008.pdf"
        ]
    },
    {
        "audit_id": "aud_c005_cloudhost",
        "supplier_name": "CloudHost India",
        "contract_file": "data/synthetic/contracts/c005_cloudhost_contract.pdf",
        "invoice_files": [
            "data/synthetic/invoices/c005_invoice_i009.pdf",
            "data/synthetic/invoices/c005_invoice_i010.pdf"
        ]
    },
    {
        "audit_id": "aud_c006_proservices",
        "supplier_name": "ProServices Consulting",
        "contract_file": "data/synthetic/contracts/c006_proservices_contract.pdf",
        "invoice_files": [
            "data/synthetic/invoices/c006_invoice_i011.pdf"
        ]
    },
    {
        "audit_id": "aud_c007_sysco",
        "supplier_name": "Sysco Food Services Solutions, LLC",
        "contract_file": "data/synthetic/contracts/c007_sysco_contract.pdf",
        "invoice_files": [
            "data/synthetic/invoices/c007_invoice_i012.pdf",
            "data/synthetic/invoices/c007_invoice_i013.pdf",
            "data/synthetic/invoices/c007_invoice_i014.pdf"
        ]
    },
    {
        "audit_id": "aud_c009_cloudscale",
        "supplier_name": "CloudScale Technologies Inc.",
        "contract_file": "data/synthetic/contracts/c009_cloudscale_technologies_edgar.pdf",
        "invoice_files": [
            "data/synthetic/invoices/c009_invoice_i018.pdf",
            "data/synthetic/invoices/c009_invoice_i019.pdf",
            "data/synthetic/invoices/c009_invoice_i020.pdf"
        ]
    },
    {
        "audit_id": "aud_c010_transnational",
        "supplier_name": "TransNational Freight Corp.",
        "contract_file": "data/synthetic/contracts/c010_transnational_freight_edgar.pdf",
        "invoice_files": [
            "data/synthetic/invoices/c010_invoice_i021.pdf",
            "data/synthetic/invoices/c010_invoice_i022.pdf"
        ]
    },
    {
        "audit_id": "aud_c011_apex_facilities",
        "supplier_name": "Apex Facilities Maintenance",
        "contract_file": "data/synthetic/contracts/c011_apex_facilities_maintenance_edgar.pdf",
        "invoice_files": [
            "data/synthetic/invoices/c011_invoice_i023.pdf",
            "data/synthetic/invoices/c011_invoice_i024.pdf",
            "data/synthetic/invoices/c011_invoice_i025.pdf"
        ]
    }
]


from sqlalchemy import text

async def clean_database_audit(session, audit_id: str):
    tables = [
        "dispute_tickets",
        "reconciliation_records",
        "finding_feedback",
        "dispute_letters",
        "supplier_scores",
        "contract_chunks",
        "audit_logs"
    ]
    for t in tables:
        try:
            await session.execute(text(f"DELETE FROM {t} WHERE audit_id = :aid"), {"aid": audit_id})
        except Exception:
            pass
    await session.execute(text("DELETE FROM audits WHERE id = :aid"), {"aid": audit_id})
    await session.commit()


async def run_batch():
    # Strict verification: Ensure c008 is NOT present in batch list
    for ds in TEST_DATASETS:
        assert "c008" not in ds["contract_file"].lower(), "CRITICAL: c008 must not be in batch test runner!"
        assert "premium" not in ds["supplier_name"].lower(), "CRITICAL: Premium Cold Foods must not be run!"

    print(f"Starting batch execution for {len(TEST_DATASETS)} test audits (excluding Premium Cold Foods)...")

    # Clean legacy demo / scratch audits
    legacy_ids_to_clean = ["trace_cloudscale_edgar", "test_apex_audit_full", "aud_test_portal_001"]
    async with AsyncSessionLocal() as session:
        for leg_id in legacy_ids_to_clean:
            await clean_database_audit(session, leg_id)

    # Stagger created_at times slightly so they sort chronologically in history
    base_time = utc_now() - timedelta(hours=len(TEST_DATASETS))

    results = []
    for idx, ds in enumerate(TEST_DATASETS):
        audit_id = ds["audit_id"]
        supplier_name = ds["supplier_name"]
        contract_file = ds["contract_file"]
        invoice_files = ds["invoice_files"]
        created_time = base_time + timedelta(hours=idx, minutes=idx * 2)

        print(f"\n[{idx + 1}/{len(TEST_DATASETS)}] Running audit '{audit_id}' for {supplier_name}...")

        async with AsyncSessionLocal() as session:
            await clean_database_audit(session, audit_id)

            new_audit = Audit(
                id=audit_id,
                status="PENDING",
                supplier_name=supplier_name,
                contract_file=contract_file,
                invoice_files=json.dumps(invoice_files),
                created_at=created_time
            )
            session.add(new_audit)
            await session.commit()

        # Run pipeline
        try:
            await run_audit_pipeline(audit_id, contract_file, invoice_files)
        except Exception as e:
            print(f"Error running pipeline for {audit_id}: {e}")

        # Check result
        async with AsyncSessionLocal() as session:
            stmt = select(Audit).where(Audit.id == audit_id)
            res = (await session.execute(stmt)).scalar_one_or_none()
            if res:
                print(f"  -> Finished: Status={res.status}, Leakage={res.total_leakage}, Supplier={res.supplier_name}")
                results.append({
                    "audit_id": res.id,
                    "supplier_name": res.supplier_name,
                    "status": res.status,
                    "total_leakage": res.total_leakage
                })

    print("\n" + "=" * 60)
    print("BATCH AUDIT RUN SUMMARY:")
    print("=" * 60)
    for r in results:
        print(f"{r['audit_id']:<26} | {r['supplier_name']:<35} | {r['status']:<14} | Leakage: {r['total_leakage']}")
    print("=" * 60)
    print("Verification: Premium Cold Foods (c008) remains completely unrun and clean for recording.")


if __name__ == "__main__":
    asyncio.run(run_batch())

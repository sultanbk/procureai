import pytest
import hashlib
import json
import asyncio
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from backend.models.audit import Contract, Audit
from backend.api.routes.contracts import register_contract
from backend.agents.contract_parser.agent import run_contract_parser
from backend.services.contract_chunker import ensure_contract_chunks
from fastapi import UploadFile
from io import BytesIO

class MockUploadFile(UploadFile):
    def __init__(self, filename: str, content: bytes):
        super().__init__(file=BytesIO(content), filename=filename)
        self._content = content

    async def read(self, size: int = -1) -> bytes:
        return self._content

class MockBackgroundTasks:
    def __init__(self):
        self.tasks = []

    def add_task(self, func, *args, **kwargs):
        self.tasks.append((func, args, kwargs))

    async def run_all(self):
        for func, args, kwargs in self.tasks:
            res = func(*args, **kwargs)
            if asyncio.iscoroutine(res):
                await res
        self.tasks.clear()

@pytest.mark.asyncio
async def test_contract_library_versioning_and_lookup(db_engine, db_session, monkeypatch):
    """
    Test the Contract Library:
    1. Register a contract (creates v1).
    2. Register the exact same contract file (detects duplicate by file_hash, skips creation).
    3. Register a new contract file for the same supplier (creates v2).
    4. Run audit parser with invoice dates, resolving correct contract version.
    """
    # Create test session maker bound to the in-memory test engine
    test_session_maker = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    # Monkeypatch AsyncSessionLocal in all relevant modules
    monkeypatch.setattr("backend.api.routes.contracts.AsyncSessionLocal", test_session_maker)
    monkeypatch.setattr("backend.agents.contract_parser.agent.AsyncSessionLocal", test_session_maker)
    monkeypatch.setattr("backend.api.routes.audit.AsyncSessionLocal", test_session_maker)

    # Mock PDF extraction to avoid parsing binary mock files
    def mock_extract_pdf_text(path_str):
        return "Section 1: Billed at INR 500 flat rate. This is dummy text for testing."

    monkeypatch.setattr("backend.services.contract_chunker.extract_pdf_text", mock_extract_pdf_text)
    monkeypatch.setattr("backend.core.pdf_extractor.extract_pdf_text", mock_extract_pdf_text)

    # Setup mock upload files
    pdf_v1_content = b"%PDF-1.4 dummy version 1 contract content"
    file_v1_hash = hashlib.sha256(pdf_v1_content).hexdigest()
    file_v1 = MockUploadFile("contract_v1.pdf", pdf_v1_content)
    
    bg_tasks = MockBackgroundTasks()

    # Monkeypatch run_baseline_extraction to mock rulebook extraction
    async def mock_run_baseline_extraction_v1(audit_id: str, contract_path: str):
        dummy_rulebook = {
            "supplier_name": "Apex Logistics Ltd",
            "contract_id": "ctr_apex_v1",
            "contract_currency": "INR",
            "rules": []
        }
        
        async with test_session_maker() as session:
            stmt = select(Audit).where(Audit.id == audit_id)
            res = await session.execute(stmt)
            db_audit = res.scalar_one_or_none()
            if db_audit:
                db_audit.rulebook = json.dumps(dummy_rulebook)
                db_audit.supplier_name = "Apex Logistics Ltd"
                db_audit.status = "CROSS_VALIDATING"
            
            stmt_contract = select(Contract).where(Contract.file_hash == file_v1_hash)
            res_contract = await session.execute(stmt_contract)
            contract = res_contract.scalar_one_or_none()
            if contract:
                contract.rulebook = json.dumps(dummy_rulebook)
                contract.supplier_name = "Apex Logistics Ltd"
            await session.commit()

    monkeypatch.setattr("backend.api.routes.contracts.run_baseline_extraction", mock_run_baseline_extraction_v1)

    # 1. Register contract v1
    res_v1 = await register_contract(
        background_tasks=bg_tasks,
        file=file_v1,
        supplier_name="Apex Logistics Ltd",
        supplier_aliases="Apex, Apex Cargo",
        valid_from="2026-01-01",
        valid_until="2026-02-28"
    )
    
    assert res_v1["supplier_name"] == "Apex Logistics Ltd"
    assert res_v1["version"] == 1
    
    # Run the background baseline extraction task
    await bg_tasks.run_all()

    # Check v1 registered in DB
    stmt = select(Contract).where(Contract.file_hash == file_v1_hash)
    res_db = await db_session.execute(stmt)
    contract_v1_db = res_db.scalar_one_or_none()
    assert contract_v1_db is not None
    assert contract_v1_db.version == 1
    assert contract_v1_db.rulebook is not None

    # 2. Try registering the duplicate PDF
    file_v1_dup = MockUploadFile("contract_v1_copy.pdf", pdf_v1_content)
    res_dup = await register_contract(
        background_tasks=bg_tasks,
        file=file_v1_dup,
        supplier_name="Apex Logistics Ltd",
        supplier_aliases="Apex",
        valid_from="2026-01-01",
        valid_until="2026-02-28"
    )
    assert "message" in res_dup
    assert res_dup["message"] == "Contract already registered"
    assert res_dup["id"] == res_v1["id"]

    # 3. Register contract v2 (different content -> different hash)
    pdf_v2_content = b"%PDF-1.4 dummy version 2 contract content"
    file_v2_hash = hashlib.sha256(pdf_v2_content).hexdigest()
    file_v2 = MockUploadFile("contract_v2.pdf", pdf_v2_content)

    # Mock v2 extraction saving rules
    async def mock_run_baseline_extraction_v2(audit_id: str, contract_path: str):
        dummy_rulebook_v2 = {
            "supplier_name": "Apex Logistics Ltd",
            "contract_id": "ctr_apex_v2",
            "contract_currency": "INR",
            "rules": []
        }
        async with test_session_maker() as session:
            stmt = select(Audit).where(Audit.id == audit_id)
            res = await session.execute(stmt)
            db_audit = res.scalar_one_or_none()
            if db_audit:
                db_audit.rulebook = json.dumps(dummy_rulebook_v2)
                db_audit.supplier_name = "Apex Logistics Ltd"
                db_audit.status = "CROSS_VALIDATING"
            
            stmt_contract = select(Contract).where(Contract.file_hash == file_v2_hash)
            res_contract = await session.execute(stmt_contract)
            contract = res_contract.scalar_one_or_none()
            if contract:
                contract.rulebook = json.dumps(dummy_rulebook_v2)
                contract.supplier_name = "Apex Logistics Ltd"
            await session.commit()

    monkeypatch.setattr("backend.api.routes.contracts.run_baseline_extraction", mock_run_baseline_extraction_v2)

    res_v2 = await register_contract(
        background_tasks=bg_tasks,
        file=file_v2,
        supplier_name="Apex Logistics Ltd",
        supplier_aliases="Apex",
        valid_from="2026-03-01",
        valid_until="2026-12-31"
    )
    assert res_v2["version"] == 2

    await bg_tasks.run_all()

    # 4. Test date-based resolution inside run_contract_parser
    # Scenario: Invoice date is 2026-01-15 (falls in v1 range: 2026-01-01 to 2026-02-28)
    audit_id = "test_audit_jan"
    new_audit = Audit(
        id=audit_id,
        status="PENDING",
        contract_file=contract_v1_db.contract_file_path,
        invoice_files="[]",
        created_at=datetime.utcnow()
    )
    db_session.add(new_audit)
    await db_session.commit()

    state = {
        "audit_id": audit_id,
        "contract_text": "Section 1: Billed at INR 500 flat rate.",
        "contract_path": contract_v1_db.contract_file_path,
        "invoice_data": [
            {
                "supplier_name": "Apex Logistics Ltd",
                "invoice_date": "2026-01-15",
                "billing_period": "January 2026"
            }
        ],
        "errors": [],
        "halt": False
    }

    # Override the monkeypatches to use the actual run_contract_parser for resolution testing
    monkeypatch.undo()
    
    # Re-apply the database session monkeypatching since monkeypatch.undo() clears everything
    monkeypatch.setattr("backend.api.routes.contracts.AsyncSessionLocal", test_session_maker)
    monkeypatch.setattr("backend.agents.contract_parser.agent.AsyncSessionLocal", test_session_maker)
    monkeypatch.setattr("backend.api.routes.audit.AsyncSessionLocal", test_session_maker)
    
    # Re-apply mock PDF extraction since monkeypatch.undo() cleared it
    monkeypatch.setattr("backend.services.contract_chunker.extract_pdf_text", mock_extract_pdf_text)
    monkeypatch.setattr("backend.core.pdf_extractor.extract_pdf_text", mock_extract_pdf_text)

    parsed_state = await run_contract_parser(state)
    assert parsed_state["rulebook"] is not None
    
    # Refetch audit record to check resolved contract rulebook
    stmt_aud = select(Audit).where(Audit.id == audit_id)
    res_aud = await db_session.execute(stmt_aud)
    audit_db = res_aud.scalar_one_or_none()
    assert audit_db is not None
    assert audit_db.supplier_name == "Apex Logistics Ltd"

    # Test chunks retrieval links to contract_id
    chunks = await ensure_contract_chunks(audit_id, db_session)
    assert len(chunks) > 0
    assert chunks[0].contract_id == contract_v1_db.id


@pytest.mark.asyncio
async def test_list_contracts_status_mapping(db_engine, db_session, monkeypatch):
    """
    Test that list_contracts returns correct statuses (PARSED/PROCESSING/FAILED)
    based on rulebook presence and baseline audit status.
    """
    from backend.api.routes.contracts import list_contracts
    
    test_session_maker = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    monkeypatch.setattr("backend.api.routes.contracts.AsyncSessionLocal", test_session_maker)
    
    # 1. Clear existing Contracts and Audits to isolate test
    from sqlalchemy import delete
    await db_session.execute(delete(Audit))
    await db_session.execute(delete(Contract))
    await db_session.commit()
    
    # 2. Add contract 1: has rulebook -> PARSED
    c1 = Contract(
        id="ctr_c1",
        supplier_name="Supplier 1",
        supplier_aliases="[]",
        contract_file_path="c1.pdf",
        original_filename="c1.pdf",
        is_active=1,
        version=1,
        rulebook='{"rules": []}'
    )
    
    # 3. Add contract 2: no rulebook, baseline audit is FAILED -> FAILED
    c2 = Contract(
        id="ctr_c2",
        supplier_name="Supplier 2",
        supplier_aliases="[]",
        contract_file_path="c2.pdf",
        original_filename="c2.pdf",
        is_active=1,
        version=1,
        rulebook=None
    )
    a2 = Audit(
        id="base_ctr_c2",
        status="FAILED",
        supplier_name="Supplier 2",
        contract_file="c2.pdf"
    )
    
    # 4. Add contract 3: no rulebook, baseline audit is CROSS_VALIDATING -> PARSED (resolves race condition)
    c3 = Contract(
        id="ctr_c3",
        supplier_name="Supplier 3",
        supplier_aliases="[]",
        contract_file_path="c3.pdf",
        original_filename="c3.pdf",
        is_active=1,
        version=1,
        rulebook=None
    )
    a3 = Audit(
        id="base_ctr_c3",
        status="CROSS_VALIDATING",
        supplier_name="Supplier 3",
        contract_file="c3.pdf"
    )
    
    # 5. Add contract 4: no rulebook, baseline audit is PENDING -> PROCESSING
    c4 = Contract(
        id="ctr_c4",
        supplier_name="Supplier 4",
        supplier_aliases="[]",
        contract_file_path="c4.pdf",
        original_filename="c4.pdf",
        is_active=1,
        version=1,
        rulebook=None
    )
    a4 = Audit(
        id="base_ctr_c4",
        status="PENDING",
        supplier_name="Supplier 4",
        contract_file="c4.pdf"
    )
    
    db_session.add_all([c1, c2, a2, c3, a3, c4, a4])
    await db_session.commit()
    
    # Call list_contracts
    contracts_list = await list_contracts()
    
    # Map by id
    by_id = {c["id"]: c for c in contracts_list}
    
    assert by_id["ctr_c1"]["status"] == "PARSED"
    assert by_id["ctr_c2"]["status"] == "FAILED"
    assert by_id["ctr_c3"]["status"] == "PARSED"
    assert by_id["ctr_c4"]["status"] == "PROCESSING"


@pytest.mark.asyncio
async def test_reactivate_archived_contract(db_engine, db_session, monkeypatch):
    """
    Test that re-registering an archived (is_active=0) contract
    successfully reactivates it (is_active=1) and updates its details.
    """
    test_session_maker = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    monkeypatch.setattr("backend.api.routes.contracts.AsyncSessionLocal", test_session_maker)
    
    # 1. Clear existing Contracts and Audits to isolate test
    from sqlalchemy import delete
    await db_session.execute(delete(Audit))
    await db_session.execute(delete(Contract))
    await db_session.commit()
    
    # 2. Add archived contract
    pdf_content = b"%PDF-1.4 dummy reactivate contract content"
    file_hash = hashlib.sha256(pdf_content).hexdigest()
    
    c = Contract(
        id="ctr_to_reactivate",
        supplier_name="Old Supplier Name",
        supplier_aliases='["Old Alias"]',
        contract_file_path="old_path.pdf",
        original_filename="old_filename.pdf",
        is_active=0,  # Archived!
        file_hash=file_hash,
        version=1,
        rulebook='{"rules": []}'
    )
    db_session.add(c)
    await db_session.commit()
    
    # Setup mock upload file
    file_mock = MockUploadFile("new_filename.pdf", pdf_content)
    bg_tasks = MockBackgroundTasks()
    
    # 3. Call register_contract to register it again
    res = await register_contract(
        background_tasks=bg_tasks,
        file=file_mock,
        supplier_name="New Reactivated Supplier",
        supplier_aliases="New Alias 1, New Alias 2",
        valid_from="2026-05-01",
        valid_until="2026-06-30"
    )
    
    # Verify response
    assert res["id"] == "ctr_to_reactivate"
    
    # Expire session to clear cache and force reloading from SQLite
    db_session.expire_all()
    
    # Verify database state
    stmt = select(Contract).where(Contract.id == "ctr_to_reactivate")
    res_db = await db_session.execute(stmt)
    contract_db = res_db.scalar_one_or_none()
    
    assert contract_db is not None
    assert contract_db.is_active == 1  # Should be reactivated!
    assert contract_db.supplier_name == "New Reactivated Supplier"
    assert json.loads(contract_db.supplier_aliases) == ["New Alias 1", "New Alias 2"]
    assert contract_db.valid_from.date().isoformat() == "2026-05-01"
    assert contract_db.valid_until.date().isoformat() == "2026-06-30"


@pytest.mark.asyncio
async def test_register_contract_without_supplier_name(db_engine, db_session, monkeypatch):
    """
    Test that registering a contract without providing a supplier name:
    1. Saves the contract with supplier name set to 'Extracting...'.
    2. Background extraction runs and updates the contract supplier name and recalculates version.
    """
    test_session_maker = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    monkeypatch.setattr("backend.api.routes.contracts.AsyncSessionLocal", test_session_maker)
    monkeypatch.setattr("backend.agents.contract_parser.agent.AsyncSessionLocal", test_session_maker)
    
    # 1. Clear existing Contracts and Audits to isolate test
    from sqlalchemy import delete
    await db_session.execute(delete(Audit))
    await db_session.execute(delete(Contract))
    await db_session.commit()
    
    # Pre-add an existing contract for "Apex Logistics Ltd" version 1
    # to test version incrementation when new contract resolves to the same supplier
    c1 = Contract(
        id="ctr_apex_v1",
        supplier_name="Apex Logistics Ltd",
        supplier_aliases="[]",
        contract_file_path="old_path.pdf",
        original_filename="old_filename.pdf",
        is_active=1,
        file_hash="some_old_hash",
        version=1,
        rulebook='{"rules": []}'
    )
    db_session.add(c1)
    await db_session.commit()
    
    # Setup mock upload file
    pdf_content = b"%PDF-1.4 dummy auto-extraction contract content"
    file_mock = MockUploadFile("apex_contract_new.pdf", pdf_content)
    bg_tasks = MockBackgroundTasks()
    
    # 2. Register without supplier_name
    res = await register_contract(
        background_tasks=bg_tasks,
        file=file_mock,
        supplier_name=None, # Not provided!
        supplier_aliases="Apex, Apex Cargo"
    )
    
    assert res["supplier_name"] == "Extracting..."
    
    # Verify DB state right after upload (is in "Extracting..." state)
    db_session.expire_all()
    stmt = select(Contract).where(Contract.id == res["id"])
    res_db = await db_session.execute(stmt)
    contract_db = res_db.scalar_one_or_none()
    assert contract_db is not None
    assert contract_db.supplier_name == "Extracting..."
    assert contract_db.version == 1  # Calculated relative to "Extracting..."
    
    # 3. Simulate background extraction returning the parsed rulebook for "Apex Logistics Ltd"
    # Mock LLM and extract functions to avoid hitting external APIs
    def mock_extract_pdf_text(path_str):
        return "Section 1: Dummy contract text."
    
    monkeypatch.setattr("backend.services.contract_chunker.extract_pdf_text", mock_extract_pdf_text)
    monkeypatch.setattr("backend.core.pdf_extractor.extract_pdf_text", mock_extract_pdf_text)
    
    # Mock the mock router to return the expected contract rulebook response
    from backend.core.mock_router import MockResponse
    
    def mock_get_mock_response(contents, generation_config):
        return MockResponse(json.dumps({
            "supplier_name": "Apex Logistics Ltd",
            "contract_id": "ctr_apex_extracted",
            "contract_currency": "USD",
            "rules": [
                {
                    "rule_id": "rule_flat_rate",
                    "rule_type": "flat_rate",
                    "description": "Flat rate pricing rule.",
                    "clause_reference": "Section 1",
                    "clause_text": "Dummy contract text.",
                    "applies_to": "all",
                    "extraction_confidence": 0.95
                }
            ]
        }))
        
    monkeypatch.setattr("backend.core.llm_client.get_mock_response", mock_get_mock_response)
    
    # Run background tasks
    await bg_tasks.run_all()
    
    # Refetch contract and verify it has been updated and version recalculated to v2
    db_session.expire_all()
    stmt = select(Contract).where(Contract.id == res["id"])
    res_db = await db_session.execute(stmt)
    contract_db = res_db.scalar_one_or_none()
    
    assert contract_db is not None
    assert contract_db.supplier_name == "Apex Logistics Ltd"
    assert contract_db.version == 2  # Recalculated from v1 of "Apex Logistics Ltd" to v2!
    assert contract_db.rulebook is not None


@pytest.mark.asyncio
async def test_permanent_delete_contract(db_engine, db_session, monkeypatch):
    """
    Test that permanently deleting a contract removes the contract,
    its baseline audit, its audit logs, and its contract chunks.
    """
    test_session_maker = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    monkeypatch.setattr("backend.api.routes.contracts.AsyncSessionLocal", test_session_maker)
    
    # 1. Clear existing Contracts and Audits to isolate test
    from sqlalchemy import delete
    from backend.models.audit import ContractChunk, AuditLog
    await db_session.execute(delete(Audit))
    await db_session.execute(delete(Contract))
    await db_session.execute(delete(ContractChunk))
    await db_session.execute(delete(AuditLog))
    await db_session.commit()
    
    # 2. Set up contract, baseline audit, audit logs, chunks
    c = Contract(
        id="ctr_to_del",
        supplier_name="Supplier Del",
        supplier_aliases="[]",
        contract_file_path="del.pdf",
        original_filename="del.pdf",
        is_active=1,
        version=1,
        rulebook='{"rules": []}'
    )
    a = Audit(
        id="base_ctr_to_del",
        status="CROSS_VALIDATING",
        supplier_name="Supplier Del",
        contract_file="del.pdf"
    )
    log = AuditLog(
        audit_id="base_ctr_to_del",
        level="INFO",
        message="test message"
    )
    chunk = ContractChunk(
        audit_id="base_ctr_to_del",
        contract_id="ctr_to_del",
        chunk_index=0,
        chunk_text="test text"
    )
    
    db_session.add_all([c, a, log, chunk])
    await db_session.commit()
    
    # Verify they exist
    assert (await db_session.execute(select(Contract).where(Contract.id == "ctr_to_del"))).scalar_one_or_none() is not None
    assert (await db_session.execute(select(Audit).where(Audit.id == "base_ctr_to_del"))).scalar_one_or_none() is not None
    assert (await db_session.execute(select(ContractChunk).where(ContractChunk.contract_id == "ctr_to_del"))).scalar_one_or_none() is not None
    assert (await db_session.execute(select(AuditLog).where(AuditLog.audit_id == "base_ctr_to_del"))).scalar_one_or_none() is not None
    
    # 3. Call delete_contract with permanent=True
    from backend.api.routes.contracts import delete_contract
    res = await delete_contract("ctr_to_del", permanent=True)
    
    # Verify database state after deletion
    db_session.expire_all()
    assert (await db_session.execute(select(Contract).where(Contract.id == "ctr_to_del"))).scalar_one_or_none() is None
    assert (await db_session.execute(select(Audit).where(Audit.id == "base_ctr_to_del"))).scalar_one_or_none() is None
    assert (await db_session.execute(select(ContractChunk).where(ContractChunk.contract_id == "ctr_to_del"))).scalar_one_or_none() is None
    assert (await db_session.execute(select(AuditLog).where(AuditLog.audit_id == "base_ctr_to_del"))).scalar_one_or_none() is None

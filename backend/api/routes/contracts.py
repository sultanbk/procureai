"""
ProcureAI - File Summary

What it does:
Defines routers to upload contracts, read parsed rules, and perform comparisons.

What it means:
Controller for contract library administration and comparison functions.

Importance in Project:
High. Enables users to manage baseline rules, upload MSAs, and inspect rule updates.
"""

# 1. Standard library
import json
import re
import uuid
import asyncio
from typing import Optional

# 2. Third-party
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update

# 3. Internal — absolute imports only (never relative)
from backend.core.db import AsyncSessionLocal
from backend.models.audit import Audit, Contract, ContractChunk, Comparison
from backend.models.schemas import ChatRequest, AliasUpdate
from backend.api.routes.upload import save_pdf_upload
from backend.core.time import utc_now

router = APIRouter(prefix="/api/contracts", tags=["contracts"])
compare_router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    supplier_name: Optional[str] = Form(None),
    supplier_aliases: str = Form(""),
    valid_from: str = Form(None),
    valid_until: str = Form(None)
):
    """
    Upload and register a contract into the library and trigger background parsing.
    """
    import hashlib
    from datetime import datetime

    # Clean supplier aliases from comma-separated string to JSON list
    try:
        aliases_list = [a.strip() for a in supplier_aliases.split(",") if a.strip()]
    except Exception:
        aliases_list = []

    supplier_name_val = (supplier_name or "").strip()
    if not supplier_name_val:
        supplier_name_val = "Extracting..."

    # Parse dates
    valid_from_dt = None
    valid_until_dt = None
    if valid_from:
        try:
            valid_from_dt = datetime.fromisoformat(valid_from.replace("Z", "+00:00"))
        except Exception:
            pass
    if valid_until:
        try:
            valid_until_dt = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
        except Exception:
            pass

    # Save PDF using shared utility
    file_path, contents = await save_pdf_upload(file, "contract")
    
    # Calculate SHA-256 hash of PDF bytes
    file_hash = hashlib.sha256(contents).hexdigest()

    async with AsyncSessionLocal() as session:
        # Check if contract with this file hash already exists
        stmt_hash = select(Contract).where(Contract.file_hash == file_hash)
        res_hash = await session.execute(stmt_hash)
        existing = res_hash.scalar_one_or_none()
        if existing:
            # Reactivate if it was soft-deleted/archived
            if existing.is_active == 0:
                existing.is_active = 1
                
            # Update fields in case they changed
            if supplier_name and supplier_name.strip():
                existing.supplier_name = supplier_name.strip()
            existing.supplier_aliases = json.dumps(aliases_list)
            existing.valid_from = valid_from_dt
            existing.valid_until = valid_until_dt
            await session.commit()

            # Self-healing: If contract exists but rulebook extraction was interrupted/aborted (rulebook is NULL),
            # re-trigger the baseline extraction background task to complete the parsing.
            if not existing.rulebook:
                from sqlalchemy import delete as sqlalchemy_delete
                base_audit_id = f"base_{existing.id}"
                await session.execute(sqlalchemy_delete(Audit).where(Audit.id == base_audit_id))
                
                baseline_audit = Audit(
                    id=base_audit_id,
                    status="PENDING",
                    supplier_name=existing.supplier_name,
                    contract_file=existing.contract_file_path,
                    created_at=utc_now()
                )
                session.add(baseline_audit)
                await session.commit()
                
                background_tasks.add_task(run_baseline_extraction, base_audit_id, existing.contract_file_path)

            return {
                "id": existing.id,
                "supplier_name": existing.supplier_name,
                "supplier_aliases": json.loads(existing.supplier_aliases or "[]"),
                "contract_file_path": existing.contract_file_path,
                "original_filename": existing.original_filename,
                "uploaded_at": existing.uploaded_at.isoformat() if existing.uploaded_at else None,
                "version": existing.version,
                "valid_from": existing.valid_from.isoformat() if existing.valid_from else None,
                "valid_until": existing.valid_until.isoformat() if existing.valid_until else None,
                "message": "Contract already registered"
            }

        # Query SQLite for the max version of contracts for this supplier
        from sqlalchemy import func
        stmt_version = select(func.max(Contract.version)).where(
            func.lower(Contract.supplier_name) == supplier_name_val.lower()
        )
        res_version = await session.execute(stmt_version)
        max_ver = res_version.scalar() or 0
        new_version = max_ver + 1

        # Generate custom contract ID
        clean_name = re.sub(r'[^a-zA-Z0-9]', '_', supplier_name_val.lower()).strip("_")
        contract_id = f"ctr_{clean_name}_{uuid.uuid4().hex[:4]}"

        contract = Contract(
            id=contract_id,
            supplier_name=supplier_name_val,
            supplier_aliases=json.dumps(aliases_list),
            contract_file_path=file_path,
            original_filename=file.filename,
            uploaded_at=utc_now(),
            is_active=1,
            file_hash=file_hash,
            version=new_version,
            valid_from=valid_from_dt,
            valid_until=valid_until_dt
        )
        
        session.add(contract)
        
        # Create a baseline audit to hold the parsed rulebook and chunks
        base_audit_id = f"base_{contract.id}"
        baseline_audit = Audit(
            id=base_audit_id,
            status="PENDING",
            supplier_name=supplier_name_val,
            contract_file=file_path,
            created_at=utc_now()
        )
        session.add(baseline_audit)
        
        await session.commit()
        
    # Trigger background parsing so it's ready for future audits
    background_tasks.add_task(run_baseline_extraction, base_audit_id, file_path)

    return {
        "id": contract.id,
        "supplier_name": contract.supplier_name,
        "supplier_aliases": aliases_list,
        "contract_file_path": contract.contract_file_path,
        "original_filename": contract.original_filename,
        "uploaded_at": contract.uploaded_at.isoformat() if contract.uploaded_at else None,
        "version": contract.version,
        "valid_from": contract.valid_from.isoformat() if contract.valid_from else None,
        "valid_until": contract.valid_until.isoformat() if contract.valid_until else None
    }

async def run_baseline_extraction(audit_id: str, contract_path: str):
    """Background task to pre-extract contract rules."""
    try:
        from backend.core.pdf_extractor import extract_pdf_text
        from backend.agents.contract_parser.agent import run_contract_parser
        contract_text = await asyncio.to_thread(extract_pdf_text, contract_path)
        
        state = {
            "audit_id": audit_id,
            "contract_text": contract_text,
            "contract_path": contract_path,
            "errors": [],
            "halt": False
        }
        await run_contract_parser(state)
    except Exception as e:
        logger.error("Baseline extraction failed", error=str(e))


@router.get("")
async def list_contracts(show_archived: bool = False):
    """
    List active or archived contracts in the library.
    """
    from backend.models.audit import Audit
    async with AsyncSessionLocal() as session:
        stmt = select(Contract, Audit.status).outerjoin(
            Audit, Audit.id == "base_" + Contract.id
        )
        if not show_archived:
            stmt = stmt.where(Contract.is_active == 1)
        result = await session.execute(stmt)
        rows = result.all()

    items = []
    for c, baseline_status in rows:
        status_label = "PARSED"
        if not c.rulebook:
            if baseline_status == "FAILED":
                status_label = "FAILED"
            elif baseline_status in ("CROSS_VALIDATING", "CHECKING_COMPLIANCE", "GENERATING_REPORT", "COMPLETE"):
                status_label = "PARSED"
            else:
                status_label = "PROCESSING"
        items.append({
            "id": c.id,
            "supplier_name": c.supplier_name,
            "supplier_aliases": json.loads(c.supplier_aliases or "[]"),
            "contract_file_path": c.contract_file_path,
            "original_filename": c.original_filename,
            "uploaded_at": c.uploaded_at.isoformat() if c.uploaded_at else None,
            "is_active": c.is_active,
            "version": c.version,
            "file_hash": c.file_hash,
            "valid_from": c.valid_from.isoformat() if c.valid_from else None,
            "valid_until": c.valid_until.isoformat() if c.valid_until else None,
            "status": status_label
        })
    return items


@router.delete("/{id}")
async def delete_contract(id: str, permanent: bool = False):
    """
    Archive (soft-delete) or permanently hard-delete a contract from the library.
    """
    async with AsyncSessionLocal() as session:
        stmt = select(Contract).where(Contract.id == id)
        result = await session.execute(stmt)
        contract = result.scalar_one_or_none()
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract with ID {id} not found"
            )
        if permanent:
            from sqlalchemy import delete as sqlalchemy_delete
            from backend.models.audit import ContractChunk, AuditLog
            
            # 1. Delete associated contract chunks
            await session.execute(sqlalchemy_delete(ContractChunk).where(ContractChunk.contract_id == id))
            
            # 2. Delete baseline audit logs
            base_audit_id = f"base_{id}"
            await session.execute(sqlalchemy_delete(AuditLog).where(AuditLog.audit_id == base_audit_id))
            
            # 3. Delete baseline audit
            await session.execute(sqlalchemy_delete(Audit).where(Audit.id == base_audit_id))
            
            # 4. Delete the contract itself
            await session.delete(contract)
        else:
            contract.is_active = 0
        await session.commit()

    return {
        "message": f"Contract {id} permanently deleted successfully" if permanent else f"Contract {id} archived successfully"
    }


@router.post("/{id}/restore")
async def restore_contract(id: str):
    """
    Restore an archived contract back to active status.
    """
    async with AsyncSessionLocal() as session:
        stmt = select(Contract).where(Contract.id == id)
        result = await session.execute(stmt)
        contract = result.scalar_one_or_none()
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract with ID {id} not found"
            )
        contract.is_active = 1
        await session.commit()

    return {"message": f"Contract {id} restored successfully"}


@router.patch("/{id}/aliases")
async def update_aliases(id: str, payload: AliasUpdate):
    """
    Add or replace supplier aliases.
    """
    async with AsyncSessionLocal() as session:
        stmt = select(Contract).where(Contract.id == id)
        result = await session.execute(stmt)
        contract = result.scalar_one_or_none()
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract with ID {id} not found"
            )
        contract.supplier_aliases = json.dumps(payload.aliases)
        await session.commit()

    return {
        "id": contract.id,
        "supplier_name": contract.supplier_name,
        "supplier_aliases": payload.aliases
    }

CLAUSE_REF_PATTERN = re.compile(
    r"Section\s+[\d.]+|Schedule\s+[A-Z\d]+|Clause\s+[\d.]+",
    re.IGNORECASE,
)
CONFIDENCE_PATTERN = re.compile(
    r"\[?\s*CONFIDENCE\s*:\s*(HIGH|MEDIUM|NOT_FOUND|NOT\s+FOUND)\s*\]?",
    re.IGNORECASE,
)


def normalize_clause_ref(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().lower().rstrip(".,;:")


def extract_confidence(answer: str) -> str:
    match = CONFIDENCE_PATTERN.search(answer or "")
    if not match:
        return "not_found"
    confidence = match.group(1).upper().replace(" ", "_")
    return "not_found" if confidence == "NOT_FOUND" else confidence.lower()


def clean_answer_for_client(answer: str) -> str:
    return CONFIDENCE_PATTERN.sub("", answer or "").strip()


def get_rule_value(rule, key: str, default=None):
    if isinstance(rule, dict):
        return rule.get(key, default)
    return getattr(rule, key, default)


def build_rule_citations(answer: str, rulebook: dict) -> list[dict]:
    rules = rulebook.get("rules", []) if isinstance(rulebook, dict) else []
    answer_refs = CLAUSE_REF_PATTERN.findall(answer or "")
    citations = []
    seen = set()

    for answer_ref in answer_refs:
        normalized_answer_ref = normalize_clause_ref(answer_ref)
        if normalized_answer_ref in seen:
            continue

        matched_rule = None
        for rule in rules:
            rule_ref = str(get_rule_value(rule, "clause_reference", "") or "")
            normalized_rule_ref = normalize_clause_ref(rule_ref)
            if normalized_answer_ref and normalized_answer_ref in normalized_rule_ref:
                matched_rule = rule
                break

        if matched_rule:
            seen.add(normalized_answer_ref)
            citations.append(
                {
                    "clause_reference": get_rule_value(matched_rule, "clause_reference", answer_ref),
                    "clause_text": get_rule_value(matched_rule, "clause_text", ""),
                    "rule_id": get_rule_value(matched_rule, "rule_id", None),
                }
            )

    return citations


async def add_chunk_citations(
    audit_id: str,
    answer: str,
    citations: list[dict],
) -> list[dict]:
    seen_refs = {normalize_clause_ref(c["clause_reference"]) for c in citations}
    answer_refs = CLAUSE_REF_PATTERN.findall(answer or "")

    async with AsyncSessionLocal() as session:
        for answer_ref in answer_refs:
            normalized_answer_ref = normalize_clause_ref(answer_ref)
            if normalized_answer_ref in seen_refs:
                continue

            stmt = (
                select(ContractChunk)
                .where(
                    ContractChunk.audit_id == audit_id,
                    ContractChunk.section_header.ilike(f"%{answer_ref}%"),
                )
                .order_by(ContractChunk.chunk_index.asc())
                .limit(1)
            )
            result = await session.execute(stmt)
            chunk = result.scalar_one_or_none()
            if not chunk:
                continue

            citations.append(
                {
                    "clause_reference": chunk.section_header,
                    "clause_text": chunk.chunk_text,
                    "rule_id": None,
                }
            )
            seen_refs.add(normalized_answer_ref)

    return citations


async def chat_stream_generator(audit_id: str, request: ChatRequest):
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        db_audit = result.scalar_one_or_none()

        if not db_audit:
            suffix_data = {"citations": [], "confidence": "not_found"}
            yield (
                "I could not find this information in the contract. The contract may\n"
                "not address this, or it may be in a section that was not extracted."
            )
            yield f"\n\n---CITATIONS---\n{json.dumps(suffix_data)}"
            return

        rulebook = {}
        if db_audit.rulebook:
            try:
                rulebook = json.loads(db_audit.rulebook)
            except json.JSONDecodeError:
                rulebook = {}

        from backend.services.contract_chunker import build_rag_context

        context_str = await build_rag_context(request.message, audit_id, rulebook, session)

    from backend.core.prompt_loader import load_prompt

    try:
        system_prompt = load_prompt("contract_qa")
    except Exception:
        system_prompt = (
            "[ROLE]\nYou are a contract intelligence assistant for ProcureAI.\n"
            "Answer only from the provided contract context.\n\n"
            "[CONTEXT]\n{context}\n\n[CHAT HISTORY]\n{chat_history}"
        )

    chat_history_str = ""
    for msg in request.history[-6:]:
        role_name = "User" if msg.role == "user" else "Assistant"
        chat_history_str += f"{role_name}: {msg.content}\n"

    prompt = system_prompt.replace("{context}", context_str).replace("{chat_history}", chat_history_str)
    prompt += f"\nUser: {request.message}\nAssistant:"

    from backend.core.llm_client import get_llm

    llm = get_llm()
    full_answer = ""

    try:
        response_stream = llm.generate_content_stream(
            prompt,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 700,
            },
        )
        done = object()

        def next_chunk():
            try:
                return next(response_stream)
            except StopIteration:
                return done

        while True:
            chunk = await asyncio.to_thread(next_chunk)
            if chunk is done:
                break
            if hasattr(chunk, "text") and chunk.text:
                token = chunk.text
                full_answer += token
                yield token
    except Exception:
        full_answer = (
            "I could not find this information in the contract. The contract may\n"
            "not address this, or it may be in a section that was not extracted.\n"
            "[CONFIDENCE: NOT_FOUND]"
        )
        yield full_answer

    try:
        confidence = extract_confidence(full_answer)
        citations = build_rule_citations(full_answer, rulebook)
        citations = await add_chunk_citations(audit_id, full_answer, citations)
        suffix_data = {
            "citations": citations,
            "confidence": confidence,
            "answer": clean_answer_for_client(full_answer),
        }
    except Exception:
        suffix_data = {
            "citations": [],
            "confidence": "not_found",
            "answer": clean_answer_for_client(full_answer),
        }

    yield f"\n\n---CITATIONS---\n{json.dumps(suffix_data)}"


@router.post("/{audit_id}/chat")
async def chat_with_contract(audit_id: str, request: ChatRequest):
    """
    RAG-powered streaming chat endpoint over contract contents.
    Returns StreamingResponse containing answer tokens, terminated by citations JSON block.
    """
    # Verify audit existence before launching async stream to fail early if ID is invalid
    async with AsyncSessionLocal() as session:
        stmt = select(Audit.id).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        audit_exists = result.scalar_one_or_none()
        
    if not audit_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID {audit_id} not found"
        )
        
    return StreamingResponse(
        chat_stream_generator(audit_id, request),
        media_type="text/plain"
    )


import structlog
logger = structlog.get_logger()

# Background task for running contract version comparison
from backend.core.pdf_extractor import extract_pdf_text
from backend.services.contract_comparator import run_comparison

async def run_comparison_task(
    comparison_id: str,
    old_contract_path: str,
    new_contract_path: str
):
    try:
        old_text, new_text = await asyncio.gather(
            asyncio.to_thread(extract_pdf_text, old_contract_path),
            asyncio.to_thread(extract_pdf_text, new_contract_path),
        )
        
        async with AsyncSessionLocal() as session:
            await run_comparison(old_text, new_text, comparison_id, session)
    except Exception as e:
        logger.error("Error in run_comparison_task", comparison_id=comparison_id, error=str(e))
        async with AsyncSessionLocal() as session:
            stmt = update(Comparison).where(Comparison.id == comparison_id).values(
                status="FAILED",
                diff_result=json.dumps({"error": str(e)})
            )
            await session.execute(stmt)
            await session.commit()


@compare_router.post("/upload")
async def upload_for_comparison(
    old_contract: UploadFile = File(...),
    new_contract: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    comparison_id = f"cmp_{uuid.uuid4().hex[:8]}"
    
    # Save old and new contract files using the shared upload utility
    old_path, _ = await save_pdf_upload(old_contract, "contract")
    new_path, _ = await save_pdf_upload(new_contract, "contract")
    
    # Create comparison record in DB
    comparison = Comparison(
        id=comparison_id,
        supplier_name="Unknown",
        old_contract_file=old_path,
        new_contract_file=new_path,
        status="PENDING"
    )
    
    async with AsyncSessionLocal() as session:
        session.add(comparison)
        await session.commit()
        
    # Queue comparison task
    background_tasks.add_task(run_comparison_task, comparison_id, old_path, new_path)
    
    return {
        "comparison_id": comparison_id,
        "status": "processing"
    }


@compare_router.get("/{comparison_id}")
async def get_comparison(comparison_id: str):
    async with AsyncSessionLocal() as session:
        stmt = select(Comparison).where(Comparison.id == comparison_id)
        res = await session.execute(stmt)
        cmp = res.scalar_one_or_none()
        
    if not cmp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison with ID {comparison_id} not found"
        )
        
    if cmp.status != "COMPLETE":
        return {
            "comparison_id": cmp.id,
            "status": "processing" if cmp.status == "PENDING" else cmp.status
        }
        
    try:
        return json.loads(cmp.diff_result)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse comparison result"
        )


@compare_router.get("")
async def list_comparisons():
    async with AsyncSessionLocal() as session:
        stmt = select(Comparison).order_by(Comparison.created_at.desc())
        res = await session.execute(stmt)
        comparisons = res.scalars().all()
        
    results = []
    for cmp in comparisons:
        parsed_diff = None
        if cmp.diff_result:
            try:
                parsed_diff = json.loads(cmp.diff_result)
            except Exception:
                pass
                
        results.append({
            "id": cmp.id,
            "supplier_name": cmp.supplier_name or "Unknown",
            "old_contract_file": cmp.old_contract_file,
            "new_contract_file": cmp.new_contract_file,
            "created_at": cmp.created_at.isoformat() if cmp.created_at else None,
            "status": cmp.status,
            "diff_result": parsed_diff
        })
    return results

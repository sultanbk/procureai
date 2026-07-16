"""
ProcureAI - File Summary

What it does:
Defines endpoints to fetch, create, delete, and control audit runs.

What it means:
Controller for managing audit execution lifecycles and viewing findings.

Importance in Project:
High. Main endpoint interacting with multi-agent pipeline triggers and database logs.
"""

import os
import json
import uuid
import asyncio
from io import BytesIO
from typing import List, Dict
from fastapi import APIRouter, HTTPException, BackgroundTasks, status, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, Response
from pypdf import PdfReader, PdfWriter
from sqlalchemy import select, desc, delete, update
from backend.core.db import AsyncSessionLocal
from backend.core.config import UPLOAD_DIR as CONFIG_UPLOAD_DIR
from backend.core.time import utc_now
from backend.models.audit import Audit, AuditLog, SupplierScore, ContractChunk, DisputeLetter, WatchedFile, FindingFeedback
from backend.models.schemas import (
    AuditRequest,
    AuditStatusResponse,
    AuditListItem,
    AuditReport
)
from pydantic import BaseModel
from typing import Optional
from backend.core.pdf_extractor import extract_pdf_text
from backend.agents.pipeline import get_pipeline
from backend.core.audit_logger import log_audit_event

router = APIRouter(prefix="/api", tags=["audit"])

UPLOAD_DIR = os.path.abspath(CONFIG_UPLOAD_DIR)

def validate_uploaded_file_path(file_id_or_path: str, file_label: str) -> str:
    if not file_id_or_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{file_label} file id is required"
        )

    candidate = file_id_or_path
    if not os.path.isabs(candidate) and not any(sep in candidate for sep in ("/", "\\")):
        candidate = os.path.join(UPLOAD_DIR, candidate)

    resolved_path = os.path.abspath(candidate)
    upload_root = os.path.abspath(UPLOAD_DIR)

    if not os.path.exists(resolved_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{file_label} file not found"
        )

    if not os.path.isfile(resolved_path) or not resolved_path.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{file_label} must be an uploaded PDF file"
        )

    synthetic_root = os.path.abspath(os.path.join("data", "synthetic"))
    under_upload = os.path.commonpath([upload_root, resolved_path]) == upload_root
    under_synthetic = os.path.commonpath([synthetic_root, resolved_path]) == synthetic_root

    if not under_upload and not under_synthetic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{file_label} file is outside the configured upload or synthetic directories"
        )

    return resolved_path.replace("\\", "/")


def resolve_audit_document(db_audit: Audit, document_id: str) -> tuple[str, str, str]:
    if document_id == "contract":
        if not db_audit.contract_file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract file not found")
        return validate_uploaded_file_path(db_audit.contract_file, "Contract"), "contract", "Contract"

    if document_id.startswith("invoice-"):
        try:
            invoice_index = int(document_id.split("-", 1)[1])
            invoice_files = json.loads(db_audit.invoice_files or "[]")
            invoice_path = invoice_files[invoice_index]
        except (ValueError, IndexError, json.JSONDecodeError):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice file not found")
        return validate_uploaded_file_path(invoice_path, "Invoice"), "invoice", f"Invoice {invoice_index + 1}"

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")


def normalize_search_text(value: str) -> str:
    return " ".join((value or "").lower().split())


def find_breach_pages(pdf_path: str, finding: dict | None) -> tuple[list[int], str]:
    reader = PdfReader(pdf_path)
    if not finding:
        return [0] if reader.pages else [], ""

    clause_text = normalize_search_text(str(finding.get("clause_text") or ""))
    clause_ref = normalize_search_text(str(finding.get("clause_reference") or ""))
    description = normalize_search_text(str(finding.get("description") or ""))
    targets = [text for text in (clause_text, clause_ref, description) if text]
    matched_pages: list[int] = []

    for page_index, page in enumerate(reader.pages):
        page_text = normalize_search_text(page.extract_text() or "")
        if not page_text:
            continue
        if any(target and (target in page_text or page_text.find(target[:120]) >= 0) for target in targets):
            matched_pages.append(page_index)

    if not matched_pages and reader.pages:
        matched_pages = [0]

    highlight_text = str(finding.get("clause_text") or finding.get("description") or "")
    return matched_pages, highlight_text

async def run_audit_pipeline(audit_id: str, contract_path: str, invoice_paths: List[str]):
    try:
        await log_audit_event(audit_id, "Initializing document audit pipeline.", "INFO", "system")
        
        # 1. Update status to EXTRACTING_PDF
        async with AsyncSessionLocal() as session:
            stmt = select(Audit).where(Audit.id == audit_id)
            result = await session.execute(stmt)
            db_audit = result.scalar_one_or_none()
            if db_audit:
                db_audit.status = "EXTRACTING_PDF"
                await session.commit()
                
        # 2. Extract PDF texts
        await log_audit_event(audit_id, "Starting PDF text extraction from contract and invoice documents.", "INFO", "pdf_extractor")
        contract_text = await asyncio.to_thread(extract_pdf_text, contract_path)
        await log_audit_event(audit_id, f"Contract PDF text successfully extracted ({len(contract_text)} characters).", "INFO", "pdf_extractor")
        
        invoice_texts = []
        for idx, ip in enumerate(invoice_paths, 1):
            inv_text = await asyncio.to_thread(extract_pdf_text, ip)
            await log_audit_event(audit_id, f"Invoice {idx} of {len(invoice_paths)} text successfully extracted ({len(inv_text)} characters).", "INFO", "pdf_extractor")
            invoice_texts.append(inv_text)
        
        # 3. Initialize pipeline state
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
        
        # 3b. Check for pre-extracted baseline rulebook in Library by file hash
        async with AsyncSessionLocal() as session:
            from backend.models.audit import Contract
            import hashlib
            import os
            
            file_hash = None
            if contract_path and os.path.exists(contract_path):
                try:
                    def _read_contract():
                        with open(contract_path, "rb") as f:
                            return f.read()
                    file_bytes = await asyncio.to_thread(_read_contract)
                    file_hash = hashlib.sha256(file_bytes).hexdigest()
                except Exception:
                    pass
            
            if file_hash:
                stmt = select(Contract).where(Contract.file_hash == file_hash)
                res = await session.execute(stmt)
                contract = res.scalar_one_or_none()
                if contract and contract.rulebook:
                    rulebook_str = contract.rulebook
                    try:
                        initial_state["rulebook"] = json.loads(rulebook_str)
                    except json.JSONDecodeError:
                        pass
                    
                    # Update current audit with rulebook and supplier name
                    audit_stmt = select(Audit).where(Audit.id == audit_id)
                    db_audit = (await session.execute(audit_stmt)).scalar_one_or_none()
                    if db_audit:
                        db_audit.rulebook = rulebook_str
                        db_audit.supplier_name = contract.supplier_name
                        db_audit.status = "CROSS_VALIDATING"
                        await session.commit()
                        
                    # Pre-load chunks for Q&A
                    from backend.services.contract_chunker import ensure_contract_chunks
                    await ensure_contract_chunks(audit_id, session)
        
        
        # 4. Run the compiled LangGraph pipeline singleton
        await log_audit_event(audit_id, "Starting multi-agent contract compliance analysis pipeline.", "INFO", "system")
        graph = get_pipeline()
        await graph.ainvoke(initial_state)
        
    except Exception as e:
        await log_audit_event(audit_id, f"Initialization or PDF Extraction failed: {str(e)}", "ERROR", "pdf_extractor")
        async with AsyncSessionLocal() as session:
            stmt = select(Audit).where(Audit.id == audit_id)
            result = await session.execute(stmt)
            db_audit = result.scalar_one_or_none()
            if db_audit:
                db_audit.status = "FAILED"
                db_audit.error_detail = f"Initialization or PDF Extraction failed: {str(e)}"
                db_audit.completed_at = utc_now()
                await session.commit()


@router.post("/audit/run", response_model=Dict[str, str], status_code=status.HTTP_202_ACCEPTED)
async def run_audit(request: AuditRequest, background_tasks: BackgroundTasks):
    contract_file = validate_uploaded_file_path(request.contract_file_id, "Contract")
    invoice_files = [
        validate_uploaded_file_path(path, "Invoice")
        for path in request.invoice_file_ids
    ]
    invoice_files_json = json.dumps(invoice_files)
    
    if not request.force:
        async with AsyncSessionLocal() as session:
            stmt = select(Audit).where(
                Audit.contract_file == contract_file,
                Audit.invoice_files == invoice_files_json
            ).order_by(desc(Audit.created_at))
            existing = (await session.execute(stmt)).scalars().first()
            if existing:
                return {"audit_id": existing.id, "status": "EXISTS"}
            
    audit_id = f"aud_{uuid.uuid4().hex[:8]}"
    
    # Save initial pending state to DB
    async with AsyncSessionLocal() as session:
        new_audit = Audit(
            id=audit_id,
            status="PENDING",
            supplier_name=request.supplier_name or "Extracting...",
            contract_file=contract_file,
            invoice_files=invoice_files_json,
            created_at=utc_now()
        )
        session.add(new_audit)
        await session.commit()
        
    background_tasks.add_task(
        run_audit_pipeline,
        audit_id=audit_id,
        contract_path=contract_file,
        invoice_paths=invoice_files
    )
    
    return {"audit_id": audit_id, "status": "PENDING"}

@router.get("/audit/{audit_id}", response_model=AuditStatusResponse)
async def get_audit_status(audit_id: str):
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        db_audit = result.scalar_one_or_none()
        
    if not db_audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID {audit_id} not found"
        )
        
    # Map status to progress percentage, current agent, completed agents
    status_map = {
        "PENDING": (5, "init", []),
        "EXTRACTING_PDF": (15, "pdf_extractor", []),
        "EXTRACTING_INVOICES": (30, "invoice_extractor", []),
        "PARSING_CONTRACT": (50, "contract_parser", ["invoice_extractor"]),
        "CROSS_VALIDATING": (70, "cross_validator", ["invoice_extractor", "contract_parser"]),
        "CHECKING_COMPLIANCE": (80, "compliance_checker", ["invoice_extractor", "contract_parser", "cross_validator"]),
        "GENERATING_REPORT": (90, "report_generator", ["invoice_extractor", "contract_parser", "cross_validator", "compliance_checker"]),
        "COMPLETE": (100, "report_generator", ["invoice_extractor", "contract_parser", "cross_validator", "compliance_checker", "report_generator"]),
        "FAILED": (100, None, [])
    }
    
    prog_pct, curr_agent, completed = status_map.get(
        db_audit.status, (0, None, [])
    )
    
    # Load partial results if available
    partial_results = {}
    if db_audit.rulebook:
        try:
            rb = json.loads(db_audit.rulebook)
            partial_results["rulebook_rule_count"] = len(rb.get("rules", []))
            if db_audit.supplier_name == "Extracting...":
                # update supplier name dynamically from rulebook in memory
                db_audit.supplier_name = rb.get("supplier_name", "Unknown")
        except json.JSONDecodeError:
            pass
            
    if db_audit.invoice_data:
        try:
            invs = json.loads(db_audit.invoice_data)
            partial_results["invoice_line_count"] = sum(len(i.get("line_items", [])) for i in invs)
        except json.JSONDecodeError:
            pass
            
    # Parse report if complete
    audit_report = None
    if db_audit.status == "COMPLETE" and db_audit.audit_report:
        try:
            audit_report = AuditReport.model_validate_json(db_audit.audit_report)
        except Exception:
            # log warning
            pass
            
    # Clean up filenames for UI display
    clean_contract_file = None
    if db_audit.contract_file:
        clean_contract_file = os.path.basename(db_audit.contract_file)
        
    clean_invoice_files = []
    if db_audit.invoice_files:
        try:
            inv_paths = json.loads(db_audit.invoice_files)
            clean_invoice_files = [os.path.basename(p) for p in inv_paths]
        except Exception:
            pass
            
    return AuditStatusResponse(
        audit_id=db_audit.id,
        status=db_audit.status,
        current_agent=curr_agent,
        progress_pct=prog_pct,
        agents_completed=completed,
        partial_results=partial_results or None,
        audit_report=audit_report,
        error_detail=db_audit.error_detail,
        created_at=db_audit.created_at.isoformat(),
        completed_at=db_audit.completed_at.isoformat() if db_audit.completed_at else None,
        supplier_name=db_audit.supplier_name,
        contract_file=clean_contract_file,
        invoice_files=clean_invoice_files
    )

@router.get("/audit/{audit_id}/report", response_model=AuditReport)
async def get_audit_report_only(audit_id: str):
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        db_audit = result.scalar_one_or_none()
        
    if not db_audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID {audit_id} not found"
        )
        
    if db_audit.status != "COMPLETE" or not db_audit.audit_report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audit is in status {db_audit.status}. Report is not ready."
        )
        
    return AuditReport.model_validate_json(db_audit.audit_report)


@router.get("/audit/{audit_id}/documents")
async def list_audit_documents(audit_id: str):
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        db_audit = result.scalar_one_or_none()

    if not db_audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID {audit_id} not found"
        )

    documents = []
    if db_audit.contract_file:
        documents.append({
            "id": "contract",
            "type": "contract",
            "label": "Contract",
            "filename": os.path.basename(db_audit.contract_file),
        })

    try:
        invoice_files = json.loads(db_audit.invoice_files or "[]")
    except json.JSONDecodeError:
        invoice_files = []

    for index, invoice_path in enumerate(invoice_files):
        documents.append({
            "id": f"invoice-{index}",
            "type": "invoice",
            "label": f"Invoice {index + 1}",
            "filename": os.path.basename(invoice_path),
        })

    return {"audit_id": audit_id, "documents": documents}


@router.get("/audit/{audit_id}/documents/{document_id}")
async def view_audit_document(audit_id: str, document_id: str):
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        db_audit = result.scalar_one_or_none()

    if not db_audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID {audit_id} not found"
        )

    path, _, label = resolve_audit_document(db_audit, document_id)
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"{label}.pdf",
        headers={"Content-Disposition": f'inline; filename="{label}.pdf"'},
    )


@router.get("/audit/{audit_id}/breach-pages/{finding_id}")
async def download_breach_pages(audit_id: str, finding_id: str):
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        db_audit = result.scalar_one_or_none()

    if not db_audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID {audit_id} not found"
        )

    path, _, _ = resolve_audit_document(db_audit, "contract")
    report = AuditReport.model_validate_json(db_audit.audit_report or "{}")
    finding = next(
        (item.model_dump() for item in report.discrepancies if item.finding_id == finding_id),
        None,
    )
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    reader = PdfReader(path)
    pages, _ = find_breach_pages(path, finding)
    writer = PdfWriter()
    for page_index in pages:
        writer.add_page(reader.pages[page_index])

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    filename = f"{audit_id}_{finding_id}_contract_pages.pdf"
    return Response(
        output.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.get("/audits", response_model=List[AuditListItem])
async def list_audits():
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(~Audit.id.like("base_%")).order_by(desc(Audit.created_at))
        result = await session.execute(stmt)
        audits = result.scalars().all()
        
    items = []
    for a in audits:
        supplier_name = a.supplier_name or "Unknown"
        if a.rulebook and (a.supplier_name is None or a.supplier_name == "Extracting..."):
            try:
                rb = json.loads(a.rulebook)
                supplier_name = rb.get("supplier_name", "Unknown")
            except json.JSONDecodeError:
                pass
        items.append(
            AuditListItem(
                audit_id=a.id,
                supplier_name=supplier_name,
                status=a.status,
                total_leakage=a.total_leakage,
                created_at=a.created_at.isoformat()
            )
        )
    return items

@router.delete("/audit/{audit_id}", response_model=Dict[str, str])
async def delete_audit(audit_id: str):
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        db_audit = result.scalar_one_or_none()
        
        if not db_audit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit with ID {audit_id} not found"
            )
            
        files_to_delete = []
        if db_audit.contract_file:
            files_to_delete.append(db_audit.contract_file)
        if db_audit.invoice_files:
            try:
                files_to_delete.extend(json.loads(db_audit.invoice_files))
            except json.JSONDecodeError:
                pass

        # Nullify WatchedFile references so they don't point to a deleted audit
        await session.execute(
            update(WatchedFile)
            .where(WatchedFile.audit_id == audit_id)
            .values(audit_id=None, status="FAILED", error_detail="Audit report was deleted.")
        )

        await session.execute(delete(AuditLog).where(AuditLog.audit_id == audit_id))
        await session.execute(delete(SupplierScore).where(SupplierScore.audit_id == audit_id))
        await session.execute(delete(ContractChunk).where(ContractChunk.audit_id == audit_id))
        await session.execute(delete(DisputeLetter).where(DisputeLetter.audit_id == audit_id))
        await session.delete(db_audit)
        await session.commit()

    for file_path in files_to_delete:
        try:
            resolved_path = validate_uploaded_file_path(file_path, "Stored audit")
            upload_root = os.path.abspath(UPLOAD_DIR)
            if os.path.commonpath([upload_root, resolved_path]) == upload_root:
                os.remove(resolved_path)
        except (HTTPException, OSError):
            pass
        
    return {"message": f"Audit {audit_id} deleted successfully"}

@router.get("/audit/{audit_id}/logs", response_model=List[Dict])
async def get_audit_logs(audit_id: str):
    async with AsyncSessionLocal() as session:
        stmt = select(AuditLog).where(AuditLog.audit_id == audit_id).order_by(AuditLog.timestamp.asc())
        result = await session.execute(stmt)
        logs = result.scalars().all()
        
    return [
        {
            "id": l.id,
            "timestamp": l.timestamp.isoformat(),
            "level": l.level,
            "agent": l.agent,
            "message": l.message
        }
        for l in logs
    ]

from pydantic import BaseModel
from typing import Optional
from backend.services.risk_scorer import compute_risk_score
from pathlib import Path

class RiskScoreRequest(BaseModel):
    supplier_name: Optional[str] = None
    invoice_file_id: Optional[str] = None

class RiskScoreResponse(BaseModel):
    supplier_name: str
    risk_level: str
    risk_score: float
    reason: str
    focus_areas: List[str]
    audits_analysed: int
    avg_leakage: str

@router.post("/predict/risk", response_model=RiskScoreResponse)
async def predict_risk(request: RiskScoreRequest):
    supplier_name = request.supplier_name
    
    if not supplier_name and request.invoice_file_id:
        from backend.services.file_watcher import extract_supplier_from_invoice
        invoice_path_str = validate_uploaded_file_path(request.invoice_file_id, "Invoice")
        supplier_name = await extract_supplier_from_invoice(Path(invoice_path_str))
        
    if not supplier_name:
        raise HTTPException(status_code=400, detail="Supplier name could not be determined")
        
    async with AsyncSessionLocal() as session:
        score_data = await compute_risk_score(supplier_name, session)
        
    return RiskScoreResponse(
        supplier_name=score_data.supplier_name,
        risk_level=score_data.level,
        risk_score=score_data.score,
        reason=score_data.reason,
        focus_areas=score_data.focus_areas,
        audits_analysed=score_data.audits_analysed,
        avg_leakage=f"${score_data.avg_leakage:,.2f}"
    )

@router.websocket("/audit/{audit_id}/ws")
async def audit_websocket(websocket: WebSocket, audit_id: str):
    """
    WebSocket endpoint that streams real-time status and telemetry logs for a running audit.
    """
    await websocket.accept()
    
    # 1. Fetch and send initial status and logs
    try:
        status_res = await get_audit_status(audit_id)
        await websocket.send_json({
            "type": "status",
            "payload": jsonable_encoder(status_res)
        })
        
        logs_res = await get_audit_logs(audit_id)
        for l in logs_res:
            await websocket.send_json({
                "type": "log",
                "payload": l
            })
    except WebSocketDisconnect:
        return
    except HTTPException as e:
        try:
            await websocket.send_json({
                "type": "error",
                "payload": {"detail": e.detail}
            })
            await websocket.close()
        except Exception:
            pass
        return
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "payload": {"detail": str(e)}
            })
            await websocket.close()
        except Exception:
            pass
        return

    # 3. Create asyncio Queue for real-time logs
    from backend.core.audit_logger import active_listeners
    queue = asyncio.Queue()
    if audit_id not in active_listeners:
        active_listeners[audit_id] = []
    active_listeners[audit_id].append(queue)

    # 4. Helper task to check status changes periodically
    async def poll_status_task():
        last_status = status_res.status
        try:
            while True:
                await asyncio.sleep(1.0)
                curr_status = await get_audit_status(audit_id)
                if curr_status.status != last_status:
                    last_status = curr_status.status
                    await websocket.send_json({
                        "type": "status",
                        "payload": jsonable_encoder(curr_status)
                    })
                if curr_status.status in ("COMPLETE", "FAILED"):
                    break
        except Exception:
            pass

    poll_task = asyncio.create_task(poll_status_task())

    try:
        # Keep connection open and send new logs
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=1.0)
                await websocket.send_json(msg)
            except asyncio.TimeoutError:
                # Proactively ping to detect connection termination
                # Send empty message/heartbeat
                pass
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        poll_task.cancel()
        if audit_id in active_listeners:
            if queue in active_listeners[audit_id]:
                active_listeners[audit_id].remove(queue)
            if not active_listeners[audit_id]:
                del active_listeners[audit_id]


class FindingFeedbackRequest(BaseModel):
    verdict: str  # CORRECT | FALSE_POSITIVE | FALSE_NEGATIVE | ADJUSTED
    reason: Optional[str] = None
    adjusted_delta: Optional[float] = None
    reviewed_by: Optional[str] = None


@router.post("/audit/{audit_id}/findings/{finding_id}/feedback", status_code=status.HTTP_200_OK)
async def post_finding_feedback(audit_id: str, finding_id: str, request: FindingFeedbackRequest):
    async with AsyncSessionLocal() as session:
        # Check if audit exists
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        db_audit = result.scalar_one_or_none()
        if not db_audit:
            raise HTTPException(status_code=404, detail="Audit not found")
            
        # Parse the supplier name and rule/finding details from the audit report/discrepancies
        supplier_name = db_audit.supplier_name
        rule_id = None
        rule_type = None
        applies_to = None
        
        # Load from full audit report to cover MC and PD findings
        if db_audit.audit_report:
            try:
                report_data = json.loads(db_audit.audit_report)
                
                # 1. Look in compliance discrepancies (F001, F002...)
                for f in report_data.get("discrepancies", []):
                    if f.get("finding_id") == finding_id:
                        rule_id = f.get("rule_id")
                        break
                
                # 2. Look in missing credits (MC001, MC002...)
                if not rule_id:
                    for f in report_data.get("missing_credits", []):
                        if f.get("finding_id") == finding_id:
                            rule_id = f.get("rule_id")
                            rule_type = f.get("rule_type")
                            break
                            
                # 3. Look in price drifts (PD001, PD002...)
                if not rule_id:
                    for f in report_data.get("price_drifts", []):
                        if f.get("finding_id") == finding_id:
                            rule_type = "price_drift"
                            applies_to = f.get("item_description")
                            break
            except Exception:
                pass
                
        # Resolve applies_to and rule_type from the rulebook if we have a rule_id
        if db_audit.rulebook and rule_id:
            try:
                rulebook_data = json.loads(db_audit.rulebook)
                for r in rulebook_data.get("rules", []):
                    if r.get("rule_id") == rule_id:
                        rule_type = r.get("rule_type")
                        applies_to = r.get("applies_to")
                        break
            except Exception:
                pass

        # Create finding feedback entry
        feedback_id = f"fb_{uuid.uuid4().hex[:8]}"
        new_feedback = FindingFeedback(
            id=feedback_id,
            audit_id=audit_id,
            finding_id=finding_id,
            supplier_name=supplier_name,
            rule_id=rule_id,
            rule_type=rule_type,
            applies_to=applies_to,
            human_verdict=request.verdict,
            adjusted_delta=request.adjusted_delta,
            reason=request.reason,
            reviewed_by=request.reviewed_by or "human_reviewer",
            reviewed_at=utc_now()
        )
        session.add(new_feedback)
        await session.commit()
        
    return {"message": "Feedback submitted successfully", "feedback_id": feedback_id}



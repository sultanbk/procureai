"""
ProcureAI - File Summary

What it does:
Endpoints to manage and watch folders for automated invoice intake.

What it means:
Controller for automated background directory monitoring configuration.

Importance in Project:
Medium. Powering the background auto-audit ingestion feature.
"""

# 1. Standard library
from datetime import datetime
from sqlalchemy import select, desc, func

# 2. Third-party
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# 3. Internal
from backend.core.db import AsyncSessionLocal
from backend.core.tasks import schedule_logged_task
from backend.models.audit import WatchedFile
from backend.services.file_watcher import (
    WATCH_DIR,
    UNMATCHED_DIR,
    retry_unmatched_file,
    scan_and_process_existing_files
)

router = APIRouter(prefix="/api/watcher", tags=["watcher"])


class RetryRequest(BaseModel):
    contract_id: str


@router.get("/status")
async def get_watcher_status():
    from backend.services.file_watcher import _watcher_paused
    
    # Count queued files (status is PENDING, MATCHING, or PROCESSING)
    async with AsyncSessionLocal() as session:
        stmt = select(func.count(WatchedFile.id)).where(
            WatchedFile.status.in_(["PENDING", "MATCHING", "PROCESSING"])
        )
        res = await session.execute(stmt)
        queue_count = res.scalar() or 0
        
    return {
        "watching": not _watcher_paused,
        "watch_dir": str(WATCH_DIR.resolve()),
        "queue_count": queue_count
    }


@router.post("/pause")
async def pause_watcher():
    import backend.services.file_watcher as fw
    fw._watcher_paused = True
    return {"watching": False}


@router.post("/resume")
async def resume_watcher():
    import backend.services.file_watcher as fw
    fw._watcher_paused = False
    
    # Scan and process any files added while paused in the background
    schedule_logged_task(scan_and_process_existing_files(), "scan-watched-invoices")
    
    return {"watching": True}


@router.get("/history")
async def get_watcher_history():
    async with AsyncSessionLocal() as session:
        stmt = select(WatchedFile).order_by(desc(WatchedFile.detected_at)).limit(50)
        res = await session.execute(stmt)
        records = res.scalars().all()
        
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "detected_at": r.detected_at.isoformat() if r.detected_at else None,
            "status": r.status,
            "matched_contract_id": r.matched_contract_id,
            "audit_id": r.audit_id,
            "supplier_name_extracted": r.supplier_name_extracted,
            "error_detail": r.error_detail,
            "processed_at": r.processed_at.isoformat() if r.processed_at else None
        }
        for r in records
    ]


@router.get("/unmatched")
async def get_unmatched_files():
    """
    Returns files in unmatched directory paired with database records showing extracted supplier name.
    """
    files = []
    if UNMATCHED_DIR.exists():
        for path in UNMATCHED_DIR.glob("*.pdf"):
            if path.is_file():
                async with AsyncSessionLocal() as session:
                    stmt = select(WatchedFile).where(WatchedFile.filename == path.name).order_by(desc(WatchedFile.detected_at))
                    res = await session.execute(stmt)
                    record = res.scalars().first()
                    
                supplier_extracted = record.supplier_name_extracted if record else "Unknown"
                detected_at = record.detected_at.isoformat() if record else datetime.fromtimestamp(path.stat().st_ctime).isoformat()
                
                files.append({
                    "filename": path.name,
                    "detected_at": detected_at,
                    "supplier_name_extracted": supplier_extracted
                })
    return files


@router.post("/retry/{filename}")
async def retry_unmatched(filename: str, payload: RetryRequest):
    """
    Trigger manual match/audit retry for an unmatched invoice.
    """
    res = await retry_unmatched_file(filename, payload.contract_id)
    if not res.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("error", "Retry processing failed")
        )
    return res

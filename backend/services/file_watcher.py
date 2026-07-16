"""
ProcureAI - File Summary

What it does:
Monitors target directories for uploaded invoices and schedules automated audits.

What it means:
Automated ingestion worker tracking directory changes.

Importance in Project:
High. Handles auto-audit pipeline runs on directory additions.
"""

# 1. Standard library
import os
import json
import shutil
import uuid
import asyncio
from pathlib import Path
from typing import Optional

# 2. Third-party
from sqlalchemy import select, func
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import structlog

# 3. Internal
from backend.core.db import AsyncSessionLocal
from backend.core.tasks import schedule_logged_task
from backend.core.time import utc_now
from backend.models.audit import WatchedFile, Contract, Audit
from backend.core.pdf_extractor import extract_pdf_text
from backend.api.routes.audit import run_audit_pipeline

logger = structlog.get_logger()

WATCH_DIR = Path("watched_invoices")
PROCESSED_DIR = WATCH_DIR / "processed"
UNMATCHED_DIR = WATCH_DIR / "unmatched"

_watcher_observer = None
_watcher_paused = False
_event_loop = None


class InvoiceFileHandler(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() != ".pdf":
            return
        
        # Skip files within subdirectory structures
        if "processed" in path.parts or "unmatched" in path.parts:
            return

        global _watcher_paused
        if _watcher_paused:
            logger.info("File watcher is paused. Ignoring event.", path=str(path))
            return

        logger.info("New invoice PDF detected by watcher.", path=str(path))
        asyncio.run_coroutine_threadsafe(
            self._process_after_stable_delay(path),
            self.loop
        )

    async def _process_after_stable_delay(self, path: Path):
        await asyncio.sleep(0.5)
        await process_new_invoice(path)


def copy_to_upload_dir(src_path: Path, prefix: str = "invoice") -> str:
    from backend.api.routes.upload import UPLOAD_DIR
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    clean_filename = "".join(
        c if c.isalnum() or c in (".", "-", "_") else "_"
        for c in src_path.name
    )
    dest_filename = f"{prefix}_{uuid.uuid4().hex[:8]}_{clean_filename}"
    dest_path = os.path.abspath(os.path.join(UPLOAD_DIR, dest_filename)).replace("\\", "/")
    shutil.copy(str(src_path), dest_path)
    return dest_path


async def extract_supplier_from_invoice(path: Path) -> str:
    """
    Extracts supplier name from PDF content using Gemini. Falls back to filename matching in offline mock mode.
    """
    if os.getenv("MOCK_LLM", "false").lower() == "true":
        filename_lower = path.name.lower()
        if "apx" in filename_lower or "apex" in filename_lower:
            return "Apex Logistics Ltd"
        elif "tss" in filename_lower or "techsoft" in filename_lower:
            return "TechSoft Solutions"
        elif "brc" in filename_lower or "buildright" in filename_lower:
            return "BuildRight Contractors"
        elif "msc" in filename_lower or "medisupply" in filename_lower:
            return "MediSupply Corp"
        elif "chi" in filename_lower or "cloudhost" in filename_lower:
            return "CloudHost India"
        elif "psc" in filename_lower or "proservices" in filename_lower:
            return "ProServices Consulting"
        return "Unknown Supplier"

    try:
        text = (await asyncio.to_thread(extract_pdf_text, str(path)))[:2000]
        if not text.strip():
            return "Unknown Supplier"
            
        from backend.core.llm_client import get_llm
        llm = get_llm()
        
        prompt = (
            "Read this invoice text and return ONLY the supplier/vendor company name.\n"
            "Return just the name, nothing else. Do not add markdown or punctuation.\n\n"
            f"Invoice Text:\n{text}"
        )
        response = await llm.async_generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error("Failed to extract supplier name from PDF via LLM", error=str(e))
        return "Unknown Supplier"


async def find_matching_contract(supplier_name: str, db) -> Optional[Contract]:
    """
    Finds a contract by matching supplier names (exact -> aliases -> partial).
    Orders matching contracts by version descending to match the latest version first.
    """
    # 1. Exact case-insensitive match
    stmt = select(Contract).where(
        func.lower(Contract.supplier_name) == supplier_name.lower(),
        Contract.is_active == 1
    ).order_by(Contract.version.desc())
    result = await db.execute(stmt)
    contract = result.scalars().first()
    if contract:
        return contract

    # 2. Check aliases
    stmt_all = select(Contract).where(Contract.is_active == 1).order_by(Contract.version.desc())
    result_all = await db.execute(stmt_all)
    all_contracts = result_all.scalars().all()

    for c in all_contracts:
        try:
            aliases = json.loads(c.supplier_aliases or "[]")
            if any(a.lower() == supplier_name.lower() for a in aliases):
                return c
        except Exception:
            pass

    # 3. Partial match
    for c in all_contracts:
        c_name = c.supplier_name.lower()
        s_name = supplier_name.lower()
        if s_name in c_name or c_name in s_name:
            return c

    return None


async def process_new_invoice(invoice_path: Path):
    """
    Automated pipeline trigger for newly watched invoice files.
    """
    async with AsyncSessionLocal() as db:
        # De-duplicate events: ignore event only if a file with the same name is currently active in the pipeline
        stmt = select(WatchedFile).where(
            WatchedFile.filename == invoice_path.name,
            WatchedFile.status.in_(["PENDING", "MATCHING", "PROCESSING"])
        )
        res = await db.execute(stmt)
        existing = res.scalars().first()
        if existing:
            return

        watched = WatchedFile(
            filename=invoice_path.name,
            status="MATCHING",
            detected_at=utc_now()
        )
        db.add(watched)
        await db.commit()

        try:
            # 1. Extract supplier
            supplier_name = await extract_supplier_from_invoice(invoice_path)
            watched.supplier_name_extracted = supplier_name
            await db.commit()

            # 2. Match contract
            contract = await find_matching_contract(supplier_name, db)
            if not contract:
                watched.status = "UNMATCHED"
                os.makedirs(UNMATCHED_DIR, exist_ok=True)
                dest = UNMATCHED_DIR / invoice_path.name
                shutil.move(str(invoice_path), str(dest))
                logger.warning("No contract matched for watched invoice.", supplier=supplier_name, file=invoice_path.name)
                await db.commit()
                return

            watched.matched_contract_id = contract.id
            watched.status = "PROCESSING"
            await db.commit()

            # 3. Copy files to upload directory
            invoice_file_path = copy_to_upload_dir(invoice_path)

            # 4. Trigger audit pipeline (same as manual route)
            audit_id = f"aud_{uuid.uuid4().hex[:8]}"
            new_audit = Audit(
                id=audit_id,
                status="PENDING",
                supplier_name=contract.supplier_name,
                contract_file=contract.contract_file_path,
                invoice_files=json.dumps([invoice_file_path]),
                created_at=utc_now()
            )
            db.add(new_audit)
            await db.commit()

            # Wait for execution and check completion
            await run_audit_pipeline(audit_id, contract.contract_file_path, [invoice_file_path])

            await db.refresh(new_audit)
            db_audit = new_audit

            if db_audit and db_audit.status == "COMPLETE":
                watched.status = "COMPLETE"
                os.makedirs(PROCESSED_DIR, exist_ok=True)
                dest = PROCESSED_DIR / f"{audit_id}_{invoice_path.name}"
                shutil.move(str(invoice_path), str(dest))
            else:
                watched.status = "FAILED"
                watched.error_detail = db_audit.error_detail if db_audit else "Audit pipeline failed"

            watched.processed_at = utc_now()
            watched.audit_id = audit_id
            await db.commit()

        except Exception as e:
            watched.status = "FAILED"
            watched.error_detail = str(e)
            await db.commit()
            logger.error("Auto-audit execution failed.", file=invoice_path.name, error=str(e))


async def retry_unmatched_file(filename: str, contract_id: str) -> dict:
    """
    Manually retries processing an unmatched invoice PDF with a selected contract_id.
    """
    async with AsyncSessionLocal() as db:
        unmatched_path = UNMATCHED_DIR / filename
        if not unmatched_path.exists():
            return {"success": False, "error": f"File {filename} not found in unmatched folder"}

        stmt = select(Contract).where(Contract.id == contract_id)
        res = await db.execute(stmt)
        contract = res.scalar_one_or_none()
        if not contract:
            return {"success": False, "error": f"Contract {contract_id} not found"}

        watched = WatchedFile(
            filename=filename,
            status="PROCESSING",
            matched_contract_id=contract_id,
            detected_at=utc_now()
        )
        db.add(watched)
        await db.commit()

        temp_path = WATCH_DIR / filename
        try:
            invoice_file_path = copy_to_upload_dir(unmatched_path)
            audit_id = f"aud_{uuid.uuid4().hex[:8]}"

            new_audit = Audit(
                id=audit_id,
                status="PENDING",
                supplier_name=contract.supplier_name,
                contract_file=contract.contract_file_path,
                invoice_files=json.dumps([invoice_file_path]),
                created_at=utc_now()
            )
            db.add(new_audit)
            await db.commit()

            # Move from unmatched folder to temporary watch folder location for processing
            shutil.move(str(unmatched_path), str(temp_path))

            await run_audit_pipeline(audit_id, contract.contract_file_path, [invoice_file_path])

            await db.refresh(new_audit)
            db_audit = new_audit

            if db_audit and db_audit.status == "COMPLETE":
                watched.status = "COMPLETE"
                os.makedirs(PROCESSED_DIR, exist_ok=True)
                dest = PROCESSED_DIR / f"{audit_id}_{filename}"
                shutil.move(str(temp_path), str(dest))
            else:
                watched.status = "FAILED"
                watched.error_detail = db_audit.error_detail if db_audit else "Audit pipeline failed"
                # Revert move on failure
                shutil.move(str(temp_path), str(unmatched_path))

            watched.processed_at = utc_now()
            watched.audit_id = audit_id
            await db.commit()

            if watched.status == "COMPLETE":
                return {"success": True, "audit_id": audit_id}
            else:
                return {"success": False, "error": watched.error_detail}

        except Exception as e:
            watched.status = "FAILED"
            watched.error_detail = str(e)
            await db.commit()
            if temp_path.exists():
                shutil.move(str(temp_path), str(unmatched_path))
            return {"success": False, "error": str(e)}


async def scan_and_process_existing_files():
    """
    Scans WATCH_DIR and processes any unhandled PDFs (picks up files added while paused).
    """
    if not WATCH_DIR.exists():
        return
    for path in WATCH_DIR.glob("*.pdf"):
        if path.is_file() and path.parent.name not in ("processed", "unmatched"):
            # Trigger process task on event loop
            schedule_logged_task(process_new_invoice(path), f"process-watched-invoice:{path.name}")


def start_file_watcher(loop) -> Observer:
    """
    Initializes watch directories and starts the watchdog filesystem listener.
    """
    global _watcher_observer, _event_loop
    _event_loop = loop

    WATCH_DIR.mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)
    UNMATCHED_DIR.mkdir(exist_ok=True)

    handler = InvoiceFileHandler(loop)
    _watcher_observer = Observer()
    _watcher_observer.schedule(handler, str(WATCH_DIR), recursive=False)
    _watcher_observer.start()
    logger.info("Auto-Audit local folder file watcher started.", watch_dir=str(WATCH_DIR.resolve()))
    return _watcher_observer

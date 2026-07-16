"""
ProcureAI - File Summary

What it does:
Handles physical uploads of PDF files to local disk storage.

What it means:
File receiver enforcing file type validation and size limits.

Importance in Project:
High. The primary entry point for raw contract/invoice document intake.
"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from backend.core.config import MAX_UPLOAD_SIZE_MB, UPLOAD_DIR
from backend.models.schemas import UploadResponse

router = APIRouter(prefix="/api", tags=["upload"])

MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

def is_pdf_upload(file: UploadFile) -> bool:
    filename = file.filename or ""
    return filename.lower().endswith(".pdf") and file.content_type in (
        "application/pdf",
        "application/octet-stream",
        None,
        "",
    )

import hashlib

def build_upload_path(prefix: str, original_filename: str, file_hash: str) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    clean_filename = "".join(
        c if c.isalnum() or c in (".", "-", "_") else "_"
        for c in original_filename
    )
    filename = f"{prefix}_{file_hash}_{clean_filename}"
    return os.path.abspath(os.path.join(UPLOAD_DIR, filename)).replace("\\", "/")

def file_id_from_path(file_path: str) -> str:
    return os.path.basename(file_path)

async def save_pdf_upload(file: UploadFile, prefix: str) -> tuple[str, bytes]:
    if not is_pdf_upload(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum upload size of {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB"
        )

    file_hash = hashlib.sha256(contents).hexdigest()[:16]
    file_path = build_upload_path(prefix, file.filename or "upload.pdf", file_hash)
    
    import asyncio
    def _write_file():
        with open(file_path, "wb") as f:
            f.write(contents)
    await asyncio.to_thread(_write_file)

    return file_path, contents

@router.post("/upload/contract", response_model=UploadResponse)
async def upload_contract(file: UploadFile = File(...)):
    file_path, contents = await save_pdf_upload(file, "contract")

    return UploadResponse(
        file_id=file_id_from_path(file_path),
        filename=file.filename,
        size_bytes=len(contents),
        file_type="contract"
    )

@router.post("/upload/invoice", response_model=UploadResponse)
async def upload_invoice(file: UploadFile = File(...)):
    file_path, contents = await save_pdf_upload(file, "invoice")

    return UploadResponse(
        file_id=file_id_from_path(file_path),
        filename=file.filename,
        size_bytes=len(contents),
        file_type="invoice"
    )

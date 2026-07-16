"""
ProcureAI - File Summary

What it does:
Routes standard health checks to confirm server status and DB connection.

What it means:
Service viability indicator.

Importance in Project:
Low. Used by load balancers and deployment scripts to verify uptime.
"""

import os
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("")
async def health_check():
    return {"status": "ok"}

@router.get("/runtime")
async def runtime_check():
    from backend.core import config
    from backend.core.db import DATABASE_URL
    from backend.core.llm_client import get_llm, is_mock_llm_enabled

    llm = get_llm()
    return {
        "status": "ok",
        "cwd": str(Path.cwd()),
        "database_url": DATABASE_URL,
        "google_cloud_project": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "google_cloud_location": os.getenv("GOOGLE_CLOUD_LOCATION"),
        "gemini_model": os.getenv("GEMINI_MODEL"),
        "mock_llm_raw": os.getenv("MOCK_LLM"),
        "allow_mock_llm_raw": os.getenv("ALLOW_MOCK_LLM"),
        "mock_llm_effective": is_mock_llm_enabled(),
        "llm_backend": llm.status_label() if hasattr(llm, "status_label") else type(llm).__name__,
        "upload_dir": config.UPLOAD_DIR,
    }

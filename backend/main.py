"""
FILE CANONICAL IDENTIFIER: backend/main.py
MODULE ROLE: Entrypoint for the FastAPI application that serves the ProcureAI API.
SYSTEM BOUNDARY: HTTP boundary layer only. Router mounting for CORS, health, upload, and compliance audit controllers.
STATE DEPENDENCY / DATA CONTRACTS: Mounts CORSMiddleware and registers API routers from backend.api.routes.
CRITICAL LOGIC: Starts the development server using uvicorn.run on host 0.0.0.0 and port 8000 with hot reload.
"""

import uvicorn
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.services.file_watcher import start_file_watcher, scan_and_process_existing_files
from backend.core.tasks import schedule_logged_task

from backend.api.routes import (
    health,
    upload,
    audit,
    suppliers,
    analytics,
    disputes,
    settings,
    contracts,
    watcher
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    observer = start_file_watcher(loop)
    schedule_logged_task(scan_and_process_existing_files(), "scan-watched-startup")
    yield
    if observer:
        observer.stop()
        observer.join()

app = FastAPI(
    title="ProcureAI API",
    description="Agentic Contract Compliance & Invoice Auditor API",
    version="1.0.0",
    lifespan=lifespan
)

from fastapi import Request
from fastapi.responses import JSONResponse
import traceback
import sys

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"GLOBAL EXCEPTION HANDLER CAUGHT: {exc}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error from Global Handler", "traceback": traceback.format_exc()}
    )


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(upload.router)
app.include_router(audit.router)
app.include_router(suppliers.router)
app.include_router(analytics.router)
app.include_router(disputes.router)
app.include_router(settings.router)
app.include_router(contracts.router)
app.include_router(contracts.compare_router)
app.include_router(watcher.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the ProcureAI API"}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

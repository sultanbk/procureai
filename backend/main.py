"""
FILE CANONICAL IDENTIFIER: backend/main.py
MODULE ROLE: Entrypoint for the FastAPI application that serves the ProcureAI API.
SYSTEM BOUNDARY: HTTP boundary layer only. Router mounting for CORS, health, upload, and compliance audit controllers.
STATE DEPENDENCY / DATA CONTRACTS: Mounts CORSMiddleware and registers API routers from backend.api.routes.
CRITICAL LOGIC: Starts the development server using uvicorn.run on host 0.0.0.0 and port 8000 with hot reload.
"""

import uvicorn
import asyncio
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.services.file_watcher import start_file_watcher, scan_and_process_existing_files
from backend.core.tasks import schedule_logged_task
from backend.core.config import CORS_ALLOW_ORIGINS
from backend.api.middleware import LoggingMiddleware, APIKeyMiddleware, RateLimitMiddleware

from backend.api.routes import (
    health,
    upload,
    audit,
    suppliers,
    analytics,
    disputes,
    settings,
    contracts,
    watcher,
    context_substrate
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist on startup
    from backend.core.db import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created on startup.")

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


# --- Global Exception Handler ---
# Fix #1: Never leak tracebacks to API consumers. Log server-side only.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception caught by global handler.",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )


# --- Middleware Stack ---
# Order matters: outermost middleware runs first.
# 1. CORS must be outermost to handle preflight OPTIONS requests
# Fix #3: Use configured origins instead of wildcard "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fix #2: Mount the security and observability middleware that was previously defined but never added
# 2. Request logging (adds X-Request-ID header, logs duration)
app.add_middleware(LoggingMiddleware)

# 3. API key verification (skips exempt paths like /docs, /api/health)
app.add_middleware(APIKeyMiddleware)

# 4. Rate limiting per client IP
app.add_middleware(RateLimitMiddleware)


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
app.include_router(context_substrate.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the ProcureAI API"}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

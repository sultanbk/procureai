"""
ProcureAI - File Summary

What it does:
Implements custom FastAPI middleware for CORS headers, rate limiting, and API key verification.

What it means:
HTTP traffic filter and backend security gatekeeper.

Importance in Project:
High. Protects endpoint routes from abuse and secures private system endpoints.
"""

import time
import uuid
from collections import defaultdict, deque
import structlog
from fastapi import Request, Response
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.config import (
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    REQUIRE_API_KEY,
    PROCUREAI_API_KEY,
)

logger = structlog.get_logger("api.middleware")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Check if request ID was sent in headers, otherwise generate a new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Clear existing context and bind new request context details
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None
        )
        
        start_time = time.perf_counter()
        
        logger.info("Request started", query_params=str(request.query_params))
        
        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            
            logger.info(
                "Request completed",
                status_code=response.status_code,
                duration_s=round(duration, 4)
            )
            
            # Inject request ID into response headers
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                "Request failed",
                error=str(e),
                duration_s=round(duration, 4),
                exc_info=True
            )
            raise e


class APIKeyMiddleware(BaseHTTPMiddleware):
    EXEMPT_PATHS = {"/", "/docs", "/openapi.json", "/redoc", "/api/health"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if not REQUIRE_API_KEY or request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        provided_key = request.headers.get("X-API-Key")
        if not PROCUREAI_API_KEY or provided_key != PROCUREAI_API_KEY:
            return JSONResponse(
                status_code=401,
                content={"detail": "A valid X-API-Key header is required."},
            )

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-client-IP rate limiting middleware.
    Fix #10: Evicts stale client entries after their window expires to prevent
    unbounded memory growth from unique client IPs.
    """
    MAX_TRACKED_CLIENTS = 10_000  # Safety cap to prevent memory abuse

    def __init__(self, app):
        super().__init__(app)
        self.requests_by_client = defaultdict(deque)
        self._last_cleanup = time.monotonic()

    async def dispatch(self, request: Request, call_next) -> Response:
        if RATE_LIMIT_REQUESTS <= 0:
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = self.requests_by_client[client]

        # Expire old entries from this client's window
        while window and now - window[0] > RATE_LIMIT_WINDOW_SECONDS:
            window.popleft()

        if len(window) >= RATE_LIMIT_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please retry later."},
            )

        window.append(now)

        # Periodic cleanup: evict all clients with empty windows (every 60s)
        if now - self._last_cleanup > 60.0:
            self._last_cleanup = now
            stale_keys = [k for k, v in self.requests_by_client.items() if not v]
            for k in stale_keys:
                del self.requests_by_client[k]

        # Safety cap: if too many unique clients, drop oldest entries
        if len(self.requests_by_client) > self.MAX_TRACKED_CLIENTS:
            excess = len(self.requests_by_client) - self.MAX_TRACKED_CLIENTS
            keys_to_remove = list(self.requests_by_client.keys())[:excess]
            for k in keys_to_remove:
                del self.requests_by_client[k]

        return await call_next(request)


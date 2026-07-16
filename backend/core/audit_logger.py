import structlog
from typing import Dict, List
import asyncio
from backend.core.db import AsyncSessionLocal
from backend.core.time import utc_now
from backend.models.audit import AuditLog

logger = structlog.get_logger("audit_logger")

# Global registry of active listeners (audit_id -> list of asyncio.Queue)
active_listeners: Dict[str, List[asyncio.Queue]] = {}

async def log_audit_event(audit_id: str, message: str, level: str = "INFO", agent: str = None):
    """
    Logs a high-level event for a specific audit.
    Writes to the standard application log (structlog) AND persists it to the database
    for frontend real-time display.
    Also forwards to any active WebSocket listeners.
    """
    # 1. Log via structlog
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, audit_id=audit_id, agent=agent)
    
    # 2. Persist to DB
    try:
        async with AsyncSessionLocal() as session:
            new_log = AuditLog(
                audit_id=audit_id,
                level=level,
                agent=agent,
                message=message,
                timestamp=utc_now()
            )
            session.add(new_log)
            await session.commit()
    except Exception as e:
        # Fallback print if DB commit fails to avoid losing log
        print(f"[Backup Log Error] Failed to write audit log to DB: {e}. Event was: audit_id={audit_id} level={level} agent={agent} msg={message}")

    # 3. Forward to active WebSocket listeners
    if audit_id in active_listeners:
        log_payload = {
            "type": "log",
            "payload": {
                "timestamp": utc_now().isoformat(),
                "level": level,
                "agent": agent,
                "message": message
            }
        }
        for queue in active_listeners[audit_id]:
            try:
                queue.put_nowait(log_payload)
            except Exception:
                pass


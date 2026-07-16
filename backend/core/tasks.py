"""
ProcureAI - File Summary

What it does:
Schedules and monitors background asynchronous coroutines safely.

What it means:
Async execution helper that traps and logs exceptions from detached threads/tasks.

Importance in Project:
Medium. Prevents silent crashes in background threads like directory watching or long running audits.
"""

import asyncio
from collections.abc import Coroutine
from typing import Any

import structlog

logger = structlog.get_logger()


def schedule_logged_task(coro: Coroutine[Any, Any, Any], name: str) -> asyncio.Task:
    task = asyncio.create_task(coro, name=name)

    def _log_result(done_task: asyncio.Task) -> None:
        try:
            done_task.result()
        except asyncio.CancelledError:
            logger.warning("Background task was cancelled.", task=name)
        except Exception as exc:
            logger.error("Background task failed.", task=name, error=str(exc))

    task.add_done_callback(_log_result)
    return task

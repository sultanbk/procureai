"""
ProcureAI — Guardrail 6: LLM Rate Limiter

Async token-bucket and sliding-window rate limiter for LLM provider API calls.
Prevents burst traffic from exceeding provider RPM (requests per minute)
and TPM (tokens per minute) quotas.
"""

import asyncio
import time
from collections import deque
from typing import Deque, Tuple
import structlog

logger = structlog.get_logger()


class LLMRateLimitExceeded(Exception):
    """Raised when rate limit wait time exceeds maximum allowable wait."""
    def __init__(self, message: str, wait_seconds: float):
        super().__init__(message)
        self.wait_seconds = wait_seconds


class LLMRateLimiter:
    """
    Sliding-window rate limiter tracking requests and tokens per 60-second window.

    Attributes:
        requests_per_minute: Max LLM API requests per minute.
        tokens_per_minute: Max LLM tokens per minute.
        window_seconds: Window duration in seconds (default: 60.0).
        max_wait_seconds: Maximum seconds acquire() is allowed to wait before raising.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 100_000,
        window_seconds: float = 60.0,
        max_wait_seconds: float = 30.0,
    ):
        self.rpm_limit = requests_per_minute
        self.tpm_limit = tokens_per_minute
        self.window_seconds = window_seconds
        self.max_wait_seconds = max_wait_seconds

        # Deque of (timestamp, token_count)
        self._history: Deque[Tuple[float, int]] = deque()
        self._lock = asyncio.Lock()

    def _prune(self, now: float) -> None:
        """Remove entries older than window_seconds."""
        cutoff = now - self.window_seconds
        while self._history and self._history[0][0] <= cutoff:
            self._history.popleft()

    @property
    def current_rpm(self) -> int:
        now = time.monotonic()
        self._prune(now)
        return len(self._history)

    @property
    def current_tpm(self) -> int:
        now = time.monotonic()
        self._prune(now)
        return sum(tokens for _, tokens in self._history)

    async def acquire(self, estimated_tokens: int = 1000) -> None:
        """
        Wait until capacity is available under both RPM and TPM limits.

        Args:
            estimated_tokens: Estimated token count for the pending LLM request.

        Raises:
            LLMRateLimitExceeded: If required wait time exceeds max_wait_seconds.
        """
        if self.rpm_limit <= 0 and self.tpm_limit <= 0:
            return

        total_waited = 0.0

        while True:
            async with self._lock:
                now = time.monotonic()
                self._prune(now)

                current_requests = len(self._history)
                current_tokens = sum(tok for _, tok in self._history)

                # Check if within bounds
                rpm_ok = (self.rpm_limit <= 0) or (current_requests < self.rpm_limit)
                tpm_ok = (self.tpm_limit <= 0) or ((current_tokens + estimated_tokens) <= self.tpm_limit)

                if rpm_ok and tpm_ok:
                    # Slot available: reserve now
                    self._history.append((now, estimated_tokens))
                    return

                # Calculate how long to sleep until oldest entry expires
                if not self._history:
                    wait_time = 0.1
                else:
                    oldest_time = self._history[0][0]
                    wait_time = max(0.05, (oldest_time + self.window_seconds) - now)

            if total_waited + wait_time > self.max_wait_seconds:
                logger.error(
                    "LLM Rate limit exceeded — required wait too high.",
                    wait_time=wait_time,
                    max_wait=self.max_wait_seconds,
                    current_rpm=current_requests,
                    current_tpm=current_tokens,
                )
                raise LLMRateLimitExceeded(
                    f"LLM rate limit wait of {wait_time:.1f}s exceeds maximum {self.max_wait_seconds}s limit",
                    wait_seconds=wait_time,
                )

            logger.info(
                "LLM rate limit reached; waiting before call.",
                wait_seconds=round(wait_time, 2),
                current_rpm=current_requests,
                current_tpm=current_tokens,
            )
            await asyncio.sleep(wait_time)
            total_waited += wait_time

    def record_usage(self, actual_tokens: int) -> None:
        """
        Update the most recent entry with the actual token usage from response.
        """
        if self._history:
            timestamp, _ = self._history[-1]
            self._history[-1] = (timestamp, actual_tokens)


# Global default limiter instance
_global_rate_limiter = None


def get_rate_limiter(rpm: int = 60, tpm: int = 100_000) -> LLMRateLimiter:
    """Singleton getter for the global LLM rate limiter."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = LLMRateLimiter(requests_per_minute=rpm, tokens_per_minute=tpm)
    return _global_rate_limiter

"""
ProcureAI — Guardrail 4: Token Budget Per Audit

Tracks and limits total LLM token consumption per pipeline run.
Prevents unbounded costs from large documents triggering excessive LLM calls.
"""

import structlog
from dataclasses import dataclass, field

logger = structlog.get_logger()


class TokenBudgetExceeded(Exception):
    """Raised when the token budget for a pipeline run is exhausted."""
    def __init__(self, used: int, limit: int):
        self.used = used
        self.limit = limit
        super().__init__(
            f"Token budget exceeded: {used:,} tokens used out of {limit:,} limit"
        )


@dataclass
class TokenBudget:
    """
    Tracks token usage for a single audit pipeline run.
    
    Usage:
        budget = TokenBudget(max_tokens=500_000)
        # ... after each LLM call:
        budget.record(prompt_tokens=1000, completion_tokens=500)
        # ... check remaining:
        if budget.remaining < estimated_next_call:
            # skip optional LLM calls
    """
    max_tokens: int = 500_000
    prompt_tokens: int = 0
    completion_tokens: int = 0
    call_count: int = 0
    _warnings_issued: int = field(default=0, repr=False)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def remaining(self) -> int:
        return max(0, self.max_tokens - self.total_tokens)

    @property
    def utilization(self) -> float:
        """Returns budget utilization as a fraction (0.0 to 1.0+)."""
        if self.max_tokens <= 0:
            return 0.0
        return self.total_tokens / self.max_tokens

    @property
    def utilization_pct(self) -> float:
        """Returns budget utilization as a percentage (0.0 to 100.0+)."""
        return round(self.utilization * 100, 1)

    def record(self, prompt_tokens: int = 0, completion_tokens: int = 0, agent: str = ""):
        """
        Record token usage from an LLM call.
        
        Raises TokenBudgetExceeded if the budget is exhausted.
        Logs a warning at 80% utilization.
        """
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.call_count += 1

        logger.debug(
            "Token budget: LLM call recorded.",
            agent=agent,
            call_prompt=prompt_tokens,
            call_completion=completion_tokens,
            total_used=self.total_tokens,
            remaining=self.remaining,
            call_count=self.call_count,
        )

        # Warning at 80% utilization
        if self.utilization >= 0.8 and self._warnings_issued == 0:
            self._warnings_issued += 1
            logger.warning(
                "Token budget at 80% utilization.",
                total_used=self.total_tokens,
                max_tokens=self.max_tokens,
                remaining=self.remaining,
                agent=agent,
            )

        # Hard stop if exceeded
        if self.total_tokens > self.max_tokens:
            logger.error(
                "Token budget EXCEEDED — halting pipeline.",
                total_used=self.total_tokens,
                max_tokens=self.max_tokens,
                call_count=self.call_count,
                agent=agent,
            )
            raise TokenBudgetExceeded(self.total_tokens, self.max_tokens)

    def to_dict(self) -> dict:
        """Serialize for inclusion in PipelineState and API responses."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "call_count": self.call_count,
            "max_tokens": self.max_tokens,
            "remaining": self.remaining,
            "utilization_pct": round(self.utilization * 100, 1),
        }

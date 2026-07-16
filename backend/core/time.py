"""
ProcureAI - File Summary

What it does:
Provides standard timezone-aware datetime wrappers.

What it means:
Date utility library guaranteeing UTC database timestamps.

Importance in Project:
Low. Establishes uniform time standards across audits and scorecards.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()

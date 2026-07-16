"""
ProcureAI - File Summary

What it does:
Loads environment configurations and specifies project-wide setting defaults.

What it means:
Centralized registry of system configurations, LLM parameters, database locations, and CORS policies.

Importance in Project:
High. Ensures all modules use consistent settings and enables environment-driven deployments.
"""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv


def _load_environment() -> None:
    root_env = Path(__file__).resolve().parents[2] / ".env"
    backend_env = Path(__file__).resolve().parents[1] / ".env"

    if root_env.exists():
        load_dotenv(root_env, override=True)
    if backend_env.exists():
        load_dotenv(backend_env, override=True)


_load_environment()


def get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def get_list(name: str, default: List[str]) -> List[str]:
    value = os.getenv(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./procureai.db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join("data", "uploads"))
MAX_UPLOAD_SIZE_MB = get_int("MAX_UPLOAD_SIZE_MB", 20)

MINIMUM_MATERIAL_THRESHOLD = get_float("MINIMUM_MATERIAL_THRESHOLD", 100.0)
COMPLIANCE_CONFIDENCE_THRESHOLD = get_float("COMPLIANCE_CONFIDENCE_THRESHOLD", 0.75)
LLM_RETRY_ATTEMPTS = get_int("LLM_RETRY_ATTEMPTS", 3)
LLM_RETRY_DELAY_SECONDS = get_float("LLM_RETRY_DELAY_SECONDS", 2.0)
LLM_CALL_TIMEOUT_SECONDS = get_int("LLM_CALL_TIMEOUT_SECONDS", 120)
PIPELINE_MAX_LLM_CALLS = get_int("PIPELINE_MAX_LLM_CALLS", 100)
PIPELINE_TIMEOUT_SECONDS = get_int("PIPELINE_TIMEOUT_SECONDS", 600)

# v4: Self-consistency extraction
SELF_CONSISTENCY_PASSES = get_int("SELF_CONSISTENCY_PASSES", 3)
# Temperatures for each pass (parsed from comma-separated string)
_sc_temps_raw = os.getenv("SELF_CONSISTENCY_TEMPERATURES", "0.0,0.1,0.2")
SELF_CONSISTENCY_TEMPERATURES = [float(t.strip()) for t in _sc_temps_raw.split(",")]

# v4: Cross-invoice price drift thresholds
PRICE_DRIFT_THRESHOLD_PCT = get_float("PRICE_DRIFT_THRESHOLD_PCT", 5.0)
PRICE_DRIFT_MIN_DELTA = get_float("PRICE_DRIFT_MIN_DELTA", 10.00)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "CONSOLE")

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", os.getenv("VITE_APP_URL", "http://localhost:5173"))
CORS_ALLOW_ORIGINS = get_list(
    "CORS_ALLOW_ORIGINS",
    ["http://localhost:5173", "http://127.0.0.1:5173"],
)

PROCUREAI_API_KEY = os.getenv("PROCUREAI_API_KEY", "")
REQUIRE_API_KEY = get_bool("REQUIRE_API_KEY", bool(PROCUREAI_API_KEY))
RATE_LIMIT_REQUESTS = get_int("RATE_LIMIT_REQUESTS", 120)
RATE_LIMIT_WINDOW_SECONDS = get_int("RATE_LIMIT_WINDOW_SECONDS", 60)

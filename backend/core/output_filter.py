"""
ProcureAI — Guardrail 2: Output Content Filter

Filters LLM-generated text (dispute letters, executive summaries, recommendations)
before returning to users. Detects and redacts PII, profanity, off-topic content,
and unsafe instructions.
"""

import re
import structlog
from dataclasses import dataclass, field
from typing import List

logger = structlog.get_logger()


@dataclass
class FilteredOutput:
    """Result of output content filtering."""
    clean_text: str
    original_text: str = ""
    flagged: bool = False
    redactions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# --- PII Detection Patterns ---

_PII_PATTERNS = [
    (
        "email",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "[EMAIL REDACTED]",
    ),
    (
        "phone_number",
        re.compile(
            r"(?<!\d)(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)"
        ),
        "[PHONE REDACTED]",
    ),
    (
        "ssn",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "[SSN REDACTED]",
    ),
    (
        "aadhaar",
        re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
        "[ID REDACTED]",
    ),
    (
        "credit_card",
        re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        "[CARD REDACTED]",
    ),
    (
        "pan_card",
        re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
        "[PAN REDACTED]",
    ),
]

# --- Unsafe Content Patterns ---

_UNSAFE_PATTERNS = [
    (
        "executable_code",
        re.compile(
            r"(?:<\s*script\b|javascript\s*:|eval\s*\(|exec\s*\(|subprocess|os\.system)",
            re.IGNORECASE,
        ),
    ),
    (
        "harmful_instructions",
        re.compile(
            r"(?:how\s+to\s+(?:hack|exploit|bypass|steal|forge)|"
            r"(?:delete|destroy|wipe)\s+(?:all|database|system|files))",
            re.IGNORECASE,
        ),
    ),
    (
        "html_injection",
        re.compile(
            r"<\s*(?:iframe|object|embed|form|input|button|meta|link)\b[^>]*>",
            re.IGNORECASE,
        ),
    ),
]

# --- Professional Tone Checks (for dispute letters) ---

_TONE_PATTERNS = [
    (
        "threatening_language",
        re.compile(
            r"\b(?:sue|lawsuit|litigation|legal\s+action|court|prosecute|"
            r"criminal|fraud(?:ulent)?|scam|cheat|steal|liar)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "informal_language",
        re.compile(
            r"\b(?:lol|wtf|omg|bruh|dude|gonna|wanna|gotta|ain't)\b",
            re.IGNORECASE,
        ),
    ),
]


def filter_output(
    text: str,
    context: str = "general",
    redact_pii: bool = True,
    check_safety: bool = True,
) -> FilteredOutput:
    """
    Filters LLM-generated text for safety and compliance.

    Args:
        text: Raw LLM output text
        context: One of "general", "dispute_letter", "summary", "recommendation"
        redact_pii: Whether to scan and redact PII patterns
        check_safety: Whether to check for unsafe content

    Returns:
        FilteredOutput with clean_text and any warnings/redactions
    """
    if not text:
        return FilteredOutput(clean_text="", original_text="")

    result = FilteredOutput(
        clean_text=text,
        original_text=text,
    )

    # 1. PII Redaction
    if redact_pii:
        clean = result.clean_text
        for pii_name, regex, replacement in _PII_PATTERNS:
            matches = regex.findall(clean)
            if matches:
                result.flagged = True
                result.redactions.append(
                    f"PII ({pii_name}): {len(matches)} occurrence(s) redacted"
                )
                clean = regex.sub(replacement, clean)
                logger.warning(
                    "PII detected in LLM output — redacted.",
                    pii_type=pii_name,
                    occurrences=len(matches),
                    context=context,
                )
        result.clean_text = clean

    # 2. Unsafe Content Check
    if check_safety:
        for pattern_name, regex in _UNSAFE_PATTERNS:
            matches = regex.findall(result.clean_text)
            if matches:
                result.flagged = True
                result.warnings.append(
                    f"Unsafe content '{pattern_name}' detected ({len(matches)} occurrence(s))"
                )
                # Remove unsafe content
                result.clean_text = regex.sub("[CONTENT REMOVED]", result.clean_text)
                logger.warning(
                    "Unsafe content detected in LLM output — removed.",
                    pattern=pattern_name,
                    occurrences=len(matches),
                    context=context,
                )

    # 3. Context-specific checks
    if context == "dispute_letter":
        for tone_name, regex in _TONE_PATTERNS:
            matches = regex.findall(result.clean_text)
            if matches:
                result.warnings.append(
                    f"Tone issue '{tone_name}': {len(matches)} occurrence(s) — "
                    f"review for professional appropriateness"
                )
                logger.info(
                    "Tone concern in dispute letter.",
                    tone_issue=tone_name,
                    occurrences=len(matches),
                    sample=matches[0] if matches else "",
                )
                # Don't auto-remove tone issues — just warn
                # Threatening language like "lawsuit" may be intentional in dispute letters

    # 4. Length sanity check
    if len(result.clean_text) > 50_000:
        result.warnings.append(
            f"Output is unusually long ({len(result.clean_text):,} chars) — may indicate LLM loop"
        )

    if result.flagged:
        logger.info(
            "Output filter complete — issues found.",
            context=context,
            redactions=len(result.redactions),
            warnings=len(result.warnings),
        )

    return result

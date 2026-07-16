"""
FILE CANONICAL IDENTIFIER: backend/core/unit_normalizer.py
MODULE ROLE: Deterministic unit extraction, compatibility checking, and conversion.
SYSTEM BOUNDARY: Pure Python — no LLM, no DB, no external calls.
STATE DEPENDENCY / DATA CONTRACTS: Standalone utility. Used by cross_validator and compliance_checker.
CRITICAL LOGIC: All conversions are explicit and logged. Never silently assumes a conversion.
"""

import re
import structlog
from decimal import Decimal
from typing import Optional, Tuple

logger = structlog.get_logger()

# Each top-level key is the "canonical unit" for a family.
# Values map aliases → conversion factor TO the canonical unit.
# e.g. "kg": Decimal("0.001") means 1 kg = 0.001 MT
UNIT_FAMILIES = {
    "MT": {
        "mt": Decimal("1"),
        "metric tonne": Decimal("1"),
        "metric ton": Decimal("1"),
        "tonne": Decimal("1"),
        "tonnes": Decimal("1"),
        "ton": Decimal("1"),
        "tons": Decimal("1"),
        "kg": Decimal("0.001"),
        "kilogram": Decimal("0.001"),
        "kilograms": Decimal("0.001"),
        "kgs": Decimal("0.001"),
        "g": Decimal("0.000001"),
        "gram": Decimal("0.000001"),
        "grams": Decimal("0.000001"),
        "quintal": Decimal("0.1"),
        "quintals": Decimal("0.1"),
    },
    "unit": {
        "unit": Decimal("1"),
        "units": Decimal("1"),
        "piece": Decimal("1"),
        "pieces": Decimal("1"),
        "pc": Decimal("1"),
        "pcs": Decimal("1"),
        "nos": Decimal("1"),
        "each": Decimal("1"),
        "ea": Decimal("1"),
        "number": Decimal("1"),
        "numbers": Decimal("1"),
        "item": Decimal("1"),
        "items": Decimal("1"),
    },
    "hour": {
        "hour": Decimal("1"),
        "hours": Decimal("1"),
        "hr": Decimal("1"),
        "hrs": Decimal("1"),
        "man-hour": Decimal("1"),
        "man-hours": Decimal("1"),
        "manhour": Decimal("1"),
        "manhours": Decimal("1"),
        "day": Decimal("8"),
        "days": Decimal("8"),
        "man-day": Decimal("8"),
        "man-days": Decimal("8"),
        "manday": Decimal("8"),
        "mandays": Decimal("8"),
    },
    "litre": {
        "litre": Decimal("1"),
        "liter": Decimal("1"),
        "litres": Decimal("1"),
        "liters": Decimal("1"),
        "l": Decimal("1"),
        "ml": Decimal("0.001"),
        "millilitre": Decimal("0.001"),
        "milliliter": Decimal("0.001"),
        "kl": Decimal("1000"),
        "kilolitre": Decimal("1000"),
        "kiloliter": Decimal("1000"),
    },
    "sqft": {
        "sqft": Decimal("1"),
        "sq ft": Decimal("1"),
        "square feet": Decimal("1"),
        "square foot": Decimal("1"),
        "sft": Decimal("1"),
        "sqm": Decimal("10.764"),
        "sq m": Decimal("10.764"),
        "square meter": Decimal("10.764"),
        "square metre": Decimal("10.764"),
        "sq meter": Decimal("10.764"),
        "sq metre": Decimal("10.764"),
    },
    "month": {
        "month": Decimal("1"),
        "months": Decimal("1"),
        "monthly": Decimal("1"),
        "per month": Decimal("1"),
        "quarter": Decimal("3"),
        "quarterly": Decimal("3"),
        "year": Decimal("12"),
        "annual": Decimal("12"),
        "annually": Decimal("12"),
        "yearly": Decimal("12"),
    },
    "bag": {
        "bag": Decimal("1"),
        "bags": Decimal("1"),
    },
}

# Build a reverse lookup: alias → (canonical_unit, factor_to_canonical)
_ALIAS_MAP = {}
for canonical, aliases in UNIT_FAMILIES.items():
    for alias, factor in aliases.items():
        _ALIAS_MAP[alias.lower()] = (canonical, factor)


# Patterns to extract units from text like "₹450 per MT", "₹12/kg", "per unit"
_UNIT_PATTERNS = [
    re.compile(r'(?:per|/)\s*([a-zA-Z][a-zA-Z\s\-]*?)(?:\s|$|,|\.|\))', re.IGNORECASE),
    re.compile(r'(?:INR|Rs\.?|\$|₹|€|£)\s*[\d,\.]+\s*/\s*([a-zA-Z][a-zA-Z\s\-]*?)(?:\s|$|,|\.|\))', re.IGNORECASE),
    re.compile(r'\b(\d+)\s*(MT|kg|kgs|tonnes?|tons?|units?|pieces?|pcs?|hrs?|hours?|bags?|litres?|liters?|sqft|sqm)\b', re.IGNORECASE),
]


def extract_unit(text: str) -> Optional[str]:
    """
    Extract the unit of measure from a text string.
    Returns the normalized alias if found, None otherwise.

    Examples:
        "₹450 per MT" → "mt"
        "₹12/kg" → "kg"
        "100 pieces" → "pieces"
        "per man-day" → "man-day"
    """
    if not text:
        return None

    text_lower = text.lower()

    # Try pattern matching first
    for pattern in _UNIT_PATTERNS:
        match = pattern.search(text_lower)
        if match:
            # Get the last group (unit text)
            unit_text = match.group(match.lastindex).strip().lower()
            if unit_text in _ALIAS_MAP:
                return unit_text

    # Fallback: look for known aliases anywhere in text (longest match first)
    sorted_aliases = sorted(_ALIAS_MAP.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        if len(alias) < 2:
            continue  # Skip single-char aliases to avoid false matches
        # Word boundary matching
        pattern = re.compile(r'\b' + re.escape(alias) + r'\b', re.IGNORECASE)
        if pattern.search(text_lower):
            return alias

    return None


def get_canonical_unit(unit: str) -> Optional[Tuple[str, Decimal]]:
    """
    Returns (canonical_unit_family, factor_to_canonical) for a given unit alias.
    Returns None if the unit is not recognized.
    """
    return _ALIAS_MAP.get(unit.lower())


def units_are_compatible(unit_a: str, unit_b: str) -> bool:
    """
    Check if two units belong to the same family (can be converted).

    Examples:
        units_are_compatible("kg", "MT") → True
        units_are_compatible("kg", "hour") → False
        units_are_compatible("piece", "nos") → True
    """
    info_a = get_canonical_unit(unit_a)
    info_b = get_canonical_unit(unit_b)

    if info_a is None or info_b is None:
        return False

    return info_a[0] == info_b[0]


def convert_unit_price(
    price: Decimal,
    from_unit: str,
    to_unit: str,
) -> Optional[Tuple[Decimal, str]]:
    """
    Convert a unit price from one unit to another.
    Returns (converted_price, explanation_string) or None if incompatible.

    Example:
        convert_unit_price(Decimal("12"), "kg", "MT")
        → (Decimal("12000.00"), "₹12/kg → ₹12,000/MT (1 MT = 1000 kg)")

    Price conversion: if 1 kg costs ₹12, then 1 MT (= 1000 kg) costs ₹12,000.
    So: price_in_to_unit = price_in_from_unit * (factor_from / factor_to)
    """
    info_from = get_canonical_unit(from_unit)
    info_to = get_canonical_unit(to_unit)

    if info_from is None or info_to is None:
        logger.warning(
            "unit_normalizer: unrecognized unit",
            from_unit=from_unit, to_unit=to_unit,
            from_known=info_from is not None,
            to_known=info_to is not None,
        )
        return None

    canonical_from, factor_from = info_from
    canonical_to, factor_to = info_to

    if canonical_from != canonical_to:
        logger.warning(
            "unit_normalizer: incompatible unit families",
            from_unit=from_unit, to_unit=to_unit,
            from_family=canonical_from, to_family=canonical_to,
        )
        return None

    if factor_from == factor_to:
        return (price, f"Same unit ({from_unit} ≡ {to_unit})")

    # Convert: price per from_unit → price per to_unit
    # If from=kg (factor=0.001) and to=MT (factor=1), ratio = 1/0.001 = 1000
    # price_per_MT = price_per_kg * 1000
    ratio = factor_to / factor_from
    converted = (price * ratio).quantize(Decimal("0.01"))

    explanation = f"{from_unit} → {to_unit} (ratio: {ratio})"
    logger.info(
        "unit_normalizer: converted price",
        original_price=str(price), from_unit=from_unit,
        converted_price=str(converted), to_unit=to_unit,
        ratio=str(ratio),
    )
    return (converted, explanation)


def convert_quantity(
    quantity: Decimal,
    from_unit: str,
    to_unit: str,
) -> Optional[Tuple[Decimal, str]]:
    """
    Convert a quantity from one unit to another.
    Returns (converted_quantity, explanation_string) or None if incompatible.

    Example:
        convert_quantity(Decimal("5000"), "kg", "MT")
        → (Decimal("5.000"), "5000 kg → 5.000 MT")

    Quantity conversion: factor_from / factor_to gives the ratio.
    5000 kg * (0.001 / 1) = 5 MT
    """
    info_from = get_canonical_unit(from_unit)
    info_to = get_canonical_unit(to_unit)

    if info_from is None or info_to is None:
        return None

    canonical_from, factor_from = info_from
    canonical_to, factor_to = info_to

    if canonical_from != canonical_to:
        return None

    if factor_from == factor_to:
        return (quantity, f"Same unit ({from_unit} ≡ {to_unit})")

    ratio = factor_from / factor_to
    converted = (quantity * ratio).quantize(Decimal("0.001"))

    explanation = f"{quantity} {from_unit} → {converted} {to_unit}"
    return (converted, explanation)

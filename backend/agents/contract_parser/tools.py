"""
ProcureAI - File Summary

What it does:
Tools providing semantic searching and chunk parsing for the contract parser agent.

What it means:
Document parsing utility bindings for contract chunk indexing.

Importance in Project:
High. Accelerates rule extraction by pinpointing relevant contract clauses.
"""

import re
from datetime import datetime
from typing import List, Dict
import structlog
from backend.models.schemas import ContractRulebook, PricingRule

logger = structlog.get_logger()

# NOTE: The pipeline (contract_parser agent) does NOT use the functions below.
# It uses split_by_sections from backend.services.contract_chunker instead,
# and v3 architecture mandates full extraction (no section filtering).
#
# However, split_contract_to_sections() and is_relevant_section() ARE still
# used by backend.services.contract_comparator for its comparison flow.
# Do NOT delete them without updating contract_comparator.py.

def split_contract_to_sections(text: str) -> List[Dict[str, str]]:
    """
    Splits contract text into sections based on headers.
    Returns a list of dicts: [{"header": str, "content": str}]

    Used by: contract_comparator.py (NOT by the pipeline).
    """
    pattern = re.compile(
        r'(?:^|\n)(Section\s+\d+(?:\.\d+)?|Schedule\s+[A-Z]|Part\s+\d+|ARTICLE\s+[IVXLCDM]+)[:\-\.\s]*([^\n]*)',
        re.IGNORECASE
    )

    sections = []
    matches = list(pattern.finditer(text))

    if not matches:
        logger.info("No section headers detected in contract text. Treating full text as one section.")
        return [{"header": "Full Document", "content": text}]

    for i, match in enumerate(matches):
        header = f"{match.group(1).strip()}"
        inline_text = (match.group(2) or "").strip()

        start_idx = match.end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
        content = text[start_idx:end_idx].strip()
        if inline_text:
            content = f"{inline_text}\n{content}".strip()
        sections.append({"header": header, "content": content})

    # Capture preamble (any text before the first section header)
    first_match_start = matches[0].start()
    if first_match_start > 0:
        preamble = text[:first_match_start].strip()
        if preamble:
            sections.insert(0, {"header": "Preamble/Header", "content": preamble})

    return sections

def is_relevant_section(header: str, content: str) -> bool:
    """
    Filters contract sections to keep only those related to pricing, payment, SLAs, penalties, and discounts.

    Used by: contract_comparator.py (NOT by the pipeline — v3 extracts ALL sections).
    """
    header_lower = header.lower()
    content_lower = content.lower()

    if "preamble" in header_lower or "header" in header_lower:
        return True

    keywords = [
        "pricing", "rate", "fee", "charge", "billing", "penalty", "discount",
        "sla", "credit", "surcharge", "cap", "payment", "schedule", "volume",
        "tier", "milestone", "adjustment", "financial", "term", "cost"
    ]

    for kw in keywords:
        if kw in header_lower or kw in content_lower:
            return True

    return False

def extract_contract_metadata(text: str) -> Dict[str, str]:
    """
    Extract obvious document-level metadata deterministically before section LLM parsing.
    """
    metadata: Dict[str, str] = {}

    contract_id_match = re.search(r"\bContract\s+ID\s*:\s*([A-Z0-9][A-Z0-9\-_/]*)", text, re.IGNORECASE)
    if contract_id_match:
        metadata["contract_id"] = contract_id_match.group(1).strip()

    supplier_patterns = [
        r"\bSupplier\s*[:\-]\s*([^\n|]+)",
        r"\band\s+(.+?)\s*\(['\"]Supplier['\"]\)",
    ]
    for pattern in supplier_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            supplier = re.sub(r"\s+", " ", match.group(1)).strip(" .")
            if supplier:
                metadata["supplier_name"] = supplier
                break

    date_match = re.search(r"\bDate\s*:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
    if date_match:
        raw_date = date_match.group(1).strip()
        try:
            metadata["contract_date"] = datetime.strptime(raw_date, "%B %d, %Y").date().isoformat()
        except ValueError:
            metadata["contract_date"] = raw_date

    currency_match = re.search(r"\b(INR|USD|EUR|GBP)\b", text, re.IGNORECASE)
    if currency_match:
        metadata["contract_currency"] = currency_match.group(1).upper()

    return metadata

def enrich_pricing_rule(rule: PricingRule) -> PricingRule:
    """
    Fill common structured fields from the exact clause text when the LLM found the
    rule but omitted a machine-readable number.
    """
    text = " ".join([rule.description or "", rule.clause_text or ""])
    clause_text = rule.clause_text or text

    if rule.rule_type == "sla_penalty":
        percentages = [float(value) / 100.0 for value in re.findall(r"(\d+(?:\.\d+)?)\s*%", text)]
        if rule.sla_threshold_pct is None and percentages:
            rule.sla_threshold_pct = max(percentages)
        penalty_match = re.search(
            r"(?:credit|penalty)\s+(?:credit\s+)?(?:equal\s+to|of)\s+(\d+(?:\.\d+)?)\s*%",
            clause_text,
            re.IGNORECASE,
        )
        if not penalty_match:
            penalty_match = re.search(
                r"(?:penalty|credit)[^.]{0,120}?(\d+(?:\.\d+)?)\s*%",
                clause_text,
                re.IGNORECASE,
            )
        if penalty_match and (
            rule.penalty_pct is None
            or rule.penalty_pct > 0.5
            or (rule.sla_threshold_pct is not None and rule.penalty_pct == rule.sla_threshold_pct)
        ):
            rule.penalty_pct = float(penalty_match.group(1)) / 100.0
        elif rule.penalty_pct is None:
            if len(percentages) >= 2:
                rule.penalty_pct = min(percentages)

    if rule.rule_type == "early_payment_discount" and rule.discount_pct is None:
        discount_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:discount|credit)", text, re.IGNORECASE)
        if discount_match:
            rule.discount_pct = float(discount_match.group(1)) / 100.0

    if rule.rule_type in {"flat_rate", "cap_rate"}:
        amount_matches = [value.replace(",", "") for value in re.findall(r"INR\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)]
        if rule.rule_type == "flat_rate" and rule.flat_unit_price is None and amount_matches:
            rule.flat_unit_price = amount_matches[0]
        if rule.rule_type == "cap_rate" and rule.cap_amount is None and amount_matches:
            rule.cap_amount = amount_matches[-1]

    return rule

def merge_rulebooks(rulebooks: List[ContractRulebook]) -> ContractRulebook:
    """
    Combines rulebooks extracted from individual sections into a single master ContractRulebook.
    Resolves supplier name, contract ID, date, currency, and aggregates/re-indexes rules.
    """
    supplier_name = "Unknown"
    contract_id = "Unknown"
    contract_date = None
    contract_currency = "INR"
    merged_rules: List[PricingRule] = []
    unextracted = []
    notes = []
    
    # 1. Resolve metadata from first successful extraction
    for rb in rulebooks:
        # Keep non-unknown supplier names
        if rb.supplier_name and rb.supplier_name not in ("Unknown", "Unknown Supplier", ""):
            if supplier_name in ("Unknown", "Unknown Supplier", ""):
                supplier_name = rb.supplier_name
                
        # Keep non-unknown contract IDs
        if rb.contract_id and rb.contract_id not in ("Unknown", "Unknown-ID", ""):
            if contract_id in ("Unknown", "Unknown-ID", ""):
                contract_id = rb.contract_id
                
        if rb.contract_date and not contract_date:
            contract_date = rb.contract_date
            
        if rb.contract_currency and rb.contract_currency != "INR":
            contract_currency = rb.contract_currency
            
        # Accumulate rules
        if rb.rules:
            merged_rules.extend(rb.rules)
        if rb.unextracted_sections:
            unextracted.extend(rb.unextracted_sections)
        if rb.extraction_notes:
            notes.append(rb.extraction_notes)

    # 2. Re-index rule IDs sequentially (R001, R002, ...) and deduplicate
    final_rules: List[PricingRule] = []
    seen_clauses = set()
    rule_index = 1
    
    for rule in merged_rules:
        # Check if the rule is empty (e.g. unknown rule type or empty clause text)
        if rule.rule_type == "unknown" and not rule.clause_text:
            continue
            
        clause_key = rule.clause_text.strip().lower() if rule.clause_text else ""
        if not clause_key:
            clause_key = rule.description.strip().lower()
            
        if clause_key in seen_clauses:
            continue
            
        seen_clauses.add(clause_key)
        rule.rule_id = f"R{rule_index:03d}"
        rule_index += 1
        final_rules.append(enrich_pricing_rule(rule))
        
    return ContractRulebook(
        supplier_name=supplier_name,
        contract_id=contract_id,
        contract_date=contract_date,
        contract_currency=contract_currency,
        rules=final_rules,
        unextracted_sections=list(set(unextracted)),
        extraction_notes=" | ".join(notes) if notes else ""
    )


def vote_on_rules(
    extractions: List[ContractRulebook],
) -> tuple:
    """
    v4: Majority-vote across multiple extraction passes for self-consistency.

    Matches rules across passes by (rule_type, applies_to) tuple.
    For each matched rule group, votes on numeric parameters:
    - 3/3 agree → use value, confidence boost to 1.0, vote_agreement = "3/3"
    - 2/3 agree → use majority value, confidence = 0.9, vote_agreement = "2/3"
    - 0/3 agree → use pass-0 (temp=0.0) value, confidence = 0.3, vote_agreement = "1/3"

    Only numeric/decimal parameters are voted on. Text fields (rule_type, applies_to,
    clause_text, description) are taken from pass 0 (most deterministic).

    Returns:
        (voted_rulebook, review_flags)
        - voted_rulebook: ContractRulebook with best-consensus rules
        - review_flags: list of dicts for rules with disagreement
    """
    if not extractions:
        return ContractRulebook(supplier_name="Unknown", contract_id="Unknown", rules=[]), []

    if len(extractions) == 1:
        # Single pass — no voting needed
        for rule in extractions[0].rules:
            rule.vote_agreement = "1/1"
        return extractions[0], []

    # Use pass 0 (temp=0.0) as the base — most deterministic
    base = extractions[0]
    num_passes = len(extractions)
    review_flags = []

    # Collect rules from all passes, keyed by (rule_type, applies_to)
    all_pass_rules = []
    for extraction in extractions:
        pass_map = {}
        for rule in extraction.rules:
            key = (rule.rule_type, rule.applies_to.strip().lower())
            pass_map[key] = rule
        all_pass_rules.append(pass_map)

    # Build the set of all rule keys across all passes
    all_keys = set()
    for pm in all_pass_rules:
        all_keys.update(pm.keys())

    # Parameters to vote on (numeric fields)
    VOTABLE_FIELDS = [
        "flat_unit_price", "standard_unit_price",
        "sla_threshold_pct", "penalty_pct",
        "payment_window_days", "discount_pct",
        "bundle_threshold", "bundle_price",
        "cap_amount",
    ]

    voted_rules = []
    for key in sorted(all_keys):
        # Collect this rule from each pass
        candidates = [pm.get(key) for pm in all_pass_rules]
        present = [c for c in candidates if c is not None]

        if not present:
            continue

        # Use pass-0 as base (or first available if pass-0 didn't extract it)
        base_rule = candidates[0] if candidates[0] is not None else present[0]
        voted_rule = base_rule.model_copy(deep=True)

        # Vote on each numeric parameter
        disagreements = []
        lowest_agreement_count = len(present)
        
        for field in VOTABLE_FIELDS:
            values = []
            for c in present:
                val = getattr(c, field, None)
                if val is not None:
                    values.append(val)

            if not values:
                continue

            # Convert to strings for comparison (handles Decimal precision differences)
            str_values = [str(v).strip() for v in values]

            # Count occurrences
            from collections import Counter
            counts = Counter(str_values)
            most_common_str, most_common_count = counts.most_common(1)[0]
            
            lowest_agreement_count = min(lowest_agreement_count, most_common_count)

            if most_common_count == len(present) and len(present) >= 2:
                # All passes agree
                pass  # Keep base value (it's in the majority)
            elif most_common_count >= 2:
                # Majority agrees — use majority value
                # Find the actual object value (not string) from a matching candidate
                for c in present:
                    if str(getattr(c, field, None)).strip() == most_common_str:
                        setattr(voted_rule, field, getattr(c, field))
                        break
            else:
                # No majority — all disagree
                disagreements.append(field)

        # Determine agreement level
        found_in_passes = sum(1 for c in candidates if c is not None)
        # The true agreement count is bounded by how many passes even found the rule
        final_agreement = min(lowest_agreement_count, found_in_passes)
        
        voted_rule.vote_agreement = f"{final_agreement}/{num_passes}"
        
        if final_agreement == num_passes:
            voted_rule.extraction_confidence = min(1.0, voted_rule.extraction_confidence + 0.1)
        elif final_agreement >= 2:
            voted_rule.extraction_confidence = max(0.5, voted_rule.extraction_confidence * 0.9)
        else:
            voted_rule.extraction_confidence = 0.3
            review_flags.append({
                "rule_id": voted_rule.rule_id,
                "reason": f"Self-consistency disagreement on {len(disagreements)} fields: "
                          f"{', '.join(disagreements) if disagreements else 'Rule missing in other passes'}. Using temp=0.0 values.",
            })

        # Vote on tiers separately (structural comparison)
        if voted_rule.rule_type == "volume_tier":
            tier_sets = []
            for c in present:
                if c.tiers:
                    tier_key = tuple(
                        (t.min_units, t.max_units, str(t.unit_price))
                        for t in sorted(c.tiers, key=lambda t: t.min_units)
                    )
                    tier_sets.append(tier_key)

            if tier_sets:
                tier_counts = Counter(tier_sets)
                best_tiers, best_count = tier_counts.most_common(1)[0]
                if best_count < len(present):
                    # Tier disagreement
                    if best_count >= 2:
                        voted_rule.vote_agreement = f"{best_count}/{num_passes}"
                    else:
                        voted_rule.extraction_confidence = 0.3
                        review_flags.append({
                            "rule_id": voted_rule.rule_id,
                            "reason": "Self-consistency disagreement on volume tiers. "
                                      "Using temp=0.0 values.",
                        })

        voted_rules.append(voted_rule)

    # Build voted rulebook using base metadata
    voted_rulebook = base.model_copy(deep=True)
    voted_rulebook.rules = voted_rules

    return voted_rulebook, review_flags


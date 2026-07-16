"""
ProcureAI - File Summary

What it does:
Compares contract versions to identify rule additions and clause modifications.

What it means:
Differential comparator highlight risk profile changes.

Importance in Project:
High. Essential for the contract comparison dashboard.
"""

import json
import structlog
from typing import Optional, List
from pydantic import ValidationError
import google.generativeai as genai

from backend.models.schemas import (
    ContractRulebook,
    PricingRule,
    RuleChange,
    ComparisonSummary,
    ComparisonResult
)
from backend.models.audit import Comparison
from backend.core.llm_client import get_llm
from backend.core.prompt_loader import load_prompt
from backend.agents.contract_parser.tools import (
    split_contract_to_sections,
    is_relevant_section,
    merge_rulebooks
)
from backend.agents.contract_parser.agent import extract_section_rulebook
from sqlalchemy import update

logger = structlog.get_logger()

class RulebookDiff:
    def __init__(self, changes: List[RuleChange]):
        self.changes = changes

async def extract_rulebook(contract_text: str) -> ContractRulebook:
    """
    Parses contract text into a validated ContractRulebook.
    Extracts sections, identifies relevant ones, calls the parser LLM, and merges the results.
    """
    sections = split_contract_to_sections(contract_text)
    relevant_sections = [
        sec for sec in sections if is_relevant_section(sec["header"], sec["content"])
    ]
    
    if not relevant_sections:
        return ContractRulebook(supplier_name="Unknown", contract_id="Unknown", rules=[])
        
    llm = get_llm()
    prompt_template = load_prompt("contract_parser")
    schema_json = json.dumps(ContractRulebook.model_json_schema(), indent=2)
    system_prompt = prompt_template.replace("{schema}", schema_json)
    
    section_rulebooks = []
    for sec in relevant_sections:
        section_content = f"--- SECTION: {sec['header']} ---\n{sec['content']}"
        try:
            rulebook = await extract_section_rulebook(llm, system_prompt, section_content)
            section_rulebooks.append(rulebook)
        except Exception as e:
            logger.warning("Failed to extract rules from section during comparison", section=sec["header"], error=str(e))
            
    if not section_rulebooks:
        return ContractRulebook(supplier_name="Unknown", contract_id="Unknown", rules=[])
        
    return merge_rulebooks(section_rulebooks)

def diff_rulebooks(old: ContractRulebook, new: ContractRulebook) -> RulebookDiff:
    """
    Match rules between old and new by rule_type + applies_to.
    """
    changes = []
    
    # We match rules on (rule_type, applies_to) semantic keys
    old_rules = {(r.rule_type, r.applies_to): r for r in old.rules}
    new_rules = {(r.rule_type, r.applies_to): r for r in new.rules}
    
    all_keys = set(old_rules.keys()) | set(new_rules.keys())
    
    for key in all_keys:
        old_rule = old_rules.get(key)
        new_rule = new_rules.get(key)
        
        if old_rule and not new_rule:
            changes.append(RuleChange(
                change_type="REMOVED",
                rule_type=key[0],
                applies_to=key[1],
                old_clause=old_rule.clause_reference,
                new_clause=None,
                old_rule=old_rule,
                new_rule=None,
                impact="NEUTRAL",
                description=f"Rule removed: {old_rule.description}"
            ))
        elif new_rule and not old_rule:
            changes.append(RuleChange(
                change_type="ADDED",
                rule_type=key[0],
                applies_to=key[1],
                old_clause=None,
                new_clause=new_rule.clause_reference,
                old_rule=None,
                new_rule=new_rule,
                impact="NEUTRAL",
                description=f"New rule added: {new_rule.description}"
            ))
        else:
            # Match exists - compare the terms/pricing structure
            change = compare_rules(old_rule, new_rule)
            if change:
                changes.append(change)
                
    return RulebookDiff(changes=changes)

def compare_rules(old: PricingRule, new: PricingRule) -> Optional[RuleChange]:
    """Compare two matched rules and determine if anything changed."""
    differences = []
    impact = "NEUTRAL"
    
    # Compare tiers (volume pricing)
    if old.tiers and new.tiers:
        # Check for changed prices in matching tiers
        for old_tier in old.tiers:
            matching_new = next(
                (t for t in new.tiers if t.min_units == old_tier.min_units), None
            )
            if matching_new and matching_new.unit_price != old_tier.unit_price:
                delta = matching_new.unit_price - old_tier.unit_price
                impact = "WORSE" if delta > 0 else "BETTER"
                differences.append(
                    f"Tier {old_tier.min_units}+ units: "
                    f"${old_tier.unit_price} → ${matching_new.unit_price} "
                    f"({'↑ you pay more' if delta > 0 else '↓ you pay less'})"
                )
        # Check for added tiers
        for new_tier in new.tiers:
            matching_old = next(
                (t for t in old.tiers if t.min_units == new_tier.min_units), None
            )
            if not matching_old:
                differences.append(
                    f"Added tier: {new_tier.min_units}+ units at ${new_tier.unit_price}"
                )
        # Check for removed tiers
        for old_tier in old.tiers:
            matching_new = next(
                (t for t in new.tiers if t.min_units == old_tier.min_units), None
            )
            if not matching_new:
                differences.append(
                    f"Removed tier: {old_tier.min_units}+ units at ${old_tier.unit_price}"
                )
                
    # Compare flat rates
    if old.flat_unit_price is not None and new.flat_unit_price is not None:
        if old.flat_unit_price != new.flat_unit_price:
            delta = new.flat_unit_price - old.flat_unit_price
            impact = "WORSE" if delta > 0 else "BETTER"
            differences.append(
                f"Unit price: ${old.flat_unit_price} → ${new.flat_unit_price} "
                f"({'↑ you pay more' if delta > 0 else '↓ you pay less'})"
            )
            
    # Compare SLA threshold (lower threshold = better for client)
    if old.sla_threshold_pct is not None and new.sla_threshold_pct is not None:
        if old.sla_threshold_pct != new.sla_threshold_pct:
            impact = "WORSE" if new.sla_threshold_pct > old.sla_threshold_pct else "BETTER"
            differences.append(
                f"SLA threshold: {old.sla_threshold_pct*100}% → {new.sla_threshold_pct*100}%"
            )
            
    # Compare penalty (higher penalty = better for client - more leverage)
    if old.penalty_pct is not None and new.penalty_pct is not None:
        if old.penalty_pct != new.penalty_pct:
            impact = "BETTER" if new.penalty_pct > old.penalty_pct else "WORSE"
            differences.append(
                f"Penalty: {old.penalty_pct*100}% → {new.penalty_pct*100}%"
            )
            
    # Compare early payment discount
    if old.discount_pct is not None and new.discount_pct is not None:
        if old.discount_pct != new.discount_pct:
            impact = "BETTER" if new.discount_pct > old.discount_pct else "WORSE"
            differences.append(
                f"Discount: {old.discount_pct*100}% → {new.discount_pct*100}%"
            )
            
    if not differences:
        return None
        
    return RuleChange(
        change_type="MODIFIED",
        rule_type=old.rule_type,
        applies_to=old.applies_to,
        old_clause=old.clause_reference,
        new_clause=new.clause_reference,
        old_rule=old,
        new_rule=new,
        impact=impact,
        differences=differences,
        description="; ".join(differences)
    )

async def generate_comparison_summary(
    diff: RulebookDiff,
    old: ContractRulebook,
    new: ContractRulebook
) -> ComparisonSummary:
    """
    Summarizes rulebook changes using the Gemini LLM.
    """
    # If there are no changes, return early
    if not diff.changes:
        return ComparisonSummary(
            executive_summary="No pricing or operational rule changes were identified between the old and new contract versions.",
            negotiation_flags=[],
            overall_impact="UNCHANGED"
        )
        
    llm = get_llm()
    
    schema_json = json.dumps(ComparisonSummary.model_json_schema(), indent=2)
    
    system_prompt = (
        "You are an expert procurement and contract comparison analyst for ProcureAI.\n"
        "Your task is to analyze the changes between two contract versions for the same supplier.\n\n"
        "Given the rule changes provided, generate a structured JSON object containing:\n"
        "1. executive_summary: A 3-sentence plain English summary for a CFO that characterizes the overall direction of the changes (did it get better, worse, or mixed for the client?)\n"
        "2. negotiation_flags: A list of specific things to push back on. Include ONLY changes where the impact is WORSE. Max 5 items. If there are no worse changes, this list should be empty.\n"
        "3. overall_impact: One of: BETTER, WORSE, MIXED, UNCHANGED\n\n"
        f"You MUST strictly follow this JSON schema:\n{schema_json}"
    )
    
    input_text = (
        f"Generate a contract comparison summary based on these rule differences:\n\n"
        f"=== CONTRACT VERSIONS ===\n"
        f"Supplier: {new.supplier_name}\n"
        f"Old Contract ID: {old.contract_id}\n"
        f"New Contract ID: {new.contract_id}\n\n"
        f"=== DETECTED CHANGES ===\n"
    )
    for c in diff.changes:
        input_text += (
            f"- Rule Type: {c.rule_type} | Applies To: {c.applies_to}\n"
            f"  Change Type: {c.change_type} | Business Impact: {c.impact}\n"
            f"  Description: {c.description}\n"
        )
        if c.old_clause:
            input_text += f"  Old Clause Reference: {c.old_clause}\n"
        if c.new_clause:
            input_text += f"  New Clause Reference: {c.new_clause}\n"
        input_text += "\n"
        
    response = await llm.async_generate_content(
        contents=[system_prompt, input_text],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=ComparisonSummary.model_json_schema()
        )
    )
    
    try:
        return ComparisonSummary.model_validate_json(response.text)
    except ValidationError as val_err:
        logger.warning("Comparison summary validation failed on first attempt. Retrying with correction prompt...")
        correction_prompt = (
            f"Your previous JSON output failed validation against the ComparisonSummary schema.\n"
            f"Validation Error: {str(val_err)}\n"
            f"Original Input:\n{input_text}\n\n"
            f"Your invalid JSON response:\n{response.text}\n\n"
            f"Please output a corrected, strictly compliant JSON object matching the schema."
        )
        retry_response = await llm.async_generate_content(
            contents=[system_prompt, correction_prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ComparisonSummary.model_json_schema()
            )
        )
        return ComparisonSummary.model_validate_json(retry_response.text)

async def run_comparison(
    old_contract_text: str,
    new_contract_text: str,
    comparison_id: str,
    db
) -> ComparisonResult:
    """
    Orchestrates the entire comparison pipeline: parsing, diffing, LLM summarizing, and saving.
    """
    logger.info("Starting run_comparison", comparison_id=comparison_id)
    
    # Step 1: Parse old and new contracts using parser logic directly
    old_rulebook = await extract_rulebook(old_contract_text)
    new_rulebook = await extract_rulebook(new_contract_text)
    
    # Step 2: Diff the rulebooks
    diff = diff_rulebooks(old_rulebook, new_rulebook)
    
    # Step 3: LLM generates change summary + negotiation flags
    summary = await generate_comparison_summary(diff, old_rulebook, new_rulebook)
    
    # Count impacts
    worse_count = sum(1 for c in diff.changes if c.impact == "WORSE")
    better_count = sum(1 for c in diff.changes if c.impact == "BETTER")
    neutral_count = sum(1 for c in diff.changes if c.impact == "NEUTRAL")
    
    result = ComparisonResult(
        comparison_id=comparison_id,
        supplier_name=new_rulebook.supplier_name or old_rulebook.supplier_name or "Unknown Supplier",
        old_contract_id=old_rulebook.contract_id or "Unknown",
        new_contract_id=new_rulebook.contract_id or "Unknown",
        changes=diff.changes,
        summary=summary.executive_summary,
        negotiation_flags=summary.negotiation_flags,
        overall_impact=summary.overall_impact,
        worse_count=worse_count,
        better_count=better_count,
        neutral_count=neutral_count
    )
    
    # Persist comparison results asynchronously
    stmt = update(Comparison).where(Comparison.id == comparison_id).values(
        supplier_name=result.supplier_name,
        old_rulebook=old_rulebook.model_dump_json(),
        new_rulebook=new_rulebook.model_dump_json(),
        diff_result=result.model_dump_json(),
        status="COMPLETE"
    )
    await db.execute(stmt)
    await db.commit()
    
    logger.info("run_comparison completed successfully", comparison_id=comparison_id)
    return result

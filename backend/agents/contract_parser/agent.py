"""
FILE CANONICAL IDENTIFIER: backend/agents/contract_parser/agent.py
MODULE ROLE: Parses raw contract text to extract pricing/billing rules and rate structures using structured LLM outputs.
SYSTEM BOUNDARY: Integrates with Google Generative AI (Gemini). Restricts data writes to the SQLite database (Audit schema status/rulebook updates) and local state.
STATE DEPENDENCY / DATA CONTRACTS: Consumes contract_text from PipelineState. Outputs serialized ContractRulebook schema to PipelineState and stores text chunks via contract_chunker.
CRITICAL LOGIC: Implements a double-attempt correction-retry loop on Pydantic ValidationError by feeding validation errors back to the LLM with a correction prompt.
"""

import json
import structlog
from pydantic import ValidationError
import google.generativeai as genai

from backend.models.schemas import PipelineState, ContractRulebook, AgentError
from backend.core.llm_client import get_llm
from backend.core.prompt_loader import load_prompt
from backend.core.db import AsyncSessionLocal
from backend.models.audit import Audit
from sqlalchemy import select

from backend.agents.contract_parser.tools import (
    merge_rulebooks,
    extract_contract_metadata,
    vote_on_rules,
)

from backend.core.audit_logger import log_audit_event

logger = structlog.get_logger()

async def run_contract_parser(state: PipelineState) -> PipelineState:
    """
    Agent 1: Contract Parser
    Input:  state["contract_text"]
    Output: state["rulebook"], state["current_agent"] = "contract_parser"
    Error:  state["errors"].append(...), state["halt"] = True if unrecoverable
    """
    state["current_agent"] = "contract_parser"
    audit_id = state.get("audit_id")
    await log_audit_event(audit_id, "Contract Parser agent started.", "INFO", "contract_parser")
    
    # Update audit status in DB to PARSING_CONTRACT
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        db_audit = result.scalar_one_or_none()
        if db_audit:
            db_audit.status = "PARSING_CONTRACT"
            await session.commit()
            
    try:
        # Calculate file_hash of the uploaded contract PDF
        import hashlib
        import os
        from backend.models.audit import Contract
        
        contract_path = state.get("contract_path")
        current_file_hash = None
        if contract_path and os.path.exists(contract_path):
            try:
                import asyncio
                def _read_contract():
                    with open(contract_path, "rb") as f:
                        return f.read()
                file_bytes = await asyncio.to_thread(_read_contract)
                current_file_hash = hashlib.sha256(file_bytes).hexdigest()
            except Exception as e:
                logger.error("Failed to calculate contract file hash", error=str(e))

        # 1. Resolve contract by Supplier and Invoice Date (highest precedence versioning resolution)
        invoice_data = state.get("invoice_data")
        if invoice_data and isinstance(invoice_data, list) and len(invoice_data) > 0:
            inv = invoice_data[0]
            inv_supplier = inv.get("supplier_name")
            inv_date_str = inv.get("invoice_date")
            
            if inv_supplier and inv_date_str:
                from datetime import datetime
                parsed_inv_date = None
                for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                    try:
                        parsed_inv_date = datetime.strptime(inv_date_str.strip().split(".")[0], fmt)
                        break
                    except ValueError:
                        continue
                
                if parsed_inv_date:
                    async with AsyncSessionLocal() as session:
                        stmt_all_ctr = select(Contract).where(Contract.is_active == 1)
                        res_all_ctr = await session.execute(stmt_all_ctr)
                        all_contracts = res_all_ctr.scalars().all()
                        
                        best_contract = None
                        for c in all_contracts:
                            is_match = False
                            if c.supplier_name.lower() == inv_supplier.lower():
                                is_match = True
                            else:
                                try:
                                    aliases = json.loads(c.supplier_aliases or "[]")
                                    if any(a.lower() == inv_supplier.lower() for a in aliases):
                                        is_match = True
                                except Exception:
                                    pass
                                
                            if is_match:
                                # Check validity window
                                valid_from_ok = (c.valid_from is None or parsed_inv_date >= c.valid_from)
                                valid_until_ok = (c.valid_until is None or parsed_inv_date <= c.valid_until)
                                if valid_from_ok and valid_until_ok:
                                    best_contract = c
                                    break
                        
                        if best_contract and best_contract.rulebook:
                            await log_audit_event(
                                audit_id,
                                f"Resolved contract from library for supplier '{inv_supplier}' "
                                f"valid on invoice date {inv_date_str}: version {best_contract.version}. Bypassing parser.",
                                "INFO", "contract_parser"
                            )
                            state["rulebook"] = json.loads(best_contract.rulebook)
                            
                            stmt_audit = select(Audit).where(Audit.id == audit_id)
                            res_audit = await session.execute(stmt_audit)
                            db_audit = res_audit.scalar_one_or_none()
                            if db_audit:
                                db_audit.rulebook = best_contract.rulebook
                                db_audit.supplier_name = best_contract.supplier_name
                                db_audit.status = "CROSS_VALIDATING"
                                await session.commit()
                                
                            from backend.services.contract_chunker import ensure_contract_chunks
                            await ensure_contract_chunks(audit_id, session)
                            return state

        # 2. Skip if rulebook is already pre-extracted from the baseline contract upload
        if state.get("rulebook"):
            await log_audit_event(audit_id, "Using pre-extracted rulebook from Contract Library.", "INFO", "contract_parser")
            async with AsyncSessionLocal() as session:
                stmt = select(Audit).where(Audit.id == audit_id)
                result = await session.execute(stmt)
                db_audit = result.scalar_one_or_none()
                if db_audit:
                    db_audit.status = "CROSS_VALIDATING"
                    await session.commit()
            return state

        # 3. Query SQLite for an existing contract with that hash
        if current_file_hash:
            async with AsyncSessionLocal() as session:
                stmt_cached = select(Contract).where(Contract.file_hash == current_file_hash)
                res_cached = await session.execute(stmt_cached)
                cached_contract = res_cached.scalar_one_or_none()
                
                if cached_contract and cached_contract.rulebook:
                    await log_audit_event(
                        audit_id,
                        f"Found cached contract rulebook in library by file hash (v{cached_contract.version}). Bypassing parser.",
                        "INFO", "contract_parser"
                    )
                    state["rulebook"] = json.loads(cached_contract.rulebook)
                    
                    # Update audit rulebook and status
                    stmt_audit = select(Audit).where(Audit.id == audit_id)
                    res_audit = await session.execute(stmt_audit)
                    db_audit = res_audit.scalar_one_or_none()
                    if db_audit:
                        db_audit.rulebook = cached_contract.rulebook
                        db_audit.supplier_name = cached_contract.supplier_name
                        db_audit.status = "CROSS_VALIDATING"
                        await session.commit()
                        
                    # Ensure contract chunks exist
                    from backend.services.contract_chunker import ensure_contract_chunks
                    await ensure_contract_chunks(audit_id, session)
                    return state

        contract_text = state.get("contract_text", "")
        if not contract_text:
            raise ValueError("Contract text is empty or missing from state.")
        document_metadata = extract_contract_metadata(contract_text)
            
        # 1. Chunk contract by section
        from backend.services.contract_chunker import split_by_sections
        sections = split_by_sections(contract_text)
        
        relevant_sections = [{"header": h, "content": c} for h, c in sections]
        await log_audit_event(audit_id, f"Split contract into {len(relevant_sections)} sections for full extraction.", "INFO", "contract_parser")
        
        if not relevant_sections:
            raise ValueError("No sections could be extracted from the contract text.")
            
        # Initialize LLM and Prompt
        llm = get_llm()
        llm_status = llm.status_label() if hasattr(llm, "status_label") else "LLM"
        await log_audit_event(audit_id, f"Contract parser LLM backend: {llm_status}.", "INFO", "contract_parser")
        prompt_template = load_prompt("contract_parser", "prompt_extract_chunk.txt")
        
        # Inject schema into prompt
        schema_json = json.dumps(ContractRulebook.model_json_schema(), indent=2)
        system_prompt = prompt_template.replace("{schema}", schema_json)
        
        # 3. For each relevant section, run multi-pass LLM extraction (v4 self-consistency)
        from backend.core.config import SELF_CONSISTENCY_PASSES, SELF_CONSISTENCY_TEMPERATURES
        
        per_pass_section_rulebooks = []  # List[List[ContractRulebook]] — one list per pass
        num_passes = max(1, SELF_CONSISTENCY_PASSES)
        temperatures = SELF_CONSISTENCY_TEMPERATURES[:num_passes]
        # Pad temperatures if fewer than passes
        while len(temperatures) < num_passes:
            temperatures.append(temperatures[-1] if temperatures else 0.0)
        
        await log_audit_event(
            audit_id,
            f"Running {num_passes} extraction pass(es) with temperatures {temperatures} for self-consistency.",
            "INFO", "contract_parser"
        )
        
        for pass_idx in range(num_passes):
            temp = temperatures[pass_idx]
            pass_rulebooks = []
            
            for sec in relevant_sections:
                await log_audit_event(
                    audit_id,
                    f"[Pass {pass_idx+1}/{num_passes}] Parsing rules in section: '{sec['header']}' using {llm_status}.",
                    "INFO", "contract_parser"
                )
                section_content = f"--- SECTION: {sec['header']} ---\n{sec['content']}"
                
                try:
                    rulebook = await extract_section_rulebook(llm, system_prompt, section_content, temperature=temp)
                    pass_rulebooks.append(rulebook)
                    await log_audit_event(
                        audit_id,
                        f"[Pass {pass_idx+1}/{num_passes}] Successfully extracted {len(rulebook.rules)} rules from section '{sec['header']}'.",
                        "INFO", "contract_parser"
                    )
                except Exception as e:
                    await log_audit_event(
                        audit_id,
                        f"[Pass {pass_idx+1}/{num_passes}] Failed to extract rules from section '{sec['header']}', skipping. Error: {str(e) or repr(e)}",
                        "WARNING", "contract_parser"
                    )
            
            per_pass_section_rulebooks.append(pass_rulebooks)
        
        # Merge each pass's section rulebooks into one rulebook per pass
        per_pass_merged = []
        for pass_idx, pass_rulebooks in enumerate(per_pass_section_rulebooks):
            if pass_rulebooks:
                merged = merge_rulebooks(pass_rulebooks)
                per_pass_merged.append(merged)
        
        if not per_pass_merged:
            raise ValueError("Failed to extract any rules from the contract sections.")
        
        # v4: Vote across passes for self-consistency
        if len(per_pass_merged) > 1:
            merged_rulebook, vote_review_flags = vote_on_rules(per_pass_merged)
            await log_audit_event(
                audit_id,
                f"Self-consistency voting complete across {len(per_pass_merged)} passes. "
                f"{len(vote_review_flags)} disagreement(s) flagged for review.",
                "INFO", "contract_parser"
            )
            # Add vote review flags to state
            review_flags = state.get("review_flags", [])
            if review_flags is None:
                review_flags = []
            review_flags.extend(vote_review_flags)
            state["review_flags"] = review_flags
        else:
            merged_rulebook = per_pass_merged[0]
            
        # 4. Apply document metadata to merged rulebook
        if document_metadata.get("supplier_name"):
            merged_rulebook.supplier_name = document_metadata["supplier_name"]
        if document_metadata.get("contract_id"):
            merged_rulebook.contract_id = document_metadata["contract_id"]
        if document_metadata.get("contract_date"):
            merged_rulebook.contract_date = document_metadata["contract_date"]
        if document_metadata.get("contract_currency"):
            merged_rulebook.contract_currency = document_metadata["contract_currency"]
        
        # 4b. Resolution pass — resolve cross-references (v3 architecture step 4)
        # Scan for rules that reference other sections not visible during extraction
        CROSS_REF_PATTERNS = ["see section", "see schedule", "as defined in", 
                              "per schedule", "refer to", "set forth in",
                              "described in section", "in accordance with schedule"]
        unresolved_rules = []
        for rule in merged_rulebook.rules:
            clause_lower = (rule.clause_text or "").lower()
            desc_lower = (rule.description or "").lower()
            combined = clause_lower + " " + desc_lower
            if any(pattern in combined for pattern in CROSS_REF_PATTERNS):
                unresolved_rules.append(rule)
        
        if unresolved_rules:
            await log_audit_event(
                audit_id, 
                f"Found {len(unresolved_rules)} rules with unresolved cross-references. "
                f"Running resolution pass with full contract text.",
                "INFO", "contract_parser"
            )
            try:
                from backend.models.schemas import PricingRule as PricingRuleSchema
                resolve_prompt_template = load_prompt("contract_parser", "prompt_resolve_refs.txt")
                resolve_schema_json = json.dumps(PricingRuleSchema.model_json_schema(), indent=2)
                
                unresolved_json = json.dumps(
                    [r.model_dump(exclude_none=True) for r in unresolved_rules],
                    default=str, indent=2
                )
                
                resolve_prompt = (
                    resolve_prompt_template
                    .replace("{unresolved_rules_json}", unresolved_json)
                    .replace("{contract_text}", contract_text[:50000])  # Cap to avoid token limits
                    .replace("{schema}", resolve_schema_json)
                )
                
                resolve_response = await llm.async_generate_content(
                    contents=[resolve_prompt],
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        temperature=0.0
                    )
                )
                
                resolved_data = json.loads(resolve_response.text)
                if isinstance(resolved_data, list):
                    # Map resolved rules back by rule_id
                    resolved_by_id = {}
                    for rd in resolved_data:
                        try:
                            resolved_rule = PricingRuleSchema.model_validate(rd)
                            resolved_by_id[resolved_rule.rule_id] = resolved_rule
                        except Exception:
                            continue
                    
                    # Replace unresolved rules with resolved versions
                    for i, rule in enumerate(merged_rulebook.rules):
                        if rule.rule_id in resolved_by_id:
                            merged_rulebook.rules[i] = resolved_by_id[rule.rule_id]
                    
                    await log_audit_event(
                        audit_id,
                        f"Cross-reference resolution complete. Resolved {len(resolved_by_id)} of {len(unresolved_rules)} rules.",
                        "INFO", "contract_parser"
                    )
            except Exception as e:
                await log_audit_event(
                    audit_id,
                    f"Cross-reference resolution failed (non-fatal): {str(e)}",
                    "WARNING", "contract_parser"
                )
        
        # Verification step (deterministic, no LLM) + v4 clause byte anchoring
        import re as _re
        for rule in merged_rulebook.rules:
            if rule.clause_text:
                # Escape special regex characters in the clause text
                escaped = _re.escape(rule.clause_text.strip())
                # Replace any sequence of spaces/newlines with a pattern matching any whitespace
                pattern_str = _re.sub(r'(?:\\\s|\s)+', r'\\s+', escaped)
                try:
                    pattern = _re.compile(pattern_str, _re.IGNORECASE)
                    match = pattern.search(contract_text)
                    if match:
                        rule.clause_start_offset = match.start()
                        rule.clause_end_offset = match.end()
                    else:
                        # Fallback substring check on normalized content
                        normalized_contract = " ".join(contract_text.split())
                        normalized_clause = " ".join(rule.clause_text.split())
                        idx = normalized_contract.find(normalized_clause)
                        if idx >= 0:
                            rule.clause_start_offset = idx
                            rule.clause_end_offset = idx + len(normalized_clause)
                        else:
                            rule.extraction_confidence = 0.0
                            rule.clause_start_offset = None
                            rule.clause_end_offset = None
                            hallucination_error = AgentError(
                                agent="contract_parser",
                                error_type="hallucinated_clause",
                                message=f"Rule {rule.rule_id} clause_text not found in contract.",
                                recoverable=True
                            )
                            state.setdefault("errors", []).append(hallucination_error.model_dump())
                except Exception:
                    rule.clause_start_offset = None
                    rule.clause_end_offset = None
            else:
                rule.clause_start_offset = None
                rule.clause_end_offset = None

        if not merged_rulebook.rules:
            raise ValueError("No valid pricing rules were successfully parsed from the contract.")
            
        # 5. Write validated rulebook to state
        state["rulebook"] = merged_rulebook.model_dump()
        
        # 6. Write preview and full rulebook to database
        async with AsyncSessionLocal() as session:
            from backend.models.audit import Contract
            stmt = select(Audit).where(Audit.id == audit_id)
            result = await session.execute(stmt)
            db_audit = result.scalar_one_or_none()
            if db_audit:
                db_audit.rulebook = json.dumps(merged_rulebook.model_dump(), default=str)
                db_audit.supplier_name = merged_rulebook.supplier_name
                db_audit.status = "CROSS_VALIDATING"
                await session.commit()
                
                # Register or update contract in the Contract Library
                contract_id_to_link = None
                if current_file_hash:
                    # Look up if contract with this file hash already exists
                    stmt_contract = select(Contract).where(Contract.file_hash == current_file_hash)
                    res_contract = await session.execute(stmt_contract)
                    contract = res_contract.scalar_one_or_none()
                    if contract:
                        # Recalculate version if the supplier name changes from placeholder
                        if contract.supplier_name != merged_rulebook.supplier_name:
                            from sqlalchemy import func
                            stmt_version = select(func.max(Contract.version)).where(
                                func.lower(Contract.supplier_name) == merged_rulebook.supplier_name.lower()
                            )
                            res_version = await session.execute(stmt_version)
                            max_ver = res_version.scalar() or 0
                            contract.version = max_ver + 1

                        contract.rulebook = json.dumps(merged_rulebook.model_dump(), default=str)
                        contract.supplier_name = merged_rulebook.supplier_name
                        await session.commit()
                        contract_id_to_link = contract.id
                    else:
                        # Auto-register new contract version
                        from sqlalchemy import func
                        from backend.core.time import utc_now
                        import re
                        import uuid
                        
                        stmt_version = select(func.max(Contract.version)).where(
                            func.lower(Contract.supplier_name) == merged_rulebook.supplier_name.lower()
                        )
                        res_version = await session.execute(stmt_version)
                        max_ver = res_version.scalar() or 0
                        new_version = max_ver + 1
                        
                        clean_name = re.sub(r'[^a-zA-Z0-9]', '_', merged_rulebook.supplier_name.lower()).strip("_")
                        contract_id = f"ctr_{clean_name}_{uuid.uuid4().hex[:4]}"
                        
                        new_contract = Contract(
                            id=contract_id,
                            supplier_name=merged_rulebook.supplier_name,
                            supplier_aliases="[]",
                            contract_file_path=contract_path if contract_path else "",
                            original_filename=os.path.basename(contract_path) if contract_path else "contract.pdf",
                            uploaded_at=utc_now(),
                            is_active=1,
                            file_hash=current_file_hash,
                            version=new_version,
                            rulebook=json.dumps(merged_rulebook.model_dump(), default=str)
                        )
                        session.add(new_contract)
                        await session.commit()
                        contract_id_to_link = new_contract.id
                
                # Chunk the contract text and store chunks for Q&A
                from backend.services.contract_chunker import chunk_contract
                await chunk_contract(contract_text, audit_id, session, contract_id=contract_id_to_link)
                
        await log_audit_event(audit_id, f"Contract parsing complete. Extracted {len(merged_rulebook.rules)} rules total for supplier '{merged_rulebook.supplier_name}'.", "INFO", "contract_parser")
        
    except Exception as e:
        await log_audit_event(audit_id, f"Contract Parser agent failed: {str(e)}", "ERROR", "contract_parser")

        error = AgentError(
            agent="contract_parser",
            error_type="validation_failed" if "validation" in str(e).lower() else "llm_call_failed",
            message=str(e),
            recoverable=False
        )
        state.setdefault("errors", []).append(error.model_dump())
        state["halt"] = True
        
        async with AsyncSessionLocal() as session:
            stmt = select(Audit).where(Audit.id == audit_id)
            result = await session.execute(stmt)
            db_audit = result.scalar_one_or_none()
            if db_audit:
                db_audit.status = "FAILED"
                db_audit.error_detail = str(e)
                await session.commit()
                
    return state

async def extract_section_rulebook(llm, system_prompt: str, section_content: str, temperature: float = 0.0) -> ContractRulebook:
    """
    Calls LLM to parse a section. Employs correction-prompt retry logic on validation failures.
    v4: Accepts temperature parameter for self-consistency multi-pass extraction.
    """
    # LLM Call 1
    response = await llm.async_generate_content(
        contents=[system_prompt, section_content],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=ContractRulebook.model_json_schema(),
            temperature=temperature
        )
    )
    
    try:
        # Validate output
        return ContractRulebook.model_validate_json(response.text)
    except ValidationError as val_err:
        logger.warning("Pydantic validation failed on first LLM attempt. Retrying with correction prompt...")
        
        # Formulate correction prompt for the single retry
        correction_prompt = (
            f"Your previous JSON output failed validation against the ContractRulebook schema.\n"
            f"Validation Error: {str(val_err)}\n"
            f"Original Section Content:\n{section_content}\n\n"
            f"Your invalid JSON response:\n{response.text}\n\n"
            f"Please output a corrected, strictly compliant JSON object matching the schema. Do not add any text other than the JSON."
        )
        
        # LLM Call 2 (Retry)
        retry_response = await llm.async_generate_content(
            contents=[system_prompt, correction_prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ContractRulebook.model_json_schema(),
                temperature=0.0
            )
        )
        # Attempt validation again. If it fails, let it raise the error to be caught by caller.
        return ContractRulebook.model_validate_json(retry_response.text)

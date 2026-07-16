"""
FILE CANONICAL IDENTIFIER: backend/agents/invoice_extractor/agent.py
MODULE ROLE: Parses raw invoice texts, extracts line items/totals using LLM and deterministic validation.
SYSTEM BOUNDARY: Integrates with Google Generative AI (Gemini) and SQLite DB (Audit schema updates). INDEPENDENT of contract parser — does NOT access state["rulebook"] (v3 architecture rule #1).
STATE DEPENDENCY / DATA CONTRACTS: Consumes invoice_texts from PipelineState. Outputs a list of dicts matching InvoiceData (backend.models.schemas.InvoiceData) schema to PipelineState.
CRITICAL LOGIC: Overrides LLM validation flags with Python-calculated deterministic results from validate_invoice_arithmetic. Per-line arithmetic checked with Decimal (never float).
"""

import json
import asyncio
import structlog
from pydantic import ValidationError
import google.generativeai as genai

from backend.models.schemas import PipelineState, InvoiceData, AgentError
from backend.core.llm_client import get_llm
from backend.core.prompt_loader import load_prompt
from backend.core.db import AsyncSessionLocal
from backend.models.audit import Audit
from sqlalchemy import select

from backend.agents.invoice_extractor.tools import extract_invoice_metadata, validate_invoice_arithmetic, vote_on_invoice_data
from backend.core.config import SELF_CONSISTENCY_PASSES
from backend.core.audit_logger import log_audit_event

logger = structlog.get_logger()

async def run_invoice_extractor(state: PipelineState) -> PipelineState:
    """
    Agent 2: Invoice Extractor (INDEPENDENT — does not read state["rulebook"])
    Input:  state["invoice_texts"]
    Output: state["invoice_data"], state["current_agent"] = "invoice_extractor"
    Error:  state["errors"].append(...), state["halt"] = True if unrecoverable
    """
    state["current_agent"] = "invoice_extractor"
    audit_id = state.get("audit_id")
    await log_audit_event(audit_id, "Invoice Extractor agent started.", "INFO", "invoice_extractor")
    
    # Update audit status in DB to EXTRACTING_INVOICES
    async with AsyncSessionLocal() as session:
        stmt = select(Audit).where(Audit.id == audit_id)
        result = await session.execute(stmt)
        db_audit = result.scalar_one_or_none()
        if db_audit:
            db_audit.status = "EXTRACTING_INVOICES"
            await session.commit()
            
    try:
        invoice_texts = state.get("invoice_texts", [])
        if not invoice_texts:
            raise ValueError("Invoice texts list is empty or missing from state.")
            
        # Initialize LLM and Prompt
        llm = get_llm()
        llm_status = llm.status_label() if hasattr(llm, "status_label") else "LLM"
        await log_audit_event(audit_id, f"Invoice extractor LLM backend: {llm_status}.", "INFO", "invoice_extractor")
        prompt_template = load_prompt("invoice_extractor", "prompt_extract_invoice.txt")
        
        # Inject schema into prompt
        schema_json = json.dumps(InvoiceData.model_json_schema(), indent=2)
        system_prompt = prompt_template.replace("{schema}", schema_json)
        
        extracted_invoices = []
        
        invoice_paths = state.get("invoice_paths", [])
        
        # Process each invoice text sequentially
        for idx, (inv_path, inv_text) in enumerate(zip(invoice_paths, invoice_texts), 1):
            await log_audit_event(audit_id, f"Processing invoice {idx} of {len(invoice_texts)}: extracting structure and mapping line items.", "INFO", "invoice_extractor")
            invoice_metadata = extract_invoice_metadata(inv_text)
            
            def _read_pdf():
                with open(inv_path, "rb") as f:
                    return f.read()
            pdf_bytes = await asyncio.to_thread(_read_pdf)
            pdf_part = llm.create_document_part(pdf_bytes, "application/pdf")
            
            input_contents = [
                f"=== INVOICE TEXT (Fallback) ===\n{inv_text}",
                pdf_part
            ]
            
            try:
                if SELF_CONSISTENCY_PASSES > 1:
                    await log_audit_event(
                        audit_id,
                        f"Running 2 extraction passes (temperatures 0.0 and 0.1) for invoice {idx} self-consistency.",
                        "INFO", "invoice_extractor"
                    )
                    pass0_obj = await extract_single_invoice(llm, system_prompt, input_contents, temperature=0.0)
                    pass1_obj = await extract_single_invoice(llm, system_prompt, input_contents, temperature=0.1)
                    
                    # Apply metadata to both passes
                    for p_obj in [pass0_obj, pass1_obj]:
                        if invoice_metadata.get("invoice_id"):
                            p_obj.invoice_id = invoice_metadata["invoice_id"]
                        if invoice_metadata.get("invoice_date"):
                            p_obj.invoice_date = invoice_metadata["invoice_date"]
                        if invoice_metadata.get("billing_period"):
                            p_obj.billing_period = invoice_metadata["billing_period"]
                        if invoice_metadata.get("supplier_name"):
                            p_obj.supplier_name = invoice_metadata["supplier_name"]
                        if invoice_metadata.get("invoice_total"):
                            p_obj.invoice_total = invoice_metadata["invoice_total"]
                            
                    invoice_data_obj, vote_review_flags = vote_on_invoice_data([pass0_obj, pass1_obj])
                    
                    # Append findings to state["review_flags"]
                    if vote_review_flags:
                        await log_audit_event(
                            audit_id,
                            f"Invoice {invoice_data_obj.invoice_id} self-consistency mismatch: {len(vote_review_flags)} flag(s) generated.",
                            "WARNING", "invoice_extractor"
                        )
                        if "review_flags" not in state or state["review_flags"] is None:
                            state["review_flags"] = []
                        state["review_flags"].extend(vote_review_flags)
                else:
                    invoice_data_obj = await extract_single_invoice(llm, system_prompt, input_contents, temperature=0.0)
                    if invoice_metadata.get("invoice_id"):
                        invoice_data_obj.invoice_id = invoice_metadata["invoice_id"]
                    if invoice_metadata.get("invoice_date"):
                        invoice_data_obj.invoice_date = invoice_metadata["invoice_date"]
                    if invoice_metadata.get("billing_period"):
                        invoice_data_obj.billing_period = invoice_metadata["billing_period"]
                    if invoice_metadata.get("supplier_name"):
                        invoice_data_obj.supplier_name = invoice_metadata["supplier_name"]
                    if invoice_metadata.get("invoice_total"):
                        invoice_data_obj.invoice_total = invoice_metadata["invoice_total"]
                
                # Run deterministic arithmetic checks in Python (Decimal only, never float)
                arithmetic_errors = validate_invoice_arithmetic(invoice_data_obj)
                
                # Override LLM-generated validation fields with deterministic Python results
                invoice_data_obj.validation.totals_match = (len(arithmetic_errors) == 0)
                invoice_data_obj.validation.arithmetic_errors = arithmetic_errors
                invoice_data_obj.invoice_arithmetic_valid = invoice_data_obj.validation.totals_match
                
                # Set per-line arithmetic_valid flags based on the Decimal check results
                # and cap extraction confidence for lines/invoices that fail
                failed_line_ids = set()
                for err_msg in arithmetic_errors:
                    # Extract line ID from error messages like "Line L001 arithmetic mismatch: ..."
                    import re as _re
                    line_match = _re.search(r'Line (\S+) arithmetic mismatch', err_msg)
                    if line_match:
                        failed_line_ids.add(line_match.group(1))
                
                for item in invoice_data_obj.line_items:
                    if item.line_id in failed_line_ids:
                        item.arithmetic_valid = False
                        item.extraction_confidence = min(item.extraction_confidence, 0.5)
                    else:
                        item.arithmetic_valid = True
                
                # Cap all line confidences if invoice-level total mismatch
                if not invoice_data_obj.invoice_arithmetic_valid:
                    for item in invoice_data_obj.line_items:
                        item.extraction_confidence = min(item.extraction_confidence, 0.5)
                        
                # Semantic mapping moved to Node 3.
                invoice_data_obj.validation.all_lines_mapped = True
                invoice_data_obj.validation.unmapped_lines = []
                
                extracted_invoices.append(invoice_data_obj.model_dump())
                await log_audit_event(audit_id, f"Invoice {idx} parsing complete. Extracted invoice ID: {invoice_data_obj.invoice_id} with {len(invoice_data_obj.line_items)} line items.", "INFO", "invoice_extractor")
                if invoice_data_obj.validation.arithmetic_errors:
                    await log_audit_event(audit_id, f"Warning: Invoice {invoice_data_obj.invoice_id} contains arithmetic errors: {', '.join(invoice_data_obj.validation.arithmetic_errors)}", "WARNING", "invoice_extractor")
                
            except Exception as e:
                await log_audit_event(audit_id, f"Failed to extract invoice {idx} (attempted retry included). Error: {str(e)}", "ERROR", "invoice_extractor")
                # We fail the entire pipeline if any invoice is unreadable or fails validation twice
                raise RuntimeError(f"Invoice {idx} parsing failed: {str(e)}") from e
                
        if not extracted_invoices:
            raise ValueError("No invoice data was successfully extracted.")
            
        # Write back to state
        state["invoice_data"] = extracted_invoices
        
        # Save results to database and update status to CHECKING_COMPLIANCE
        async with AsyncSessionLocal() as session:
            stmt = select(Audit).where(Audit.id == audit_id)
            result = await session.execute(stmt)
            db_audit = result.scalar_one_or_none()
            if db_audit:
                db_audit.invoice_data = json.dumps(extracted_invoices, default=str)
                db_audit.status = "PARSING_CONTRACT"
                await session.commit()
                
        await log_audit_event(audit_id, f"Invoice extraction complete. Extracted total {len(extracted_invoices)} invoice(s).", "INFO", "invoice_extractor")
        
    except Exception as e:
        await log_audit_event(audit_id, f"Invoice Extractor agent failed: {str(e)}", "ERROR", "invoice_extractor")

        error = AgentError(
            agent="invoice_extractor",
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

async def extract_single_invoice(llm, system_prompt: str, input_contents: list, temperature: float = 0.0) -> InvoiceData:
    """
    Calls LLM to extract invoice data. Employs correction-prompt retry logic on validation failures.
    """
    # LLM Call 1
    response = await llm.async_generate_content(
        contents=[system_prompt] + input_contents,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=InvoiceData.model_json_schema(),
            temperature=temperature
        )
    )
    
    try:
        # Validate output
        return InvoiceData.model_validate_json(response.text)
    except ValidationError as val_err:
        logger.warning("Pydantic validation failed on first invoice extraction attempt. Retrying with correction prompt...")
        
        # Formulate correction prompt for the single retry
        correction_prompt = (
            f"Your previous JSON output failed validation against the InvoiceData schema.\n"
            f"Validation Error: {str(val_err)}\n"
            f"Your invalid JSON response:\n{response.text}\n\n"
            f"Please output a corrected, strictly compliant JSON object matching the schema. Do not add any text other than the JSON."
        )
        
        # LLM Call 2 (Retry)
        retry_response = await llm.async_generate_content(
            contents=[system_prompt] + input_contents + [correction_prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=InvoiceData.model_json_schema(),
                temperature=0.0
            )
        )
        # Attempt validation again. If it fails, let it raise the error to be caught by caller.
        return InvoiceData.model_validate_json(retry_response.text)

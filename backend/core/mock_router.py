# backend/core/mock_router.py
# Cognitive router simulating LLM responses for various multi-agent tasks, QA, and report generations.

import os
import json
import re
from datetime import datetime
import structlog
from backend.core.mock_data import MOCK_CONTRACT_RULES, MOCK_INVOICE_DATA

logger = structlog.get_logger()

LAST_MOCK_CONTRACT_ID = None

class MockResponse:
    def __init__(self, text: str):
        self.text = text


def get_sqlite_database_path() -> str:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./procureai.db")
    if database_url.startswith("sqlite+aiosqlite://"):
        database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)

    if database_url.startswith("sqlite:///"):
        return database_url[len("sqlite:///"):] or "./procureai.db"

    return "procureai.db"


def get_mock_response(contents, generation_config):
    global LAST_MOCK_CONTRACT_ID
    # Log generation_config details for debugging
    logger.info("get_mock_response invoked", generation_config_type=str(type(generation_config)))
    
    # Flatten contents to a single string and track input_str (the actual specific query input text)
    content_str = ""
    input_str = ""
    if isinstance(contents, list):
        for item in contents:
            item_text = ""
            if hasattr(item, 'parts'):
                for p in item.parts:
                    item_text += p.text + " "
            elif isinstance(item, str):
                item_text += item + " "
            content_str += item_text
            if item_text.strip():
                input_str = item_text  # The last non-empty item contains the specific input text
    else:
        content_str = str(contents)
        input_str = content_str
        
    content_str_lower = content_str.lower()
    input_str_lower = input_str.lower()

    # Extract schema title if available
    schema_title = ""
    if generation_config is not None:
        try:
            schema = None
            if isinstance(generation_config, dict):
                schema = generation_config.get("response_schema")
            else:
                schema = getattr(generation_config, "response_schema", None)
            
            if schema and isinstance(schema, dict):
                schema_title = schema.get("title", "")
        except Exception as e:
            logger.warning("Failed to extract response_schema title", error=str(e))

    # Determine which mock task to run based on the response schema title first, then fallback to content search
    is_task_1 = False
    is_task_2 = False
    is_task_3 = False
    is_task_4 = False
    is_task_9 = False

    if schema_title:
        if schema_title == "InvoiceRuleMapping":
            is_task_1 = True
        elif schema_title == "DiscrepancyNarrative":
            is_task_2 = True
        elif schema_title == "InvoiceData":
            is_task_3 = True
        elif schema_title == "ContractRulebook":
            is_task_4 = True
        elif schema_title == "CriticReflection":
            is_task_9 = True
    else:
        # Fallback to string matching if no schema title is found
        if "invoicerulemapping" in content_str_lower or ("mappings" in content_str_lower and "discrepancynarrative" not in content_str_lower and "evidence narration" not in content_str_lower and "criticreflection" not in content_str_lower and "critic reflection" not in content_str_lower):
            is_task_1 = True
        elif "discrepancynarrative" in content_str_lower or "evidence narration" in content_str_lower:
            is_task_2 = True
        elif "invoicedata" in content_str_lower or "line_items" in content_str_lower or "invoice_id" in content_str_lower:
            is_task_3 = True
        elif "contractrulebook" in content_str_lower or "contract_id" in content_str_lower:
            is_task_4 = True
        elif "criticreflection" in content_str_lower or "critic reflection" in content_str_lower:
            is_task_9 = True

    # 1. Invoice Rule Mapping Mocking (Compliance Checker Task 1)
    if is_task_1:
        candidate_rules = {}
        # Parse candidate context from content_str
        match = re.search(r"=== CANDIDATE RULES PER LINE ===[^{]*(\{.*\})", content_str, re.DOTALL)
        if match:
            try:
                candidate_rules = json.loads(match.group(1))
            except Exception:
                pass
        
        # If candidate_rules is empty, try to match using the hardcoded fallbacks
        mappings = []
        if candidate_rules:
            for line_id, rules in candidate_rules.items():
                applicable_ids = []
                for r in rules:
                    rule_type = r.get("rule_type", "")
                    desc = (r.get("description") or "").lower()
                    clause = (r.get("clause_text") or "").lower()
                    applies = (r.get("applies_to") or "").lower()
                    combined = " ".join([desc, clause, applies])
                    
                    is_credit = rule_type == "sla_penalty" or any(
                        token in combined
                        for token in ("milestone", "delay penalty", "penalty credit", "shall credit", "liquidated damages")
                    )
                    if not is_credit:
                        applicable_ids.append(r.get("rule_id"))
                mappings.append({
                    "line_id": line_id,
                    "applicable_rule_ids": applicable_ids,
                    "confidence": 1.0,
                    "justification": "Dynamically mapped by mock router."
                })
        else:
            # Hardcoded fallbacks if parsing failed
            if "apex" in input_str_lower or "inv-apx" in input_str_lower:
                mappings = [{"line_id": "L001", "applicable_rule_ids": ["R001"]}]
            elif "techsoft" in input_str_lower or "inv-tss" in input_str_lower:
                if "202409" in input_str_lower:
                    mappings = [{"line_id": "L001", "applicable_rule_ids": ["R001"]}, {"line_id": "L002", "applicable_rule_ids": ["R002"]}]
                else:
                    mappings = [{"line_id": "L001", "applicable_rule_ids": ["R001"]}, {"line_id": "L002", "applicable_rule_ids": ["R003"]}]
            elif "buildright" in input_str_lower or "inv-brc" in input_str_lower:
                if "202410" in input_str_lower:
                    mappings = [{"line_id": "L001", "applicable_rule_ids": ["R001"]}, {"line_id": "L002", "applicable_rule_ids": ["R003"]}]
                else:
                    mappings = [{"line_id": "L001", "applicable_rule_ids": []}]
            elif "medisupply" in input_str_lower or "inv-msc" in input_str_lower:
                mappings = [{"line_id": "L001", "applicable_rule_ids": ["R001"]}, {"line_id": "L002", "applicable_rule_ids": ["R002"]}]
            elif "cloudhost" in input_str_lower or "inv-chi" in input_str_lower:
                if "202410" in input_str_lower:
                    mappings = [{"line_id": "L001", "applicable_rule_ids": ["R001", "R003"]}]
                else:
                    mappings = [{"line_id": "L001", "applicable_rule_ids": ["R001"]}]
            elif "proservices" in input_str_lower or "inv-psc" in input_str_lower:
                mappings = [
                    {"line_id": "L001", "applicable_rule_ids": ["R001"]},
                    {"line_id": "L002", "applicable_rule_ids": ["R002"]}
                ]
                    
        return MockResponse(json.dumps({"mappings": mappings}))

    # 2. Compliance Checker Discrepancy Narrative Mocking (Compliance Checker Task 2)
    if is_task_2:
        supplier = "apex"
        if "techsoft" in input_str_lower:
            supplier = "techsoft"
        elif "buildright" in input_str_lower:
            supplier = "buildright"
        elif "medisupply" in input_str_lower:
            supplier = "medisupply"
        elif "cloudhost" in input_str_lower:
            supplier = "cloudhost"
        elif "proservices" in input_str_lower:
            supplier = "proservices"

        matched_rule = "R001"
        for i in range(1, 18):
            r_id = f"R{i:03d}"
            if r_id.lower() in input_str_lower:
                matched_rule = r_id
                break
                
        descriptions_map = {
            "apex": {
                "R001": "Volume discount not applied. October quantity of 1,240 units qualifies for Tier 2 pricing (INR 11.50/unit) under Section 4.2. Supplier charged Tier 1 rate (INR 12.50/unit).",
                "R002": "Missed SLA penalty. November on-time delivery rate was 94.2%, falling below the contractually agreed 97.0% threshold. Supplier did not credit 12% of the month's invoice total.",
                "R003": "Early payment discount missed."
            },
            "techsoft": {
                "R001": "Incorrect Consulting rate charged.",
                "R002": "QA Testing bundle discount not applied. Total hours exceeded 20 days, but charged standard rate.",
                "R003": "Project Management fee exceeds monthly contract cap of INR 30,000.00."
            },
            "buildright": {
                "R001": "Excavation volume discount tier mismatch.",
                "R002": "Foundation Completion milestone delay penalty of INR 5,000.00 per day was not credited.",
                "R003": "Cement Supply bag unit cap exceeded. Billed at INR 450.00 per bag, but capped at INR 400.00."
            },
            "medisupply": {
                "R001": "Surgical Gloves volume tier discount not applied.",
                "R002": "Regulatory Surcharge exceeds maximum cap of INR 2,000.00."
            },
            "cloudhost": {
                "R001": "VM Hosting hourly rate charged incorrectly.",
                "R002": "SLA Credit of 20% missed for VM hosting. Availability was 99.5%, falling below 99.9% guarantee.",
                "R003": "Commitment discount of 15% missed. VM hosting hours exceeded 10,000, but discount was not credited."
            },
            "proservices": {
                "R001": "IT Consulting rate discrepancy. December Senior IT Consultant services were billed at INR 13,000.00/day, exceeding the contract rate of INR 12,000.00/day.",
                "R002": "Project Management advisory rate matched correctly.",
                "R003": "Missed SLA penalty. Consulting Dashboard uptime fell to 96.5% in December, below the contractual 98.0% threshold. The 10% penalty credit was not applied."
            }
        }
        
        clauses_map = {
            "apex": {
                "R001": "For monthly shipment volumes of 500-1,999 units, the applicable unit price shall be INR 11.50.",
                "R002": "Should the Supplier's on-time delivery rate fall below 97% in any calendar month, the Supplier shall issue a credit equal to 12% of that month's invoice total.",
                "R003": "A discount of 2% shall apply to any invoice settled within 10 business days of the invoice date."
            },
            "techsoft": {
                "R001": "Senior Developer Consulting services shall be billed at a flat rate of INR 8,000.00 per day.",
                "R002": "If the customer licenses more than 20 days of QA Testing Services in a billing period, a discounted rate of INR 3,200.00 per day shall apply to all QA days billed.",
                "R003": "Project Management Services shall be billed hourly at a rate of INR 1,500.00 per hour, subject to a maximum cap of INR 30,000.00 per month."
            },
            "buildright": {
                "R001": "For 101 to 500 cubic meters, the rate is INR 450.00 per cubic meter.",
                "R002": "If the project milestone designated 'Foundation Completion' is delayed beyond the agreed target date of October 15, 2024, the Supplier shall credit the Client a delay penalty of INR 5,000.00 per calendar day of delay.",
                "R003": "The cost for Cement bags supplied for construction shall be billed at actual supplier cost plus a 10% markup, subject to an absolute maximum cap of INR 400.00 per bag. Under no circumstances shall the billed rate per bag exceed INR 400.00."
            },
            "medisupply": {
                "R001": "Surgical Gloves shall be priced based on order size: 1,001 to 5,000 boxes at INR 220.00 per box.",
                "R002": "The total regulatory surcharge per invoice is subject to a maximum limit of INR 2,000.00."
            },
            "cloudhost": {
                "R001": "VM Hosting Services shall be billed at a usage-based rate of INR 10.00 per instance-hour.",
                "R002": "The Supplier guarantees a monthly VM service uptime of 99.9%. If the actual VM uptime in any calendar month falls below 99.9%, a credit equal to 20% of that month's total hosting charges shall be applied to the invoice.",
                "R003": "If the total hosting VM hours in a billing month exceed 10,000 hours, a commitment volume discount of 15% shall be applied to the total hosting charges for that month."
            },
            "proservices": {
                "R001": "Senior IT Consultant services shall be billed at a standard daily rate of INR 12,000.00.",
                "R002": "Project Management advisory services shall be billed at a standard daily rate of INR 10,000.00.",
                "R003": "Should the consulting dashboard availability fall below 98.0% in any month, a penalty credit of 10% of that month's total billing shall be applied to the invoice."
            }
        }
        
        return MockResponse(json.dumps({
            "description": descriptions_map.get(supplier, {}).get(matched_rule, "Pricing compliance discrepancy found."),
            "clause_text": clauses_map.get(supplier, {}).get(matched_rule, "")
        }))

    # 3. Invoice Extractor Mocking
    if is_task_3:
        matched_invoice = None
        for inv_id in MOCK_INVOICE_DATA:
            if inv_id.lower() in input_str_lower or inv_id.replace("-", "").lower() in input_str_lower:
                matched_invoice = inv_id
                break
                
        # If not matched by invoice ID, check by supplier and period combinations
        if not matched_invoice:
            if "apex" in input_str_lower:
                matched_invoice = "INV-APX-202410" if "oct" in input_str_lower or "10" in input_str_lower else "INV-APX-202411"
            elif "techsoft" in input_str_lower:
                matched_invoice = "INV-TSS-202409" if "sep" in input_str_lower or "09" in input_str_lower else "INV-TSS-202410"
            elif "buildright" in input_str_lower:
                matched_invoice = "INV-BRC-202410" if "oct" in input_str_lower or "10" in input_str_lower else "INV-BRC-202411"
            elif "medisupply" in input_str_lower:
                matched_invoice = "INV-MSC-202410" if "oct" in input_str_lower or "10" in input_str_lower else "INV-MSC-202411"
            elif "cloudhost" in input_str_lower:
                matched_invoice = "INV-CHI-202410" if "oct" in input_str_lower or "10" in input_str_lower else "INV-CHI-202411"
            elif "proservices" in input_str_lower:
                matched_invoice = "INV-PSC-202412"
                
        if matched_invoice:
            inv_data = MOCK_INVOICE_DATA[matched_invoice]
            response_json = {
                "invoice_id": inv_data["invoice_id"],
                "invoice_date": inv_data["invoice_date"],
                "billing_period": inv_data["billing_period"],
                "supplier_name": inv_data["supplier_name"],
                "invoice_total": inv_data["invoice_total"],
                "line_items": inv_data["line_items"],
                "validation": {
                    "totals_match": True,
                    "all_lines_mapped": True,
                    "arithmetic_errors": [],
                    "unmapped_lines": []
                }
            }
            return MockResponse(json.dumps(response_json))
            
        return MockResponse(json.dumps({
            "invoice_id": "Unknown-Invoice",
            "invoice_date": "2026-01-01",
            "billing_period": "Unknown",
            "supplier_name": "Unknown",
            "invoice_total": "0.00",
            "line_items": [],
            "validation": {
                "totals_match": False,
                "all_lines_mapped": False,
                "arithmetic_errors": ["Invoice ID could not be identified from raw text"],
                "unmapped_lines": []
            }
        }))

    # 4. Contract Parser Mocking
    if is_task_4:
        matched_contract = None
        for cid in MOCK_CONTRACT_RULES:
            if cid.lower() in input_str_lower or cid.replace("-", "").lower() in input_str_lower:
                matched_contract = cid
                break
        
        if not matched_contract:
            if "apex" in input_str_lower:
                matched_contract = "MSA-2024-APX-001"
            elif "techsoft" in input_str_lower:
                matched_contract = "MSA-2024-TSS-002"
            elif "buildright" in input_str_lower:
                matched_contract = "MSA-2024-BRC-003"
            elif "medisupply" in input_str_lower:
                matched_contract = "MSA-2024-MSC-004"
            elif "cloudhost" in input_str_lower:
                matched_contract = "MSA-2024-CHI-005"
            elif "proservices" in input_str_lower:
                matched_contract = "MSA-2024-PSC-006"
                
        if not matched_contract:
            import sqlite3
            try:
                conn = sqlite3.connect(get_sqlite_database_path())
                cursor = conn.cursor()
                # Try to get the most recent audit in PARSING_CONTRACT status
                cursor.execute("SELECT contract_file FROM audits WHERE status = 'PARSING_CONTRACT' ORDER BY created_at DESC LIMIT 1")
                row = cursor.fetchone()
                if not row:
                    # Fallback to the most recent audit overall
                    cursor.execute("SELECT contract_file FROM audits ORDER BY created_at DESC LIMIT 1")
                    row = cursor.fetchone()
                if row and row[0]:
                    contract_file = row[0].lower()
                    if "c001" in contract_file or "apex" in contract_file:
                        matched_contract = "MSA-2024-APX-001"
                    elif "c002" in contract_file or "techsoft" in contract_file:
                        matched_contract = "MSA-2024-TSS-002"
                    elif "c003" in contract_file or "buildright" in contract_file:
                        matched_contract = "MSA-2024-BRC-003"
                    elif "c004" in contract_file or "medisupply" in contract_file:
                        matched_contract = "MSA-2024-MSC-004"
                    elif "c005" in contract_file or "cloudhost" in contract_file:
                        matched_contract = "MSA-2024-CHI-005"
                    elif "c006" in contract_file or "proservices" in contract_file:
                        matched_contract = "MSA-2024-PSC-006"
                conn.close()
            except Exception as db_err:
                logger.warning("Failed to query database for contract", error=str(db_err))

        if not matched_contract and LAST_MOCK_CONTRACT_ID:
            matched_contract = LAST_MOCK_CONTRACT_ID
                
        if matched_contract:
            LAST_MOCK_CONTRACT_ID = matched_contract
            rules_data = MOCK_CONTRACT_RULES[matched_contract]
            section_rules = []
            
            is_preamble = "preamble" in input_str_lower or "master services agreement" in input_str_lower or "software services" in input_str_lower or "construction services" in input_str_lower or "medical equipment" in input_str_lower or "cloud infrastructure" in input_str_lower
            
            for rule in rules_data["rules"]:
                clause_ref = rule["clause_reference"].lower()
                if (clause_ref in input_str_lower) or (rule["rule_type"].lower() in input_str_lower) or (rule["description"].lower() in input_str_lower):
                    section_rules.append(rule)
            
            if not section_rules and not is_preamble:
                if "volume" in input_str_lower or "tier" in input_str_lower:
                    section_rules = [r for r in rules_data["rules"] if r["rule_type"] == "volume_tier"]
                elif "sla" in input_str_lower or "penalty" in input_str_lower or "uptime" in input_str_lower:
                    section_rules = [r for r in rules_data["rules"] if r["rule_type"] == "sla_penalty"]
                elif "payment" in input_str_lower or "early" in input_str_lower:
                    section_rules = [r for r in rules_data["rules"] if r["rule_type"] == "early_payment_discount"]
                elif "flat" in input_str_lower or "consulting" in input_str_lower:
                    section_rules = [r for r in rules_data["rules"] if r["rule_type"] == "flat_rate"]
                elif "bundle" in input_str_lower or "qa" in input_str_lower:
                    section_rules = [r for r in rules_data["rules"] if r["rule_type"] == "bundle_discount"]
                elif "cap" in input_str_lower or "cement" in input_str_lower or "surcharge" in input_str_lower:
                    section_rules = [r for r in rules_data["rules"] if r["rule_type"] == "cap_rate"]
            
            response_json = {
                "supplier_name": rules_data["supplier_name"],
                "contract_id": rules_data["contract_id"],
                "contract_date": rules_data["contract_date"],
                "contract_currency": rules_data["contract_currency"],
                "rules": section_rules,
                "unextracted_sections": [],
                "extraction_notes": f"Mock extraction for section: {rules_data['supplier_name']}"
            }
            return MockResponse(json.dumps(response_json))
        
        return MockResponse(json.dumps({
            "supplier_name": "Unknown",
            "contract_id": "Unknown",
            "rules": [],
            "unextracted_sections": [],
            "extraction_notes": "Could not identify supplier from section content"
        }))

    # 5. Report Generator Mocking (ReportShorthand)
    is_task_5 = (schema_title == "ReportShorthand") or (
        not schema_title and "report_generator" in content_str_lower
    )
    if is_task_5:
        # Determine the supplier from input
        supplier = "unknown"
        if "apex" in input_str_lower or "apx" in input_str_lower:
            supplier = "apex"
        elif "techsoft" in input_str_lower or "tss" in input_str_lower:
            supplier = "techsoft"
        elif "buildright" in input_str_lower or "brc" in input_str_lower:
            supplier = "buildright"
        elif "medisupply" in input_str_lower or "msc" in input_str_lower:
            supplier = "medisupply"
        elif "cloudhost" in input_str_lower or "chi" in input_str_lower:
            supplier = "cloudhost"
        elif "proservices" in input_str_lower or "psc" in input_str_lower:
            supplier = "proservices"
            
        reports = {
            "apex": {
                "executive_summary": "An audit of Apex Logistics Ltd for October and November 2024 revealed total financial leakage of INR 4,180.00. The primary findings include a volume pricing discrepancy on line items and a missed SLA penalty credit for the month of November. Recommendations include raising a dispute for the overcharged rate and reclaiming the unapplied SLA penalty credit.",
                "recommendations": [
                    "Dispute the Tier 1 rate charged on INV-APX-202410 and request a credit of INR 1,240.00 to align with the Tier 2 contract rate.",
                    "Escalate the unapplied 12% SLA penalty credit for November on INV-APX-202411 to reclaim INR 2,940.00 due to on-time delivery rate of 94.2%.",
                    "Establish a monthly compliance check process to verify logistics SLA compliance prior to invoice approvals."
                ]
            },
            "techsoft": {
                "executive_summary": "The audit of TechSoft Solutions for September and October 2024 identified total leakage of INR 25,200.00. Key discrepancies include unapplied bundle discount for QA Testing Services and billings exceeding the monthly consulting project management cap. It is recommended to recover these overcharges and enforce monthly invoice caps.",
                "recommendations": [
                    "Request a credit of INR 19,200.00 for September QA Testing Services on INV-TSS-202409, as volume exceeded 20 days and qualifies for the discounted INR 3,200.00 daily rate.",
                    "Dispute the Project Management charges on INV-TSS-202410, which exceeded the monthly cap of INR 30,000.00 by INR 6,000.00.",
                    "Automate invoice validations against contractual capping rules to prevent future over-billing."
                ]
            },
            "buildright": {
                "executive_summary": "An audit of BuildRight Contractors for October and November 2024 revealed total leakage of INR 35,000.00. The findings include an overcharge on Cement Supply bags due to unit price capping and a missed milestone delay penalty for the Foundation Completion. Actionable recommendations are provided to claim credits and enforce capping.",
                "recommendations": [
                    "Reclaim INR 10,000.00 for Cement Supply on INV-BRC-202410, as the price was billed at INR 450.00 per bag instead of the contractual cap of INR 400.00.",
                    "Dispute the Foundation Completion delay on INV-BRC-202411 and claim a penalty credit of INR 25,000.00 (5 days of delay at INR 5,000.00 per day).",
                    "Implement regular milestone tracking checks prior to milestone-linked invoice clearance."
                ]
            },
            "medisupply": {
                "executive_summary": "An audit of MediSupply Corp for October and November 2024 identified total leakage of INR 35,000.00. Key violations include unapplied volume tier pricing for Surgical Gloves and a regulatory surcharge billing exceeding the invoice limit. We recommend requesting immediate credits.",
                "recommendations": [
                    "Dispute the unit price for Surgical Gloves on INV-MSC-202410 and request a credit of INR 22,000.00 to align with Tier 2 pricing (INR 220.00/box instead of INR 250.00).",
                    "Claim a credit of INR 13,000.00 for the Regulatory Surcharge on INV-MSC-202410, which exceeded the invoice cap of INR 2,000.00.",
                    "Verify regulatory surcharges on medical consumables invoices against contractual limits before making payments."
                ]
            },
            "cloudhost": {
                "executive_summary": "An audit of CloudHost India for October and November 2024 identified total billing leakage of INR 34,000.00. Findings show that a monthly VM hosting commitment discount was not applied, and a VM service uptime SLA penalty credit was missed. Recommendations include disputing these overcharges.",
                "recommendations": [
                    "Request a credit of INR 18,000.00 on INV-CHI-202410 for unapplied VM Hosting commitment discount, as VM hours exceeded the 10,000-hour threshold.",
                    "Claim a 20% SLA credit of INR 16,000.00 on INV-CHI-202411, as monthly VM service availability fell to 99.50% (below the 99.90% SLA threshold).",
                    "Integrate cloud monitoring dashboards with invoice validation to dynamically verify monthly uptime and commitment hours."
                ]
            },
            "proservices": {
                "executive_summary": "An audit of ProServices Consulting for December 2024 identified total leakage of INR 38,000.00. Discrepancies include a rate overcharge for Senior IT Consultant services and a missed SLA penalty credit due to system dashboard uptime falling below the 98.0% threshold. We recommend recovery of these overcharges.",
                "recommendations": [
                    "Dispute the Senior IT Consultant rate on INV-PSC-202412 and request a credit of INR 15,000.00 to align with the contractual daily rate of INR 12,000.00.",
                    "Claim the 10% SLA penalty credit of INR 23,000.00 on INV-PSC-202412 due to system dashboard uptime of 96.5% falling below the 98.0% guarantee.",
                    "Review consulting performance metrics monthly to ensure appropriate SLA penalty application before payment."
                ]
            }
        }
        
        rep = reports.get(supplier, {
            "executive_summary": "An audit of the supplier invoices identified pricing discrepancies. Action is required to recover overcharges.",
            "recommendations": [
                "Dispute detected pricing discrepancies with the supplier.",
                "Review contract terms and billing practices to prevent future leakage."
            ]
        })
        return MockResponse(json.dumps(rep))

    # 9. Critic Reflection Mocking
    if is_task_9:
        return MockResponse(json.dumps({
            "status": "CONFIRMED",
            "reasoning": "The mathematical discrepancy has been verified and matches the contract clauses."
        }))

    # 6. Dispute Letter Mocking
    is_dispute = (schema_title == "DisputeLetterLLMResponse") or ("dispute_generator" in content_str_lower or "dispute letter" in content_str_lower)
    if is_dispute:
        company_name = "Our Company"
        m = re.search(r"Company Name:\s*(.*)", content_str)
        if m: company_name = m.group(1).strip()

        signatory_name = "Signatory Name"
        m = re.search(r"Signatory Name:\s*(.*)", content_str)
        if m: signatory_name = m.group(1).strip()

        signatory_title = "Head of Procurement"
        m = re.search(r"Signatory Title:\s*(.*)", content_str)
        if m: signatory_title = m.group(1).strip()

        supplier_contact = "Supplier Contact"
        m = re.search(r"Supplier Contact:\s*(.*)", content_str)
        if m: supplier_contact = m.group(1).strip()

        supplier_name = "Supplier Name"
        m = re.search(r"Supplier Name:\s*(.*)", content_str)
        if m: supplier_name = m.group(1).strip()

        due_date = "Due Date"
        m = re.search(r"Due Date:\s*(.*)", content_str)
        if m: due_date = m.group(1).strip()

        reference_number = None
        m = re.search(r"Reference Number:\s*(.*)", content_str)
        if m:
            val = m.group(1).strip()
            if val != "N/A":
                reference_number = val

        audit_date = "Audit Date"
        m = re.search(r"Audit Date:\s*(.*)", content_str)
        if m: audit_date = m.group(1).strip()

        billing_period = "Billing Period"
        m = re.search(r"Billing Period:\s*(.*)", content_str)
        if m: billing_period = m.group(1).strip()

        contract_id = "Contract ID"
        m = re.search(r"Contract ID:\s*(.*)", content_str)
        if m: contract_id = m.group(1).strip()

        findings = []
        try:
            summary_idx = content_str.find("=== FINDINGS SUMMARY ===")
            if summary_idx != -1:
                array_start = content_str.find("[", summary_idx)
                if array_start != -1:
                    bracket_count = 0
                    array_end = -1
                    for idx in range(array_start, len(content_str)):
                        if content_str[idx] == '[':
                            bracket_count += 1
                        elif content_str[idx] == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                array_end = idx + 1
                                break
                    if array_end != -1:
                        findings = json.loads(content_str[array_start:array_end])
        except Exception as parse_err:
            logger.warning("Failed to parse findings in mock dispute letter", error=str(parse_err))

        total_disputed = 0.0
        for f in findings:
            try:
                total_disputed += abs(float(f.get("delta", 0.0)))
            except Exception:
                pass

        date_str = datetime.now().strftime("%B %d, %Y")
        ref_line = f"Reference Number: {reference_number}\n" if reference_number else ""
        subject = f"Formal Dispute — Invoice Audit Findings | {contract_id} | {billing_period}"

        # Plain text letter
        text = f"Date: {date_str}\n{ref_line}"
        text += f"To:\n{supplier_contact}\n{supplier_name}\n\n"
        text += f"Subject: {subject}\n\n"
        text += f"Dear {supplier_contact},\n\n"
        text += f"I am writing on behalf of {company_name} to formally dispute certain charges billed under Contract ID {contract_id} for the billing period {billing_period}. Following a compliance audit completed on {audit_date}, we identified billing discrepancies resulting in financial leakage.\n\n"
        text += f"The total amount under dispute is ${total_disputed:,.2f} across {len(findings)} identified discrepancy/discrepancies. Below are the details of the specific findings and corresponding contractual violations:\n\n"
        for i, f in enumerate(findings, 1):
            text += f"{i}. Finding {f.get('finding_id')}: {f.get('description')}\n"
            text += f"   - Contract Clause: \"{f.get('clause_text')}\" ({f.get('clause_reference')})\n"
            text += f"   - Charged Amount: ${float(f.get('line_total_charged') or f.get('charged') or 0.0):,.2f} | Expected Amount: ${float(f.get('line_total_expected') or f.get('expected') or 0.0):,.2f} | Overcharge: ${float(f.get('delta') or 0.0):,.2f}\n\n"
        text += f"Please review the attached details and issue a credit note or corrected invoice for the total disputed amount of ${total_disputed:,.2f} by {due_date}.\n\n"
        text += f"We value our partnership with {supplier_name} and hope to resolve this matter amicably. However, please note that unresolved disputes will be escalated to senior management and legal counsel as per contract terms.\n\n"
        text += f"Sincerely,\n\n{signatory_name}\n{signatory_title}\n{company_name}"

        # HTML letter
        html = f"<p><strong>Date:</strong> {date_str}</p>"
        if reference_number:
            html += f"<p><strong>Reference Number:</strong> {reference_number}</p>"
        html += f"<p><strong>To:</strong><br>{supplier_contact}<br>{supplier_name}</p>"
        html += f"<p><strong>Subject:</strong> {subject}</p>"
        html += f"<p>Dear {supplier_contact},</p>"
        html += f"<p>I am writing on behalf of <strong>{company_name}</strong> to formally dispute certain charges billed under Contract ID <strong>{contract_id}</strong> for the billing period <strong>{billing_period}</strong>. Following a compliance audit completed on {audit_date}, we identified billing discrepancies resulting in financial leakage.</p>"
        html += f"<p>The total amount under dispute is <strong>${total_disputed:,.2f}</strong> across <strong>{len(findings)}</strong> identified discrepancy/discrepancies. Below are the details of the specific findings and corresponding contractual violations:</p>"

        for i, f in enumerate(findings, 1):
            html += f"<p><strong>{i}. Finding {f.get('finding_id')}:</strong> {f.get('description')}<br>"
            html += f"<strong>Contract Clause:</strong> \"{f.get('clause_text')}\" ({f.get('clause_reference')})<br>"
            html += f"<strong>Charged Amount:</strong> ${float(f.get('line_total_charged') or f.get('charged') or 0.0):,.2f} | <strong>Expected Amount:</strong> ${float(f.get('line_total_expected') or f.get('expected') or 0.0):,.2f} | <strong>Overcharge:</strong> ${float(f.get('delta') or 0.0):,.2f}</p>"

        html += "<table>"
        html += "<tr><th>Finding</th><th>Description</th><th>Clause</th><th>Charged</th><th>Expected</th><th>Overcharge</th></tr>"
        for f in findings:
            html += f"<tr><td>{f.get('finding_id')}</td><td>{f.get('description')}</td><td>{f.get('clause_reference')}</td><td>${float(f.get('line_total_charged') or f.get('charged') or 0.0):,.2f}</td><td>${float(f.get('line_total_expected') or f.get('expected') or 0.0):,.2f}</td><td>${float(f.get('delta') or 0.0):,.2f}</td></tr>"
        html += "</table>"

        html += f"<p>Please review the attached details and issue a credit note or corrected invoice for the total disputed amount of <strong>${total_disputed:,.2f}</strong> by <strong>{due_date}</strong>.</p>"
        html += f"<p>We value our partnership with {supplier_name} and hope to resolve this matter amicably. However, please note that unresolved disputes will be escalated to senior management and legal counsel as per contract terms.</p>"
        html += f"<p>Sincerely,<br><br><strong>{signatory_name}</strong><br>{signatory_title}<br><strong>{company_name}</strong></p>"

        return MockResponse(json.dumps({
            "letter_text": text,
            "letter_html": html
        }))

    # 7. Comparison Summary Mocking
    is_comparison_summary = (schema_title == "ComparisonSummary") or (
        not schema_title and "comparison summary" in content_str_lower
    )
    if is_comparison_summary:
        supplier = "CloudHost India"
        if "apex" in content_str_lower:
            supplier = "Apex Logistics"
            
        summary_data = {
            "executive_summary": f"The new contract version for {supplier} introduces mixed changes. Flat prices are unchanged, but SLA terms and early discount rates have been revised. CFO approval is recommended prior to signing.",
            "negotiation_flags": [
                "Push back on early payment discount decrease from 2% to 1%",
                "SLA threshold was raised, making penalty triggers less favorable"
            ],
            "overall_impact": "MIXED"
        }
        
        # Check if the diff lists no changes
        if "no changes" in content_str_lower or "detected changes: \n\n" in content_str_lower or "detected changes:\n\n" in content_str_lower:
            summary_data = {
                "executive_summary": "No pricing or operational rule changes were identified between the old and new contract versions.",
                "negotiation_flags": [],
                "overall_impact": "UNCHANGED"
            }
            
        return MockResponse(json.dumps(summary_data))

    # 8. Contract Q&A Chat Mocking
    is_qa = (
        "contract compliance analyst agent for procureai" in content_str_lower or
        "contract intelligence assistant for procureai" in content_str_lower or
        "contract_qa" in content_str_lower or
        "rag context" in content_str_lower or
        "confidence assessment" in content_str_lower or
        "confidence levels" in content_str_lower
    )
    if is_qa:
        user_question = ""
        user_matches = re.findall(r"User:\s*(.*?)(?=\nAssistant:|\Z)", content_str, re.IGNORECASE | re.DOTALL)
        if user_matches:
            user_question = user_matches[-1].strip()
        user_question_lower = user_question.lower()

        # Determine the supplier
        supplier = "unknown"
        if "apex" in content_str_lower:
            supplier = "apex"
        elif "techsoft" in content_str_lower:
            supplier = "techsoft"
        elif "buildright" in content_str_lower:
            supplier = "buildright"
        elif "medisupply" in content_str_lower:
            supplier = "medisupply"
        elif "cloudhost" in content_str_lower:
            supplier = "cloudhost"
        elif "proservices" in content_str_lower:
            supplier = "proservices"
            
        if any(term in user_question_lower for term in ("hello", "hi", "hey")):
            response_text = (
                "Hello. I can answer questions about this contract's clauses, pricing, SLA penalties, discounts, and caps.\n\n"
                "[CONFIDENCE: HIGH]"
            )

        elif "sla" in user_question_lower or "penalty" in user_question_lower or "credit" in user_question_lower or "uptime" in user_question_lower:
            not_found_answer = (
                "I could not find this information in the contract. The contract may\n"
                "not address this, or it may be in a section that was not extracted.\n\n"
                "[CONFIDENCE: NOT_FOUND]"
            )
            if supplier == "apex":
                response_text = (
                    "Under Section 8.1, the SLA delivery rules state:\n"
                    "Should the Supplier's on-time delivery rate fall below 97% in any calendar month, the Supplier shall issue a credit equal to 12% of that month's invoice total.\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "buildright":
                response_text = (
                    "Under Section 5.3, if the 'Foundation Completion' milestone is delayed beyond the target date of October 15, 2024, the Supplier shall credit the Client a delay penalty of INR 5,000.00 per calendar day of delay.\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "cloudhost":
                response_text = (
                    "Under Section 5.2, the SLA uptime rules state:\n"
                    "The Supplier guarantees a monthly VM service uptime of 99.9%. If the actual VM uptime in any calendar month falls below 99.9%, a credit equal to 20% of that month's total hosting charges shall be applied to the invoice.\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "proservices":
                response_text = (
                    "Under Section 6.2, the SLA terms state:\n"
                    "Should the consulting dashboard availability fall below 98.0% in any month, a penalty credit of 10% of that month's total billing shall be applied to the invoice.\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            else:
                response_text = not_found_answer

        elif "discount" in user_question_lower or "early" in user_question_lower:
            if supplier == "apex":
                response_text = (
                    "Under Section 12.4, an early payment discount of 2% applies to any invoice settled within 10 business days of the invoice date.\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "techsoft":
                response_text = (
                    "Under Section 3.2, a QA Testing Services bundle discount of 20% is applied, reducing the rate from INR 4,000.00/day to INR 3,200.00/day if more than 20 days are licensed in a billing period.\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "cloudhost":
                response_text = (
                    "Under Section 8.4, a commitment volume discount of 15% is applied, reducing the VM hosting rate from INR 10.00 to INR 8.50 per hour if total hosting hours in a billing month exceed 10,000 hours.\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            else:
                response_text = (
                    "I could not find this information in the contract. The contract may\n"
                    "not address this, or it may be in a section that was not extracted.\n\n"
                    "[CONFIDENCE: NOT_FOUND]"
                )

        elif "tier" in user_question_lower or "price" in user_question_lower or "pricing" in user_question_lower or "rate" in user_question_lower or "charge" in user_question_lower:
            if supplier == "apex":
                response_text = (
                    "Under Section 4.2, the pricing tiers for Standard Delivery - Domestic are:\n"
                    "- 0-499 units: INR 14.00 per unit\n"
                    "- 500-1,999 units: INR 11.50 per unit\n"
                    "- 2,000 units and above: INR 9.80 per unit.\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "techsoft":
                response_text = (
                    "According to the contract, the daily consulting rates are:\n"
                    "- Senior Developer Consulting: Flat rate of INR 8,000.00 per day (Section 3.1)\n"
                    "- QA Testing Services: Standard rate of INR 4,000.00 per day, which reduces to INR 3,200.00 per day if more than 20 days are licensed in a billing period (Section 3.2)\n"
                    "- Project Management Services: Billed at INR 1,500.00 per hour, capped at INR 30,000.00 per month (Section 3.3).\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "buildright":
                response_text = (
                    "Under the contract, Site Excavation Services (cubic meters) are priced based on the following volume tiers:\n"
                    "- 0-100 cubic meters: INR 500.00 per cubic meter\n"
                    "- 101-500 cubic meters: INR 450.00 per cubic meter\n"
                    "- Exceeding 500 cubic meters: INR 400.00 per cubic meter (Section 4.1).\n"
                    "Additionally, Cement Supply is billed at actual cost plus a 10% markup, capped at a maximum of INR 400.00 per bag (Section 7.2).\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "medisupply":
                response_text = (
                    "For Surgical Gloves (Sterile, Latex Free), the volume tier pricing is as follows:\n"
                    "- 0-1,000 boxes: INR 250.00 per box\n"
                    "- 1,001-5,000 boxes: INR 220.00 per box\n"
                    "- 5,001 boxes and above: INR 200.00 per box (Section 2.1).\n"
                    "There is also a regulatory surcharge of 5% of the glove order value, capped at a maximum limit of INR 2,000.00 per invoice (Section 6.5).\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "cloudhost":
                response_text = (
                    "VM Hosting Services are billed at a usage-based rate of INR 10.00 per instance-hour (Section 3.1).\n"
                    "If the total hosting VM hours in a month exceed 10,000 hours, a commitment volume discount of 15% is applied, reducing the rate to INR 8.50 per hour (Section 8.4).\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "proservices":
                response_text = (
                    "According to the contract, the daily consulting rates are:\n"
                    "- Senior IT Consultant: Standard daily rate of INR 12,000.00 (Section 3.1)\n"
                    "- Project Management advisory: Standard daily rate of INR 10,000.00 (Section 3.2).\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            else:
                response_text = "I could not locate specific pricing or rate details for the requested supplier in the contract context.\n\n[CONFIDENCE: NOT_FOUND]"

        else:
            response_text = (
                "I am sorry, but the contract context provided does not contain information to answer that specific query. Please try rephrasing or asking about pricing tiers, SLAs, or discount terms.\n\n"
                "[CONFIDENCE: NOT_FOUND]"
            )
            
        return MockResponse(response_text)

    # Fallback default mock
    return MockResponse("{}")

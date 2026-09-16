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
        mappings = []
        if "c007" in input_str_lower or "inv-sysco" in input_str_lower or ("sysco" in input_str_lower and "pcf" not in input_str_lower and "cold foods" not in input_str_lower and "c008" not in input_str_lower):
            if "202610" in input_str_lower or "i012" in input_str_lower:
                mappings = [
                    {"line_id": "L001", "applicable_rule_ids": ["R003"], "confidence": 1.0, "justification": "Refrigerated cargo matches Section 5.1 volume tier."},
                    {"line_id": "L002", "applicable_rule_ids": ["R001"], "confidence": 1.0, "justification": "Dry goods matches Section 4.2 flat rate."},
                    {"line_id": "L003", "applicable_rule_ids": ["R002"], "confidence": 1.0, "justification": "Fuel surcharge matches Section 4.3 cap."}
                ]
            elif "202611" in input_str_lower or "i013" in input_str_lower:
                mappings = [
                    {"line_id": "L001", "applicable_rule_ids": ["R003"], "confidence": 1.0, "justification": "Refrigerated cargo matches Section 5.1 volume tier."},
                    {"line_id": "L002", "applicable_rule_ids": ["R001"], "confidence": 1.0, "justification": "Dry goods matches Section 4.2 flat rate."},
                    {"line_id": "L003", "applicable_rule_ids": ["R002"], "confidence": 1.0, "justification": "Fuel surcharge matches Section 4.3 cap."}
                ]
            else:
                mappings = [
                    {"line_id": "L001", "applicable_rule_ids": ["R003"], "confidence": 1.0, "justification": "Refrigerated cargo matches Section 5.1 volume tier."},
                    {"line_id": "L002", "applicable_rule_ids": ["R001", "R006"], "confidence": 1.0, "justification": "Dry goods matches Section 4.2 flat rate and Section 8.2 prompt payment discount."},
                    {"line_id": "L003", "applicable_rule_ids": ["R002"], "confidence": 1.0, "justification": "Fuel surcharge matches Section 4.3 cap."}
                ]
            return MockResponse(json.dumps({"mappings": mappings}))
        elif "pcf" in input_str_lower or "cold foods" in input_str_lower or "inv-pcf" in input_str_lower or "c008" in input_str_lower:
            if "202611" in input_str_lower or "i015" in input_str_lower:
                mappings = [
                    {"line_id": "L001", "applicable_rule_ids": ["R004"], "confidence": 1.0, "justification": "Produce boxes match Section 4.1 flat rate."},
                    {"line_id": "L002", "applicable_rule_ids": ["R006"], "confidence": 1.0, "justification": "Fuel surcharge matches Section 6.2 monthly cap."}
                ]
            elif "202612" in input_str_lower or "i016" in input_str_lower:
                mappings = [
                    {"line_id": "L001", "applicable_rule_ids": ["R004"], "confidence": 1.0, "justification": "Produce boxes match Section 4.1 flat rate."},
                    {"line_id": "L002", "applicable_rule_ids": ["R007"], "confidence": 1.0, "justification": "Frozen Food bulk qualifies for Section 5.1 volume discount."},
                    {"line_id": "L003", "applicable_rule_ids": ["R006"], "confidence": 1.0, "justification": "Fuel surcharge matches Section 6.2 monthly cap."}
                ]
            else:
                mappings = [
                    {"line_id": "L001", "applicable_rule_ids": ["R004", "R011"], "confidence": 1.0, "justification": "Produce boxes match base rate and early payment discount."},
                    {"line_id": "L002", "applicable_rule_ids": ["R006"], "confidence": 1.0, "justification": "Fuel surcharge matches Section 6.2 monthly cap."}
                ]
            return MockResponse(json.dumps({"mappings": mappings}))
        elif "apex" in input_str_lower or "inv-apx" in input_str_lower or "c001" in input_str_lower:
            mappings = [{"line_id": "L001", "applicable_rule_ids": ["R001"], "confidence": 1.0, "justification": "Matched Apex logistics rate."}]
            return MockResponse(json.dumps({"mappings": mappings}))
        elif "techsoft" in input_str_lower or "inv-tss" in input_str_lower or "c002" in input_str_lower:
            if "202409" in input_str_lower or "i003" in input_str_lower:
                mappings = [
                    {"line_id": "L001", "applicable_rule_ids": ["R001"], "confidence": 1.0, "justification": "Developer consulting."},
                    {"line_id": "L002", "applicable_rule_ids": ["R002"], "confidence": 1.0, "justification": "QA testing."}
                ]
            else:
                mappings = [
                    {"line_id": "L001", "applicable_rule_ids": ["R001"], "confidence": 1.0, "justification": "Developer consulting."},
                    {"line_id": "L002", "applicable_rule_ids": ["R003"], "confidence": 1.0, "justification": "Project management."}
                ]
            return MockResponse(json.dumps({"mappings": mappings}))
        elif "buildright" in input_str_lower or "inv-brc" in input_str_lower or "c003" in input_str_lower:
            if "202410" in input_str_lower or "i005" in input_str_lower:
                mappings = [
                    {"line_id": "L001", "applicable_rule_ids": ["R001"], "confidence": 1.0, "justification": "Excavation."},
                    {"line_id": "L002", "applicable_rule_ids": ["R003"], "confidence": 1.0, "justification": "Cement."}
                ]
            else:
                mappings = [{"line_id": "L001", "applicable_rule_ids": [], "confidence": 1.0, "justification": "No match."}]
            return MockResponse(json.dumps({"mappings": mappings}))
        elif "medisupply" in input_str_lower or "inv-msc" in input_str_lower or "c004" in input_str_lower:
            mappings = [
                {"line_id": "L001", "applicable_rule_ids": ["R001"], "confidence": 1.0, "justification": "Gloves."},
                {"line_id": "L002", "applicable_rule_ids": ["R002"], "confidence": 1.0, "justification": "Regulatory."}
            ]
            return MockResponse(json.dumps({"mappings": mappings}))
        elif "cloudhost" in input_str_lower or "inv-chi" in input_str_lower or "c005" in input_str_lower:
            if "202410" in input_str_lower or "i009" in input_str_lower:
                mappings = [{"line_id": "L001", "applicable_rule_ids": ["R001", "R003"], "confidence": 1.0, "justification": "Hosting and commitment."}]
            else:
                mappings = [{"line_id": "L001", "applicable_rule_ids": ["R001"], "confidence": 1.0, "justification": "Hosting."}]
            return MockResponse(json.dumps({"mappings": mappings}))
        elif "proservices" in input_str_lower or "inv-psc" in input_str_lower or "c006" in input_str_lower:
            mappings = [
                {"line_id": "L001", "applicable_rule_ids": ["R001"], "confidence": 1.0, "justification": "Consultant."},
                {"line_id": "L002", "applicable_rule_ids": ["R002"], "confidence": 1.0, "justification": "Project advisory."}
            ]
            return MockResponse(json.dumps({"mappings": mappings}))

        # Dynamic fallback from candidate rules if not a known synthetic supplier
        candidate_rules = {}
        match = re.search(r"=== CANDIDATE RULES PER LINE ===[^{]*(\{.*\})", content_str, re.DOTALL)
        if match:
            try:
                candidate_rules = json.loads(match.group(1))
            except Exception:
                pass
        
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
        elif "pcf" in input_str_lower or "cold foods" in input_str_lower or "premium" in input_str_lower or "sysco" in input_str_lower:
            supplier = "pcf"

        matched_rule = "R001"
        for i in range(1, 18):
            r_id = f"R{i:03d}"
            if r_id.lower() in input_str_lower:
                matched_rule = r_id
                break
                
        descriptions_map = {
            "apex": {
                "R001": "Volume discount not applied. October quantity of 1,240 units qualifies for Tier 2 pricing ($11.50/unit) under Section 4.2. Supplier charged Tier 1 rate ($12.50/unit).",
                "R002": "Missed SLA penalty. November on-time delivery rate was 94.2%, falling below the contractually agreed 97.0% threshold. Supplier did not credit 12% of the month's invoice total.",
                "R003": "Early payment discount missed."
            },
            "techsoft": {
                "R001": "Incorrect Consulting rate charged.",
                "R004": "Incorrect Consulting rate charged.",
                "R002": "QA Testing bundle discount not applied. Total hours exceeded 20 days, but charged standard rate.",
                "R005": "QA Testing bundle discount not applied. Total hours exceeded 20 days, but charged standard rate.",
                "R003": "Project Management fee exceeds monthly contract cap of $30,000.00.",
                "R006": "Project Management fee exceeds monthly contract cap of $30,000.00."
            },
            "buildright": {
                "R001": "Excavation volume discount tier mismatch.",
                "R007": "Excavation volume discount tier mismatch.",
                "R002": "Foundation Completion milestone delay penalty of $5,000.00 per day was not credited.",
                "R008": "Foundation Completion milestone delay penalty of $5,000.00 per day was not credited.",
                "R003": "Cement Supply bag unit cap exceeded. Billed at $450.00 per bag, but capped at $400.00.",
                "R009": "Cement Supply bag unit cap exceeded. Billed at $450.00 per bag, but capped at $400.00."
            },
            "medisupply": {
                "R001": "Surgical Gloves volume tier discount not applied.",
                "R010": "Surgical Gloves volume tier discount not applied.",
                "R002": "Regulatory Surcharge exceeds maximum cap of $2,000.00.",
                "R011": "Regulatory Surcharge exceeds maximum cap of $2,000.00."
            },
            "cloudhost": {
                "R001": "VM Hosting hourly rate charged incorrectly.",
                "R012": "VM Hosting hourly rate charged incorrectly.",
                "R002": "SLA Credit of 20% missed for VM hosting. Availability was 99.5%, falling below 99.9% guarantee.",
                "R013": "SLA Credit of 20% missed for VM hosting. Availability was 99.5%, falling below 99.9% guarantee.",
                "R003": "Commitment discount of 15% missed. VM hosting hours exceeded 10,000, but discount was not credited.",
                "R014": "Commitment discount of 15% missed. VM hosting hours exceeded 10,000, but discount was not credited."
            },
            "proservices": {
                "R001": "IT Consulting rate discrepancy. December Senior IT Consultant services were billed at $13,000.00/day, exceeding the contract rate of $12,000.00/day.",
                "R015": "IT Consulting rate discrepancy. December Senior IT Consultant services were billed at $13,000.00/day, exceeding the contract rate of $12,000.00/day.",
                "R002": "Project Management advisory rate matched correctly.",
                "R016": "Project Management advisory rate matched correctly.",
                "R003": "Missed SLA penalty. Consulting Dashboard uptime fell to 96.5% in December, below the contractual 98.0% threshold. The 10% penalty credit was not applied.",
                "R017": "Missed SLA penalty. Consulting Dashboard uptime fell to 96.5% in December, below the contractual 98.0% threshold. The 10% penalty credit was not applied."
            },
            "pcf": {
                "R004": "Standard produce boxes flat rate of USD 4.50 per box correctly mapped.",
                "R005": "Standard frozen food cases billed at standard rate when volume qualified for discounted pricing.",
                "R006": "Fuel surcharge exceeds contractual ceiling cap. Billed at USD 2,500.00, exceeding monthly cap of USD 2,000.00 under Section 6.2.",
                "R007": "Frozen Food cases volume tier discount not applied. Volume exceeded 10,000 cases (11,500 cases billed), but charged standard rate USD 5.80 instead of discounted USD 5.00 under Section 5.1.",
                "R008": "Unapplied temperature SLA credit penalty. December temperature compliance was 96.5%, falling below 98.0% threshold. The 8% credit penalty was not applied under Section 7.1.",
                "R009": "Milestone delay penalty not credited. Mid-West Cold Chain Integration milestone completed on November 5, 2026, 4 days past the November 1 target date. Penalty of USD 1,500.00/day was not credited under Section 8.2.",
                "R011": "Prompt payment discount missed. Invoice was settled within 9 days of invoice date, qualifying for a 3% prompt payment discount under Section 9.2."
            }
        }
        
        clauses_map = {
            "apex": {
                "R001": "For monthly shipment volumes of 500-1,999 units, the applicable unit price shall be $11.50.",
                "R002": "Should the Supplier's on-time delivery rate fall below 97% in any calendar month, the Supplier shall issue a credit equal to 12% of that month's invoice total.",
                "R003": "A discount of 2% shall apply to any invoice settled within 10 business days of the invoice date."
            },
            "techsoft": {
                "R001": "Senior Developer Consulting services shall be billed at a flat rate of $8,000.00 per day.",
                "R004": "Senior Developer Consulting services shall be billed at a flat rate of $8,000.00 per day.",
                "R002": "If the customer licenses more than 20 days of QA Testing Services in a billing period, a discounted rate of $3,200.00 per day shall apply to all QA days billed.",
                "R005": "If the customer licenses more than 20 days of QA Testing Services in a billing period, a discounted rate of $3,200.00 per day shall apply to all QA days billed.",
                "R003": "Project Management Services shall be billed hourly at a rate of $1,500.00 per hour, subject to a maximum cap of $30,000.00 per month.",
                "R006": "Project Management Services shall be billed hourly at a rate of $1,500.00 per hour, subject to a maximum cap of $30,000.00 per month."
            },
            "buildright": {
                "R001": "For 101 to 500 cubic meters, the rate is $450.00 per cubic meter.",
                "R007": "For 101 to 500 cubic meters, the rate is $450.00 per cubic meter.",
                "R002": "If the project milestone designated 'Foundation Completion' is delayed beyond the agreed target date of October 15, 2024, the Supplier shall credit the Client a delay penalty of $5,000.00 per calendar day of delay.",
                "R008": "If the project milestone designated 'Foundation Completion' is delayed beyond the agreed target date of October 15, 2024, the Supplier shall credit the Client a delay penalty of $5,000.00 per calendar day of delay.",
                "R003": "The cost for Cement bags supplied for construction shall be billed at actual supplier cost plus a 10% markup, subject to an absolute maximum cap of $400.00 per bag. Under no circumstances shall the billed rate per bag exceed $400.00.",
                "R009": "The cost for Cement bags supplied for construction shall be billed at actual supplier cost plus a 10% markup, subject to an absolute maximum cap of $400.00 per bag. Under no circumstances shall the billed rate per bag exceed $400.00."
            },
            "medisupply": {
                "R001": "Surgical Gloves shall be priced based on order size: 1,001 to 5,000 boxes at $220.00 per box.",
                "R010": "Surgical Gloves shall be priced based on order size: 1,001 to 5,000 boxes at $220.00 per box.",
                "R002": "The total regulatory surcharge per invoice is subject to a maximum limit of $2,000.00.",
                "R011": "The total regulatory surcharge per invoice is subject to a maximum limit of $2,000.00."
            },
            "cloudhost": {
                "R001": "VM Hosting Services shall be billed at a usage-based rate of $10.00 per instance-hour.",
                "R012": "VM Hosting Services shall be billed at a usage-based rate of $10.00 per instance-hour.",
                "R002": "The Supplier guarantees a monthly VM service uptime of 99.9%. If the actual VM uptime in any calendar month falls below 99.9%, a credit equal to 20% of that month's total hosting charges shall be applied to the invoice.",
                "R013": "The Supplier guarantees a monthly VM service uptime of 99.9%. If the actual VM uptime in any calendar month falls below 99.9%, a credit equal to 20% of that month's total hosting charges shall be applied to the invoice.",
                "R003": "If the total hosting VM hours in a billing month exceed 10,000 hours, a commitment volume discount of 15% shall be applied to the total hosting charges for that month.",
                "R014": "If the total hosting VM hours in a billing month exceed 10,000 hours, a commitment volume discount of 15% shall be applied to the total hosting charges for that month."
            },
            "proservices": {
                "R001": "Senior IT Consultant services shall be billed at a standard daily rate of $12,000.00.",
                "R015": "Senior IT Consultant services shall be billed at a standard daily rate of $12,000.00.",
                "R002": "Project Management advisory services shall be billed at a standard daily rate of $10,000.00.",
                "R016": "Project Management advisory services shall be billed at a standard daily rate of $10,000.00.",
                "R003": "Should the consulting dashboard availability fall below 98.0% in any month, a penalty credit of 10% of that month's total billing shall be applied to the invoice.",
                "R017": "Should the consulting dashboard availability fall below 98.0% in any month, a penalty credit of 10% of that month's total billing shall be applied to the invoice."
            },
            "pcf": {
                "R004": "Standard Produce Boxes delivered to Sysco hubs shall be billed at a flat rate of USD 4.50 per box.",
                "R005": "Standard Frozen Food cases delivered under this Agreement shall be billed at USD 5.80 per case.",
                "R006": "Fuel surcharges applied to any monthly invoice shall not exceed USD 2,000.00. Under no circumstances shall Sysco be billed a fuel surcharge higher than USD 2,000.00.",
                "R007": "If the monthly volume of Frozen Food cases shipped to Sysco hubs exceeds 10,000 cases in any calendar month, a discounted rate of USD 5.00 per case shall apply to all Frozen Food cases billed in that month.",
                "R008": "The Supplier guarantees that the temperature compliance rate for all shipments in a calendar month shall be at least 98.0%. If the monthly temperature compliance rate falls below 98.0%, the Supplier shall issue a credit penalty equal to 8.0% of that month's total invoice amount.",
                "R009": "If the logistics integration milestone designated 'Mid-West Cold Chain Integration' is delayed beyond the target date of November 1, 2026, the Supplier shall credit the Client a delay penalty of USD 1,500.00 per calendar day of delay.",
                "R011": "A prompt payment discount of 3.0% shall apply to Standard Produce Box charges if settled within 12 days of the invoice date."
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
            elif "c007" in input_str_lower or "inv-sysco" in input_str_lower or ("sysco" in input_str_lower and "pcf" not in input_str_lower and "cold foods" not in input_str_lower and "c008" not in input_str_lower):
                if "202610" in input_str_lower or "i012" in input_str_lower or "oct" in input_str_lower:
                    matched_invoice = "INV-SYSCO-202610"
                elif "202611" in input_str_lower or "i013" in input_str_lower or "nov" in input_str_lower:
                    matched_invoice = "INV-SYSCO-202611"
                elif "202612" in input_str_lower or "i014" in input_str_lower or "dec" in input_str_lower:
                    matched_invoice = "INV-SYSCO-202612"
                else:
                    matched_invoice = "INV-SYSCO-202610"
            elif "pcf" in input_str_lower or "cold foods" in input_str_lower or "c008" in input_str_lower:
                if "202611" in input_str_lower or "nov" in input_str_lower or "i015" in input_str_lower:
                    matched_invoice = "INV-PCF-202611"
                elif "202612" in input_str_lower or "dec" in input_str_lower or "i016" in input_str_lower:
                    matched_invoice = "INV-PCF-202612"
                elif "202701" in input_str_lower or "jan" in input_str_lower or "i017" in input_str_lower:
                    matched_invoice = "INV-PCF-202701"
                else:
                    matched_invoice = "INV-PCF-202611"
                
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
            elif "c007" in input_str_lower or "ghg" in input_str_lower or ("sysco" in input_str_lower and "pcf" not in input_str_lower and "cold foods" not in input_str_lower and "c008" not in input_str_lower):
                matched_contract = "CTR-SYSCO-GHG-2026-001"
            elif "pcf" in input_str_lower or "cold foods" in input_str_lower or "c008" in input_str_lower:
                matched_contract = "CTR-SYSCO-PCF-2026-002"
                
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
                    elif "c007" in contract_file or "ghg" in contract_file:
                        matched_contract = "CTR-SYSCO-GHG-2026-001"
                    elif "c008" in contract_file or "pcf" in contract_file or "cold foods" in contract_file:
                        matched_contract = "CTR-SYSCO-PCF-2026-002"
                conn.close()
            except Exception as db_err:
                logger.warning("Failed to query database for contract", error=str(db_err))

        if not matched_contract and LAST_MOCK_CONTRACT_ID:
            matched_contract = LAST_MOCK_CONTRACT_ID
                
        if matched_contract:
            LAST_MOCK_CONTRACT_ID = matched_contract
            rules_data = MOCK_CONTRACT_RULES[matched_contract]
            section_rules = []
            
            is_preamble = "preamble" in input_str_lower or "master services agreement" in input_str_lower or "software services" in input_str_lower or "construction services" in input_str_lower or "medical equipment" in input_str_lower or "cloud infrastructure" in input_str_lower or "master food supply" in input_str_lower or "sysco" in input_str_lower
            
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
                elif "milestone" in input_str_lower or "delay" in input_str_lower or "integration" in input_str_lower:
                    section_rules = [r for r in rules_data["rules"] if r["rule_type"] == "milestone_penalty"]
            
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
        elif "c007" in input_str_lower or "ghg" in input_str_lower or ("sysco" in input_str_lower and "pcf" not in input_str_lower and "cold foods" not in input_str_lower and "c008" not in input_str_lower):
            supplier = "sysco"
        elif "pcf" in input_str_lower or "cold foods" in input_str_lower or "c008" in input_str_lower:
            supplier = "pcf"
            
        reports = {
            "sysco": {
                "executive_summary": "An audit of Sysco Food Services Solutions, LLC for October through December 2026 revealed total financial leakage of USD 9,924.00. Key discrepancies include fuel surcharges exceeding the contractual monthly cap, volume tier overbilling on refrigerated cargo, an uncredited 10.0% temperature SLA penalty for November, a milestone delay penalty on the North-East transition, and missed prompt payment discounts.",
                "recommendations": [
                    "Dispute the USD 300.00 fuel surcharge overage on INV-SYSCO-202610 and enforce the USD 1,500.00 monthly cap per Section 4.3.",
                    "Reclaim USD 3,100.00 for Refrigerated Cargo on INV-SYSCO-202611 to reflect the Tier 3 rate (USD 2.50/case) under Section 5.1.",
                    "Claim a 10.0% temperature SLA penalty credit of USD 4,140.00 on INV-SYSCO-202611 due to 97.2% compliance falling below the 99.0% threshold under Section 7.1.",
                    "Assess USD 5,000.00 in liquidated damages for the 5-day delay on the North-East Distribution Transition milestone under Section 7.3.",
                    "Request a credit of USD 324.00 for the unapplied 2.0% prompt payment discount on INV-SYSCO-202612 settled within 8 days under Section 8.2."
                ]
            },
            "apex": {
                "executive_summary": "An audit of Apex Logistics Ltd for October and November 2024 revealed total financial leakage of $4,180.00. The primary findings include a volume pricing discrepancy on line items and a missed SLA penalty credit for the month of November. Recommendations include raising a dispute for the overcharged rate and reclaiming the unapplied SLA penalty credit.",
                "recommendations": [
                    "Dispute the Tier 1 rate charged on INV-APX-202410 and request a credit of $1,240.00 to align with the Tier 2 contract rate.",
                    "Escalate the unapplied 12% SLA penalty credit for November on INV-APX-202411 to reclaim $2,940.00 due to on-time delivery rate of 94.2%.",
                    "Establish a monthly compliance check process to verify logistics SLA compliance prior to invoice approvals."
                ]
            },
            "techsoft": {
                "executive_summary": "The audit of TechSoft Solutions for September and October 2024 identified total leakage of $25,200.00. Key discrepancies include unapplied bundle discount for QA Testing Services and billings exceeding the monthly consulting project management cap. It is recommended to recover these overcharges and enforce monthly invoice caps.",
                "recommendations": [
                    "Request a credit of $19,200.00 for September QA Testing Services on INV-TSS-202409, as volume exceeded 20 days and qualifies for the discounted $3,200.00 daily rate.",
                    "Dispute the Project Management charges on INV-TSS-202410, which exceeded the monthly cap of $30,000.00 by $6,000.00.",
                    "Automate invoice validations against contractual capping rules to prevent future over-billing."
                ]
            },
            "buildright": {
                "executive_summary": "An audit of BuildRight Contractors for October and November 2024 revealed total leakage of $35,000.00. The findings include an overcharge on Cement Supply bags due to unit price capping and a missed milestone delay penalty for the Foundation Completion. Actionable recommendations are provided to claim credits and enforce capping.",
                "recommendations": [
                    "Reclaim $10,000.00 for Cement Supply on INV-BRC-202410, as the price was billed at $450.00 per bag instead of the contractual cap of $400.00.",
                    "Dispute the Foundation Completion delay on INV-BRC-202411 and claim a penalty credit of $25,000.00 (5 days of delay at $5,000.00 per day).",
                    "Implement regular milestone tracking checks prior to milestone-linked invoice clearance."
                ]
            },
            "medisupply": {
                "executive_summary": "An audit of MediSupply Corp for October and November 2024 identified total leakage of $35,000.00. Key violations include unapplied volume tier pricing for Surgical Gloves and a regulatory surcharge billing exceeding the invoice limit. We recommend requesting immediate credits.",
                "recommendations": [
                    "Dispute the unit price for Surgical Gloves on INV-MSC-202410 and request a credit of $22,000.00 to align with Tier 2 pricing ($220.00/box instead of $250.00).",
                    "Claim a credit of $13,000.00 for the Regulatory Surcharge on INV-MSC-202410, which exceeded the invoice cap of $2,000.00.",
                    "Verify regulatory surcharges on medical consumables invoices against contractual limits before making payments."
                ]
            },
            "cloudhost": {
                "executive_summary": "An audit of CloudHost India for October and November 2024 identified total billing leakage of $34,000.00. Findings show that a monthly VM hosting commitment discount was not applied, and a VM service uptime SLA penalty credit was missed. Recommendations include disputing these overcharges.",
                "recommendations": [
                    "Request a credit of $18,000.00 on INV-CHI-202410 for unapplied VM Hosting commitment discount, as VM hours exceeded the 10,000-hour threshold.",
                    "Claim a 20% SLA credit of $16,000.00 on INV-CHI-202411, as monthly VM service availability fell to 99.50% (below the 99.90% SLA threshold).",
                    "Integrate cloud monitoring dashboards with invoice validation to dynamically verify monthly uptime and commitment hours."
                ]
            },
            "proservices": {
                "executive_summary": "An audit of ProServices Consulting for December 2024 identified total leakage of $38,000.00. Discrepancies include a rate overcharge for Senior IT Consultant services and a missed SLA penalty credit due to system dashboard uptime falling below the 98.0% threshold. We recommend recovery of these overcharges.",
                "recommendations": [
                    "Dispute the Senior IT Consultant rate on INV-PSC-202412 and request a credit of $15,000.00 to align with the contractual daily rate of $12,000.00.",
                    "Claim the 10% SLA penalty credit of $23,000.00 on INV-PSC-202412 due to system dashboard uptime of 96.5% falling below the 98.0% guarantee.",
                    "Review consulting performance metrics monthly to ensure appropriate SLA penalty application before payment."
                ]
            },
            "pcf": {
                "executive_summary": "An audit of Premium Cold Foods, Inc. for November 2026 through January 2027 identified billing discrepancies under contract CTR-SYSCO-PCF-2026-002. Key findings include fuel surcharges exceeding the USD 2,000.00 ceiling, unapplied Frozen Food volume tier discounts, an uncredited 8.0% temperature SLA penalty for December 2026, liquidated damages for a 4-day milestone delay on the Mid-West Cold Chain Integration, and missed prompt payment discounts. Total recoverable leakage has been cataloged for commercial dispute recovery.",
                "recommendations": [
                    "Dispute the USD 500.00 fuel surcharge overage on INV-PCF-202611 and enforce the USD 2,000.00 monthly cap per Section 6.2.",
                    "Reclaim USD 9,200.00 for Frozen Food cases on INV-PCF-202612 to reflect the USD 5.00/case volume tier rate for shipments exceeding 10,000 cases under Section 5.1.",
                    "Claim an 8.0% temperature SLA credit penalty of USD 8,336.00 on INV-PCF-202612 due to 96.5% compliance falling below the 98.0% threshold under Section 7.1.",
                    "Assess USD 6,000.00 in liquidated damages for the 4-day delay on the Mid-West Cold Chain Integration milestone under Section 8.2.",
                    "Request a credit of USD 1,215.00 for the unapplied 3.0% prompt payment discount on INV-PCF-202701 settled within 9 days under Section 9.2."
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
        elif "pcf" in content_str_lower or "cold foods" in content_str_lower or "sysco" in content_str_lower:
            supplier = "Premium Cold Foods, Inc."
            
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
        elif "pcf" in content_str_lower or "cold foods" in content_str_lower or "sysco" in content_str_lower or "c008" in content_str_lower:
            supplier = "pcf"
            
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
                    "Under Section 5.3, if the 'Foundation Completion' milestone is delayed beyond the target date of October 15, 2024, the Supplier shall credit the Client a delay penalty of $5,000.00 per calendar day of delay.\n\n"
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
            elif supplier == "pcf":
                response_text = (
                    "Under CTR-SYSCO-PCF-2026-002, the SLA terms are:\n"
                    "- Section 7.1: Temperature compliance rate must be at least 98.0%. If monthly compliance falls below 98.0%, an 8.0% credit penalty applies to the month's total invoice amount.\n"
                    "- Section 8.2: If the 'Mid-West Cold Chain Integration' milestone is delayed beyond November 1, 2026, a liquidated damages penalty of USD 1,500.00 per calendar day of delay applies.\n\n"
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
                    "Under Section 3.2, a QA Testing Services bundle discount of 20% is applied, reducing the rate from $4,000.00/day to $3,200.00/day if more than 20 days are licensed in a billing period.\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "cloudhost":
                response_text = (
                    "Under Section 8.4, a commitment volume discount of 15% is applied, reducing the VM hosting rate from $10.00 to $8.50 per hour if total hosting hours in a billing month exceed 10,000 hours.\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "pcf":
                response_text = (
                    "Under CTR-SYSCO-PCF-2026-002, the discount terms are:\n"
                    "- Section 9.2: A prompt payment discount of 3.0% applies to Standard Produce Box charges if settled within 12 days of invoice date.\n"
                    "- Section 5.1: If monthly Frozen Food cases exceed 10,000 cases, a volume discount rate of USD 5.00 per case applies to all cases in that month.\n\n"
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
                    "- 0-499 units: $14.00 per unit\n"
                    "- 500-1,999 units: $11.50 per unit\n"
                    "- 2,000 units and above: $9.80 per unit.\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "techsoft":
                response_text = (
                    "According to the contract, the daily consulting rates are:\n"
                    "- Senior Developer Consulting: Flat rate of $8,000.00 per day (Section 3.1)\n"
                    "- QA Testing Services: Standard rate of $4,000.00 per day, which reduces to $3,200.00 per day if more than 20 days are licensed in a billing period (Section 3.2)\n"
                    "- Project Management Services: Billed at $1,500.00 per hour, capped at $30,000.00 per month (Section 3.3).\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "buildright":
                response_text = (
                    "Under the contract, Site Excavation Services (cubic meters) are priced based on the following volume tiers:\n"
                    "- 0-100 cubic meters: $500.00 per cubic meter\n"
                    "- 101-500 cubic meters: $450.00 per cubic meter\n"
                    "- Exceeding 500 cubic meters: $400.00 per cubic meter (Section 4.1).\n"
                    "Additionally, Cement Supply is billed at actual cost plus a 10% markup, capped at a maximum of $400.00 per bag (Section 7.2).\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "medisupply":
                response_text = (
                    "For Surgical Gloves (Sterile, Latex Free), the volume tier pricing is as follows:\n"
                    "- 0-1,000 boxes: $250.00 per box\n"
                    "- 1,001-5,000 boxes: $220.00 per box\n"
                    "- 5,001 boxes and above: $200.00 per box (Section 2.1).\n"
                    "There is also a regulatory surcharge of 5% of the glove order value, capped at a maximum limit of $2,000.00 per invoice (Section 6.5).\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "cloudhost":
                response_text = (
                    "VM Hosting Services are billed at a usage-based rate of $10.00 per instance-hour (Section 3.1).\n"
                    "If the total hosting VM hours in a month exceed 10,000 hours, a commitment volume discount of 15% is applied, reducing the rate to $8.50 per hour (Section 8.4).\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "proservices":
                response_text = (
                    "According to the contract, the daily consulting rates are:\n"
                    "- Senior IT Consultant: Standard daily rate of $12,000.00 (Section 3.1)\n"
                    "- Project Management advisory: Standard daily rate of $10,000.00 (Section 3.2).\n\n"
                    "[CONFIDENCE: HIGH]"
                )
            elif supplier == "pcf":
                response_text = (
                    "According to contract CTR-SYSCO-PCF-2026-002, the pricing structure is:\n"
                    "- Standard Produce Boxes: Flat rate of USD 4.50 per box (Section 4.2)\n"
                    "- Standard Frozen Food Cases: USD 5.80 per case standard; discounted to USD 5.00 per case if monthly volume exceeds 10,000 cases (Sections 4.3 & 5.1)\n"
                    "- Fuel Surcharges: Billed monthly, strictly subject to a ceiling cap of USD 2,000.00 per month (Section 6.2).\n\n"
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

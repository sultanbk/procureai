# backend/core/mock_data.py
# Contains all the hardcoded mock contract rulebooks and invoice data.

MOCK_CONTRACT_RULES = {
    # C001 - Apex Logistics
    "MSA-2024-APX-001": {
        "supplier_name": "Apex Logistics Ltd",
        "contract_id": "MSA-2024-APX-001",
        "contract_date": "2024-01-01",
        "contract_currency": "USD",
        "rules": [
            {
                "rule_id": "R001",
                "rule_type": "volume_tier",
                "description": "Standard Delivery - Domestic pricing tiers",
                "clause_reference": "Section 4.2",
                "clause_text": "For monthly shipment volumes of 0-499 units, the applicable unit price shall be $14.00. For 500-1,999 units, the unit price shall be $11.50. For 2,000 units and above, the unit price shall be $9.80.",
                "applies_to": "Standard Delivery - Domestic",
                "tiers": [
                    {"min_units": 0, "max_units": 499, "unit_price": "14.00"},
                    {"min_units": 500, "max_units": 1999, "unit_price": "11.50"},
                    {"min_units": 2000, "max_units": None, "unit_price": "9.80"}
                ],
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R002",
                "rule_type": "sla_penalty",
                "description": "Monthly credit of 12% if on-time delivery rate falls below 97%",
                "clause_reference": "Section 8.1",
                "clause_text": "Should the Supplier's on-time delivery rate fall below 97% in any calendar month, the Supplier shall issue a credit equal to 12% of that month's invoice total.",
                "applies_to": "monthly_invoice_total",
                "sla_threshold_pct": 0.97,
                "penalty_pct": 0.12,
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R003",
                "rule_type": "early_payment_discount",
                "description": "2% discount for early payment settled within 10 business days",
                "clause_reference": "Section 12.4",
                "clause_text": "A discount of 2% shall apply to any invoice settled within 10 business days of the invoice date.",
                "applies_to": "invoice_total",
                "payment_window_days": 10,
                "discount_pct": 0.02,
                "extraction_confidence": 1.0
            }
        ],
        "unextracted_sections": [],
        "extraction_notes": "All core logistics, SLA, and payment rules parsed successfully."
    },
    # C002 - TechSoft Solutions
    "MSA-2024-TSS-002": {
        "supplier_name": "TechSoft Solutions",
        "contract_id": "MSA-2024-TSS-002",
        "contract_date": "2024-02-15",
        "contract_currency": "USD",
        "rules": [
            {
                "rule_id": "R004",
                "rule_type": "flat_rate",
                "description": "Senior Developer flat daily consulting rate",
                "clause_reference": "Section 3.1",
                "clause_text": "Senior Developer Consulting services shall be billed at a flat rate of $8,000.00 per day.",
                "applies_to": "Senior Developer Consulting",
                "flat_unit_price": "8000.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R005",
                "rule_type": "bundle_discount",
                "description": "QA Testing Services volume discount rate",
                "clause_reference": "Section 3.2",
                "clause_text": "QA Testing Services shall be billed at a standard rate of $4,000.00 per day. If the customer licenses more than 20 days of QA Testing Services in a billing period, a discounted rate of $3,200.00 per day shall apply to all QA days billed.",
                "applies_to": "QA Testing Services",
                "bundle_threshold": 20,
                "bundle_price": "3200.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R006",
                "rule_type": "cap_rate",
                "description": "Project Management hourly rate capped monthly",
                "clause_reference": "Section 3.3",
                "clause_text": "Project Management Services shall be billed hourly at a rate of $1,500.00 per hour, subject to a maximum cap of $30,000.00 per month.",
                "applies_to": "Project Management Services",
                "cap_amount": "30000.00",
                "cap_applies_to": "Project Management Services",
                "extraction_confidence": 1.0
            }
        ],
        "unextracted_sections": [],
        "extraction_notes": "IT consulting and Project Management caps extracted successfully."
    },
    # C003 - BuildRight Contractors
    "MSA-2024-BRC-003": {
        "supplier_name": "BuildRight Contractors",
        "contract_id": "MSA-2024-BRC-003",
        "contract_date": "2024-03-10",
        "contract_currency": "USD",
        "rules": [
            {
                "rule_id": "R007",
                "rule_type": "volume_tier",
                "description": "Site Excavation unit volume tiers",
                "clause_reference": "Section 4.1",
                "clause_text": "For cumulative volume of 0 to 100 cubic meters in a billing period, the rate is $500.00 per cubic meter. For 101 to 500 cubic meters, the rate is $450.00 per cubic meter. For volumes exceeding 500 cubic meters, the rate is $400.00 per cubic meter.",
                "applies_to": "Site Excavation Services (cubic meters)",
                "tiers": [
                    {"min_units": 0, "max_units": 100, "unit_price": "500.00"},
                    {"min_units": 101, "max_units": 500, "unit_price": "450.00"},
                    {"min_units": 501, "max_units": None, "unit_price": "400.00"}
                ],
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R008",
                "rule_type": "flat_rate",
                "description": "Foundation Completion milestone delay penalty",
                "clause_reference": "Section 5.3",
                "clause_text": "If the project milestone designated 'Foundation Completion' is delayed beyond the agreed target date of October 15, 2024, the Supplier shall credit the Client a delay penalty of $5,000.00 per calendar day of delay.",
                "applies_to": "Foundation Completion delay",
                "flat_unit_price": "5000.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R009",
                "rule_type": "cap_rate",
                "description": "Cement Supply per bag cost ceiling",
                "clause_reference": "Section 7.2",
                "clause_text": "The cost for Cement bags supplied for construction shall be billed at actual supplier cost plus a 10% markup, subject to an absolute maximum cap of $400.00 per bag. Under no circumstances shall the billed rate per bag exceed $400.00.",
                "applies_to": "Cement Supply (Bags)",
                "cap_amount": "400.00",
                "cap_applies_to": "Cement Supply (Bags)",
                "extraction_confidence": 1.0
            }
        ],
        "unextracted_sections": [],
        "extraction_notes": "Excavation, milestone delay and cement capping rates successfully extracted."
    },
    # C004 - MediSupply Corp
    "MSA-2024-MSC-004": {
        "supplier_name": "MediSupply Corp",
        "contract_id": "MSA-2024-MSC-004",
        "contract_date": "2024-04-01",
        "contract_currency": "USD",
        "rules": [
            {
                "rule_id": "R010",
                "rule_type": "volume_tier",
                "description": "Surgical Gloves volume tier rates",
                "clause_reference": "Section 2.1",
                "clause_text": "Surgical Gloves shall be priced based on order size: 0 to 1,000 boxes at $250.00 per box. 1,001 to 5,000 boxes at $220.00 per box. 5,001 boxes and above at $200.00 per box.",
                "applies_to": "Surgical Gloves (Sterile, Latex Free)",
                "tiers": [
                    {"min_units": 0, "max_units": 1000, "unit_price": "250.00"},
                    {"min_units": 1001, "max_units": 5000, "unit_price": "220.00"},
                    {"min_units": 5001, "max_units": None, "unit_price": "200.00"}
                ],
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R011",
                "rule_type": "cap_rate",
                "description": "Regulatory Surcharge maximum billing limit",
                "clause_reference": "Section 6.5",
                "clause_text": "A regulatory surcharge of 5.0% of the glove order value may be added to each invoice. The total regulatory surcharge per invoice is subject to a maximum limit of $2,000.00.",
                "applies_to": "Regulatory Surcharge (5% of order)",
                "cap_amount": "2000.00",
                "cap_applies_to": "Regulatory Surcharge (5% of order)",
                "extraction_confidence": 1.0
            }
        ],
        "unextracted_sections": [],
        "extraction_notes": "Surgical consumables volume pricing and regulatory caps extracted."
    },
    # C005 - CloudHost India
    "MSA-2024-CHI-005": {
        "supplier_name": "CloudHost India",
        "contract_id": "MSA-2024-CHI-005",
        "contract_date": "2024-05-01",
        "contract_currency": "USD",
        "rules": [
            {
                "rule_id": "R012",
                "rule_type": "flat_rate",
                "description": "VM Hosting standard usage hourly rate",
                "clause_reference": "Section 3.1",
                "clause_text": "VM Hosting Services shall be billed at a usage-based rate of $10.00 per instance-hour.",
                "applies_to": "VM Hosting Services (Standard Linux Instances)",
                "flat_unit_price": "10.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R013",
                "rule_type": "sla_penalty",
                "description": "SLA Credit of 20% if monthly VM uptime falls below 99.9%",
                "clause_reference": "Section 5.2",
                "clause_text": "The Supplier guarantees a monthly VM service uptime of 99.9%. If the actual VM uptime in any calendar month falls below 99.9%, a credit equal to 20% of that month's total hosting charges shall be applied to the invoice.",
                "applies_to": "monthly_invoice_total",
                "sla_threshold_pct": 0.999,
                "penalty_pct": 0.20,
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R014",
                "rule_type": "bundle_discount",
                "description": "Commitment volume discount of 15% if VM hours exceed 10,000",
                "clause_reference": "Section 8.4",
                "clause_text": "If the total hosting VM hours in a billing month exceed 10,000 hours, a commitment volume discount of 15% shall be applied to the total hosting charges for that month.",
                "applies_to": "VM Hosting Services (Standard Linux Instances)",
                "bundle_threshold": 10000,
                "bundle_price": "8.50",
                "extraction_confidence": 1.0
            }
        ],
        "unextracted_sections": [],
        "extraction_notes": "Cloud infrastructure standard rates, SLA availability tiers, and commitment discounts extracted."
    },
    # C006 - ProServices Consulting
    "MSA-2024-PSC-006": {
        "supplier_name": "ProServices Consulting",
        "contract_id": "MSA-2024-PSC-006",
        "contract_date": "2024-06-01",
        "contract_currency": "USD",
        "rules": [
            {
                "rule_id": "R015",
                "rule_type": "flat_rate",
                "description": "Senior IT Consultant standard daily rate",
                "clause_reference": "Section 3.1",
                "clause_text": "Senior IT Consultant services shall be billed at a standard daily rate of $12,000.00.",
                "applies_to": "Senior IT Consultant",
                "flat_unit_price": "12000.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R016",
                "rule_type": "flat_rate",
                "description": "Project Management advisory standard daily rate",
                "clause_reference": "Section 3.2",
                "clause_text": "Project Management advisory services shall be billed at a standard daily rate of $10,000.00.",
                "applies_to": "Project Management advisory",
                "flat_unit_price": "10000.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R017",
                "rule_type": "sla_penalty",
                "description": "10% penalty credit if Consulting Dashboard availability falls below 98.0%",
                "clause_reference": "Section 6.2",
                "clause_text": "Should the consulting dashboard availability fall below 98.0% in any month, a penalty credit of 10% of that month's total billing shall be applied to the invoice.",
                "applies_to": "monthly_invoice_total",
                "sla_threshold_pct": 0.98,
                "penalty_pct": 0.10,
                "extraction_confidence": 1.0
            }
        ],
        "unextracted_sections": [],
        "extraction_notes": "IT Consulting daily rates and dashboard uptime SLAs extracted successfully."
    },
    # C007 - Sysco Food Services Solutions, LLC
    "CTR-SYSCO-GHG-2026-001": {
        "supplier_name": "Sysco Food Services Solutions, LLC",
        "contract_id": "CTR-SYSCO-GHG-2026-001",
        "contract_date": "2026-01-01",
        "contract_currency": "USD",
        "rules": [
            {
                "rule_id": "R001",
                "rule_type": "flat_rate",
                "description": "Standard dry goods freight delivery flat rate of USD 1.80 per case",
                "clause_reference": "Section 4.2",
                "clause_text": "Standard dry goods freight delivery shall be billed at a flat rate of USD 1.80 per case.",
                "applies_to": "Standard Dry Goods Freight (Case Distribution)",
                "flat_unit_price": "1.80",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R002",
                "rule_type": "cap_rate",
                "description": "Fuel surcharges monthly ceiling cap of USD 1,500.00",
                "clause_reference": "Section 4.3",
                "clause_text": "Fuel surcharges applied to any single monthly billing cycle shall not exceed USD 1,500.00. Under no circumstances shall the client be billed a fuel surcharge higher than USD 1,500.00.",
                "applies_to": "Monthly Fuel Surcharge",
                "cap_amount": "1500.00",
                "cap_applies_to": "Monthly Fuel Surcharge",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R003",
                "rule_type": "volume_tier",
                "description": "Refrigerated Cargo monthly volume discount tiers",
                "clause_reference": "Section 5.1",
                "clause_text": "For monthly delivery volumes of Refrigerated Cargo: 0-999 cases, the unit rate is USD 3.50 per case. For 1,000-4,999 cases, the unit rate is USD 3.00 per case. For 5,000 cases and above, the unit rate is USD 2.50 per case.",
                "applies_to": "Refrigerated Cargo Delivery (Express Cold Chain)",
                "tiers": [
                    {"min_units": 0, "max_units": 999, "unit_price": "3.50"},
                    {"min_units": 1000, "max_units": 4999, "unit_price": "3.00"},
                    {"min_units": 5000, "max_units": None, "unit_price": "2.50"}
                ],
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R004",
                "rule_type": "sla_penalty",
                "description": "10% credit penalty if monthly temperature compliance rate falls below 99.0%",
                "clause_reference": "Section 7.1",
                "clause_text": "Should the temperature-controlled delivery compliance rate fall below 99.0% in any calendar month, the Supplier shall issue a credit equal to 10.0% of that month's total logistics charges.",
                "applies_to": "monthly_invoice_total",
                "sla_threshold_pct": 0.99,
                "penalty_pct": 0.10,
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R005",
                "rule_type": "milestone_penalty",
                "description": "North-East Distribution Transition milestone delay penalty of USD 1,000.00 per calendar day past October 15, 2026",
                "clause_reference": "Section 7.3",
                "clause_text": "If the logistics transition milestone designated 'North-East Distribution Transition' is delayed beyond the agreed target date of October 15, 2026, the Supplier shall credit the Client a delay penalty of USD 1,000.00 per calendar day of delay.",
                "applies_to": "North-East Distribution Transition milestone delay",
                "flat_unit_price": "1000.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R006",
                "rule_type": "early_payment_discount",
                "description": "2% prompt payment discount on Standard Dry Goods Freight if settled within 10 business days",
                "clause_reference": "Section 8.2",
                "clause_text": "A prompt payment discount of 2.0% shall apply to Standard Dry Goods Freight charges settled within 10 business days of the invoice date.",
                "applies_to": "Standard Dry Goods Freight (Case Distribution)",
                "payment_window_days": 10,
                "discount_pct": 0.02,
                "extraction_confidence": 1.0
            }
        ],
        "unextracted_sections": [],
        "extraction_notes": "Sysco food distribution standard freight rates, fuel caps, volume tiers, cold chain SLAs, and milestone penalties extracted successfully."
    },
    # C010 - TransNational Freight Corp
    "CTR-EDGAR-TNF-2024": {
        "supplier_name": "TransNational Freight Corp",
        "contract_id": "CTR-EDGAR-TNF-2024",
        "contract_date": "2024-01-01",
        "contract_currency": "USD",
        "rules": [
            {
                "rule_id": "R001",
                "rule_type": "volume_tier",
                "description": "Standard Temperature-Controlled Pallet Transport tiers",
                "clause_reference": "Section 1.1",
                "clause_text": "Refrigerated standard freight (2°C - 8°C) shall be billed based on monthly cumulative pallet volume: 0 to 499 pallets at USD 65.00, 500 to 1,499 pallets at USD 52.00, 1,500 pallets or more at USD 42.00 per pallet.",
                "applies_to": "Standard Temperature-Controlled Pallet Transport",
                "tiers": [
                    {"min_units": 0, "max_units": 499, "unit_price": "65.00"},
                    {"min_units": 500, "max_units": 1499, "unit_price": "52.00"},
                    {"min_units": 1500, "max_units": None, "unit_price": "42.00"}
                ],
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R002",
                "rule_type": "flat_rate",
                "description": "Dedicated point-to-point interstate linehaul trips flat rate",
                "clause_reference": "Section 1.2",
                "clause_text": "Dedicated point-to-point interstate linehaul trips shall be billed at a flat rate of USD 1,450.00 per trip.",
                "applies_to": "Dedicated Interstate Linehaul",
                "flat_unit_price": "1450.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R003",
                "rule_type": "cap_rate",
                "description": "Fuel surcharge ceiling cap of USD 350.00",
                "clause_reference": "Section 2.1",
                "clause_text": "Fuel surcharges may be assessed based on regional diesel indices but shall be strictly capped at a maximum rate of USD 350.00 per shipment run.",
                "applies_to": "Fuel Surcharge Assessment",
                "cap_amount": "350.00",
                "cap_applies_to": "Fuel Surcharge Assessment",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R004",
                "rule_type": "sla_penalty",
                "description": "Carrier On-Time Delivery Rate 8% penalty credit if below 96.0%",
                "clause_reference": "Section 3.1",
                "clause_text": "In the event On-Time Delivery Rate falls below 96.0% in any calendar month, Carrier shall apply a penalty credit of 8% against that month's invoice total.",
                "applies_to": "monthly_invoice_total",
                "sla_threshold_pct": 0.96,
                "penalty_pct": 0.08,
                "extraction_confidence": 1.0
            }
        ],
        "unextracted_sections": [],
        "extraction_notes": "TransNational freight tariffs, linehaul flat rates, fuel caps, and on-time SLA rules extracted successfully."
    },
    # C011 - Apex Facilities Services LLC
    "CTR-EDGAR-AFS-2024": {
        "supplier_name": "Apex Facilities Services LLC",
        "contract_id": "CTR-EDGAR-AFS-2024",
        "contract_date": "2024-01-01",
        "contract_currency": "USD",
        "rules": [
            {
                "rule_id": "R001",
                "rule_type": "flat_rate",
                "description": "Monthly Scheduled Preventive Maintenance flat fee",
                "clause_reference": "Section 1.1",
                "clause_text": "Contractor shall perform comprehensive preventive maintenance across all facility HVAC, electrical, and plumbing systems for a flat fee of USD 12,500.00 per month.",
                "applies_to": "Monthly Preventive Maintenance",
                "flat_unit_price": "12500.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R002",
                "rule_type": "flat_rate",
                "description": "Certified technician standard hourly rate of USD 85.00",
                "clause_reference": "Section 1.2",
                "clause_text": "Standard certified technician hourly rate for corrective repair is fixed at USD 85.00 per hour.",
                "applies_to": "Certified Technician Standard Labor",
                "flat_unit_price": "85.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R003",
                "rule_type": "flat_rate",
                "description": "Emergency and after-hours overtime hourly rate of USD 120.00",
                "clause_reference": "Section 1.2",
                "clause_text": "Emergency and after-hours technician overtime rate is fixed at USD 120.00 per hour.",
                "applies_to": "Emergency Overtime Repair Labor",
                "flat_unit_price": "120.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R004",
                "rule_type": "milestone_penalty",
                "description": "Critical milestone completion delay penalty of USD 400.00 per day",
                "clause_reference": "Section 2.1",
                "clause_text": "For each calendar day of unapproved completion delay beyond the agreed milestone completion date, Contractor shall credit Client USD 400.00 per day as liquidated damages.",
                "applies_to": "Milestone completion delay penalty",
                "flat_unit_price": "400.00",
                "extraction_confidence": 1.0
            }
        ],
        "unextracted_sections": [],
        "extraction_notes": "Facility maintenance baseline PM rates, technician repair rates, and milestone delay penalties parsed successfully."
    },
    # C008 - Premium Cold Foods, Inc. (Sysco)
    "CTR-SYSCO-PCF-2026-002": {
        "supplier_name": "Premium Cold Foods, Inc.",
        "contract_id": "CTR-SYSCO-PCF-2026-002",
        "contract_date": "2026-06-01",
        "contract_currency": "USD",
        "rules": [
            {
                "rule_id": "R004",
                "rule_type": "flat_rate",
                "description": "Standard Produce Boxes delivered to Sysco regional distribution hubs flat rate",
                "clause_reference": "Section 4.2",
                "clause_text": "Standard Produce Boxes delivered to Sysco hubs shall be billed at a flat rate of USD 4.50 per box.",
                "applies_to": "Standard Produce Boxes",
                "flat_unit_price": "4.50",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R005",
                "rule_type": "flat_rate",
                "description": "Standard Frozen Food cases delivered under agreement flat rate",
                "clause_reference": "Section 4.3",
                "clause_text": "Standard Frozen Food cases delivered under this Agreement shall be billed at USD 5.80 per case.",
                "applies_to": "Standard Frozen Food cases",
                "flat_unit_price": "5.80",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R006",
                "rule_type": "cap_rate",
                "description": "Fuel surcharges monthly ceiling cap of USD 2,000.00",
                "clause_reference": "Section 6.2",
                "clause_text": "Fuel surcharges applied to any monthly invoice shall not exceed USD 2,000.00. Under no circumstances shall Sysco be billed a fuel surcharge higher than USD 2,000.00.",
                "applies_to": "Standard Fuel Surcharge",
                "cap_amount": "2000.00",
                "cap_applies_to": "Standard Fuel Surcharge",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R007",
                "rule_type": "volume_tier",
                "description": "Frozen Food cases monthly volume discount of USD 5.00 per case for volumes exceeding 10,000 cases",
                "clause_reference": "Section 5.1",
                "clause_text": "If the monthly volume of Frozen Food cases shipped to Sysco hubs exceeds 10,000 cases in any calendar month, a discounted rate of USD 5.00 per case shall apply to all Frozen Food cases billed in that month.",
                "applies_to": "Standard Frozen Food cases",
                "tiers": [
                    {"min_units": 0, "max_units": 10000, "unit_price": "5.80"},
                    {"min_units": 10001, "max_units": None, "unit_price": "5.00"}
                ],
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R008",
                "rule_type": "sla_penalty",
                "description": "8% credit penalty if monthly temperature compliance rate falls below 98.0%",
                "clause_reference": "Section 7.1",
                "clause_text": "The Supplier guarantees that the temperature compliance rate for all shipments in a calendar month shall be at least 98.0%. If the monthly temperature compliance rate falls below 98.0%, the Supplier shall issue a credit penalty equal to 8.0% of that month's total invoice amount.",
                "applies_to": "monthly_invoice_total",
                "sla_threshold_pct": 0.98,
                "penalty_pct": 0.08,
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R009",
                "rule_type": "milestone_penalty",
                "description": "Mid-West Cold Chain Integration milestone delay penalty of USD 1,500.00 per calendar day past November 1, 2026",
                "clause_reference": "Section 8.2",
                "clause_text": "If the logistics integration milestone designated 'Mid-West Cold Chain Integration' is delayed beyond the target date of November 1, 2026, the Supplier shall credit the Client a delay penalty of USD 1,500.00 per calendar day of delay.",
                "applies_to": "Mid-West Cold Chain Integration milestone delay",
                "flat_unit_price": "1500.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R011",
                "rule_type": "early_payment_discount",
                "description": "3% prompt payment discount on Standard Produce Boxes if settled within 12 days",
                "clause_reference": "Section 9.2",
                "clause_text": "A prompt payment discount of 3.0% shall apply to Standard Produce Box charges if settled within 12 days of the invoice date.",
                "applies_to": "Standard Produce Boxes",
                "payment_window_days": 12,
                "discount_pct": 0.03,
                "extraction_confidence": 1.0
            }
        ],
        "unextracted_sections": [],
        "extraction_notes": "Produce rates, frozen volume rebates, fuel caps, temperature SLAs, and milestone liquidated damages parsed successfully."
    }
}

# Aliases for compatibility
MOCK_CONTRACT_RULES["CTR-SYSCO-APX-2024-001"] = MOCK_CONTRACT_RULES["MSA-2024-APX-001"]
MOCK_CONTRACT_RULES["CTR-SYSCO-TSS-2024-002"] = MOCK_CONTRACT_RULES["MSA-2024-TSS-002"]
MOCK_CONTRACT_RULES["CTR-SYSCO-BRC-2024-003"] = MOCK_CONTRACT_RULES["MSA-2024-BRC-003"]
MOCK_CONTRACT_RULES["CTR-SYSCO-MSC-2024-004"] = MOCK_CONTRACT_RULES["MSA-2024-MSC-004"]
MOCK_CONTRACT_RULES["CTR-SYSCO-CHI-2024-005"] = MOCK_CONTRACT_RULES["MSA-2024-CHI-005"]
MOCK_CONTRACT_RULES["CTR-SYSCO-PSC-2024-006"] = MOCK_CONTRACT_RULES["MSA-2024-PSC-006"]

MOCK_INVOICE_DATA = {
    # C001: Apex Logistics Ltd
    "INV-APX-202410": {
        "invoice_id": "INV-APX-202410",
        "invoice_date": "2024-11-15",
        "billing_period": "October 2024",
        "supplier_name": "Apex Logistics Ltd",
        "invoice_total": "15500.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Standard Delivery - Domestic (Express Parcel Services)",
                "mapped_contract_item": "Standard Delivery - Domestic",
                "mapping_confidence": 0.95,
                "quantity": "1240",
                "unit_price_charged": "12.50",
                "line_total_charged": "15500.00",
                "billing_period": "October 2024",
                "sla_actual_pct": None,
                "notes": "Monthly SLA performance: 98.5%"
            }
        ]
    },
    "INV-APX-202411": {
        "invoice_id": "INV-APX-202411",
        "invoice_date": "2024-12-15",
        "billing_period": "November 2024",
        "supplier_name": "Apex Logistics Ltd",
        "invoice_total": "24500.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Standard Delivery - Domestic (Express Parcel Services)",
                "mapped_contract_item": "Standard Delivery - Domestic",
                "mapping_confidence": 0.95,
                "quantity": "2500",
                "unit_price_charged": "9.80",
                "line_total_charged": "24500.00",
                "billing_period": "November 2024",
                "sla_actual_pct": 0.942,
                "notes": "Monthly SLA performance: 94.2%"
            }
        ]
    },
    # C002: TechSoft Solutions
    "INV-TSS-202409": {
        "invoice_id": "INV-TSS-202409",
        "invoice_date": "2024-10-01",
        "billing_period": "September 2024",
        "supplier_name": "TechSoft Solutions",
        "invoice_total": "256000.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Senior Developer Consulting",
                "mapped_contract_item": "Senior Developer Consulting",
                "mapping_confidence": 1.0,
                "quantity": "20",
                "unit_price_charged": "8000.00",
                "line_total_charged": "160000.00",
                "billing_period": "September 2024",
                "notes": ""
            },
            {
                "line_id": "L002",
                "raw_description": "QA Testing Services",
                "mapped_contract_item": "QA Testing Services",
                "mapping_confidence": 1.0,
                "quantity": "24",
                "unit_price_charged": "4000.00",
                "line_total_charged": "96000.00",
                "billing_period": "September 2024",
                "notes": ""
            }
        ]
    },
    "INV-TSS-202410": {
        "invoice_id": "INV-TSS-202410",
        "invoice_date": "2024-11-01",
        "billing_period": "October 2024",
        "supplier_name": "TechSoft Solutions",
        "invoice_total": "116000.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Senior Developer Consulting",
                "mapped_contract_item": "Senior Developer Consulting",
                "mapping_confidence": 1.0,
                "quantity": "10",
                "unit_price_charged": "8000.00",
                "line_total_charged": "80000.00",
                "billing_period": "October 2024",
                "notes": ""
            },
            {
                "line_id": "L002",
                "raw_description": "Project Management Services",
                "mapped_contract_item": "Project Management Services",
                "mapping_confidence": 1.0,
                "quantity": "24",
                "unit_price_charged": "1500.00",
                "line_total_charged": "36000.00",
                "billing_period": "October 2024",
                "notes": "PM Hours: 24"
            }
        ]
    },
    # C003: BuildRight Contractors
    "INV-BRC-202410": {
        "invoice_id": "INV-BRC-202410",
        "invoice_date": "2024-11-05",
        "billing_period": "October 2024",
        "supplier_name": "BuildRight Contractors",
        "invoice_total": "144000.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Site Excavation Services (cubic meters)",
                "mapped_contract_item": "Site Excavation Services (cubic meters)",
                "mapping_confidence": 1.0,
                "quantity": "120",
                "unit_price_charged": "450.00",
                "line_total_charged": "54000.00",
                "billing_period": "October 2024",
                "notes": "Excavation volume: 120m3"
            },
            {
                "line_id": "L002",
                "raw_description": "Cement Supply (Bags)",
                "mapped_contract_item": "Cement Supply (Bags)",
                "mapping_confidence": 1.0,
                "quantity": "200",
                "unit_price_charged": "450.00",
                "line_total_charged": "90000.00",
                "billing_period": "October 2024",
                "notes": "Cement bags: 200 bags"
            }
        ]
    },
    "INV-BRC-202411": {
        "invoice_id": "INV-BRC-202411",
        "invoice_date": "2024-12-05",
        "billing_period": "November 2024",
        "supplier_name": "BuildRight Contractors",
        "invoice_total": "40000.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Site Excavation Services (cubic meters)",
                "mapped_contract_item": "Site Excavation Services (cubic meters)",
                "mapping_confidence": 1.0,
                "quantity": "80",
                "unit_price_charged": "500.00",
                "line_total_charged": "40000.00",
                "billing_period": "November 2024",
                "notes": "Foundation Completion milestone delay: 5 days. Completion date: October 20, 2024."
            }
        ]
    },
    # C004: MediSupply Corp
    "INV-MSC-202410": {
        "invoice_id": "INV-MSC-202410",
        "invoice_date": "2024-11-10",
        "billing_period": "October 2024",
        "supplier_name": "MediSupply Corp",
        "invoice_total": "315000.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Surgical Gloves (Sterile, Latex Free)",
                "mapped_contract_item": "Surgical Gloves (Sterile, Latex Free)",
                "mapping_confidence": 1.0,
                "quantity": "1200",
                "unit_price_charged": "250.00",
                "line_total_charged": "300000.00",
                "billing_period": "October 2024",
                "notes": ""
            },
            {
                "line_id": "L002",
                "raw_description": "Regulatory Surcharge (5% of order)",
                "mapped_contract_item": "Regulatory Surcharge (5% of order)",
                "mapping_confidence": 1.0,
                "quantity": "1",
                "unit_price_charged": "15000.00",
                "line_total_charged": "15000.00",
                "billing_period": "October 2024",
                "notes": ""
            }
        ]
    },
    "INV-MSC-202411": {
        "invoice_id": "INV-MSC-202411",
        "invoice_date": "2024-12-10",
        "billing_period": "November 2024",
        "supplier_name": "MediSupply Corp",
        "invoice_total": "210000.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Surgical Gloves (Sterile, Latex Free)",
                "mapped_contract_item": "Surgical Gloves (Sterile, Latex Free)",
                "mapping_confidence": 1.0,
                "quantity": "800",
                "unit_price_charged": "250.00",
                "line_total_charged": "200000.00",
                "billing_period": "November 2024",
                "notes": ""
            },
            {
                "line_id": "L002",
                "raw_description": "Regulatory Surcharge (5% of order)",
                "mapped_contract_item": "Regulatory Surcharge (5% of order)",
                "mapping_confidence": 1.0,
                "quantity": "1",
                "unit_price_charged": "10000.00",
                "line_total_charged": "10000.00",
                "billing_period": "November 2024",
                "notes": ""
            }
        ]
    },
    # C005: CloudHost India
    "INV-CHI-202410": {
        "invoice_id": "INV-CHI-202410",
        "invoice_date": "2024-11-08",
        "billing_period": "October 2024",
        "supplier_name": "CloudHost India",
        "invoice_total": "120000.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "VM Hosting Services (Standard Linux Instances)",
                "mapped_contract_item": "VM Hosting Services (Standard Linux Instances)",
                "mapping_confidence": 1.0,
                "quantity": "12000",
                "unit_price_charged": "10.00",
                "line_total_charged": "120000.00",
                "billing_period": "October 2024",
                "sla_actual_pct": 0.9995,
                "notes": "Actual VM service availability was 99.95%. VM Hours: 12,000"
            }
        ]
    },
    "INV-CHI-202411": {
        "invoice_id": "INV-CHI-202411",
        "invoice_date": "2024-12-08",
        "billing_period": "November 2024",
        "supplier_name": "CloudHost India",
        "invoice_total": "80000.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "VM Hosting Services (Standard Linux Instances)",
                "mapped_contract_item": "VM Hosting Services (Standard Linux Instances)",
                "mapping_confidence": 1.0,
                "quantity": "8000",
                "unit_price_charged": "10.00",
                "line_total_charged": "80000.00",
                "billing_period": "November 2024",
                "sla_actual_pct": 0.995,
                "notes": "Actual VM service availability was 99.5%. VM Hours: 8,000"
            }
        ]
    },
    # C006: ProServices Consulting
    "INV-PSC-202412": {
        "invoice_id": "INV-PSC-202412",
        "invoice_date": "2024-12-20",
        "billing_period": "December 2024",
        "supplier_name": "ProServices Consulting",
        "invoice_total": "245000.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Senior IT Consultant",
                "mapped_contract_item": "Senior IT Consultant",
                "mapping_confidence": 1.0,
                "quantity": "15",
                "unit_price_charged": "13000.00",
                "line_total_charged": "195000.00",
                "billing_period": "December 2024",
                "sla_actual_pct": 0.965,
                "notes": "Consulting Dashboard Uptime: 96.5%"
            },
            {
                "line_id": "L002",
                "raw_description": "Project Management advisory",
                "mapped_contract_item": "Project Management advisory",
                "mapping_confidence": 1.0,
                "quantity": "5",
                "unit_price_charged": "10000.00",
                "line_total_charged": "50000.00",
                "billing_period": "December 2024",
                "sla_actual_pct": 0.965,
                "notes": "Consulting Dashboard Uptime: 96.5%"
            }
        ]
    },
    # C008: Premium Cold Foods, Inc. (Sysco Corporation)
    "INV-PCF-202611": {
        "invoice_id": "INV-PCF-202611",
        "invoice_date": "2026-12-10",
        "billing_period": "November 2026",
        "supplier_name": "Premium Cold Foods, Inc.",
        "invoice_total": "56500.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Standard Produce Boxes (Organic Harvest)",
                "mapped_contract_item": "Standard Produce Boxes",
                "mapping_confidence": 0.98,
                "quantity": "12000",
                "unit_price_charged": "4.50",
                "line_total_charged": "54000.00",
                "billing_period": "November 2026",
                "notes": "Monthly SLA Metric: Temperature-Controlled compliance rate for November 2026 was 99.1%. Paid in 15 days of invoice date."
            },
            {
                "line_id": "L002",
                "raw_description": "Standard Fuel Surcharge",
                "mapped_contract_item": "Standard Fuel Surcharge",
                "mapping_confidence": 0.95,
                "quantity": "1",
                "unit_price_charged": "2500.00",
                "line_total_charged": "2500.00",
                "billing_period": "November 2026",
                "notes": "Monthly fuel surcharge. Cap is USD 2,000.00."
            }
        ]
    },
    "INV-PCF-202612": {
        "invoice_id": "INV-PCF-202612",
        "invoice_date": "2027-01-10",
        "billing_period": "December 2026",
        "supplier_name": "Premium Cold Foods, Inc.",
        "invoice_total": "104200.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Standard Produce Boxes (Organic Harvest)",
                "mapped_contract_item": "Standard Produce Boxes",
                "mapping_confidence": 0.98,
                "quantity": "8000",
                "unit_price_charged": "4.50",
                "line_total_charged": "36000.00",
                "billing_period": "December 2026",
                "notes": ""
            },
            {
                "line_id": "L002",
                "raw_description": "Standard Frozen Food cases (Cold Storage Bulk)",
                "mapped_contract_item": "Standard Frozen Food cases",
                "mapping_confidence": 0.98,
                "quantity": "11500",
                "unit_price_charged": "5.80",
                "line_total_charged": "66700.00",
                "billing_period": "December 2026",
                "notes": "Shipped volume 11,500 cases qualifies for USD 5.00 volume rate."
            },
            {
                "line_id": "L003",
                "raw_description": "Standard Fuel Surcharge",
                "mapped_contract_item": "Standard Fuel Surcharge",
                "mapping_confidence": 0.95,
                "quantity": "1",
                "unit_price_charged": "1500.00",
                "line_total_charged": "1500.00",
                "billing_period": "December 2026",
                "sla_actual_pct": 0.965,
                "notes": "Monthly SLA Metric: Temperature-Controlled compliance rate for December 2026 was 96.5%. Mid-West Cold Chain Integration milestone was completed on November 5, 2026. Paid in 20 days."
            }
        ]
    },
    "INV-PCF-202701": {
        "invoice_id": "INV-PCF-202701",
        "invoice_date": "2027-02-10",
        "billing_period": "January 2027",
        "supplier_name": "Premium Cold Foods, Inc.",
        "invoice_total": "41700.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Standard Produce Boxes (Organic Harvest)",
                "mapped_contract_item": "Standard Produce Boxes",
                "mapping_confidence": 0.98,
                "quantity": "9000",
                "unit_price_charged": "4.50",
                "line_total_charged": "40500.00",
                "billing_period": "January 2027",
                "notes": "Monthly SLA Metric: Temperature-Controlled compliance rate for January 2027 was 99.4%. Paid in 9 days. Payment within 9 days of invoice date."
            },
            {
                "line_id": "L002",
                "raw_description": "Standard Fuel Surcharge",
                "mapped_contract_item": "Standard Fuel Surcharge",
                "mapping_confidence": 0.95,
                "quantity": "1",
                "unit_price_charged": "1200.00",
                "line_total_charged": "1200.00",
                "billing_period": "January 2027",
                "notes": ""
            }
        ]
    },
    # C007 - Sysco Food Services Solutions, LLC
    "INV-SYSCO-202610": {
        "invoice_id": "INV-SYSCO-202610",
        "invoice_date": "2026-11-15",
        "billing_period": "October 2026",
        "supplier_name": "Sysco Food Services Solutions, LLC",
        "invoice_total": "29700.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Refrigerated Cargo Delivery (Express Cold Chain)",
                "mapped_contract_item": "Refrigerated Cargo Delivery (Express Cold Chain)",
                "mapping_confidence": 0.98,
                "quantity": "4500",
                "unit_price_charged": "3.00",
                "line_total_charged": "13500.00",
                "billing_period": "October 2026",
                "notes": ""
            },
            {
                "line_id": "L002",
                "raw_description": "Standard Dry Goods Freight (Case Distribution)",
                "mapped_contract_item": "Standard Dry Goods Freight (Case Distribution)",
                "mapping_confidence": 0.98,
                "quantity": "8000",
                "unit_price_charged": "1.80",
                "line_total_charged": "14400.00",
                "billing_period": "October 2026",
                "notes": ""
            },
            {
                "line_id": "L003",
                "raw_description": "Monthly Fuel Surcharge",
                "mapped_contract_item": "Monthly Fuel Surcharge",
                "mapping_confidence": 0.95,
                "quantity": "1",
                "unit_price_charged": "1800.00",
                "line_total_charged": "1800.00",
                "billing_period": "October 2026",
                "notes": "Monthly SLA Metric: Temperature-Controlled Delivery compliance rate for October 2026 was 99.5%. Paid in 15 days of invoice date."
            }
        ]
    },
    "INV-SYSCO-202611": {
        "invoice_id": "INV-SYSCO-202611",
        "invoice_date": "2026-12-15",
        "billing_period": "November 2026",
        "supplier_name": "Sysco Food Services Solutions, LLC",
        "invoice_total": "41400.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Refrigerated Cargo Delivery (Express Cold Chain)",
                "mapped_contract_item": "Refrigerated Cargo Delivery (Express Cold Chain)",
                "mapping_confidence": 0.98,
                "quantity": "6200",
                "unit_price_charged": "3.00",
                "line_total_charged": "18600.00",
                "billing_period": "November 2026",
                "notes": ""
            },
            {
                "line_id": "L002",
                "raw_description": "Standard Dry Goods Freight (Case Distribution)",
                "mapped_contract_item": "Standard Dry Goods Freight (Case Distribution)",
                "mapping_confidence": 0.98,
                "quantity": "12000",
                "unit_price_charged": "1.80",
                "line_total_charged": "21600.00",
                "billing_period": "November 2026",
                "notes": ""
            },
            {
                "line_id": "L003",
                "raw_description": "Monthly Fuel Surcharge",
                "mapped_contract_item": "Monthly Fuel Surcharge",
                "mapping_confidence": 0.95,
                "quantity": "1",
                "unit_price_charged": "1200.00",
                "line_total_charged": "1200.00",
                "billing_period": "November 2026",
                "sla_actual_pct": 0.972,
                "notes": "Monthly SLA Metric: Temperature-Controlled Delivery compliance rate for November 2026 was 97.2%. North-East Distribution Transition milestone was completed on October 20, 2026. Paid in 18 days of invoice date."
            }
        ]
    },
    "INV-SYSCO-202612": {
        "invoice_id": "INV-SYSCO-202612",
        "invoice_date": "2027-01-15",
        "billing_period": "December 2026",
        "supplier_name": "Sysco Food Services Solutions, LLC",
        "invoice_total": "27800.00",
        "line_items": [
            {
                "line_id": "L001",
                "raw_description": "Refrigerated Cargo Delivery (Express Cold Chain)",
                "mapped_contract_item": "Refrigerated Cargo Delivery (Express Cold Chain)",
                "mapping_confidence": 0.98,
                "quantity": "3500",
                "unit_price_charged": "3.00",
                "line_total_charged": "10500.00",
                "billing_period": "December 2026",
                "notes": ""
            },
            {
                "line_id": "L002",
                "raw_description": "Standard Dry Goods Freight (Case Distribution)",
                "mapped_contract_item": "Standard Dry Goods Freight (Case Distribution)",
                "mapping_confidence": 0.98,
                "quantity": "9000",
                "unit_price_charged": "1.80",
                "line_total_charged": "16200.00",
                "billing_period": "December 2026",
                "notes": ""
            },
            {
                "line_id": "L003",
                "raw_description": "Monthly Fuel Surcharge",
                "mapped_contract_item": "Monthly Fuel Surcharge",
                "mapping_confidence": 0.95,
                "quantity": "1",
                "unit_price_charged": "1100.00",
                "line_total_charged": "1100.00",
                "billing_period": "December 2026",
                "notes": "Monthly SLA Metric: Temperature-Controlled Delivery compliance rate for December 2026 was 99.6%. Paid in 8 days. Payment within 8 days of invoice date."
            }
        ]
    }
}

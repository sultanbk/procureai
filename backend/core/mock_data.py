# backend/core/mock_data.py
# Contains all the hardcoded mock contract rulebooks and invoice data.

MOCK_CONTRACT_RULES = {
    # C001 - Apex Logistics
    "MSA-2024-APX-001": {
        "supplier_name": "Apex Logistics Ltd",
        "contract_id": "MSA-2024-APX-001",
        "contract_date": "2024-01-01",
        "contract_currency": "INR",
        "rules": [
            {
                "rule_id": "R001",
                "rule_type": "volume_tier",
                "description": "Standard Delivery - Domestic pricing tiers",
                "clause_reference": "Section 4.2",
                "clause_text": "For monthly shipment volumes of 0-499 units, the applicable unit price shall be INR 14.00. For 500-1,999 units, the unit price shall be INR 11.50. For 2,000 units and above, the unit price shall be INR 9.80.",
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
        "contract_currency": "INR",
        "rules": [
            {
                "rule_id": "R004",
                "rule_type": "flat_rate",
                "description": "Senior Developer flat daily consulting rate",
                "clause_reference": "Section 3.1",
                "clause_text": "Senior Developer Consulting services shall be billed at a flat rate of INR 8,000.00 per day.",
                "applies_to": "Senior Developer Consulting",
                "flat_unit_price": "8000.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R005",
                "rule_type": "bundle_discount",
                "description": "QA Testing Services volume discount rate",
                "clause_reference": "Section 3.2",
                "clause_text": "QA Testing Services shall be billed at a standard rate of INR 4,000.00 per day. If the customer licenses more than 20 days of QA Testing Services in a billing period, a discounted rate of INR 3,200.00 per day shall apply to all QA days billed.",
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
                "clause_text": "Project Management Services shall be billed hourly at a rate of INR 1,500.00 per hour, subject to a maximum cap of INR 30,000.00 per month.",
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
        "contract_currency": "INR",
        "rules": [
            {
                "rule_id": "R007",
                "rule_type": "volume_tier",
                "description": "Site Excavation unit volume tiers",
                "clause_reference": "Section 4.1",
                "clause_text": "For cumulative volume of 0 to 100 cubic meters in a billing period, the rate is INR 500.00 per cubic meter. For 101 to 500 cubic meters, the rate is INR 450.00 per cubic meter. For volumes exceeding 500 cubic meters, the rate is INR 400.00 per cubic meter.",
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
                "clause_text": "If the project milestone designated 'Foundation Completion' is delayed beyond the agreed target date of October 15, 2024, the Supplier shall credit the Client a delay penalty of INR 5,000.00 per calendar day of delay.",
                "applies_to": "Foundation Completion delay",
                "flat_unit_price": "5000.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R009",
                "rule_type": "cap_rate",
                "description": "Cement Supply per bag cost ceiling",
                "clause_reference": "Section 7.2",
                "clause_text": "The cost for Cement bags supplied for construction shall be billed at actual supplier cost plus a 10% markup, subject to an absolute maximum cap of INR 400.00 per bag. Under no circumstances shall the billed rate per bag exceed INR 400.00.",
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
        "contract_currency": "INR",
        "rules": [
            {
                "rule_id": "R010",
                "rule_type": "volume_tier",
                "description": "Surgical Gloves volume tier rates",
                "clause_reference": "Section 2.1",
                "clause_text": "Surgical Gloves shall be priced based on order size: 0 to 1,000 boxes at INR 250.00 per box. 1,001 to 5,000 boxes at INR 220.00 per box. 5,001 boxes and above at INR 200.00 per box.",
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
                "clause_text": "A regulatory surcharge of 5.0% of the glove order value may be added to each invoice. The total regulatory surcharge per invoice is subject to a maximum limit of INR 2,000.00.",
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
        "contract_currency": "INR",
        "rules": [
            {
                "rule_id": "R012",
                "rule_type": "flat_rate",
                "description": "VM Hosting standard usage hourly rate",
                "clause_reference": "Section 3.1",
                "clause_text": "VM Hosting Services shall be billed at a usage-based rate of INR 10.00 per instance-hour.",
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
        "contract_currency": "INR",
        "rules": [
            {
                "rule_id": "R015",
                "rule_type": "flat_rate",
                "description": "Senior IT Consultant standard daily rate",
                "clause_reference": "Section 3.1",
                "clause_text": "Senior IT Consultant services shall be billed at a standard daily rate of INR 12,000.00.",
                "applies_to": "Senior IT Consultant",
                "flat_unit_price": "12000.00",
                "extraction_confidence": 1.0
            },
            {
                "rule_id": "R016",
                "rule_type": "flat_rate",
                "description": "Project Management advisory standard daily rate",
                "clause_reference": "Section 3.2",
                "clause_text": "Project Management advisory services shall be billed at a standard daily rate of INR 10,000.00.",
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
    }
}

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
    }
}

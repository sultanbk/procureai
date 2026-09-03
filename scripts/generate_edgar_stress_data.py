"""
FILE CANONICAL IDENTIFIER: scripts/generate_edgar_stress_data.py
PURPOSE: Generates realistic SEC EDGAR Exhibit 10 style commercial contracts and matching multi-month stress-test invoice packs with injected ground-truth discrepancies.
"""

import os
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Base Directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTRACTS_DIR = os.path.join(BASE_DIR, "data", "synthetic", "contracts")
INVOICES_DIR = os.path.join(BASE_DIR, "data", "synthetic", "invoices")

os.makedirs(CONTRACTS_DIR, exist_ok=True)
os.makedirs(INVOICES_DIR, exist_ok=True)

def create_pdf(filename, story):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )
    doc.build(story)

def get_edgar_styles():
    styles = getSampleStyleSheet()
    
    primary = colors.HexColor("#0f172a")     # Slate 900
    secondary = colors.HexColor("#1e3a8a")   # Blue 900
    accent = colors.HexColor("#0369a1")      # Sky 700
    text_dark = colors.HexColor("#1e293b")   # Slate 800
    muted = colors.HexColor("#64748b")       # Slate 500
    
    return {
        "title": ParagraphStyle(
            "EdgarTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            alignment=1, # Center
            textColor=primary,
            spaceAfter=6
        ),
        "subtitle": ParagraphStyle(
            "EdgarSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            alignment=1,
            textColor=muted,
            spaceAfter=15
        ),
        "section": ParagraphStyle(
            "EdgarSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=secondary,
            spaceBefore=12,
            spaceAfter=5,
            keepWithNext=True
        ),
        "body": ParagraphStyle(
            "EdgarBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=text_dark,
            spaceAfter=6
        ),
        "clause": ParagraphStyle(
            "EdgarClause",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=text_dark,
            leftIndent=15,
            spaceAfter=6
        ),
        "table_header": ParagraphStyle(
            "EdgarTH",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10.5,
            textColor=colors.white,
            alignment=0
        ),
        "table_cell": ParagraphStyle(
            "EdgarTD",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=text_dark
        ),
        "table_cell_bold": ParagraphStyle(
            "EdgarTDBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=text_dark
        ),
        "inv_header": ParagraphStyle(
            "InvHeader",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=secondary,
            spaceAfter=4
        ),
        "inv_sub": ParagraphStyle(
            "InvSub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=muted,
            spaceAfter=12
        ),
        "inv_notes": ParagraphStyle(
            "InvNotes",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#475569"),
            spaceBefore=8,
            spaceAfter=4
        )
    }

# ==========================================
# CONTRACT 1: CloudScale Technologies (SEC EDGAR Exhibit 10)
# ==========================================
def build_contract_c009_cloudscale():
    filename = os.path.join(CONTRACTS_DIR, "c009_cloudscale_technologies_edgar.pdf")
    s = get_edgar_styles()
    story = []
    
    story.append(Paragraph("EXHIBIT 10.14", s["subtitle"]))
    story.append(Paragraph("MASTER CLOUD SERVICES AND INFRASTRUCTURE AGREEMENT", s["title"]))
    story.append(Paragraph("CONFIDENTIAL EXECUTION COPY | SEC FILE NUMBER 001-38492 | EFFECTIVE: JAN 01, 2024", s["subtitle"]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(
        "This Master Cloud Services Agreement (\"Agreement\") is entered into as of January 1, 2024 (\"Effective Date\"), "
        "by and between <b>Enterprise Operations Corp.</b> (\"Customer\" or \"Client\") and <b>CloudScale Technologies Inc.</b> (\"Supplier\" or \"CloudScale\").",
        s["body"]
    ))
    
    story.append(Paragraph("1. RECITALS & DEFINITIONS", s["section"]))
    story.append(Paragraph(
        "Supplier provides high-availability cloud compute, egress data transmission, and enterprise managed cloud storage infrastructure.",
        s["body"]
    ))
    
    story.append(Paragraph("2. PRICING & BILLING SCHEDULE (SCHEDULE A)", s["section"]))
    story.append(Paragraph(
        "All services shall be billed monthly in arrears based on metered utilization as set forth below:",
        s["body"]
    ))
    
    story.append(Paragraph("<b>Section 2.1 — Standard Cloud Compute (vCPU Instance Hours):</b>", s["clause"]))
    story.append(Paragraph(
        "Standard Compute 4-Core vCPU instance runtime shall be billed at a fixed rate of USD 0.45 per instance hour.",
        s["clause"]
    ))
    
    story.append(Paragraph("<b>Section 2.2 — High-Performance Compute (8-Core vCPU):</b>", s["clause"]))
    story.append(Paragraph(
        "High-Performance 8-Core vCPU nodes shall be billed at a fixed rate of USD 0.90 per instance hour.",
        s["clause"]
    ))
    
    story.append(Paragraph("<b>Section 2.3 — Volume Tiered Data Egress Bandwidth:</b>", s["clause"]))
    story.append(Paragraph(
        "Monthly global data egress bandwidth shall be billed on a volume tiered pricing model as follows: "
        "(a) For monthly volume between 0 and 9,999 GB (Tier 1), the unit rate shall be USD 0.08 per GB. "
        "(b) For monthly volume between 10,000 and 49,999 GB (Tier 2), the unit rate shall be USD 0.05 per GB. "
        "(c) For monthly volume of 50,000 GB and above (Tier 3), the unit rate shall be USD 0.03 per GB.",
        s["clause"]
    ))
    
    story.append(Paragraph("<b>Section 2.4 — Premium Enterprise Support Monthly Cap:</b>", s["clause"]))
    story.append(Paragraph(
        "Dedicated Technical Account Management and 24/7 Premium Support shall be billed at USD 150.00 per engineer hour, "
        "subject to a hard contractual monthly cap amount of USD 5,000.00. The monthly total charged to Customer for support shall not exceed USD 5,000.00 under any circumstances.",
        s["clause"]
    ))
    
    story.append(Paragraph("3. SERVICE LEVEL AGREEMENT & PERFORMANCE CREDITS (SCHEDULE B)", s["section"]))
    story.append(Paragraph("<b>Section 3.1 — Production Uptime Commitment:</b>", s["clause"]))
    story.append(Paragraph(
        "Supplier guarantees 99.90% monthly service availability for all production workloads. "
        "If monthly availability falls below 99.90% but remains equal to or above 99.00%, Supplier shall automatically issue a SLA penalty credit equal to 10% of that month's total invoice. "
        "If monthly availability falls below 99.00%, Supplier shall automatically issue a SLA penalty credit equal to 25% of that month's total invoice.",
        s["clause"]
    ))
    
    story.append(Paragraph("4. PAYMENT TERMS & EARLY SETTLEMENT DISCOUNT", s["section"]))
    story.append(Paragraph("<b>Section 4.1 — Payment Window & Early Discount:</b>", s["clause"]))
    story.append(Paragraph(
        "Invoices are payable within Net-30 days. If Customer settles the invoice within 10 days of the invoice date, Customer shall be entitled to an early payment discount of 2% on the invoice total.",
        s["clause"]
    ))
    
    create_pdf(filename, story)
    print(f"Generated: {filename}")

# ==========================================
# CONTRACT 2: TransNational Freight (SEC EDGAR Exhibit 10)
# ==========================================
def build_contract_c010_transnational():
    filename = os.path.join(CONTRACTS_DIR, "c010_transnational_freight_edgar.pdf")
    s = get_edgar_styles()
    story = []
    
    story.append(Paragraph("EXHIBIT 10.22", s["subtitle"]))
    story.append(Paragraph("MASTER COLD-CHAIN TRANSPORTATION AND LOGISTICS SERVICES AGREEMENT", s["title"]))
    story.append(Paragraph("SEC REGISTRATION NO. 333-219402 | VENDOR: TRANSNATIONAL FREIGHT CORP | EFFECTIVE: JAN 01, 2024", s["subtitle"]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(
        "This Master Transportation Services Agreement (\"Agreement\") is entered into between <b>Global Supply Network Ltd</b> (\"Shipper\") "
        "and <b>TransNational Freight Corp</b> (\"Carrier\" or \"Supplier\").",
        s["body"]
    ))
    
    story.append(Paragraph("1. FREIGHT TARIFF SCHEDULE & VOLUME TIERS", s["section"]))
    story.append(Paragraph("<b>Section 1.1 — Standard Temperature-Controlled Pallet Transport:</b>", s["clause"]))
    story.append(Paragraph(
        "Refrigerated standard freight (2°C - 8°C) shall be billed based on monthly cumulative pallet volume: "
        "(a) For monthly volumes of 0 to 499 pallets, unit price is USD 65.00 per pallet. "
        "(b) For monthly volumes of 500 to 1,499 pallets, unit price is USD 52.00 per pallet. "
        "(c) For monthly volumes of 1,500 pallets or more, unit price is USD 42.00 per pallet.",
        s["clause"]
    ))
    
    story.append(Paragraph("<b>Section 1.2 — Express Dedicated Linehaul:</b>", s["clause"]))
    story.append(Paragraph(
        "Dedicated point-to-point interstate linehaul trips shall be billed at a flat rate of USD 1,450.00 per trip.",
        s["clause"]
    ))
    
    story.append(Paragraph("2. SURCHARGES AND CAP LIMITS", s["section"]))
    story.append(Paragraph("<b>Section 2.1 — Variable Fuel Surcharge Ceiling Cap:</b>", s["clause"]))
    story.append(Paragraph(
        "Fuel surcharges may be assessed based on regional diesel indices but shall be strictly capped at a maximum rate of USD 350.00 per shipment run.",
        s["clause"]
    ))
    
    story.append(Paragraph("3. ON-TIME PERFORMANCE & RELIABILITY PENALTIES", s["section"]))
    story.append(Paragraph("<b>Section 3.1 — On-Time Delivery Service Level:</b>", s["clause"]))
    story.append(Paragraph(
        "Carrier shall maintain a minimum monthly On-Time Delivery Rate of 96.0%. "
        "In the event On-Time Delivery Rate falls below 96.0% in any calendar month, Carrier shall apply a penalty credit of 8% against that month's invoice total.",
        s["clause"]
    ))
    
    create_pdf(filename, story)
    print(f"Generated: {filename}")

# ==========================================
# CONTRACT 3: Apex Facilities Maintenance (SEC EDGAR Exhibit 10)
# ==========================================
def build_contract_c011_apex_facilities():
    filename = os.path.join(CONTRACTS_DIR, "c011_apex_facilities_maintenance_edgar.pdf")
    s = get_edgar_styles()
    story = []
    
    story.append(Paragraph("EXHIBIT 10.08", s["subtitle"]))
    story.append(Paragraph("MASTER INDUSTRIAL FACILITY OPERATIONS AND MAINTENANCE AGREEMENT", s["title"]))
    story.append(Paragraph("SEC FILE NO. 001-14920 | SUPPLIER: APEX FACILITIES SERVICES LLC | EFFECTIVE: JAN 01, 2024", s["subtitle"]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(
        "This Master Industrial Facility Operations and Maintenance Agreement (\"Agreement\") is entered into between "
        "<b>NorthStar Industrial Holdings Inc.</b> (\"Client\") and <b>Apex Facilities Services LLC</b> (\"Contractor\").",
        s["body"]
    ))
    
    story.append(Paragraph("1. SCHEDULE OF BASE SERVICES & HOURLY RATES", s["section"]))
    story.append(Paragraph("<b>Section 1.1 — Monthly Scheduled Preventive Maintenance:</b>", s["clause"]))
    story.append(Paragraph(
        "Contractor shall perform comprehensive preventive maintenance across all facility HVAC, electrical, and plumbing systems for a flat fee of USD 12,500.00 per month.",
        s["clause"]
    ))
    
    story.append(Paragraph("<b>Section 1.2 — Corrective & Emergency Repair Labor Rates:</b>", s["clause"]))
    story.append(Paragraph(
        "Standard certified technician hourly rate for corrective repair is fixed at USD 85.00 per hour. "
        "Emergency and after-hours technician overtime rate is fixed at USD 120.00 per hour.",
        s["clause"]
    ))
    
    story.append(Paragraph("2. MILESTONES, SLA DELAYS & LIQUIDATED DAMAGES", s["section"]))
    story.append(Paragraph("<b>Section 2.1 — Critical Milestone Delivery & Delay Penalties:</b>", s["clause"]))
    story.append(Paragraph(
        "For major scheduled capital repairs and overhaul milestones, Contractor shall complete work on or before the agreed milestone date. "
        "For each calendar day of unapproved completion delay beyond the agreed milestone completion date, Contractor shall credit Client USD 400.00 per day as liquidated damages.",
        s["clause"]
    ))
    
    story.append(Paragraph("3. PAYMENT AND TERMS", s["section"]))
    story.append(Paragraph("<b>Section 3.1 — Annual Price Escalation Clause:</b>", s["clause"]))
    story.append(Paragraph(
        "Contract rates are firm and fixed for Year 1 (2024). Any rate adjustment shall not exceed 3.0% per annum starting from January 1, 2025.",
        s["clause"]
    ))
    
    create_pdf(filename, story)
    print(f"Generated: {filename}")


# ==========================================
# INVOICE GENERATOR HELPER
# ==========================================
def generate_invoice_pdf(filename, supplier_name, inv_num, inv_date, billing_period, line_items, total, notes="", styles=None):
    if not styles:
        styles = get_edgar_styles()
    story = []
    
    story.append(Paragraph(supplier_name.upper(), styles["inv_header"]))
    story.append(Paragraph(
        f"<b>Invoice No:</b> {inv_num} &nbsp;|&nbsp; <b>Invoice Date:</b> {inv_date} &nbsp;|&nbsp; <b>Billing Period:</b> {billing_period}",
        styles["inv_sub"]
    ))
    
    # Table Header
    headers = ["Item Code / Description", "Qty", "Unit Price", "Total (USD)"]
    header_row = [Paragraph(h, styles["table_header"]) for h in headers]
    
    table_data = [header_row]
    for row in line_items:
        # row: [desc, qty, rate, total]
        table_data.append([
            Paragraph(str(row[0]), styles["table_cell"]),
            Paragraph(str(row[1]), styles["table_cell"]),
            Paragraph(f"${float(row[2]):,.2f}", styles["table_cell"]),
            Paragraph(f"${float(row[3]):,.2f}", styles["table_cell_bold"])
        ])
    
    t = Table(table_data, colWidths=[240, 60, 100, 110])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")])
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    
    # Total Box
    total_data = [
        [Paragraph("<b>SUBTOTAL:</b>", styles["table_cell_bold"]), Paragraph(f"<b>${float(total):,.2f}</b>", styles["table_cell_bold"])],
        [Paragraph("<b>TOTAL DUE (USD):</b>", styles["table_cell_bold"]), Paragraph(f"<b>${float(total):,.2f}</b>", styles["table_cell_bold"])]
    ]
    tot_table = Table(total_data, colWidths=[380, 130])
    tot_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#e2e8f0")),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8"))
    ]))
    story.append(tot_table)
    
    if notes:
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<b>Operational Notes & Audit Telemetry:</b> {notes}", styles["inv_notes"]))
        
    create_pdf(filename, story)
    print(f"Generated: {filename}")


# ==========================================
# BUILD INVOICES FOR CLOUDSCALE (c009)
# ==========================================
def build_invoices_c009():
    styles = get_edgar_styles()
    
    # Invoice 1 (c009_invoice_i018.pdf): Month 1 - Clean Compliant Control
    # 5,000 vCPU hours @ 0.45 = 2,250.00
    # 12,000 GB egress (Tier 2) @ 0.05 = 600.00
    # 20 support hours @ 150.00 = 3,000.00 (within $5,000 cap)
    # Total: $5,850.00 | Uptime: 99.98% (Compliant)
    generate_invoice_pdf(
        filename=os.path.join(INVOICES_DIR, "c009_invoice_i018.pdf"),
        supplier_name="CloudScale Technologies Inc.",
        inv_num="INV-CS-2024-01",
        inv_date="2024-02-01",
        billing_period="January 2024",
        line_items=[
            ["CLD-COMP-4VCPU (Standard Compute 4-Core vCPU)", 5000, 0.45, 2250.00],
            ["CLD-EGR-TIER2 (Data Egress Bandwidth)", 12000, 0.05, 600.00],
            ["CLD-SUPP-PREM (Dedicated Premium Support)", 20, 150.00, 3000.00]
        ],
        total=5850.00,
        notes="Service uptime recorded: 99.98%. All SLAs met. Payment terms Net-30.",
        styles=styles
    )
    
    # Invoice 2 (c009_invoice_i019.pdf): Month 2 - Tier Overcharge + Unapplied SLA Penalty Credit
    # 8,000 vCPU hours @ 0.45 = 3,600.00
    # 65,000 GB egress charged at Tier 1 rate $0.08 instead of Tier 3 rate $0.03!
    # Charged: 65,000 * 0.08 = 5,200.00. Expected: 65,000 * 0.03 = 1,950.00 (Overcharge = $3,250.00)
    # Support: 40 hrs @ 150 = 6,000.00 (Cap exceeded by $1,000.00)
    # Uptime recorded: 98.40% (Below 99.00% -> triggers 25% credit on total = $3,700.00 credit unapplied!)
    # Total charged: $14,800.00
    generate_invoice_pdf(
        filename=os.path.join(INVOICES_DIR, "c009_invoice_i019.pdf"),
        supplier_name="CloudScale Technologies Inc.",
        inv_num="INV-CS-2024-02",
        inv_date="2024-03-01",
        billing_period="February 2024",
        line_items=[
            ["CLD-COMP-4VCPU (Standard Compute 4-Core vCPU)", 8000, 0.45, 3600.00],
            ["CLD-EGR-BANDWIDTH (Data Egress Volume)", 65000, 0.08, 5200.00],
            ["CLD-SUPP-PREM (Dedicated Premium Support)", 40, 150.00, 6000.00]
        ],
        total=14800.00,
        notes="Outage event logged on Feb 14. Monthly availability reported: 98.40%. SLA breach logged.",
        styles=styles
    )
    
    # Invoice 3 (c009_invoice_i020.pdf): Month 3 - Early Payment Discount Eligible
    # 6,000 vCPU hours @ 0.45 = 2,700.00
    # 8,000 GB egress @ 0.08 = 640.00
    # Total: $3,340.00 | Paid in 7 days (2% discount expected = $66.80)
    generate_invoice_pdf(
        filename=os.path.join(INVOICES_DIR, "c009_invoice_i020.pdf"),
        supplier_name="CloudScale Technologies Inc.",
        inv_num="INV-CS-2024-03",
        inv_date="2024-04-01",
        billing_period="March 2024",
        line_items=[
            ["CLD-COMP-4VCPU (Standard Compute 4-Core vCPU)", 6000, 0.45, 2700.00],
            ["CLD-EGR-TIER1 (Data Egress Bandwidth)", 8000, 0.08, 640.00]
        ],
        total=3340.00,
        notes="Payment received and settled within 7 days of invoice date. Availability 99.95%.",
        styles=styles
    )


# ==========================================
# BUILD INVOICES FOR TRANSNATIONAL FREIGHT (c010)
# ==========================================
def build_invoices_c010():
    styles = get_edgar_styles()
    
    # Invoice 1 (c010_invoice_i021.pdf): Month 1 - Clean Control
    # 400 pallets @ 65.00 = 26,000.00
    # 2 dedicated trips @ 1,450.00 = 2,900.00
    # Fuel surcharge 1 run @ 300.00 = 300.00 (within $350 cap)
    # Total: $29,200.00 | On-Time: 98.2% (Compliant)
    generate_invoice_pdf(
        filename=os.path.join(INVOICES_DIR, "c010_invoice_i021.pdf"),
        supplier_name="TransNational Freight Corp",
        inv_num="INV-TNF-2024-01",
        inv_date="2024-02-05",
        billing_period="January 2024",
        line_items=[
            ["COLD-PLT-STD (Refrigerated Pallet Transport)", 400, 65.00, 26000.00],
            ["LINEHAUL-EXP (Dedicated Interstate Linehaul)", 2, 1450.00, 2900.00],
            ["FUEL-SURCH-STD (Fuel Surcharge Run)", 1, 300.00, 300.00]
        ],
        total=29200.00,
        notes="Monthly on-time delivery rate: 98.2%. Temperature logs within 2C-8C nominal band.",
        styles=styles
    )
    
    # Invoice 2 (c010_invoice_i022.pdf): Month 2 - Volume Tier Overcharge + Fuel Surcharge Cap Exceeded + SLA Breach
    # 1,600 pallets charged at Tier 1 rate $65.00 instead of Tier 3 rate $42.00!
    # Charged: 1,600 * 65.00 = 104,000.00. Expected: 1,600 * 42.00 = 67,200.00 (Overcharge = $36,800.00)
    # Fuel surcharge charged at $550.00 (Exceeds $350.00 cap by $200.00)
    # On-Time delivery rate: 92.5% (Below 96.0% -> triggers 8% penalty credit on $104,550 total = $8,364.00 unapplied credit)
    generate_invoice_pdf(
        filename=os.path.join(INVOICES_DIR, "c010_invoice_i022.pdf"),
        supplier_name="TransNational Freight Corp",
        inv_num="INV-TNF-2024-02",
        inv_date="2024-03-05",
        billing_period="February 2024",
        line_items=[
            ["COLD-PLT-STD (Refrigerated Pallet Transport)", 1600, 65.00, 104000.00],
            ["FUEL-SURCH-ADJ (Fuel Surcharge Assessment)", 1, 550.00, 550.00]
        ],
        total=104550.00,
        notes="Severe winter weather delays recorded. Monthly on-time delivery rate: 92.5%.",
        styles=styles
    )


# ==========================================
# BUILD INVOICES FOR APEX FACILITIES (c011)
# ==========================================
def build_invoices_c011():
    styles = get_edgar_styles()
    
    # Series of 3 invoices testing Multi-Month Price Creep (Cross-Invoice Analyzer) & Milestone Delay
    
    # Invoice 1 (c011_invoice_i023.pdf): Month 1 - Compliant baseline
    # PM fee: 12,500.00
    # Corrective Repair: 50 hrs @ 85.00 = 4,250.00
    # Overtime: 20 hrs @ 120.00 = 2,400.00
    # Total: $19,150.00
    generate_invoice_pdf(
        filename=os.path.join(INVOICES_DIR, "c011_invoice_i023.pdf"),
        supplier_name="Apex Facilities Services LLC",
        inv_num="INV-AFS-2024-01",
        inv_date="2024-02-02",
        billing_period="January 2024",
        line_items=[
            ["FAC-PM-MONTHLY (Monthly Preventive Maintenance)", 1, 12500.00, 12500.00],
            ["FAC-LABOR-STD (Certified Technician Standard Labor)", 50, 85.00, 4250.00],
            ["FAC-LABOR-OT (Emergency & Overtime Repair Labor)", 20, 120.00, 2400.00]
        ],
        total=19150.00,
        notes="All scheduled January preventive maintenance completed. Response times within contract.",
        styles=styles
    )
    
    # Invoice 2 (c011_invoice_i024.pdf): Month 2 - Stealth Price Creep (+6.5% on hourly rate)
    # PM fee: 12,500.00
    # Corrective Repair: 60 hrs @ 90.50 (+5.50 creep) = 5,430.00 (Expected: 60 * 85.00 = 5,100.00)
    # Overtime: 25 hrs @ 128.00 (+8.00 creep) = 3,200.00 (Expected: 25 * 120.00 = 3,000.00)
    # Total: $21,130.00
    generate_invoice_pdf(
        filename=os.path.join(INVOICES_DIR, "c011_invoice_i024.pdf"),
        supplier_name="Apex Facilities Services LLC",
        inv_num="INV-AFS-2024-02",
        inv_date="2024-03-02",
        billing_period="February 2024",
        line_items=[
            ["FAC-PM-MONTHLY (Monthly Preventive Maintenance)", 1, 12500.00, 12500.00],
            ["FAC-LABOR-STD (Certified Technician Standard Labor)", 60, 90.50, 5430.00],
            ["FAC-LABOR-OT (Emergency & Overtime Repair Labor)", 25, 128.00, 3200.00]
        ],
        total=21130.00,
        notes="February maintenance log. Standard labor rate adjusted for inflation.",
        styles=styles
    )
    
    # Invoice 3 (c011_invoice_i025.pdf): Month 3 - Further Price Creep (+13% on rate) + Milestone Delay Liquidated Damages
    # PM fee: 12,500.00
    # Corrective Repair: 70 hrs @ 96.00 (+11.00 creep) = 6,720.00 (Expected: 70 * 85.00 = 5,950.00)
    # Overtime: 30 hrs @ 135.00 (+15.00 creep) = 4,050.00 (Expected: 30 * 120.00 = 3,600.00)
    # Milestone Overhaul: Scheduled target date March 15, 2024. Actual completion date March 23, 2024 (8 days delay * $400/day = $3,200 penalty)
    # Total: $23,270.00
    generate_invoice_pdf(
        filename=os.path.join(INVOICES_DIR, "c011_invoice_i025.pdf"),
        supplier_name="Apex Facilities Services LLC",
        inv_num="INV-AFS-2024-03",
        inv_date="2024-04-02",
        billing_period="March 2024",
        line_items=[
            ["FAC-PM-MONTHLY (Monthly Preventive Maintenance)", 1, 12500.00, 12500.00],
            ["FAC-LABOR-STD (Certified Technician Standard Labor)", 70, 96.00, 6720.00],
            ["FAC-LABOR-OT (Emergency & Overtime Repair Labor)", 30, 135.00, 4050.00],
            ["FAC-CHILLER-OVERHAUL (HVAC Chiller Overhaul Milestone - Target: March 15, 2024 | Completed: March 23, 2024)", 1, 0.00, 0.00]
        ],
        total=23270.00,
        notes="Chiller plant overhaul completed on March 23, 2024. Target milestone was March 15, 2024. Delay 8 days.",
        styles=styles
    )


def main():
    print("Generating SEC EDGAR Exhibit 10 Commercial Contracts...")
    build_contract_c009_cloudscale()
    build_contract_c010_transnational()
    build_contract_c011_apex_facilities()
    
    print("\nGenerating Stress-Test Multi-Month Invoices...")
    build_invoices_c009()
    build_invoices_c010()
    build_invoices_c011()
    print("\nAll datasets generated successfully!")

if __name__ == "__main__":
    main()

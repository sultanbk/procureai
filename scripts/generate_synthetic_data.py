import os
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Define directories
CONTRACTS_DIR = os.path.join("data", "synthetic", "contracts")
INVOICES_DIR = os.path.join("data", "synthetic", "invoices")

# Ensure directories exist
os.makedirs(CONTRACTS_DIR, exist_ok=True)
os.makedirs(INVOICES_DIR, exist_ok=True)

# Common Styling Functions
def create_pdf(filename, story):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    doc.build(story)

def get_custom_styles():
    styles = getSampleStyleSheet()
    
    # Custom color palette
    primary_color = colors.HexColor("#0f172a") # Navy Dark
    secondary_color = colors.HexColor("#1e3a8a") # Dark Blue
    text_color = colors.HexColor("#334155") # Charcoal Text
    
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=secondary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=text_color,
        spaceAfter=8
    )
    
    clause_style = ParagraphStyle(
        "ClauseTextCustom",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=10
    )
    
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white
    )
    
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        textColor=text_color
    )
    
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=table_cell_style,
        fontName="Helvetica-Bold"
    )
    
    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "section": section_style,
        "body": body_style,
        "clause": clause_style,
        "table_header": table_header_style,
        "table_cell": table_cell_style,
        "table_cell_bold": table_cell_bold
    }

# --- PDF Generation Helpers ---

def add_header(story, title_text, subtitle_text, styles):
    story.append(Paragraph(title_text, styles["title"]))
    story.append(Paragraph(subtitle_text, styles["subtitle"]))
    story.append(Spacer(1, 10))

def add_section(story, section_title, styles):
    story.append(Paragraph(section_title, styles["section"]))

def add_clause(story, prefix, text, styles):
    story.append(Paragraph(f"<b>{prefix}:</b> {text}", styles["clause"]))

def generate_invoice_table(story, headers, rows, styles):
    # Prepare data wrapping text in Paragraph flowables for wrapping
    data = []
    
    # Header Row
    header_row = [Paragraph(h, styles["table_header"]) for h in headers]
    data.append(header_row)
    
    # Data Rows
    for row in rows:
        row_cells = []
        for i, val in enumerate(row):
            val_str = str(val)
            # Make the last column (Line Total) or key columns bold if they look like totals
            is_bold = (i == len(row) - 1) or ("Total" in headers[i])
            style = styles["table_cell_bold"] if is_bold else styles["table_cell"]
            row_cells.append(Paragraph(val_str, style))
        data.append(row_cells)
        
    # Create Table with styling
    t = Table(data, colWidths=[200, 60, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")])
    ]))
    story.append(t)
    story.append(Spacer(1, 15))


# --- Contract & Invoice Content Builders ---

def build_c001_apex_logistics():
    # C001 - Apex Logistics Ltd
    filename = os.path.join(CONTRACTS_DIR, "c001_apex_logistics_contract.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "MASTER SERVICES AGREEMENT", "Contract Ref: MSA-2024-APX-001 | Date: January 1, 2024", styles)
    
    story.append(Paragraph("This Master Services Agreement ('Agreement') is entered into by and between <b>Global Procurement Inc.</b> ('Client') and <b>Apex Logistics Ltd</b> ('Supplier'). This Agreement governs all logistics and transport services provided by the Supplier.", styles["body"]))
    story.append(Spacer(1, 8))
    
    add_section(story, "Section 1: Scope of Work", styles)
    story.append(Paragraph("The Supplier shall perform standard domestic delivery services, including express courier, regional parcel distribution, and domestic shipping services, in accordance with the Client's purchase orders.", styles["body"]))
    
    add_section(story, "Section 4: Rates and Billing Structure", styles)
    story.append(Paragraph("All billing for Standard Delivery - Domestic shipping shall be calculated monthly on a volume tier basis as described in Schedule B.", styles["body"]))
    
    add_clause(story, "Section 4.2", "For monthly shipment volumes of 0-499 units, the applicable unit price shall be INR 14.00. For 500-1,999 units, the unit price shall be INR 11.50. For 2,000 units and above, the unit price shall be INR 9.80.", styles)
    
    add_section(story, "Section 8: Performance and Service Levels", styles)
    story.append(Paragraph("The Supplier commits to high standards of operational reliability. The metric used to evaluate performance is the On-Time Delivery Rate.", styles["body"]))
    
    add_clause(story, "Section 8.1", "Should the Supplier's on-time delivery rate fall below 97% in any calendar month, the Supplier shall issue a credit equal to 12% of that month's invoice total.", styles)
    
    add_section(story, "Section 12: General Payment Terms", styles)
    story.append(Paragraph("Invoices shall be generated monthly. The standard payment window is Net-30 days from the invoice date.", styles["body"]))
    
    add_clause(story, "Section 12.4", "A discount of 2% shall apply to any invoice settled within 10 business days of the invoice date.", styles)
    
    create_pdf(filename, story)

def build_c001_apex_logistics_v2():
    # C001 - Apex Logistics Ltd
    filename = os.path.join(CONTRACTS_DIR, "c001_apex_logistics_contract_v2.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "MASTER SERVICES AGREEMENT", "Contract Ref: MSA-2025-APX-002 | Date: January 1, 2025", styles)
    
    story.append(Paragraph("This Master Services Agreement ('Agreement') is entered into by and between <b>Global Procurement Inc.</b> ('Client') and <b>Apex Logistics Ltd</b> ('Supplier'). This Agreement governs all logistics and transport services provided by the Supplier.", styles["body"]))
    story.append(Spacer(1, 8))
    
    add_section(story, "Section 1: Scope of Work", styles)
    story.append(Paragraph("The Supplier shall perform standard domestic delivery services, including express courier, regional parcel distribution, and domestic shipping services, in accordance with the Client's purchase orders.", styles["body"]))
    
    add_section(story, "Section 4: Rates and Billing Structure", styles)
    story.append(Paragraph("All billing for Standard Delivery - Domestic shipping shall be calculated monthly on a volume tier basis as described in Schedule B.", styles["body"]))
    
    add_clause(story, "Section 4.2", "For monthly shipment volumes of 0-499 units, the applicable unit price shall be USD 15.00. For 500-1,999 units, the unit price shall be USD 12.50. For 2,000 units and above, the unit price shall be USD 10.50.", styles)
    
    add_section(story, "Section 8: Performance and Service Levels", styles)
    story.append(Paragraph("The Supplier commits to high standards of operational reliability. The metric used to evaluate performance is the On-Time Delivery Rate.", styles["body"]))
    
    add_clause(story, "Section 8.1", "Should the Supplier's on-time delivery rate fall below 98% in any calendar month, the Supplier shall issue a credit equal to 15% of that month's invoice total.", styles)
    
    add_section(story, "Section 12: General Payment Terms", styles)
    story.append(Paragraph("Invoices shall be generated monthly. The standard payment window is Net-30 days from the invoice date.", styles["body"]))
    
    add_clause(story, "Section 12.4", "A discount of 3% shall apply to any invoice settled within 10 business days of the invoice date.", styles)
    
    create_pdf(filename, story)

def build_i001_apex_oct():
    filename = os.path.join(INVOICES_DIR, "c001_invoice_i001.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "TAX INVOICE - APEX LOGISTICS LTD", "Invoice No: INV-APX-202410 | Date: November 15, 2024", styles)
    
    # Metadata table
    meta_data = [
        [Paragraph("<b>Supplier:</b> Apex Logistics Ltd<br/>Mumbai Office, India", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> October 2024<br/><b>Client Ref:</b> Global Procurement Inc.", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    # Line Item Table
    headers = ["Service Description", "Quantity", "Rate Billed (INR)", "Line Total (INR)"]
    rows = [
        ["Standard Delivery - Domestic (Express Parcel Services)", "1240", "12.50", "15500.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    # Summary Details
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: INR 15,500.00", styles["body"]))
    story.append(Paragraph("SLA Penalty/Credit Applied: INR 0.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: INR 15,500.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Monthly SLA Metric: On-time delivery performance for October 2024 was 98.5%. Early payment terms: 2% Net-10 eligible.</i>", styles["body"]))
    
    create_pdf(filename, story)

def build_i002_apex_nov():
    filename = os.path.join(INVOICES_DIR, "c001_invoice_i002.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "TAX INVOICE - APEX LOGISTICS LTD", "Invoice No: INV-APX-202411 | Date: December 15, 2024", styles)
    
    meta_data = [
        [Paragraph("<b>Supplier:</b> Apex Logistics Ltd<br/>Mumbai Office, India", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> November 2024<br/><b>Client Ref:</b> Global Procurement Inc.", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    headers = ["Service Description", "Quantity", "Rate Billed (INR)", "Line Total (INR)"]
    rows = [
        ["Standard Delivery - Domestic (Express Parcel Services)", "2500", "9.80", "24500.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: INR 24,500.00", styles["body"]))
    story.append(Paragraph("SLA Penalty/Credit Applied: INR 0.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: INR 24,500.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Monthly SLA Metric: On-time delivery performance for November 2024 was 94.2%. Early payment terms: 2% Net-10 eligible.</i>", styles["body"]))
    
    create_pdf(filename, story)


def build_c002_techsoft_solutions():
    # C002 - TechSoft Solutions
    filename = os.path.join(CONTRACTS_DIR, "c002_techsoft_solutions_contract.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "SOFTWARE SERVICES & CONSULTING CONTRACT", "Contract Ref: MSA-2024-TSS-002 | Date: February 15, 2024", styles)
    
    story.append(Paragraph("This Contract is entered into between <b>Global Procurement Inc.</b> ('Client') and <b>TechSoft Solutions</b> ('Supplier') to govern the delivery of software development, consulting, and project management services.", styles["body"]))
    story.append(Spacer(1, 8))
    
    add_section(story, "Section 3: Financial Terms and Rates", styles)
    
    add_clause(story, "Section 3.1", "Senior Developer Consulting services shall be billed at a flat rate of INR 8,000.00 per day.", styles)
    
    add_clause(story, "Section 3.2", "QA Testing Services shall be billed at a standard rate of INR 4,000.00 per day. If the customer licenses more than 20 days of QA Testing Services in a billing period, a discounted rate of INR 3,200.00 per day shall apply to all QA days billed.", styles)
    
    add_clause(story, "Section 3.3", "Project Management Services shall be billed hourly at a rate of INR 1,500.00 per hour, subject to a maximum cap of INR 30,000.00 per month.", styles)
    
    create_pdf(filename, story)

def build_i003_techsoft_sep():
    filename = os.path.join(INVOICES_DIR, "c002_invoice_i003.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "INVOICE - TECHSOFT SOLUTIONS", "Invoice No: INV-TSS-202409 | Date: October 1, 2024", styles)
    
    meta_data = [
        [Paragraph("<b>Supplier:</b> TechSoft Solutions<br/>Bengaluru, India", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> September 2024<br/><b>Client Ref:</b> Global Procurement Inc.", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    headers = ["Resource / Service", "Days", "Daily Rate (INR)", "Line Total (INR)"]
    rows = [
        ["Senior Developer Consulting", "20", "8000.00", "160000.00"],
        ["QA Testing Services", "24", "4000.00", "96000.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: INR 256,000.00", styles["body"]))
    story.append(Paragraph("Taxes & Surcharges: INR 0.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: INR 256,000.00</b>", styles["body"]))
    
    create_pdf(filename, story)

def build_i004_techsoft_oct():
    filename = os.path.join(INVOICES_DIR, "c002_invoice_i004.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "INVOICE - TECHSOFT SOLUTIONS", "Invoice No: INV-TSS-202410 | Date: November 1, 2024", styles)
    
    meta_data = [
        [Paragraph("<b>Supplier:</b> TechSoft Solutions<br/>Bengaluru, India", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> October 2024<br/><b>Client Ref:</b> Global Procurement Inc.", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    # We change columns to [Description, Quantity, Rate, Line Total]
    # Here quantity is hours for PM, days for Developer. We label the second column Qty.
    headers = ["Resource / Service", "Quantity", "Rate (INR)", "Line Total (INR)"]
    rows = [
        ["Senior Developer Consulting", "10", "8000.00", "80000.00"],
        ["Project Management Services", "24", "1500.00", "36000.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: INR 116,000.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: INR 116,000.00</b>", styles["body"]))
    
    create_pdf(filename, story)


def build_c003_buildright_contractors():
    # C003 - BuildRight Contractors
    filename = os.path.join(CONTRACTS_DIR, "c003_buildright_contractors_contract.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "CONSTRUCTION SERVICES AGREEMENT", "Contract Ref: MSA-2024-BRC-003 | Date: March 10, 2024", styles)
    
    story.append(Paragraph("This Construction Services Agreement ('Agreement') is made between <b>Global Procurement Inc.</b> ('Client') and <b>BuildRight Contractors</b> ('Supplier') for providing excavation, masonry, and raw material supply services.", styles["body"]))
    story.append(Spacer(1, 8))
    
    add_section(story, "Section 4: Excavation Services & Tiers", styles)
    story.append(Paragraph("Excavation services shall be billed on a unit volume basis as described below:", styles["body"]))
    
    add_clause(story, "Section 4.1", "For cumulative volume of 0 to 100 cubic meters in a billing period, the rate is INR 500.00 per cubic meter. For 101 to 500 cubic meters, the rate is INR 450.00 per cubic meter. For volumes exceeding 500 cubic meters, the rate is INR 400.00 per cubic meter.", styles)
    
    add_section(story, "Section 5: Project Milestones & Penalties", styles)
    story.append(Paragraph("The project must adhere to the timeline agreed in Project Schedule A. Key milestone dates are strict.", styles["body"]))
    
    add_clause(story, "Section 5.3", "If the project milestone designated 'Foundation Completion' is delayed beyond the agreed target date of October 15, 2024, the Supplier shall credit the Client a delay penalty of INR 5,000.00 per calendar day of delay.", styles)
    
    add_section(story, "Section 7: Material Procurement", styles)
    story.append(Paragraph("Materials procured by the Supplier on behalf of the Client will be billed with markup.", styles["body"]))
    
    add_clause(story, "Section 7.2", "The cost for Cement bags supplied for construction shall be billed at actual supplier cost plus a 10% markup, subject to an absolute maximum cap of INR 400.00 per bag. Under no circumstances shall the billed rate per bag exceed INR 400.00.", styles)
    
    create_pdf(filename, story)

def build_i005_buildright_oct():
    filename = os.path.join(INVOICES_DIR, "c003_invoice_i005.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "INVOICE - BUILDRIGHT CONTRACTORS", "Invoice No: INV-BRC-202410 | Date: October 31, 2024", styles)
    
    meta_data = [
        [Paragraph("<b>Supplier:</b> BuildRight Contractors<br/>Delhi NCR, India", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> October 2024<br/><b>Client Ref:</b> Global Procurement Inc.", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    headers = ["Material / Service Description", "Quantity", "Rate Billed (INR)", "Line Total (INR)"]
    rows = [
        ["Site Excavation Services (cubic meters)", "120", "450.00", "54000.00"],
        ["Cement Supply (Bags)", "200", "450.00", "90000.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: INR 144,000.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: INR 144,000.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Foundation Completion milestone was achieved on-time. No delays recorded for this billing cycle.</i>", styles["body"]))
    
    create_pdf(filename, story)

def build_i006_buildright_nov():
    filename = os.path.join(INVOICES_DIR, "c003_invoice_i006.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "INVOICE - BUILDRIGHT CONTRACTORS", "Invoice No: INV-BRC-202411 | Date: November 30, 2024", styles)
    
    meta_data = [
        [Paragraph("<b>Supplier:</b> BuildRight Contractors<br/>Delhi NCR, India", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> November 2024<br/><b>Client Ref:</b> Global Procurement Inc.", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    headers = ["Material / Service Description", "Quantity", "Rate Billed (INR)", "Line Total (INR)"]
    rows = [
        ["General Construction Services", "1", "120000.00", "120000.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: INR 120,000.00", styles["body"]))
    story.append(Paragraph("SLA/Milestone Penalties Applied: INR 0.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: INR 120,000.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Foundation Completion milestone was completed on October 20, 2024. No penalty has been applied.</i>", styles["body"]))
    
    create_pdf(filename, story)


def build_c004_medisupply():
    # C004 - MediSupply Corp
    filename = os.path.join(CONTRACTS_DIR, "c004_medisupply_contract.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "MEDICAL EQUIPMENT SUPPLY AGREEMENT", "Contract Ref: MSA-2024-MSC-004 | Date: April 1, 2024", styles)
    
    story.append(Paragraph("This Supply Agreement is between <b>Global Procurement Inc.</b> ('Client') and <b>MediSupply Corp</b> ('Supplier') to govern the purchase of surgical consumables and medical items.", styles["body"]))
    story.append(Spacer(1, 8))
    
    add_section(story, "Section 2: Pricing of Consumables", styles)
    story.append(Paragraph("Pricing for consumables shall be calculated on a volume tier basis based on the quantity ordered in each purchase order:", styles["body"]))
    
    add_clause(story, "Section 2.1", "Surgical Gloves shall be priced based on order size: 0 to 1,000 boxes at INR 250.00 per box. 1,001 to 5,000 boxes at INR 220.00 per box. 5,001 boxes and above at INR 200.00 per box.", styles)
    
    add_section(story, "Section 6: Fees and Surcharges", styles)
    story.append(Paragraph("Additional handling or compliance fees may be added to invoices as follows:", styles["body"]))
    
    add_clause(story, "Section 6.5", "A regulatory surcharge of 5.0% of the glove order value may be added to each invoice. The total regulatory surcharge per invoice is subject to a maximum limit of INR 2,000.00.", styles)
    
    create_pdf(filename, story)

def build_i007_medisupply_oct():
    filename = os.path.join(INVOICES_DIR, "c004_invoice_i007.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "TAX INVOICE - MEDISUPPLY CORP", "Invoice No: INV-MSC-202410 | Date: October 20, 2024", styles)
    
    meta_data = [
        [Paragraph("<b>Supplier:</b> MediSupply Corp<br/>Chennai, India", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> October 2024<br/><b>Client Ref:</b> Global Procurement Inc.", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    headers = ["Item Description", "Quantity (Boxes)", "Rate Charged (INR)", "Line Total (INR)"]
    rows = [
        ["Surgical Gloves (Sterile, Latex Free)", "1200", "250.00", "300000.00"],
        ["Regulatory Surcharge (5% of order)", "1", "15000.00", "15000.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: INR 315,000.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: INR 315,000.00</b>", styles["body"]))
    
    create_pdf(filename, story)

def build_i008_medisupply_nov():
    filename = os.path.join(INVOICES_DIR, "c004_invoice_i008.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "TAX INVOICE - MEDISUPPLY CORP", "Invoice No: INV-MSC-202411 | Date: November 22, 2024", styles)
    
    meta_data = [
        [Paragraph("<b>Supplier:</b> MediSupply Corp<br/>Chennai, India", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> November 2024<br/><b>Client Ref:</b> Global Procurement Inc.", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    headers = ["Item Description", "Quantity (Boxes)", "Rate Charged (INR)", "Line Total (INR)"]
    rows = [
        ["Surgical Gloves (Sterile, Latex Free)", "800", "250.00", "200000.00"],
        ["Regulatory Surcharge (5% of order)", "1", "10000.00", "10000.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: INR 210,000.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: INR 210,000.00</b>", styles["body"]))
    
    create_pdf(filename, story)


def build_c005_cloudhost():
    # C005 - CloudHost India
    filename = os.path.join(CONTRACTS_DIR, "c005_cloudhost_contract.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "CLOUD INFRASTRUCTURE MASTER AGREEMENT", "Contract Ref: MSA-2024-CHI-005 | Date: May 1, 2024", styles)
    
    story.append(Paragraph("This Infrastructure Agreement is between <b>Global Procurement Inc.</b> ('Client') and <b>CloudHost India</b> ('Supplier') to govern the VM hosting services and cloud infrastructure provisioning.", styles["body"]))
    story.append(Spacer(1, 8))
    
    add_section(story, "Section 3: Computing Services and VM Rates", styles)
    
    add_clause(story, "Section 3.1", "VM Hosting Services shall be billed at a usage-based rate of INR 10.00 per instance-hour.", styles)
    
    add_section(story, "Section 5: Service Level Agreement Credits", styles)
    story.append(Paragraph("The Supplier provides a high availability guarantee for computing hosting services.", styles["body"]))
    
    add_clause(story, "Section 5.2", "The Supplier guarantees a monthly VM service uptime of 99.9%. If the actual VM uptime in any calendar month falls below 99.9%, a credit equal to 20% of that month's total hosting charges shall be applied to the invoice.", styles)
    
    add_section(story, "Section 8: Volume Commitments", styles)
    story.append(Paragraph("Clients who deploy high density VM instances are eligible for volume discounts.", styles["body"]))
    
    add_clause(story, "Section 8.4", "If the total hosting VM hours in a billing month exceed 10,000 hours, a commitment volume discount of 15% shall be applied to the total hosting charges for that month.", styles)
    
    create_pdf(filename, story)

def build_i009_cloudhost_oct():
    filename = os.path.join(INVOICES_DIR, "c005_invoice_i009.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "INVOICE - CLOUDHOST INDIA", "Invoice No: INV-CHI-202410 | Date: November 2, 2024", styles)
    
    meta_data = [
        [Paragraph("<b>Supplier:</b> CloudHost India<br/>Delhi, India", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> October 2024<br/><b>Client Ref:</b> Global Procurement Inc.", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    headers = ["Service Description", "Quantity (Hours)", "Rate Charged (INR)", "Line Total (INR)"]
    rows = [
        ["VM Hosting Services (Standard Linux Instances)", "12000", "10.00", "120000.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: INR 120,000.00", styles["body"]))
    story.append(Paragraph("Volume Commitments Discount: INR 0.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: INR 120,000.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Actual VM service availability for October 2024: 99.95%. VM Hours: 12,000.</i>", styles["body"]))
    
    create_pdf(filename, story)

def build_i010_cloudhost_nov():
    filename = os.path.join(INVOICES_DIR, "c005_invoice_i010.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "INVOICE - CLOUDHOST INDIA", "Invoice No: INV-CHI-202411 | Date: December 2, 2024", styles)
    
    meta_data = [
        [Paragraph("<b>Supplier:</b> CloudHost India<br/>Delhi, India", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> November 2024<br/><b>Client Ref:</b> Global Procurement Inc.", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    headers = ["Service Description", "Quantity (Hours)", "Rate Charged (INR)", "Line Total (INR)"]
    rows = [
        ["VM Hosting Services (Standard Linux Instances)", "8000", "10.00", "80000.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: INR 80,000.00", styles["body"]))
    story.append(Paragraph("SLA Credit Applied: INR 0.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: INR 80,000.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Actual VM service availability for November 2024 was 99.5%. VM Hours: 8,000. No SLA credit applied.</i>", styles["body"]))
    
    create_pdf(filename, story)


def build_c006_proservices():
    # C006 - ProServices Consulting
    filename = os.path.join(CONTRACTS_DIR, "c006_proservices_contract.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "PROFESSIONAL SERVICES MASTER AGREEMENT", "Contract Ref: MSA-2024-PSC-006 | Date: June 1, 2024", styles)
    
    story.append(Paragraph("This Agreement is entered into by and between <b>Global Procurement Inc.</b> ('Client') and <b>ProServices Consulting</b> ('Supplier'). This Agreement governs all IT consulting and advisory services provided by the Supplier.", styles["body"]))
    story.append(Spacer(1, 8))
    
    add_section(story, "Section 3: Consulting Rates", styles)
    
    add_clause(story, "Section 3.1", "Senior IT Consultant services shall be billed at a standard daily rate of INR 12,000.00.", styles)
    
    add_clause(story, "Section 3.2", "Project Management advisory services shall be billed at a standard daily rate of INR 10,000.00.", styles)
    
    add_section(story, "Section 6: Service Levels and Performance", styles)
    story.append(Paragraph("The Supplier guarantees that overall service availability/uptime of the consulting system dashboard shall be at least 98.0% in any calendar month.", styles["body"]))
    
    add_clause(story, "Section 6.2", "Should the consulting dashboard availability fall below 98.0% in any month, a penalty credit of 10% of that month's total billing shall be applied to the invoice.", styles)
    
    create_pdf(filename, story)


def build_i011_proservices_dec():
    filename = os.path.join(INVOICES_DIR, "c006_invoice_i011.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "INVOICE - PROSERVICES CONSULTING", "Invoice No: INV-PSC-202412 | Date: December 20, 2024", styles)
    
    meta_data = [
        [Paragraph("<b>Supplier:</b> ProServices Consulting<br/>Hyderabad, India", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> December 2024<br/><b>Client Ref:</b> Global Procurement Inc.", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    headers = ["Service Description", "Days", "Daily Rate Billed (INR)", "Line Total (INR)"]
    rows = [
        ["Senior IT Consultant", "15", "13000.00", "195000.00"],
        ["Project Management advisory", "5", "10000.00", "50000.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: INR 245,000.00", styles["body"]))
    story.append(Paragraph("SLA Credit Applied: INR 0.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: INR 245,000.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Consulting Dashboard Uptime for December 2024 was 96.5%. No SLA credit applied.</i>", styles["body"]))
    
    create_pdf(filename, story)


def main():
    print("Generating synthetic contracts...")
    build_c001_apex_logistics()
    build_c001_apex_logistics_v2()
    build_c002_techsoft_solutions()
    build_c003_buildright_contractors()
    build_c004_medisupply()
    build_c005_cloudhost()
    build_c006_proservices()
    print("Contracts generated successfully.")
    
    print("Generating synthetic invoices...")
    build_i001_apex_oct()
    build_i002_apex_nov()
    build_i003_techsoft_sep()
    build_i004_techsoft_oct()
    build_i005_buildright_oct()
    build_i006_buildright_nov()
    build_i007_medisupply_oct()
    build_i008_medisupply_nov()
    build_i009_cloudhost_oct()
    build_i010_cloudhost_nov()
    build_i011_proservices_dec()
    print("Invoices generated successfully.")

if __name__ == "__main__":
    main()


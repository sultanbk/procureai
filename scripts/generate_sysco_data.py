import os
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
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
    
    # Custom color palette (Sysco-themed: Slate Blue and Crimson)
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

def add_header(story, title_text, subtitle_text, styles):
    story.append(Paragraph(title_text, styles["title"]))
    story.append(Paragraph(subtitle_text, styles["subtitle"]))
    story.append(Spacer(1, 10))

def add_section(story, section_title, styles):
    story.append(Paragraph(section_title, styles["section"]))

def add_clause(story, prefix, text, styles):
    story.append(Paragraph(f"<b>{prefix}:</b> {text}", styles["clause"]))

def generate_invoice_table(story, headers, rows, styles):
    data = []
    
    # Header Row
    header_row = [Paragraph(h, styles["table_header"]) for h in headers]
    data.append(header_row)
    
    # Data Rows
    for row in rows:
        row_cells = []
        for i, val in enumerate(row):
            val_str = str(val)
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


def build_sysco_contract():
    filename = os.path.join(CONTRACTS_DIR, "c007_sysco_contract.pdf")
    styles = get_custom_styles()
    story = []
    
    # PAGE 1: COVER PAGE
    story.append(Spacer(1, 40))
    story.append(Paragraph("MASTER FOOD DISTRIBUTION & LOGISTICS SERVICES AGREEMENT", styles["title"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Contract Ref:</b> CTR-SYSCO-GHG-2026-001", styles["body"]))
    story.append(Paragraph("<b>Effective Date:</b> January 1, 2026", styles["body"]))
    story.append(Paragraph("<b>Supplier:</b> Sysco Food Services Solutions, LLC", styles["body"]))
    story.append(Paragraph("<b>Client:</b> Global Hospitality & Food Services Group, Inc.", styles["body"]))
    story.append(Spacer(1, 100))
    story.append(Paragraph("CONFIDENTIAL DOCUMENT", styles["subtitle"]))
    story.append(Paragraph("This Agreement contains proprietary commercial terms and conditions governing food storage, distribution, temperature-controlled logistics, and delivery services.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 2: TABLE OF CONTENTS
    add_header(story, "TABLE OF CONTENTS", "Outline of Agreement Sections", styles)
    story.append(Paragraph("<b>Section 1:</b> Parties and Purpose .......................................................................................... Page 3", styles["body"]))
    story.append(Paragraph("<b>Section 2:</b> Scope of Distribution Services .............................................................................. Page 4", styles["body"]))
    story.append(Paragraph("<b>Section 3:</b> Temperature-Controlled Logistics Requirements ....................................................... Page 5", styles["body"]))
    story.append(Paragraph("<b>Section 4:</b> Standard Delivery & Fuel Surcharges ...................................................................... Page 6", styles["body"]))
    story.append(Paragraph("<b>Section 5:</b> Volume Discount & Rebate Structure ...................................................................... Page 7", styles["body"]))
    story.append(Paragraph("<b>Section 6:</b> Quality Assurance & Cold Chain Compliance .............................................................. Page 8", styles["body"]))
    story.append(Paragraph("<b>Section 7:</b> SLA Penalties for Delivery Interruptions .................................................................... Page 9", styles["body"]))
    story.append(Paragraph("<b>Section 8:</b> Early Payment Discounts & Payment Terms ................................................................. Page 10", styles["body"]))
    story.append(Paragraph("<b>Section 9:</b> Indemnification and Liability ................................................................................. Page 11", styles["body"]))
    story.append(Paragraph("<b>Section 10:</b> Force Majeure & Service Disruptions ........................................................................ Page 12", styles["body"]))
    story.append(Paragraph("<b>Section 11:</b> Regulatory Compliance and Auditing ........................................................................... Page 13", styles["body"]))
    story.append(Paragraph("<b>Section 12:</b> Term and Termination ........................................................................................ Page 14", styles["body"]))
    story.append(Paragraph("<b>Section 13:</b> Governing Law and Dispute Resolution ................................................................... Page 15", styles["body"]))
    story.append(Paragraph("<b>Section 14:</b> Confidentiality and Data Protection ........................................................................... Page 16", styles["body"]))
    story.append(Paragraph("<b>Section 15:</b> Miscellaneous Provisions ..................................................................................... Page 17", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 3: SECTION 1
    add_section(story, "Section 1: Parties and Purpose", styles)
    story.append(Paragraph("This Master Food Distribution and Logistics Agreement ('Agreement') is entered into by and between Global Hospitality & Food Services Group, Inc. ('Client') and Sysco Food Services Solutions, LLC ('Supplier').", styles["body"]))
    story.append(Paragraph("WHEREAS, Supplier is a premier distributor of food products, food-away-from-home merchandise, and logistics solutions; and WHEREAS, Client desires to retain Supplier to perform warehousing, shipping, inventory management, and case distribution services to its designated network of restaurants, educational venues, and hotels.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 4: SECTION 2
    add_section(story, "Section 2: Scope of Distribution Services", styles)
    story.append(Paragraph("Supplier shall purchase, warehouse, sell, and distribute a massive catalog of food and non-food products to Client's locations as requested via purchase orders.", styles["body"]))
    story.append(Paragraph("The services shall include standard case receiving, bulk warehousing, order selection, refrigerated line-haul transportation, and local last-mile delivery to restaurants, entertainment venues, and hospitality properties.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 5: SECTION 3
    add_section(story, "Section 3: Temperature-Controlled Logistics Requirements", styles)
    story.append(Paragraph("Supplier must maintain strict cold chain controls for all perishable food products. Frozen products shall be stored and transported at 0°F (-18°C) or lower, and refrigerated items must be kept between +34°F and +38°F (+1°C to +3°C) at all times.", styles["body"]))
    story.append(Paragraph("Supplier shall utilize active temperature data loggers inside all distribution vehicles and provide detailed cold chain custody reports to the Client upon request.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 6: SECTION 4
    add_section(story, "Section 4: Standard Delivery & Fuel Surcharges", styles)
    story.append(Paragraph("Supplier agrees to distribute Dry Goods and Non-Food supplies at a fixed rate per case, and to apply monthly fuel surcharges governed by maximum invoice ceilings.", styles["body"]))
    add_clause(story, "Section 4.2", "Standard dry goods freight delivery shall be billed at a flat rate of USD 1.80 per case.", styles)
    add_clause(story, "Section 4.3", "Fuel surcharges applied to any single monthly billing cycle shall not exceed USD 1,500.00. Under no circumstances shall the client be billed a fuel surcharge higher than USD 1,500.00.", styles)
    story.append(PageBreak())
    
    # PAGE 7: SECTION 5
    add_section(story, "Section 5: Volume Discount & Rebate Structure", styles)
    story.append(Paragraph("All billing for temperature-sensitive cargo (Refrigerated Cargo Delivery) shall be calculated monthly on a volume tier basis in accordance with case quantities shipped.", styles["body"]))
    add_clause(story, "Section 5.1", "For monthly delivery volumes of Refrigerated Cargo: 0-999 cases, the unit rate is USD 3.50 per case. For 1,000-4,999 cases, the unit rate is USD 3.00 per case. For 5,000 cases and above, the unit rate is USD 2.50 per case.", styles)
    story.append(PageBreak())
    
    # PAGE 8: SECTION 6
    add_section(story, "Section 6: Quality Assurance & Cold Chain Compliance", styles)
    story.append(Paragraph("Supplier shall implement hazard analysis critical control point (HACCP) programs at all distribution facilities. Supplier warrants that all food products supplied under this Agreement are safe, wholesome, and comply with the Federal Food, Drug, and Cosmetic Act.", styles["body"]))
    story.append(Paragraph("All products delivered must have a remaining shelf life of at least fourteen (14) days upon delivery, unless otherwise agreed.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 9: SECTION 7
    add_section(story, "Section 7: SLA Penalties for Delivery Interruptions", styles)
    story.append(Paragraph("The Supplier commits to high operational standards of cold chain and milestone reliability. Evaluation of performance is conducted on a monthly cycle.", styles["body"]))
    add_clause(story, "Section 7.1", "Supplier guarantees that the temperature of all refrigerated and frozen food products shall be maintained within the specified ranges during transport. Should the temperature-controlled delivery compliance rate fall below 99.0% in any calendar month, the Supplier shall issue a credit equal to 10.0% of that month's total logistics charges.", styles)
    add_clause(story, "Section 7.3", "If the logistics transition milestone designated 'North-East Distribution Transition' is delayed beyond the agreed target date of October 15, 2026, the Supplier shall credit the Client a delay penalty of USD 1,000.00 per calendar day of delay.", styles)
    story.append(PageBreak())
    
    # PAGE 10: SECTION 8
    add_section(story, "Section 8: Early Payment Discounts & Payment Terms", styles)
    story.append(Paragraph("Invoices shall be generated monthly. The standard payment window is Net-30 days from the invoice date. Early settlements are eligible for prompt payment discounts.", styles["body"]))
    add_clause(story, "Section 8.2", "A prompt payment discount of 2.0% shall apply to Standard Dry Goods Freight charges settled within 10 business days of the invoice date.", styles)
    story.append(PageBreak())
    
    # PAGE 11: SECTION 9
    add_section(story, "Section 9: Indemnification and Liability", styles)
    story.append(Paragraph("Each party shall defend, indemnify, and hold harmless the other party, its affiliates, officers, directors, and employees, from and against any third-party claims, liabilities, losses, damages, or costs (including reasonable attorneys' fees) arising out of or relating to negligence or willful misconduct.", styles["body"]))
    story.append(Paragraph("Under no circumstances shall either party be liable for any indirect, incidental, special, or consequential damages, including lost profits, arising out of this Agreement.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 12: SECTION 10
    add_section(story, "Section 10: Force Majeure & Service Disruptions", styles)
    story.append(Paragraph("Neither party shall be liable for delays or failures in performance resulting from acts beyond its reasonable control, including, but not limited to, acts of God, labor disputes, material shortages, riots, acts of war, government regulations, or natural disasters.", styles["body"]))
    story.append(Paragraph("In the event of a force majeure, the affected party shall notify the other party in writing within three (3) business days, describing the nature and expected duration of the delay.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 13: SECTION 11
    add_section(story, "Section 11: Regulatory Compliance and Auditing", styles)
    story.append(Paragraph("Supplier warrants that its operations comply with all local, state, and federal regulatory standards, including FDA, USDA, and OSHA guidelines.", styles["body"]))
    story.append(Paragraph("Client shall have the right, upon reasonable prior written notice, to audit Supplier's billing, logs, and delivery records to verify compliance with the pricing and SLA terms of this Agreement.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 14: SECTION 12
    add_section(story, "Section 12: Term and Termination", styles)
    story.append(Paragraph("The initial term of this Agreement shall be three (3) years from the Effective Date, unless terminated earlier in accordance with the provisions herein.", styles["body"]))
    story.append(Paragraph("Either party may terminate this Agreement for convenience upon ninety (90) days prior written notice, or for cause immediately upon written notice if the other party breaches any material term and fails to cure such breach within thirty (30) days.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 15: SECTION 13
    add_section(story, "Section 13: Governing Law and Dispute Resolution", styles)
    story.append(Paragraph("This Agreement shall be governed by, and construed in accordance with, the laws of the State of Texas, without regard to its conflict of laws principles.", styles["body"]))
    story.append(Paragraph("Any dispute, controversy, or claim arising out of or relating to this Agreement shall be resolved through binding arbitration in Houston, Texas, under the rules of the American Arbitration Association.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 16: SECTION 14
    add_section(story, "Section 14: Confidentiality and Data Protection", styles)
    story.append(Paragraph("Each party agrees to maintain the confidentiality of all proprietary or non-public information disclosed by the other party, including but not limited to pricing structures, customer lists, and logistics methods.", styles["body"]))
    story.append(Paragraph("This confidentiality obligation shall survive the expiration or termination of this Agreement for a period of five (5) years.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 17: SECTION 15
    add_section(story, "Section 15: Miscellaneous Provisions", styles)
    story.append(Paragraph("This Agreement constitutes the entire agreement between the parties and supersedes all prior discussions, negotiations, or understandings.", styles["body"]))
    story.append(Paragraph("No amendment or modification of this Agreement shall be valid unless in writing and signed by authorized representatives of both parties.", styles["body"]))
    story.append(Spacer(1, 30))
    story.append(Paragraph("IN WITNESS WHEREOF, the parties hereto have executed this Agreement as of the Effective Date.", styles["body"]))
    
    create_pdf(filename, story)
    print("Sysco Contract generated successfully (17 pages).")


def build_sysco_invoice_1():
    filename = os.path.join(INVOICES_DIR, "c007_invoice_i012.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "INVOICE - SYSCO FOOD SERVICES SOLUTIONS", "Invoice No: INV-SYSCO-202610 | Date: November 15, 2026", styles)
    
    # Metadata table
    meta_data = [
        [Paragraph("<b>Supplier:</b> Sysco Food Services Solutions, LLC<br/>Houston HQ, Texas", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> October 2026<br/><b>Client Ref:</b> Global Hospitality & Food Services Group", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    # Line Item Table
    headers = ["Service Description", "Quantity", "Rate Billed (USD)", "Line Total (USD)"]
    rows = [
        ["Refrigerated Cargo Delivery (Express Cold Chain)", "4500", "3.00", "13500.00"],
        ["Standard Dry Goods Freight (Case Distribution)", "8000", "1.80", "14400.00"],
        ["Monthly Fuel Surcharge", "1", "1800.00", "1800.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    # Summary Details
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: USD 29,700.00", styles["body"]))
    story.append(Paragraph("SLA Penalty/Credit Applied: USD 0.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: USD 29,700.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Monthly SLA Metric: Temperature-Controlled Delivery compliance rate for October 2026 was 99.5%. Paid in 15 days of invoice date.</i>", styles["body"]))
    
    create_pdf(filename, story)
    print("Invoice 1 (October 2026) generated.")


def build_sysco_invoice_2():
    filename = os.path.join(INVOICES_DIR, "c007_invoice_i013.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "INVOICE - SYSCO FOOD SERVICES SOLUTIONS", "Invoice No: INV-SYSCO-202611 | Date: December 15, 2026", styles)
    
    # Metadata table
    meta_data = [
        [Paragraph("<b>Supplier:</b> Sysco Food Services Solutions, LLC<br/>Houston HQ, Texas", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> November 2026<br/><b>Client Ref:</b> Global Hospitality & Food Services Group", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    # Line Item Table
    headers = ["Service Description", "Quantity", "Rate Billed (USD)", "Line Total (USD)"]
    rows = [
        ["Refrigerated Cargo Delivery (Express Cold Chain)", "6200", "3.00", "18600.00"],
        ["Standard Dry Goods Freight (Case Distribution)", "12000", "1.80", "21600.00"],
        ["Monthly Fuel Surcharge", "1", "1200.00", "1200.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    # Summary Details
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: USD 41,400.00", styles["body"]))
    story.append(Paragraph("SLA Penalty/Credit Applied: USD 0.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: USD 41,400.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Monthly SLA Metric: Temperature-Controlled Delivery compliance rate for November 2026 was 97.2%. North-East Distribution Transition milestone was completed on October 20, 2026. Paid in 18 days of invoice date.</i>", styles["body"]))
    
    create_pdf(filename, story)
    print("Invoice 2 (November 2026) generated.")


def build_sysco_invoice_3():
    filename = os.path.join(INVOICES_DIR, "c007_invoice_i014.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "INVOICE - SYSCO FOOD SERVICES SOLUTIONS", "Invoice No: INV-SYSCO-202612 | Date: January 15, 2027", styles)
    
    # Metadata table
    meta_data = [
        [Paragraph("<b>Supplier:</b> Sysco Food Services Solutions, LLC<br/>Houston HQ, Texas", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> December 2026<br/><b>Client Ref:</b> Global Hospitality & Food Services Group", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    # Line Item Table
    headers = ["Service Description", "Quantity", "Rate Billed (USD)", "Line Total (USD)"]
    rows = [
        ["Refrigerated Cargo Delivery (Express Cold Chain)", "3500", "3.00", "10500.00"],
        ["Standard Dry Goods Freight (Case Distribution)", "9000", "1.80", "16200.00"],
        ["Monthly Fuel Surcharge", "1", "1100.00", "1100.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    # Summary Details
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: USD 27,800.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: USD 27,800.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Monthly SLA Metric: Temperature-Controlled Delivery compliance rate for December 2026 was 99.6%. Paid in 8 days. Payment within 8 days of invoice date.</i>", styles["body"]))
    
    create_pdf(filename, story)
    print("Invoice 3 (December 2026) generated.")


def main():
    print("Generating Sysco contract and invoices...")
    build_sysco_contract()
    build_sysco_invoice_1()
    build_sysco_invoice_2()
    build_sysco_invoice_3()
    print("All files generated successfully.")

if __name__ == "__main__":
    main()

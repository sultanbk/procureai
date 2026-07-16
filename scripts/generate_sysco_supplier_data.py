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
    
    primary_color = colors.HexColor("#065f46") # Emerald Dark (Supplier theme)
    secondary_color = colors.HexColor("#0f766e") # Teal Dark
    text_color = colors.HexColor("#1e293b") # Slate Dark
    
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
        textColor=colors.HexColor("#475569"),
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
    header_row = [Paragraph(h, styles["table_header"]) for h in headers]
    data.append(header_row)
    
    for row in rows:
        row_cells = []
        for i, val in enumerate(row):
            val_str = str(val)
            is_bold = (i == len(row) - 1) or ("Total" in headers[i])
            style = styles["table_cell_bold"] if is_bold else styles["table_cell"]
            row_cells.append(Paragraph(val_str, style))
        data.append(row_cells)
        
    t = Table(data, colWidths=[200, 60, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#065f46")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")])
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

def build_sysco_supplier_contract():
    filename = os.path.join(CONTRACTS_DIR, "c008_premium_cold_foods_contract.pdf")
    styles = get_custom_styles()
    story = []
    
    # PAGE 1: COVER PAGE
    story.append(Spacer(1, 40))
    story.append(Paragraph("MASTER FOOD SUPPLY & COLD CHAIN LOGISTICS AGREEMENT", styles["title"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Contract Ref:</b> CTR-SYSCO-PCF-2026-002", styles["body"]))
    story.append(Paragraph("<b>Effective Date:</b> June 1, 2026", styles["body"]))
    story.append(Paragraph("<b>Supplier:</b> Premium Cold Foods, Inc.", styles["body"]))
    story.append(Paragraph("<b>Client / Buyer:</b> Sysco Corporation", styles["body"]))
    story.append(Spacer(1, 100))
    story.append(Paragraph("CONFIDENTIAL LEGAL INSTRUMENT", styles["subtitle"]))
    story.append(Paragraph("This supply agreement governs the wholesale supply, temperature-sensitive logistics, compliance criteria, pricing structures, and SLA thresholds between Premium Cold Foods, Inc. and Sysco Corporation.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 2: TABLE OF CONTENTS
    add_header(story, "TABLE OF CONTENTS", "Outline of Agreement Sections", styles)
    story.append(Paragraph("<b>Section 1:</b> Parties, Purpose & Recitals .......................................................................................... Page 3", styles["body"]))
    story.append(Paragraph("<b>Section 2:</b> Scope of Supply & Wholesale Delivery .............................................................................. Page 4", styles["body"]))
    story.append(Paragraph("<b>Section 3:</b> Quality Standards & Cold Chain Integrity ........................................................................... Page 5", styles["body"]))
    story.append(Paragraph("<b>Section 4:</b> Standard Pricing Rates & Case Tariffs .......................................................................... Page 6", styles["body"]))
    story.append(Paragraph("<b>Section 5:</b> Volume-Based Discounts & Rebate Structures .................................................................. Page 7", styles["body"]))
    story.append(Paragraph("<b>Section 6:</b> Logistics Surcharges & Fuel Ceiling Caps ....................................................................... Page 8", styles["body"]))
    story.append(Paragraph("<b>Section 7:</b> SLA Temperature Compliance Metrics & Penalty Credits ........................................................ Page 9", styles["body"]))
    story.append(Paragraph("<b>Section 8:</b> Integration Milestones and Delay Liquidated Damages ........................................................... Page 10", styles["body"]))
    story.append(Paragraph("<b>Section 9:</b> Early Settlement Terms and Prompt Payment Incentives ....................................................... Page 11", styles["body"]))
    story.append(Paragraph("<b>Section 10:</b> Product Inspection, Rejection & Claims Procedure ........................................................... Page 12", styles["body"]))
    story.append(Paragraph("<b>Section 11:</b> Warranties, Recalls & Liability Indemnity ....................................................................... Page 13", styles["body"]))
    story.append(Paragraph("<b>Section 12:</b> Force Majeure and Business Continuity Standards .......................................................... Page 14", styles["body"]))
    story.append(Paragraph("<b>Section 13:</b> Regulatory Compliance and Food Safety Certifications ........................................................... Page 15", styles["body"]))
    story.append(Paragraph("<b>Section 14:</b> Governing Law, Arbitration Venue & Jurisdiction ................................................................ Page 16", styles["body"]))
    story.append(Paragraph("<b>Section 15:</b> Confidentiality, Non-Disclosure & Data Security ............................................................... Page 17", styles["body"]))
    story.append(Paragraph("<b>Section 16:</b> Miscellaneous Covenants and Signatures ........................................................................... Page 18", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 3: SECTION 1
    add_section(story, "Section 1: Parties, Purpose & Recitals", styles)
    story.append(Paragraph("This Master Food Supply and Cold Chain Logistics Agreement ('Agreement') is made and entered into on this 1st day of June, 2026, by and between:", styles["body"]))
    story.append(Paragraph("<b>Premium Cold Foods, Inc.</b>, a corporation organized under the laws of the State of Delaware, with its principal business office at 100 Harvest Way, Wilmington, DE 19801 (hereinafter referred to as 'Supplier'), and", styles["body"]))
    story.append(Paragraph("<b>Sysco Corporation</b>, a corporation organized under the laws of the State of Delaware, with its global headquarters at 1390 Enclave Parkway, Houston, TX 77077 (hereinafter referred to as 'Client' or 'Sysco').", styles["body"]))
    story.append(Paragraph("WHEREAS, Supplier specializes in the production, wholesale packaging, storage, and transport of organic produce and premium frozen food products; and WHEREAS, Sysco is the world's largest food-away-from-home distributor and requires a reliable supply of fresh and frozen items for its distribution network.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 4: SECTION 2
    add_section(story, "Section 2: Scope of Supply & Wholesale Delivery", styles)
    story.append(Paragraph("Supplier shall supply, sell, and deliver fresh produce and frozen food products to Sysco's regional distribution centers as specified in periodic Purchase Orders issued by Sysco.", styles["body"]))
    story.append(Paragraph("The scope includes wholesale produce shipping, high-capacity cold storage, mixed-pallet ordering, and active refrigerated transportation. All deliveries must match specified quantities, packaging standards, and shelf-life parameters.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 5: SECTION 3
    add_section(story, "Section 3: Quality Standards & Cold Chain Integrity", styles)
    story.append(Paragraph("All products supplied under this Agreement must be shipped utilizing refrigerated transport that complies with strict FDA Sanitary Transportation rules.", styles["body"]))
    story.append(Paragraph("Fresh produce boxes must be kept at a temperature range of +34°F to +38°F. Frozen products must be maintained at 0°F or lower throughout the entire logistics chain.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 6: SECTION 4
    add_section(story, "Section 4: Standard Pricing Rates & Case Tariffs", styles)
    story.append(Paragraph("The standard rates for products delivered under this Agreement are determined on a unit-case basis. Rates are set for the initial year of the contract.", styles["body"]))
    add_clause(story, "Section 4.2", "Standard Produce Boxes delivered to Sysco hubs shall be billed at a flat rate of USD 4.50 per box.", styles)
    add_clause(story, "Section 4.3", "Standard Frozen Food cases delivered under this Agreement shall be billed at USD 5.80 per case.", styles)
    story.append(PageBreak())
    
    # PAGE 7: SECTION 5
    add_section(story, "Section 5: Volume-Based Discounts & Rebate Structures", styles)
    story.append(Paragraph("To incentivize high-volume distribution, the parties agree to a monthly volume rebate mechanism applied directly to the billing cycle.", styles["body"]))
    add_clause(story, "Section 5.1", "If the monthly volume of Frozen Food cases shipped to Sysco hubs exceeds 10,000 cases in any calendar month, a discounted rate of USD 5.00 per case shall apply to all Frozen Food cases billed in that month.", styles)
    story.append(PageBreak())
    
    # PAGE 8: SECTION 6
    add_section(story, "Section 6: Logistics Surcharges & Fuel Ceiling Caps", styles)
    story.append(Paragraph("Supplier may apply logistics surcharges and fuel cost adjustments. Surcharges must be validated and are capped on a monthly basis.", styles["body"]))
    add_clause(story, "Section 6.2", "Fuel surcharges applied to any monthly invoice shall not exceed USD 2,000.00. Under no circumstances shall Sysco be billed a fuel surcharge higher than USD 2,000.00.", styles)
    story.append(PageBreak())
    
    # PAGE 9: SECTION 7
    add_section(story, "Section 7: SLA Temperature Compliance Metrics & Penalty Credits", styles)
    story.append(Paragraph("Operational SLA performance is critical to maintaining food safety and fresh shelf life. Compliance is evaluated over monthly periods.", styles["body"]))
    add_clause(story, "Section 7.1", "The Supplier guarantees that the temperature compliance rate for all shipments in a calendar month shall be at least 98.0%. If the monthly temperature compliance rate falls below 98.0%, the Supplier shall issue a credit penalty equal to 8.0% of that month's total invoice amount.", styles)
    story.append(PageBreak())
    
    # PAGE 10: SECTION 8
    add_section(story, "Section 8: Integration Milestones and Delay Liquidated Damages", styles)
    story.append(Paragraph("Supplier must execute logistics integrations to align with Sysco's tracking infrastructure. Delays in integration trigger milestone liquidated damages.", styles["body"]))
    add_clause(story, "Section 8.2", "If the logistics integration milestone designated 'Mid-West Cold Chain Integration' is delayed beyond the target date of November 1, 2026, the Supplier shall credit the Client a delay penalty of USD 1,500.00 per calendar day of delay.", styles)
    story.append(PageBreak())
    
    # PAGE 11: SECTION 9
    add_section(story, "Section 9: Early Settlement Terms and Prompt Payment Incentives", styles)
    story.append(Paragraph("The standard payment term is Net-30 days from invoice date. Sysco is entitled to discounts for prompt payment settlements.", styles["body"]))
    add_clause(story, "Section 9.2", "A prompt payment discount of 3.0% shall apply to Standard Produce Box charges if settled within 12 days of the invoice date.", styles)
    story.append(PageBreak())
    
    # PAGE 12: SECTION 10
    add_section(story, "Section 10: Product Inspection, Rejection & Claims Procedure", styles)
    story.append(Paragraph("Sysco shall have the right to inspect all shipments at the time of delivery. Any damaged, spoiled, or off-temperature products may be rejected on the spot.", styles["body"]))
    story.append(Paragraph("Supplier must issue full credits for any rejected items within five (5) business days. Claims for latent defects must be filed within ten (10) business days of delivery.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 13: SECTION 11
    add_section(story, "Section 11: Warranties, Recalls & Liability Indemnity", styles)
    story.append(Paragraph("Supplier warrants that all products supplied are pure, unadulterated, and packaged in compliance with USDA organic guidelines.", styles["body"]))
    story.append(Paragraph("In the event of a product recall, Supplier shall bear all recall costs, including logistics, product destruction, notification costs, and fines.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 14: SECTION 12
    add_section(story, "Section 12: Force Majeure and Business Continuity Standards", styles)
    story.append(Paragraph("Supplier must maintain a comprehensive disaster recovery and business continuity plan to ensure continuity of supply to Sysco hubs.", styles["body"]))
    story.append(Paragraph("Force majeure events include acts of God, war, labor disputes, and crop failures. The affected party must notify the other within forty-eight (48) hours.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 15: SECTION 13
    add_section(story, "Section 13: Regulatory Compliance and Food Safety Certifications", styles)
    story.append(Paragraph("Supplier warrants compliance with the FDA Food Safety Modernization Act (FSMA) and must maintain third-party GFSI audit certifications.", styles["body"]))
    story.append(Paragraph("Supplier shall grant Sysco or its designated auditor access to check facilities, logging records, and cold chain custody logs upon request.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 16: SECTION 14
    add_section(story, "Section 14: Governing Law, Arbitration Venue & Jurisdiction", styles)
    story.append(Paragraph("This Agreement shall be governed by, and construed in accordance with, the laws of the State of Delaware, without regard to conflict of law principles.", styles["body"]))
    story.append(Paragraph("Any controversy or claim arising out of this Agreement shall be settled by binding arbitration in Wilmington, Delaware, under AAA commercial rules.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 17: SECTION 15
    add_section(story, "Section 15: Confidentiality, Non-Disclosure & Data Security", styles)
    story.append(Paragraph("Supplier shall protect all Sysco pricing data, proprietary distribution schedules, and supplier-client details as Confidential Information.", styles["body"]))
    story.append(Paragraph("Confidentiality obligations shall survive termination or expiration of this Agreement for a period of seven (7) years.", styles["body"]))
    story.append(PageBreak())
    
    # PAGE 18: SECTION 16
    add_section(story, "Section 16: Miscellaneous Covenants and Signatures", styles)
    story.append(Paragraph("This Agreement constitutes the entire contract between the parties. It supersedes all prior agreements, oral or written, and cannot be modified except in writing signed by authorized officers of both parties.", styles["body"]))
    story.append(Spacer(1, 40))
    story.append(Paragraph("IN WITNESS WHEREOF, the parties hereto have executed this Agreement by their authorized officers.", styles["body"]))
    
    create_pdf(filename, story)
    print("Premium Cold Foods Contract generated successfully (18 pages).")

def build_pcf_invoice_1():
    filename = os.path.join(INVOICES_DIR, "c008_invoice_i015.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "INVOICE - PREMIUM COLD FOODS", "Invoice No: INV-PCF-202611 | Date: December 10, 2026", styles)
    
    # Metadata table
    meta_data = [
        [Paragraph("<b>Supplier:</b> Premium Cold Foods, Inc.<br/>100 Harvest Way, Wilmington, DE", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> November 2026<br/><b>Client / Buyer:</b> Sysco Corporation", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    # Line Item Table
    headers = ["Produce Description", "Quantity", "Rate Billed (USD)", "Line Total (USD)"]
    rows = [
        ["Standard Produce Boxes (Organic Harvest)", "12000", "4.50", "54000.00"],
        ["Standard Fuel Surcharge", "1", "2500.00", "2500.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    # Summary Details
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: USD 56,500.00", styles["body"]))
    story.append(Paragraph("SLA Penalty/Credit Applied: USD 0.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: USD 56,500.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Monthly SLA Metric: Temperature-Controlled compliance rate for November 2026 was 99.1%. Paid in 15 days of invoice date.</i>", styles["body"]))
    
    create_pdf(filename, story)
    print("Invoice 1 (November 2026) generated.")

def build_pcf_invoice_2():
    filename = os.path.join(INVOICES_DIR, "c008_invoice_i016.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "INVOICE - PREMIUM COLD FOODS", "Invoice No: INV-PCF-202612 | Date: January 10, 2027", styles)
    
    # Metadata table
    meta_data = [
        [Paragraph("<b>Supplier:</b> Premium Cold Foods, Inc.<br/>100 Harvest Way, Wilmington, DE", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> December 2026<br/><b>Client / Buyer:</b> Sysco Corporation", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    # Line Item Table
    headers = ["Produce Description", "Quantity", "Rate Billed (USD)", "Line Total (USD)"]
    rows = [
        ["Standard Produce Boxes (Organic Harvest)", "8000", "4.50", "36000.00"],
        ["Standard Frozen Food cases (Cold Storage Bulk)", "11500", "5.80", "66700.00"], # Volume tier overcharge! 11500 cases should be billed at 5.00
        ["Standard Fuel Surcharge", "1", "1500.00", "1500.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    # Summary Details
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: USD 104,200.00", styles["body"]))
    story.append(Paragraph("SLA Penalty/Credit Applied: USD 0.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: USD 104,200.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Monthly SLA Metric: Temperature-Controlled compliance rate for December 2026 was 96.5%. Mid-West Cold Chain Integration milestone was completed on November 5, 2026. Paid in 20 days.</i>", styles["body"]))
    
    create_pdf(filename, story)
    print("Invoice 2 (December 2026) generated.")

def build_pcf_invoice_3():
    filename = os.path.join(INVOICES_DIR, "c008_invoice_i017.pdf")
    styles = get_custom_styles()
    story = []
    
    add_header(story, "INVOICE - PREMIUM COLD FOODS", "Invoice No: INV-PCF-202701 | Date: February 10, 2027", styles)
    
    # Metadata table
    meta_data = [
        [Paragraph("<b>Supplier:</b> Premium Cold Foods, Inc.<br/>100 Harvest Way, Wilmington, DE", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> January 2027<br/><b>Client / Buyer:</b> Sysco Corporation", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    # Line Item Table
    headers = ["Produce Description", "Quantity", "Rate Billed (USD)", "Line Total (USD)"]
    rows = [
        ["Standard Produce Boxes (Organic Harvest)", "9000", "4.50", "40500.00"],
        ["Standard Fuel Surcharge", "1", "1200.00", "1200.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    # Summary Details
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: USD 41,700.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: USD 41,700.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Monthly SLA Metric: Temperature-Controlled compliance rate for January 2027 was 99.4%. Paid in 9 days. Payment within 9 days of invoice date.</i>", styles["body"]))
    
    create_pdf(filename, story)
    print("Invoice 3 (January 2027) generated.")

def main():
    print("Generating Premium Cold Foods contract and invoices...")
    build_sysco_supplier_contract()
    build_pcf_invoice_1()
    build_pcf_invoice_2()
    build_pcf_invoice_3()
    print("All files generated successfully.")

if __name__ == "__main__":
    main()

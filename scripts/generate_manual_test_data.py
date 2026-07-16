import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Directories
UPLOADS_DIR = os.path.join("data", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

CONTRACT_PATH = os.path.join(UPLOADS_DIR, "manual_test_acme_contract.pdf")
INVOICE_PATH = os.path.join(UPLOADS_DIR, "manual_test_acme_invoice.pdf")

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
    
    primary_color = colors.HexColor("#0f172a") # Navy Dark
    secondary_color = colors.HexColor("#1e3a8a") # Dark Blue
    text_color = colors.HexColor("#334155") # Charcoal Text
    
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=12
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
        fontSize=12,
        leading=15,
        textColor=secondary_color,
        spaceBefore=12,
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
        spaceAfter=8
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

def build_acme_contract():
    styles = get_custom_styles()
    story = []
    
    add_header(story, "MASTER SERVICES AGREEMENT", "Contract ID: MSA-2026-ACM-007 | Date: January 1, 2026", styles)
    
    story.append(Paragraph("This Master Services Agreement ('Agreement') is entered into by and between <b>Global Procurement Inc.</b> ('Client') and <b>Acme Corporation</b> ('Supplier'). This Agreement governs the professional consulting and project management services provided by the Supplier.", styles["body"]))
    story.append(Spacer(1, 8))
    
    add_section(story, "Section 1: Scope of Services", styles)
    story.append(Paragraph("The Supplier shall provide software development consulting, technical advisory, and professional project management services as defined by individual statements of work.", styles["body"]))
    
    add_section(story, "Section 3: Consulting Rates & Capping", styles)
    
    add_clause(story, "Section 3.1", "Software Development Services shall be billed at a flat daily rate of INR 5,000.00 per consultant-day.", styles)
    
    add_clause(story, "Section 3.2", "Project Management Services shall be billed hourly at a rate of INR 2,000.00 per hour, subject to a monthly cap of INR 40,000.00. Under no circumstances shall the client be billed more than INR 40,000.00 for project management services in any calendar month.", styles)
    
    add_section(story, "Section 5: Service Level Agreement (SLA) & Credits", styles)
    story.append(Paragraph("The Supplier guarantees the availability and performance of the custom analytics dashboard developed for the Client.", styles["body"]))
    
    add_clause(story, "Section 5.1", "The Supplier guarantees a monthly dashboard uptime availability of 99.0%. Should the dashboard uptime fall below 99.0% in any calendar month, the Supplier shall apply a penalty credit equal to 5.0% of that month's total invoice billing value to the Client.", styles)
    
    add_section(story, "Section 10: Billing and Payments", styles)
    story.append(Paragraph("All invoices shall be generated monthly. The standard payment window is Net-30 days from the invoice date.", styles["body"]))
    
    create_pdf(CONTRACT_PATH, story)
    print(f"Generated Contract PDF: {CONTRACT_PATH}")

def build_acme_invoice():
    styles = get_custom_styles()
    story = []
    
    add_header(story, "TAX INVOICE - ACME CORPORATION", "Invoice No: INV-ACM-202606 | Date: June 1, 2026", styles)
    
    meta_data = [
        [Paragraph("<b>Supplier:</b> Acme Corporation<br/>Tech Hub Phase 1, Bangalore", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> May 2026<br/><b>Client Ref:</b> Global Procurement Inc.", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    headers = ["Service Description", "Quantity", "Rate Billed (INR)", "Line Total (INR)"]
    rows = [
        ["Software Development Services (Days)", "10", "6000.00", "60000.00"],
        ["Project Management Services (Hours)", "25", "2000.00", "50000.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: INR 110,000.00", styles["body"]))
    story.append(Paragraph("SLA Uptime Credit Applied: INR 0.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: INR 110,000.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Monthly SLA Metric: Analytics dashboard uptime for May 2026 was 98.5%. Payment terms: standard Net-30.</i>", styles["body"]))
    
    create_pdf(INVOICE_PATH, story)
    print(f"Generated Invoice PDF: {INVOICE_PATH}")

if __name__ == "__main__":
    build_acme_contract()
    build_acme_invoice()

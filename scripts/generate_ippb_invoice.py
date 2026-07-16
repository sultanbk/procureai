import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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
        "table_header": table_header_style,
        "table_cell": table_cell_style,
        "table_cell_bold": table_cell_bold
    }

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
        
    t = Table(data, colWidths=[220, 60, 90, 90])
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

def build_ippb_invoice():
    invoices_dir = os.path.join("data", "synthetic", "invoices")
    os.makedirs(invoices_dir, exist_ok=True)
    filename = os.path.join(invoices_dir, "ippb_invoice.pdf")
    
    styles = get_custom_styles()
    story = []
    
    story.append(Paragraph("TAX INVOICE - SERVICE PROVIDER", styles["title"]))
    story.append(Paragraph("Invoice No: INV-IPPB-202601 | Date: June 7, 2026", styles["subtitle"]))
    story.append(Spacer(1, 10))
    
    meta_data = [
        [Paragraph("<b>Supplier:</b> Service Provider<br/>Registered Address Placeholder<br/>New Delhi, India", styles["table_cell"]),
         Paragraph("<b>Billing Period:</b> May 2026<br/><b>Client:</b> India Post Payments Bank Limited (IPPB)", styles["table_cell"])]
    ]
    t_meta = Table(meta_data, colWidths=[230, 230])
    t_meta.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    headers = ["Service Description", "Quantity", "Rate (INR)", "Line Total (INR)"]
    rows = [
        ["Operational Support and Procurement Services", "1", "50000.00", "50000.00"]
    ]
    generate_invoice_table(story, headers, rows, styles)
    
    story.append(Paragraph("<b>Billing Summary:</b>", styles["section"]))
    story.append(Paragraph("Subtotal: INR 50,000.00", styles["body"]))
    story.append(Paragraph("Liquidated Damages / Penalty Applied: INR 0.00", styles["body"]))
    story.append(Paragraph("<b>Total Stated Amount Due: INR 50,000.00</b>", styles["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Delivery of procurement items was delayed by 3 weeks due to logistical challenges. No penalty has been applied to this invoice.</i>", styles["body"]))
    
    create_pdf(filename, story)
    print(f"Generated invoice PDF at {filename}")

if __name__ == "__main__":
    build_ippb_invoice()

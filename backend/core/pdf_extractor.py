"""
ProcureAI - File Summary

What it does:
Extracts text from PDF documents using pdfplumber with a pypdf fallback.

What it means:
The document digestion layer converting uploaded contracts and invoices to raw text.

Importance in Project:
High. Ground-zero for ingestion; failures here prevent any downstream parsing or analysis.
"""

import os
import pypdf
import pdfplumber
import structlog

logger = structlog.get_logger()

def extract_pdf_text(file_path: str) -> str:
    """
    Extracts text from a PDF file using pdfplumber as the primary extractor
    and falling back to pypdf.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at {file_path}")
        
    text_content = []
    
    # Try pdfplumber first
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
                else:
                    logger.warning("Empty page or image-only page detected with pdfplumber", file=file_path, page=page_num)
    except Exception as e:
        logger.error("pdfplumber extraction failed, falling back to pypdf", error=str(e), file=file_path)
        text_content = []
        
    # If pdfplumber failed or extracted nothing, try pypdf
    if not text_content:
        try:
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for page_num, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
        except Exception as e:
            logger.error("pypdf extraction failed", error=str(e), file=file_path)
            raise RuntimeError(f"Could not extract text from {os.path.basename(file_path)}. Ensure PDF is not scanned-only or corrupted.") from e
            
    final_text = "\n\n--- PAGE BREAK ---\n\n".join(text_content).strip()
    if not final_text:
        raise RuntimeError(f"Could not extract text from {os.path.basename(file_path)}. Ensure PDF is not scanned-only.")
        
    return final_text

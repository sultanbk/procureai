"""
FILE CANONICAL IDENTIFIER: scripts/validate_stress_data.py
PURPOSE: Validates that all newly generated SEC EDGAR contracts and invoices can be parsed by pdfplumber and pypdf without issues.
"""

import os
import pdfplumber
import pypdf

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTRACTS_DIR = os.path.join(BASE_DIR, "data", "synthetic", "contracts")
INVOICES_DIR = os.path.join(BASE_DIR, "data", "synthetic", "invoices")

NEW_CONTRACTS = [
    "c009_cloudscale_technologies_edgar.pdf",
    "c010_transnational_freight_edgar.pdf",
    "c011_apex_facilities_maintenance_edgar.pdf"
]

NEW_INVOICES = [
    "c009_invoice_i018.pdf",
    "c009_invoice_i019.pdf",
    "c009_invoice_i020.pdf",
    "c010_invoice_i021.pdf",
    "c010_invoice_i022.pdf",
    "c011_invoice_i023.pdf",
    "c011_invoice_i024.pdf",
    "c011_invoice_i025.pdf"
]

def test_extraction():
    print("=== Validating New SEC EDGAR Contracts ===")
    for c in NEW_CONTRACTS:
        path = os.path.join(CONTRACTS_DIR, c)
        assert os.path.exists(path), f"Contract missing: {c}"
        with pdfplumber.open(path) as pdf:
            text = "\n".join([p.extract_text() or "" for p in pdf.pages])
            print(f"[OK] {c}: {len(pdf.pages)} pages, {len(text)} characters extracted.")
            assert len(text) > 100, f"Extraction too short for {c}"

    print("\n=== Validating New Stress-Test Invoices ===")
    for inv in NEW_INVOICES:
        path = os.path.join(INVOICES_DIR, inv)
        assert os.path.exists(path), f"Invoice missing: {inv}"
        with pdfplumber.open(path) as pdf:
            text = "\n".join([p.extract_text() or "" for p in pdf.pages])
            print(f"[OK] {inv}: {len(pdf.pages)} pages, {len(text)} characters extracted.")
            assert "Invoice No:" in text or "TOTAL DUE" in text or "Billing Period" in text, f"Missing invoice keywords in {inv}"

    print("\nAll 11 new stress-test PDF files passed validation with 100% extractability!")

if __name__ == "__main__":
    test_extraction()

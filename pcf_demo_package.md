# Sysco Supplier Demo Package - Premium Cold Foods, Inc.

This document contains the complete details and verification for the **Premium Cold Foods, Inc.** (Supplier) and **Sysco Corporation** (Client/Buyer) demo package. 

---

## 1. Demo Data Overview

### A. Contract Document
* **Supplier Name**: `Premium Cold Foods, Inc.`
* **Client / Buyer**: `Sysco Corporation`
* **Contract Ref**: `CTR-SYSCO-PCF-2026-002`
* **Length**: 18 pages (satisfying the 15+ pages requirement).
* **Location**: [c008_premium_cold_foods_contract.pdf](file:///d:/SupplierGuard/data/synthetic/contracts/c008_premium_cold_foods_contract.pdf)
* **Key Pricing Rules & SLAs**:
  * **Rule R004 (Flat Rate)**: Standard produce boxes at flat rate USD 4.50 per box.
  * **Rule R005 (Flat Rate)**: Standard frozen food cases at flat rate USD 5.80 per case.
  * **Rule R006 (Monthly Cap)**: Fuel surcharges capped at USD 2,000.00 per single monthly billing cycle.
  * **Rule R007 (Volume Tiers)**: If monthly Frozen Food cases exceed 10,000 cases, a discounted rate of USD 5.00 per case applies to all Frozen Food cases in that month.
  * **Rule R008 (SLA Penalty)**: 8% credit of the month's total invoice amount if temperature compliance falls below 98.0%.
  * **Rule R009 (Milestone Penalty)**: USD 1,500.00 per day penalty if the 'Mid-West Cold Chain Integration' milestone is delayed beyond November 1, 2026.
  * **Rule R011 (Prompt Payment Discount)**: 3.0% discount on standard produce box charges if paid within 12 days.

### B. Invoices
* **Location**: [data/synthetic/invoices/](file:///d:/SupplierGuard/data/synthetic/invoices/)
* **Invoice 1: `INV-PCF-202611` (November 2026)**
  * Standard Produce Boxes: 12,000 boxes @ USD 4.50
  * Fuel Surcharge: Charged USD 2,500.00 (Exceeds contract cap of USD 2,000.00)
  * **Intentional Compliance Leak**: USD 500.00 overcharge.
* **Invoice 2: `INV-PCF-202612` (December 2026)**
  * Standard Produce Boxes: 8,000 boxes @ USD 4.50 = USD 36,000.00
  * Frozen Food cases: 11,500 cases @ USD 5.80 = USD 66,700.00 (Should be USD 5.00 under volume discount since 11,500 > 10,000).
  * **Intentional Compliance Leaks**:
    * Frozen food volume tier overcharge: 11,500 * (5.80 - 5.00) = USD 9,200.00 overcharge.
    * SLA violation: Temperature compliance rate was 96.5% (below 98.0%). Triggers 8% credit of total invoice amount: 8% of (36000 + 66700 + 1500) = **USD 8,336.00 penalty**.
    * Milestone Delay: Mid-West integration completed on November 5, 2026 (4 days delayed from Nov 1). Triggers 4 days * USD 1,500.00/day = **USD 6,000.00 penalty**.
* **Invoice 3: `INV-PCF-202701` (January 2027)**
  * Standard Produce Boxes: 9,000 boxes @ USD 4.50 = USD 40,500.00
  * Paid within 9 days of invoice date (eligible for prompt discount).
  * **Intentional Compliance Leak**: 3% prompt discount not applied: 3% of 40,500 = **USD 1,215.00 overcharge**.

---

## 2. Verification & Audit Results

The compliance audit successfully processes these documents and flags **USD 16,051.00** in total leakage:

| Invoice ID | Discrepancy Type | Rule ID | Billed (USD) | Expected (USD) | Delta / Leakage (USD) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `INV-PCF-202611` | Fuel Cap Overcharge | `R006` | 2,500.00 | 2,000.00 | **-500.00** (Overcharge) |
| `INV-PCF-202612` | Milestone Delay Penalty | `R009` | 0.00 | -6,000.00 | **-6,000.00** (Unapplied penalty) |
| `INV-PCF-202612` | Temperature SLA Penalty | `R007` | 0.00 | -8,336.00 | **-8,336.00** (Unapplied penalty) |
| `INV-PCF-202701` | Missed Prompt Discount | `R011` | 40,500.00 | 39,285.00 | **-1,215.00** (Needs Review) |
| **Total** | | | | | **-16,051.00** |

---

## 3. Portal Screenshots & Walkthrough Video

Below is the verification documentation showing the Premium Cold Foods audit results in the portal:

### A. Contract Library Page
Shows the contract registered under the **PARSED** status:
![Contract Library Page](/C:/Users/tipusultan.bk/.gemini/antigravity-ide/brain/f1993cac-3a4c-470b-9278-73694f58c32e/contract_library_filtered_1782231651468.png)

### B. Audit History Page
Shows the completed audit run (`aud_sysco_supplier_test_run`) with USD 16,051.00 leakage:
![Audit History Page](/C:/Users/tipusultan.bk/.gemini/antigravity-ide/brain/f1993cac-3a4c-470b-9278-73694f58c32e/audits_list_1782231495759.png)

### C. Detailed Audit Report Page
Shows the detailed findings list:
![Detailed Audit Report Page](/C:/Users/tipusultan.bk/.gemini/antigravity-ide/brain/f1993cac-3a4c-470b-9278-73694f58c32e/detailed_audit_report_1782231574672.png)

### D. Walkthrough Video
Here is the recorded video session showing the walkthrough of this second demo package:
![Portal Walkthrough Video](/C:/Users/tipusultan.bk/.gemini/antigravity-ide/brain/f1993cac-3a4c-470b-9278-73694f58c32e/pcf_demo_flow_1782231434126.webp)

# The Invoice Extractor Agent: A Guide for Beginners

Imagine you are hired to be a detective, but instead of solving crimes, your job is to read bills from different companies and write down exactly what they are charging you for. You have to be super careful to write down every detail, check their math, and organize it so your boss can understand it.

That is exactly what the **Invoice Extractor** agent does in the SupplierGuard system!

---

## 📚 Important Definitions

Before we dive into what the agent does, let's learn a few important terms:

> [!NOTE]
> **Invoice:** A document (like a receipt or a bill) that a supplier sends you when they want to get paid for goods or services they provided.
> 
> **Line Item:** A single row on an invoice that describes one specific thing you are being charged for. An invoice is usually just a list of line items added together.
> 
> **Quantity:** How many of that item you bought (e.g., 50 bags of cement, or 10 hours of work).
> 
> **Unit Price (Rate):** How much *one* single item or hour costs.
> 
> **Line Total:** The total cost for that specific row (`Quantity` multiplied by `Unit Price`).

### Example of an Invoice:
| Item Description (Line Item) | Quantity | Unit Price | Line Total |
| :--- | :--- | :--- | :--- |
| Excavation Work | 100 cubic meters | $500 | $50,000 |
| Cement Bags | 50 bags | $400 | $20,000 |

*(Total Amount Due: $70,000)*

---

## 🤖 What does the Invoice Extractor Agent do?

The Invoice Extractor is an AI-powered reader. It looks at a messy PDF invoice and turns it into neat, structured data that a computer can process. It follows a strict 3-step process:

### Step 1: Extract the "Header" Information
First, it reads the top of the invoice to answer the basic questions:
* **Who sent this?** (`supplier_name`)
* **What is the bill number?** (`invoice_id`)
* **When was it sent?** (`invoice_date`)
* **What time period is this for?** (`billing_period` — e.g., "October 2024")
* **What is the grand total they want us to pay?** (`invoice_total`)

### Step 2: Extract the Line Items (The Details)
Next, it goes through the main table of the invoice row by row. For every single **line item**, the agent creates a digital record with an ID (like `L001`, `L002`).

It captures:
* What exactly the supplier is billing for (`description`)
* How many they provided (`quantity`)
* The cost of each one (`unit_price`)
* The total cost for that row (`line_total`)

It also looks for secret clues! Sometimes suppliers hide performance metrics in the line items. For example, if a line item says "Server Maintenance - Uptime 99.5%", the agent is smart enough to extract `99.5%` and save it as an `SLA` (Service Level Agreement) score.

### Step 3: Check the Math! 🧮
Suppliers are humans, and humans make math mistakes. Sometimes they try to charge you $70,000 when the line items only add up to $60,000! 

The Invoice Extractor uses a pure Python calculator to deterministically check the math. It does not trust the AI to do math.
1. It multiplies `Quantity` × `Unit Price` for every single line item to make sure it equals the `Line Total`.
2. It adds up all the `Line Totals` to make sure they match the `Grand Total` at the bottom of the invoice.

If the math is wrong, the agent throws a **red flag** and lowers its confidence score, warning the rest of the system that the invoice has calculation errors.

### Step 4: Extract the Notes and Footers
Finally, it reads the fine print at the bottom of the invoice. Sometimes a supplier writes things like:
* *"Milestone 1 completed on Oct 25th."*
* *"We deducted $5,000 because we were late."*

The agent grabs these notes and saves them so the rest of the system can verify if the supplier is telling the truth according to the contract.

---

## 🎯 The Final Output

Once the agent is done, it takes all this messy PDF text and bundles it up into a clean, digital package called `InvoiceData`. 

This clean package is then handed over to the next agent (the **Compliance Checker**), which compares the extracted invoice against the extracted contract rules to find any overcharges or missing penalties!

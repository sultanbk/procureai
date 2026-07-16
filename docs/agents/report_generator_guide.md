# The Report Generator: A Guide for Beginners

Imagine going to a doctor who runs 100 complex blood tests on you. You don't want the doctor to just hand you 50 pages of raw spreadsheets filled with numbers and chemical names. You want them to sit down and give you a simple, well-formatted summary: *"Here is what is healthy, here is what is wrong, and here is what you need to do next."*

That is exactly what the **Report Generator** does in SupplierGuard!

---

## 📚 Important Definitions

> [!NOTE]
> **Audit:** An official inspection of financial accounts or bills to make sure everything is accurate and honest.
> 
> **Leakage:** The total amount of money a company lost because a supplier overcharged them or forgot to apply a discount.
> 
> **Severity:** How bad a mistake is. A $5 mistake might be "Low Severity," while a $50,000 mistake is "Critical."

---

## 🤖 What does the Report Generator do?

The Report Generator is the final step (Node 5) in the SupplierGuard pipeline. By the time the data reaches this agent, all the hard work (reading the contract, doing the math, finding the discrepancies) is already finished. 

The Report Generator's job is purely about **communication and presentation**.

### Step 1: Gathering the Findings
It takes the massive pile of data from the previous agents, including:
* The total amount of money leaked.
* The list of compliant (correct) lines.
* The list of Discrepancies (mistakes/overcharges).
* Any "Needs Human Review" flags.
* Any errors or missing data alerts.

### Step 2: Categorization and Sorting
Nobody wants to read a random, disorganized list of mistakes. The Report Generator acts as a smart editor. It groups the discrepancies into categories:
1. **Critical Issues:** Massive overcharges that need immediate attention.
2. **Medium/Low Issues:** Smaller math errors or slight rate discrepancies.
3. **Missing Data/Information:** Areas where the audit couldn't be completed because the supplier didn't provide enough information on the invoice.

### Step 3: Writing the Executive Summary
The AI acts as a professional financial consultant. It writes a top-level **Executive Summary** aimed at managers and executives. This summary highlights the total financial impact, the general health of the invoice, and the major reasons for the leakages.

### Step 4: Formatting the Output
Finally, it packages all of this information into a beautiful, easy-to-read format (like HTML or Markdown). It creates clean tables, bolded headings, and bullet points so that human auditors can easily copy-paste the report into an email and send it straight to the supplier to demand their money back!

---

## 🎯 The Final Output

The final output is the **Audit Report**. It is the polished, final product of the entire SupplierGuard system. Once this report is generated, the pipeline successfully ends, and the human team takes over to recover the funds!

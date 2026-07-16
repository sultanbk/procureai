# SupplierGuard — Problem Statement
# WHO THIS FILE IS FOR: AI code assistants working on this project.
# PURPOSE: Understand the business problem deeply before touching any code.
# This file is intentionally non-technical. No schemas, no code, no architecture.
# Read this first. Understand what we are trying to solve. Then read ARCHITECTURE.md.

---

## The Short Version

Large companies sign complex legal agreements with their suppliers that
contain detailed pricing rules. Every month, suppliers send invoices (bills)
to get paid. Nobody checks whether those bills match what the contract
actually says. Money quietly leaks out — sometimes millions of rupees —
because the overcharges are subtle, the contracts are long, and the
accounts payable team is too busy to cross-check every line item against
a 60-page legal document.

SupplierGuard reads both documents and finds every discrepancy, automatically.

---

## Who Are the People in This Story?

### The Buying Company (the Client)
A large enterprise — a manufacturer, a hospital network, a utility company,
a retail chain. They buy goods and services from many suppliers. They have
a procurement team that negotiates contracts and an accounts payable (AP)
team that pays the bills.

The procurement team is small and strategic — they negotiate deals.
The AP team is operational — they process invoices as fast as possible.
These two teams rarely communicate about specific invoice line items.

### The Supplier
A company that provides goods or services — logistics, construction,
software, raw materials, healthcare products, cloud infrastructure.
They send invoices every month (or quarter, or after milestones).
Some suppliers make honest billing errors. Some suppliers systematically
overcharge, knowing nobody checks carefully.

### The Finance Director / CFO
Wants to know: how much are we spending with suppliers, and are we
getting what we paid for? Currently has no visibility into whether
invoices match contract terms. Gets a total spend number, not a
compliance number.

---

## What Is a Supplier Contract?

When a company decides to buy something significant from a supplier,
they do not just shake hands and agree on a price. They sign a formal
legal agreement — usually called a Master Services Agreement (MSA),
a Procurement Contract, or a Service Level Agreement (SLA).

These documents are long. Typically 30 to 100 pages. They are written
by lawyers. They contain highly specific rules about:

- How much the supplier charges for each unit of goods or service
- How the price changes based on volume (buy more, pay less per unit)
- What happens if the supplier delivers late or performs poorly
- Whether the client gets a discount for paying early
- What the maximum chargeable amount is for any given item
- What credits or penalties apply under specific conditions

These rules are not simple. They are conditional. They refer to other
sections of the document. They have thresholds and tiers and exceptions.

The contract exists to protect the buying company. But if nobody reads it
when the invoice arrives, it protects nobody.

---

## What Is an Invoice?

An invoice is the bill the supplier sends when they want to get paid.
It lists what was provided, how much of it, at what price, for what period.

A typical invoice looks like this:

```
INVOICE — Apex Logistics Ltd
Invoice No: INV-APX-NOV-2024
Billing Period: October 2024

Description                    Qty    Rate (INR)    Total (INR)
------------------------------------------------------------
Domestic Freight — Standard   1,240     12.50        15,500.00
Express Handling Fee             18    850.00        15,300.00
Fuel Surcharge                    1  4,200.00         4,200.00
------------------------------------------------------------
TOTAL DUE:                                           35,000.00
```

The accounts payable team receives this invoice. They check:
- Does the total arithmetic add up? (15,500 + 15,300 + 4,200 = 35,000 ✓)
- Is this from a vendor we work with? Yes.
- Is the amount roughly what we expect? More or less.
- Approve and pay.

What they do NOT check:
- What does the contract say the rate for "Domestic Freight — Standard" should be?
- Does 1,240 units cross a volume threshold that triggers a lower price?
- Was the fuel surcharge rate within the contractually capped limit?

They do not check these things because it would take 30–40 minutes per invoice
to find the right contract, locate the right clause, and do the calculation.
A mid-size enterprise processes 3,000 to 10,000 invoices per month.
Doing this manually is not humanly possible.

---

## Concrete Example 1 — Volume Discount Not Applied

### The Contract Says:

Section 4.2 of the Apex Logistics MSA:

> "For monthly domestic freight shipments of 0 to 499 units, the applicable
> unit rate shall be INR 14.00. For monthly shipments of 500 to 1,999 units,
> the applicable unit rate shall be INR 11.50. For monthly shipments of 2,000
> units and above, the applicable unit rate shall be INR 9.80."

This is called a volume tier. The more you ship, the less you pay per unit.
This is a discount the company EARNED by committing to high volumes.

### The Invoice Says:

1,240 units × INR 12.50 per unit = INR 15,500.00

### What Actually Should Have Happened:

1,240 units falls in the 500–1,999 tier.
The correct rate is INR 11.50, not INR 12.50.
Correct charge: 1,240 × 11.50 = INR 14,260.00

### The Overcharge:

INR 15,500 − INR 14,260 = INR 1,240 on this single invoice.

Over 12 months, if this happens every month at similar volumes,
that is roughly INR 14,880 lost — from one clause, one supplier.
A company with 50 active supplier contracts can have dozens of these.

### Why Nobody Caught It:

The AP team saw that 1,240 × 12.50 = 15,500 and the arithmetic was correct.
The invoice looked fine. Nobody knew to check whether 1,240 units crossed
the threshold for a lower tier rate. Nobody had the contract open.

---

## Concrete Example 2 — SLA Penalty Credit Not Applied

### The Contract Says:

Section 8.1 of the Apex Logistics MSA:

> "Should the Supplier's on-time delivery rate fall below 97% in any
> calendar month, the Supplier shall issue a credit equal to 12% of
> that month's total invoice value to the Client. This credit shall
> appear as a line item on the following month's invoice."

This is called an SLA penalty clause. If the supplier performs poorly,
the client gets money back. This protects the client from poor service.

### What Actually Happened:

In October, Apex Logistics delivered 94.2% of shipments on time.
94.2% is below the 97% threshold. A credit should have been issued.

12% of October's invoice (INR 35,000) = INR 4,200 credit owed.

### The November Invoice Says:

No credit appears. The invoice for November shows full charges with
a note: "SLA/Service Credits Applied: INR 0.00."

### The Hidden Loss:

INR 4,200 that the company was contractually owed — never received.

The procurement team negotiated this penalty clause specifically to
create accountability. But if nobody tracks actual delivery performance
against the 97% threshold each month, the clause is worthless.

---

## Concrete Example 3 — Cap Rate Exceeded

### The Contract Says:

Section 7.2 of a Construction Services Agreement:

> "The cost for Cement bags supplied for construction shall be billed
> at actual supplier cost plus a 10% markup, subject to an absolute
> maximum cap of INR 400.00 per bag. Under no circumstances shall the
> billed rate per bag exceed INR 400.00."

This cap protects the client from price inflation in raw materials.
No matter what cement costs on the market, the supplier cannot charge
more than INR 400 per bag.

### The Invoice Says:

Cement Supply — 200 bags × INR 450.00 = INR 90,000.00

### What Should Have Happened:

Maximum allowable rate: INR 400.00 per bag.
Correct charge: 200 × 400.00 = INR 80,000.00

### The Overcharge:

INR 90,000 − INR 80,000 = INR 10,000 on this single invoice.

If the company orders cement from this supplier every month,
this overcharge compounds to INR 1,20,000 per year —
from one capped item, whose cap the supplier simply ignored.

---

## Concrete Example 4 — Early Payment Discount Not Reflected

### The Contract Says:

Section 12.4 of the Apex Logistics MSA:

> "A discount of 2% shall apply to any invoice settled within 10
> business days of the invoice date. This discount shall be deducted
> from the total invoice value at the time of payment."

The company pays their invoices within 5 business days as a policy.
They have always done this. They ALWAYS qualify for this 2% discount.

### The Invoice Says:

Total Due: INR 35,000.00
Early Payment Discount: Not mentioned.

### What Should Have Happened:

2% of INR 35,000 = INR 700 discount.
Amount payable: INR 34,300.

### The Hidden Loss:

The company pays INR 35,000. Every month. For years.
INR 700 × 12 months = INR 8,400 per year — from one clause.
Multiplied across 20 suppliers with similar clauses = significant money.

The discount exists in the contract. The company qualifies every time.
But because AP pays the stated amount without cross-referencing Clause 12.4,
the discount is never taken.

---

## Concrete Example 5 — The Milestone Penalty Problem

### The Contract Says:

Section 5.3 of a Construction Services Agreement:

> "If the project milestone designated 'Foundation Completion' is delayed
> beyond the agreed target date of October 15, 2024, the Supplier shall
> credit the Client a delay penalty of INR 5,000.00 per calendar day
> of delay."

### The November Invoice Says:

General Construction Services — 1 × INR 1,20,000.00
SLA/Milestone Penalties Applied: INR 0.00

### The Critical Question:

Was the Foundation Completion milestone actually delayed beyond October 15?

The contract says IF delayed THEN penalty. But the invoice itself says
no penalties were applied. Whether this is correct depends entirely on
whether the milestone was actually delayed — information that lives
outside both documents, in a project management system or site log.

### Why This Is Genuinely Different From the Other Examples:

Examples 1–4 can be verified using only the contract and the invoice.
The rate is either correct or it is not. The cap was either respected or it was not.

Example 5 cannot be verified from documents alone. You need to know the actual
milestone completion date. If Foundation Completion happened on October 10,
the supplier was on time and no penalty applies — and the invoice is correct.
If it happened on October 22, the supplier was 7 days late and a credit of
INR 35,000 (7 × 5,000) should have been applied.

This distinction is fundamental to how SupplierGuard works:

DOCUMENT-RESOLVABLE RULES: Can be verified from the contract + invoice alone.
  Volume tiers, flat rates, cap rates, bundle discounts, early payment discounts.
  → SupplierGuard can produce a definitive finding.

EXTERNALLY-DEPENDENT RULES: Require real-world data not in the documents.
  SLA performance metrics, milestone completion dates, delivery records.
  → SupplierGuard flags the clause and asks for the data. It never invents the answer.

This is the most important thing SupplierGuard must understand:
NEVER produce a financial finding for an externally-dependent rule
without the external data to support it. A wrong finding is worse than
no finding — it damages trust in the entire system.

---

## How Big Is This Problem Really?

Industry research is consistent:

- Enterprises lose 6–12% of total procurement spend to contract leakage
- A company spending INR 500 crore annually with suppliers loses INR 30–60 crore
- Most large enterprises have 200–500 active supplier contracts
- AP teams process 3,000–10,000 invoices per month
- Less than 5% of invoices are ever cross-checked against contract terms

The leakage is not usually dramatic. It is not one massive fraud. It is
hundreds of small discrepancies across many suppliers over many months —
each one individually below the threshold of anyone's attention, but
collectively enormous.

A supplier consistently charging INR 1.00 per unit above the Tier 2 rate,
on 2,000 units per month, for 18 months, with nobody noticing: INR 36,000.

Across 50 suppliers with similar patterns: INR 18,00,000 per year.
Quietly. Without anyone doing anything deliberately wrong.
Just because nobody reads the contract when the invoice arrives.

---

## What SupplierGuard Does

SupplierGuard reads both documents — the contract and the invoice —
and produces a precise audit report answering the question:

"Does every line on this invoice match what the contract says it should be?"

For every line item on every invoice, it:
1. Identifies which contract clause governs that line item
2. Determines what the correct charge should be under that clause
3. Compares the correct charge to what was actually billed
4. If there is a discrepancy, reports it with the exact clause text,
   the exact arithmetic, and a recommendation (dispute / escalate / monitor)

The output is not "this invoice looks wrong." The output is:

> "Line L002 — Cement Supply — 200 bags × INR 450.00 = INR 90,000.00 charged.
> Contract Section 7.2 specifies a maximum cap of INR 400.00 per bag.
> Quoted clause: 'Under no circumstances shall the billed rate per bag exceed
> INR 400.00.'
> Expected charge: 200 × INR 400.00 = INR 80,000.00.
> Overcharge: INR 10,000.00.
> Recommendation: DISPUTE — Request credit note for INR 10,000."

A procurement manager can take that output and send a dispute letter to the
supplier immediately. No further research needed. The evidence is complete.

---

## What SupplierGuard Does NOT Do

Understanding the boundaries is as important as understanding the capability.

**SupplierGuard does not make assumptions about real-world events.**
If a contract says "penalty if delivered late" and the invoice says "no
penalties applied," SupplierGuard does not guess whether there was a delay.
It flags the clause and requests the actual delivery data. Guessing is wrong.

**SupplierGuard does not make legal interpretations.**
If a contract clause is ambiguous — if two reasonable readings lead to
different financial outcomes — SupplierGuard flags it for human review.
It does not pick an interpretation. That is legal territory.

**SupplierGuard does not replace a contract analyst.**
It handles the 80% of cases that are clear-cut and deterministic, freeing
the analyst to focus on the 20% that require judgment, negotiation, or
legal interpretation.

**SupplierGuard does not handle verbal agreements or email negotiations.**
It only works from the signed written contract. Side agreements, email
commitments, and informal adjustments are outside its scope unless they
appear as formal contract amendments in writing.

---

## The Most Common Mistakes That SupplierGuard Must Never Make

### Mistake 1 — Inventing a finding without evidence
The system must never report a discrepancy it cannot prove from the documents.
"The supplier probably should have applied an SLA credit" is not a finding.
"The invoice shows on-time delivery was 94.2% and the contract says credit
applies below 97%, therefore credit of INR X is owed" is a finding.

### Mistake 2 — Wrong unit for a cap
"Maximum INR 400 per bag" means each individual bag cannot exceed INR 400.
It does NOT mean the total for all bags combined cannot exceed INR 400.
200 bags at INR 400 each = INR 80,000 maximum total. Not INR 400 total.
This sounds obvious. It is the source of one of the most critical bugs in
the system's history. Always check whether a cap is per-unit or total.

### Mistake 3 — Marking a line as both compliant and disputed
A line item either has a finding or it does not. The compliance score
is derived from the number of lines that have no findings. A system that
reports "100% compliant, 2 disputes" has a broken logic layer.

### Mistake 4 — Ignoring the invoice's own statements
Invoices often contain explicit notes: "Foundation milestone achieved
on-time," or "SLA penalties: INR 0 applied." These statements are
evidence. They must be read and factored into the analysis.
An invoice that explicitly says "no delays" cannot have a delay penalty
finding raised against it — unless external data contradicts the statement.

### Mistake 5 — Mapping a vague line item to a penalty clause with low confidence
"General Construction Services" is not the same as "Foundation Completion
Milestone." If a line item's description is vague and the connection to a
specific contract clause is uncertain, that uncertainty must be reported
as uncertainty — not converted into a CRITICAL finding.

---

## How to Think About Confidence

Every finding SupplierGuard produces has a confidence level. Think of it
like a dial from 0% to 100%.

100% confidence: The contract says rate = INR 450/unit for Tier 2.
The invoice charges INR 500/unit. Quantity = 120. This is Tier 2 (101–500).
Overcharge = INR 50 × 120 = INR 6,000. Nothing to interpret. Pure math.

75% confidence: The invoice line says "Logistics Services — Priority."
The contract has a "Priority Shipment" rate of INR 1,200/delivery.
The match is likely correct but the description isn't identical.
Report the finding with a note that the mapping is semantically inferred.

Below 60% confidence: "General Construction Services" might relate to
any of three contract clauses. The mapping is too uncertain.
Report as "Uncertain — requires manual review." Create no financial finding.

The system should always prefer "I am not sure" over "I invented an answer."

---

## The Story That Motivates Every Design Decision

Imagine a procurement analyst named Priya. She manages 45 supplier contracts.
Every month she receives 300+ invoices. She has 8 working hours a day.
Checking one invoice against one contract takes 30–45 minutes when done properly.

She can check roughly 10–12 invoices per day properly. That is 240 per month.
She receives 300+. Even if she worked every minute on nothing else,
she could not check them all.

So she checks the ones that look suspicious. The ones with unusual amounts.
The ones from suppliers she doesn't trust. The obvious ones.

The subtle ones — the volume tier that was off by one tier,
the fuel surcharge that exceeded the cap by 3%, the SLA credit that was
never issued — these never get checked. Not because Priya doesn't care.
Because there are not enough hours.

SupplierGuard gives Priya her time back. It checks every single invoice,
every single line item, against every applicable contract clause, in under
2 minutes. It gives her a ranked list of what to dispute, with the evidence
already assembled.

She spends her time acting on findings — not hunting for them.

That is the problem SupplierGuard solves. That is what every feature,
every agent, every schema, and every test case is ultimately in service of.

---

## Glossary (for AI assistants unfamiliar with procurement terminology)

**MSA (Master Services Agreement):** The main legal contract between a
buyer and supplier. Defines all terms, pricing, SLAs, and penalties.

**Invoice:** The bill the supplier sends requesting payment.

**Line item:** A single row on an invoice — one product or service,
with quantity, rate, and total.

**Volume tier:** A pricing structure where the rate per unit decreases
as quantity increases. Common in logistics, manufacturing, SaaS.

**SLA (Service Level Agreement):** The performance standard the supplier
must maintain. Breaching the SLA triggers penalties or credits.

**Cap rate:** A contractually defined maximum price per unit. The supplier
cannot bill above this regardless of actual cost.

**Leakage:** Money that should have stayed with the buying company but
flowed to the supplier due to billing errors, unapplied discounts,
or missed penalty credits. Not fraud — just unverified invoices.

**Dispute:** A formal communication to the supplier saying "this invoice
is incorrect, here is why, here is what you owe us."

**Credit note:** A document the supplier issues reducing the amount owed.
The resolution to a successfully disputed finding.

**AP (Accounts Payable):** The team inside the buying company responsible
for receiving invoices and making payments.

**Procurement:** The team responsible for negotiating contracts and
managing supplier relationships.

**Compliance score:** A measure (0–100) of how well a supplier's invoices
match their contract terms across all audits. 100 = every line correct.
0 = every line has a discrepancy.

**DataRequiredFlag:** When SupplierGuard detects a contract clause that
could apply but cannot be verified without external data (actual delivery
performance, milestone dates), it raises a flag instead of a finding.
The flag says: "This clause exists. We need this specific information
to determine whether a discrepancy occurred."

---

END OF PROBLEM STATEMENT
Read ARCHITECTURE.md next to understand how SupplierGuard solves this problem technically.

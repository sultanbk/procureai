# The Compliance Checker: A Guide for Beginners

If the Invoice Extractor and Contract Parser are the researchers, and the Cross-Validator is the bouncer, then the **Compliance Checker** is the judge and jury. 

This is the core "brain" of the SupplierGuard system. Its job is to take the rules and the invoice, do the math, and officially declare whether the supplier is overcharging you.

---

## 📚 Important Definitions

> [!NOTE]
> **Discrepancy:** A fancy word for "leakage" or a "mistake." It means the amount the supplier charged does not match what the contract says they are allowed to charge.
> 
> **Delta:** The mathematical difference between two numbers. If the expected cost is $50, but the charged cost is $60, the Delta is -$10 (an overcharge).
> 
> **Compliant:** Following the rules perfectly.

---

## 🤖 What does the Compliance Checker do?

The Compliance Checker handles the most complex tasks in the pipeline. It combines AI intelligence with strict calculator math.

### Step 1: The Final Mapping (Connecting the Dots)
Thanks to the *Cross-Validator*, the Compliance Checker receives a short list of possible rules for every invoice line. It uses AI to look at the exact context and make a final, official decision: *"Line Item 1 is officially governed by Contract Rule #4."*

### Step 2: The Math Engine (The Rule Evaluator)
Once it knows which rule applies, it completely turns off the AI and uses a pure Python math calculator. 

It looks at the contract rule (e.g., *"Volume Tier: If over 100 bags, charge $400 each"*). Then it looks at the invoice quantity (e.g., *150 bags*). The Python engine calculates the **Expected Total** ($60,000). 

It then subtracts the **Charged Total** on the invoice from the **Expected Total**.
* If the difference is zero, the line is marked **Compliant**.
* If the difference is massive, it generates a **Discrepancy** (a leakage alert).

### Step 3: Checking Whole-Invoice Penalties
Not all rules apply to a single row on an invoice. Sometimes, a contract says, *"If the project is delivered late, the supplier owes us $5,000."* 

The Compliance Checker creates a "Dummy Line" to evaluate this rule against the whole invoice. It calculates how much the supplier *should* have deducted as a penalty. If the supplier didn't deduct it from the grand total, the agent catches it as an **"Unapplied Penalty."**

### Step 4: The AI "Critic" (The Second Opinion)
Before officially declaring a discrepancy, the agent asks an internal AI "Critic" to double-check its work. 

The Critic reads the plain English text of the contract, looks at the math the Python engine did, and says either:
* **"CONFIRMED"** (Yes, this math makes logical sense based on the English words).
* **"NEEDS HUMAN REVIEW"** (Wait, the English is a bit ambiguous. Let's flag this for a human auditor to double-check).

---

## 🎯 The Final Output

The Compliance Checker produces the master **Discrepancy List**. This is a detailed log showing exactly where the supplier overcharged, by how much, and exactly which contract rule they broke to do it!

# The Contract Parser Agent: A Guide for Beginners

Imagine playing a complicated board game where the rulebook is 50 pages long. Before you can check if a player is cheating, you first need to read the entire rulebook and write down every single rule about how points are scored or lost.

That is exactly what the **Contract Parser** agent does in SupplierGuard!

---

## 📚 Important Definitions

> [!NOTE]
> **Contract:** A legal agreement between a company and a supplier. It dictates what the supplier is supposed to do and how much they are allowed to charge for it.
> 
> **Pricing Rule:** A specific instruction in the contract about money. For example: "If they buy more than 100 laptops, they get a 10% discount."
> 
> **Penalty (Credit):** A rule that says the supplier must give money *back* to the company if they fail to do their job properly (e.g., if a project is delivered 5 days late).

---

## 🤖 What does the Contract Parser Agent do?

While the *Invoice Extractor* is reading the bill, the **Contract Parser** is reading the actual legal contract. Its job is to find every single rule about money and extract it into a neat, organized list.

It follows a very thorough process:

### Step 1: The Full Read-Through
Unlike some basic AI tools that only look up rules when asked, this agent reads the **entire contract** from top to bottom. It breaks the long document into small chunks and reads every single section.

Why read the whole thing? Because if a supplier was supposed to give you a discount or a penalty, but they *forgot* to put it on the invoice, the only way to catch them is if the AI knows that the rule exists! If the AI only searched for things already on the invoice, it would be blind to omissions.

### Step 2: Categorize the Rules
When it finds a sentence about money, it doesn't just copy it. It categorizes it into specific rule types:
* **Flat Rate:** "Laptops cost $1,000 each."
* **Volume Tier:** "The first 50 laptops cost $1,000, but any laptops after 50 cost $900."
* **SLA Penalty:** "If the server goes down for more than 1 hour, the supplier owes us 5% of the total bill."
* **Milestone Penalty:** "If the foundation isn't built by October 15th, they owe us $5,000 per day."
* **Cap Rate:** "They can charge us for travel, but it cannot exceed $500."

### Step 3: Extract the Details
For every rule it finds, the agent writes down:
1. **Rule ID:** A unique tag (like `R001`).
2. **Clause Text:** The *exact* legal quote copied straight from the contract.
3. **Applies To:** What item or service this rule governs.
4. **The Math:** The exact limits, prices, and percentages involved.

### Step 4: The Hallucination Check! 🕵️‍♂️
AI models sometimes invent things (called "hallucinating"). To prevent the AI from making up a fake rule, the system runs a strict **Python check**. 

It takes the exact legal quote the AI extracted and searches the original PDF to see if those words actually exist. If it can't find the exact quote, it drops its confidence score to `0.0` and flags it as a potential hallucination!

---

## 🎯 The Final Output

At the end, the Contract Parser agent hands over a digital **Rulebook** (`ContractRulebook`). This rulebook contains a perfect summary of every financial rule in the contract, ready to be used by the rest of the system to catch any billing mistakes!

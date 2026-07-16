# Needs Human Review User Guide

**Audience:** End users and business reviewers.

`NEEDS_HUMAN_REVIEW` means SupplierGuard found a possible issue, kept the finding visible, and is asking a human to make the final judgment.

## What It Means

A finding can need review when:

- The contract wording is ambiguous.
- The invoice contains notes or exceptions.
- The billed item does not clearly match a contract rule.
- The system lacks operational data needed to confirm the rule.
- Prior reviewer feedback suggests similar findings may be false positives.

## What To Do

1. Open the completed audit report.
2. Find the human review or compliance flags section.
3. Read the finding, clause, amount, and critic reasoning.
4. Inspect the original contract and invoice evidence.
5. Submit a verdict with a short reason.

## Verdicts

| Verdict | Use when |
|---|---|
| `CORRECT` | The finding is valid and should remain disputed |
| `FALSE_POSITIVE` | The finding should not be disputed |
| `FALSE_NEGATIVE` | The system missed or understated an issue |
| `ADJUSTED` | The finding is directionally right but the amount needs correction |

## Important Note

The AI critic does not remove findings. It only annotates them. A human decision is required to resolve business ambiguity.

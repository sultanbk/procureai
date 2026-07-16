"""
ProcureAI - File Summary

What it does:
Computes mathematical evaluation metrics like accuracy, recall, and extraction score.

What it means:
Agent performance grader.

Importance in Project:
Medium. Standardizes metrics for test harness reports.
"""

from typing import List, Dict, Any, Tuple
from decimal import Decimal

def calculate_precision_recall(
    predicted: List[Dict[str, Any]],
    expected: List[Dict[str, Any]]
) -> Tuple[float, float, int, int, int]:
    """
    Computes Precision and Recall.
    Matches are checked by comparing rule_id.
    Returns: (precision, recall, TP, FP, FN)
    """
    tp = 0
    fp = 0
    
    predicted_rules = [p.get("rule_id") for p in predicted if p.get("rule_id")]
    expected_rules = [e.get("rule_id") for e in expected if e.get("rule_id")]
    
    for p_rule in predicted_rules:
        if p_rule in expected_rules:
            tp += 1
        else:
            fp += 1
            
    fn = len(expected_rules) - tp
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    
    return precision, recall, tp, fp, fn

def calculate_delta_accuracy(
    predicted: List[Dict[str, Any]],
    expected: List[Dict[str, Any]],
    tolerance: float = 10.0
) -> float:
    """
    Calculates the % of True Positives where the predicted delta matches the expected delta within tolerance.
    """
    tp_deltas_correct = 0
    tp_count = 0
    
    for exp in expected:
        exp_rule = exp.get("rule_id")
        exp_delta = Decimal(str(exp.get("expected_delta", 0)))
        
        # Find matching predicted
        pred_match = next((p for p in predicted if p.get("rule_id") == exp_rule), None)
        if pred_match:
            tp_count += 1
            pred_delta = Decimal(str(pred_match.get("delta", 0)))
            if abs(pred_delta - exp_delta) <= Decimal(str(tolerance)):
                tp_deltas_correct += 1
                
    if tp_count == 0:
        return 1.0
        
    return tp_deltas_correct / tp_count

def calculate_extraction_accuracy(
    extracted_rulebook: Dict[str, Any],
    expected_rule_ids: List[str]
) -> float:
    """
    Calculates the % of expected rule IDs successfully extracted by the Contract Parser.
    """
    if not expected_rule_ids:
        return 1.0
        
    extracted_rules = extracted_rulebook.get("rules", [])
    extracted_ids = {r.get("rule_id") for r in extracted_rules if r.get("rule_id")}
    
    matched = sum(1 for rid in expected_rule_ids if rid in extracted_ids)
    return matched / len(expected_rule_ids)

"""
ProcureAI - File Summary

What it does:
Provides high-fidelity mock knowledge graphs, 4-store embeddings, amendment hierarchies,
and SOP procedural DAGs based on the SynaptAI Context Substrate specification.

What it means:
Enables deterministic, high-speed, zero-dependency execution for local testing, CI/CD,
and fail-safe offline presentations.

Importance in Project:
High. Guarantees 100% availability of Context Substrate features regardless of external network state.
"""

from typing import Dict, Any, List

# Standard Operating Procedures as DAGs (Milvus PS + Neo4j)
MOCK_PROCEDURE_DAGS: Dict[str, Dict[str, Any]] = {
    "dispute_recovery": {
        "procedure_id": "proc_sop_coldchain_001",
        "name": "Food Supply & Cold Chain Discrepancy Recovery Playbook",
        "intent": "Standard operating procedure to formalize produce/frozen billing overcharges, apply cold chain SLA credits, and enforce contract caps per CTR-SYSCO-PCF-2026-002.",
        "version": "2.1",
        "steps": [
            {
                "step_id": "step_1",
                "title": "Evidence Verification & Delta Reconciliation",
                "description": "Cross-reference invoice line item against Section 5.1 (volume rebate $5.00/case), Section 6.2 ($2,000 fuel cap), or Section 7.1 (temperature telemetry logs).",
                "order": 1,
                "required_role": "Procurement Auditor",
                "status": "COMPLETED"
            },
            {
                "step_id": "step_2",
                "title": "Draft Formal Dispute Notice",
                "description": "Generate formal Notice of Dispute specifying invoice ID, overcharge delta, clause citations (Section 5.1/6.2/7.1), and 14-day cure deadline to Premium Cold Foods, Inc.",
                "order": 2,
                "required_role": "Procurement Auditor",
                "status": "IN_PROGRESS"
            },
            {
                "step_id": "step_3",
                "title": "Payment Withholding Authorization",
                "description": "Instruct Accounts Payable to withhold the unearned fuel surcharge excess ($500) and volume delta while releasing undisputed balance per Section 10.",
                "order": 3,
                "required_role": "Finance Director",
                "status": "PENDING"
            },
            {
                "step_id": "step_4",
                "title": "Cold Chain & Logistics Account Review",
                "description": "Convene formal review with Premium Cold Foods Account Director to validate delivery temperature logs and secure 8% SLA credit note.",
                "order": 4,
                "required_role": "Head of Strategic Sourcing",
                "status": "PENDING"
            },
            {
                "step_id": "step_5",
                "title": "Credit Memo Execution & Ledger Reconciliation",
                "description": "Validate receipt of signed credit note and verify credit application against the subsequent Sysco monthly billing cycle.",
                "order": 5,
                "required_role": "Procurement Auditor",
                "status": "PENDING"
            }
        ],
        "edges": [
            {"from": "step_1", "to": "step_2", "type": "PRECEDES"},
            {"from": "step_2", "to": "step_3", "type": "PRECEDES"},
            {"from": "step_3", "to": "step_4", "type": "PRECEDES"},
            {"from": "step_4", "to": "step_5", "type": "PRECEDES"}
        ]
    },
    "circuit_decom": {
        "procedure_id": "proc_sop_decom_002",
        "name": "Circuit Decommissioning and Billing Cessation",
        "intent": "Decommission enterprise telecom circuit and cease recurring billing with carrier.",
        "version": "1.4",
        "steps": [
            {
                "step_id": "decom_1",
                "title": "Notify Carrier of Pending Decommission",
                "description": "Send formal 30-day notice to carrier requesting confirmation of circuit cease date.",
                "order": 1,
                "required_role": "Network Operations",
                "status": "COMPLETED"
            },
            {
                "step_id": "decom_2",
                "title": "Audit In-Flight Traffic & Confirm Reroute",
                "description": "Verify zero active packet throughput across physical CE router interfaces.",
                "order": 2,
                "required_role": "Network Engineer",
                "status": "COMPLETED"
            },
            {
                "step_id": "decom_3",
                "title": "Remove Circuit Config from Edge Routers",
                "description": "Decommission BGP session and archive router interface configuration.",
                "order": 3,
                "required_role": "Network Engineer",
                "status": "IN_PROGRESS"
            },
            {
                "step_id": "decom_4",
                "title": "Enforce Billing Cut-Off & Reconcile MRC",
                "description": "Ensure no post-cease date Monthly Recurring Charges (MRC) appear on subsequent carrier invoices.",
                "order": 4,
                "required_role": "Telecom Auditor",
                "status": "PENDING"
            }
        ],
        "edges": [
            {"from": "decom_1", "to": "decom_2", "type": "PRECEDES"},
            {"from": "decom_2", "to": "decom_3", "type": "PRECEDES"},
            {"from": "decom_3", "to": "decom_4", "type": "PRECEDES"}
        ]
    }
}

# Master graph of entities, concepts, clauses, and amendments (Primary: Premium Cold Foods & Sysco Corporation)
PREMIUM_COLD_FOODS_KNOWLEDGE_GRAPH: Dict[str, Any] = {
    "nodes": [
        {
            "id": "node_org_pcf",
            "label": "Premium Cold Foods, Inc.",
            "type": "Entity",
            "properties": {"category": "Vendor", "state": "Delaware", "facility": "Wilmington, DE", "description": "Wholesale organic produce & cold-chain logistics supplier"},
            "is_anchor": False
        },
        {
            "id": "node_org_sysco",
            "label": "Sysco Corporation",
            "type": "Entity",
            "properties": {"category": "Customer", "headquarters": "Houston, TX", "description": "Global food distributor and contracting enterprise customer"},
            "is_anchor": False
        },
        {
            "id": "node_doc_pcf_msa",
            "label": "Master Food Supply Agreement (CTR-SYSCO-PCF-2026-002)",
            "type": "Document",
            "properties": {"effective_date": "2026-06-01", "status": "Active", "governing_law": "Delaware", "jurisdiction": "AAA Arbitration"},
            "is_anchor": False
        },
        {
            "id": "node_rule_sec_4_2",
            "label": "Section 4.2: Standard Produce Boxes ($4.50/box)",
            "type": "Rule",
            "properties": {"rate": "$4.50/box", "product": "Standard Produce Boxes", "clause_ref": "Section 4.2", "packaging": "Wholesale organic harvest"},
            "is_anchor": True
        },
        {
            "id": "node_rule_sec_4_3",
            "label": "Section 4.3: Frozen Food Standard Rate ($5.80/case)",
            "type": "Rule",
            "properties": {"rate": "$5.80/case", "product": "Standard Frozen Food Cases", "clause_ref": "Section 4.3", "temp_req": "0°F or lower"},
            "is_anchor": False
        },
        {
            "id": "node_rule_sec_5_1",
            "label": "Section 5.1: Volume Tier Discount ($5.00/case > 10k)",
            "type": "Rule",
            "properties": {"rate": "$5.00/case", "threshold": "> 10,000 cases/mo", "clause_ref": "Section 5.1", "supersedes_rate": "$5.80/case"},
            "is_anchor": True
        },
        {
            "id": "node_rule_sec_6_2",
            "label": "Section 6.2: Fuel Surcharge Ceiling ($2,000.00 Max Cap)",
            "type": "Rule",
            "properties": {"ceiling_cap": "$2,000.00/month", "clause_ref": "Section 6.2", "condition": "Strict maximum monthly allowable fuel cost"},
            "is_anchor": True
        },
        {
            "id": "node_rule_sec_7_1",
            "label": "Section 7.1: Cold Chain Temperature SLA (98% / 8% Credit)",
            "type": "Rule",
            "properties": {"sla_threshold": "98.0%", "penalty_credit": "8.0% of monthly invoice total", "clause_ref": "Section 7.1"},
            "is_anchor": True
        },
        {
            "id": "node_rule_sec_8_2",
            "label": "Section 8.2: Mid-West Integration Milestone Delay ($1,500/day)",
            "type": "Rule",
            "properties": {"target_date": "2026-11-01", "liquidated_damages": "$1,500.00 per calendar day", "clause_ref": "Section 8.2"},
            "is_anchor": False
        },
        {
            "id": "node_rule_sec_9_2",
            "label": "Section 9.2: Prompt Payment Discount (3.0% Net-12)",
            "type": "Rule",
            "properties": {"discount_pct": "3.0%", "payment_window": "Within 12 days", "clause_ref": "Section 9.2"},
            "is_anchor": False
        },
        {
            "id": "node_chunk_sec_5_1",
            "label": "Chunk: Section 5.1 Volume Rebate Schedule",
            "type": "Chunk",
            "properties": {"tokens": 156, "text": "If monthly volume of Frozen Food cases shipped exceeds 10,000 cases, a discounted rate of USD 5.00 per case shall apply to all Frozen Food cases billed."},
            "is_anchor": True
        },
        {
            "id": "node_chunk_sec_6_2",
            "label": "Chunk: Section 6.2 Fuel Surcharge Monthly Ceiling Cap",
            "type": "Chunk",
            "properties": {"tokens": 112, "text": "Fuel surcharges applied to any monthly invoice shall not exceed USD 2,000.00. Under no circumstances shall Sysco be billed a fuel surcharge higher than USD 2,000.00."},
            "is_anchor": True
        }
    ],
    "edges": [
        {"source": "node_doc_pcf_msa", "target": "node_org_pcf", "type": "GOVERNED_BY"},
        {"source": "node_doc_pcf_msa", "target": "node_org_sysco", "type": "GOVERNED_BY"},
        {"source": "node_doc_pcf_msa", "target": "node_rule_sec_4_2", "type": "CONTAINS"},
        {"source": "node_doc_pcf_msa", "target": "node_rule_sec_4_3", "type": "CONTAINS"},
        {"source": "node_doc_pcf_msa", "target": "node_rule_sec_5_1", "type": "CONTAINS"},
        {"source": "node_doc_pcf_msa", "target": "node_rule_sec_6_2", "type": "CONTAINS"},
        {"source": "node_doc_pcf_msa", "target": "node_rule_sec_7_1", "type": "CONTAINS"},
        {"source": "node_doc_pcf_msa", "target": "node_rule_sec_8_2", "type": "CONTAINS"},
        {"source": "node_doc_pcf_msa", "target": "node_rule_sec_9_2", "type": "CONTAINS"},
        {"source": "node_rule_sec_5_1", "target": "node_rule_sec_4_3", "type": "SUPERSEDES"},
        {"source": "node_chunk_sec_5_1", "target": "node_rule_sec_5_1", "type": "ASSERTS"},
        {"source": "node_chunk_sec_6_2", "target": "node_rule_sec_6_2", "type": "ASSERTS"}
    ]
}

# Legacy benchmark graph kept for fallback reference
APEX_TELECOM_KNOWLEDGE_GRAPH = {
    "nodes": [
        {"id": "node_org_apex", "label": "Apex Telecom Ltd", "type": "Entity", "properties": {"category": "Vendor"}, "is_anchor": False},
        {"id": "node_doc_msa", "label": "Master Services Agreement", "type": "Document", "properties": {"status": "Active"}, "is_anchor": False},
        {"id": "node_doc_amend_1", "label": "Amendment 1", "type": "Document", "properties": {"status": "Active"}, "is_anchor": False},
        {"id": "node_rule_sec_4_1", "label": "Section 4.1: Rate ($1,200/mo)", "type": "Rule", "properties": {"rate": "$1,200/mo"}, "is_anchor": False},
        {"id": "node_rule_amend_1_sec_2", "label": "Amendment 1: Rate ($950/mo)", "type": "Rule", "properties": {"rate": "$950/mo"}, "is_anchor": True},
    ],
    "edges": [
        {"source": "node_doc_msa", "target": "node_doc_amend_1", "type": "SUPERSEDES"},
        {"source": "node_rule_amend_1_sec_2", "target": "node_rule_sec_4_1", "type": "SUPERSEDES"},
        {"source": "node_doc_msa", "target": "node_org_apex", "type": "GOVERNED_BY"},
    ]
}

# Default knowledge graph points directly to Premium Cold Foods
SAMPLE_KNOWLEDGE_GRAPH: Dict[str, Any] = PREMIUM_COLD_FOODS_KNOWLEDGE_GRAPH


def generate_default_pass_card(query: str, confidence_level: str = "HIGH") -> Dict[str, Any]:
    """Generates a realistic 5-stage Retrieval Pass Card based on Context Substrate spec."""
    is_high = confidence_level.upper() == "HIGH"
    
    return {
        "knowledge_store": {
            "score": 92.0 if is_high else 74.0,
            "confidence": 0.92 if is_high else 0.74,
            "quality_signals": {
                "retrieval_confidence": 0.94 if is_high else 0.78,
                "avg_similarity": 0.89 if is_high else 0.72,
                "coverage": 0.95 if is_high else 0.70,
                "source_diversity": 0.88 if is_high else 0.65
            },
            "risk_signals": {
                "hallucination_risk": 0.04 if is_high else 0.18,
                "knowledge_gap": 0.05 if is_high else 0.22,
                "noise_ratio": 0.06 if is_high else 0.15
            }
        },
        "context_graph": {
            "score": 96.0 if is_high else 78.0,
            "confidence": 0.96 if is_high else 0.78,
            "quality_signals": {
                "entity_match_score": 0.98 if is_high else 0.80,
                "relationship_confidence": 0.95 if is_high else 0.76,
                "graph_relevance": 0.96 if is_high else 0.79,
                "completeness": 0.94 if is_high else 0.75
            },
            "risk_signals": {
                "contradiction_probability": 0.02 if is_high else 0.12,
                "missing_context_risk": 0.03 if is_high else 0.19,
                "fragmentation_risk": 0.04 if is_high else 0.16
            }
        },
        "procedure_store": {
            "score": 88.0 if is_high else 68.0,
            "confidence": 0.88 if is_high else 0.68,
            "quality_signals": {
                "match_score": 0.90 if is_high else 0.70,
                "step_coverage": 0.92 if is_high else 0.65,
                "execution_readiness": 0.89 if is_high else 0.67,
                "policy_alignment": 0.95 if is_high else 0.75
            },
            "risk_signals": {
                "ambiguity_risk": 0.05 if is_high else 0.20,
                "missing_steps_risk": 0.04 if is_high else 0.24,
                "failure_risk": 0.03 if is_high else 0.15
            }
        },
        "fusion_layer": {
            "score": 94.0 if is_high else 76.0,
            "confidence": 0.94 if is_high else 0.76,
            "quality_signals": {
                "cross_source_agreement": 0.96 if is_high else 0.79,
                "consistency_score": 0.95 if is_high else 0.77,
                "source_balance": 0.92 if is_high else 0.73
            },
            "risk_signals": {
                "conflict_probability": 0.02 if is_high else 0.14,
                "signal_entropy": 0.06 if is_high else 0.21
            }
        },
        "generation": {
            "score": 95.0 if is_high else 79.0,
            "confidence": 0.95 if is_high else 0.79,
            "quality_signals": {
                "groundedness": 0.98 if is_high else 0.82,
                "faithfulness": 0.97 if is_high else 0.80,
                "answer_relevance": 0.96 if is_high else 0.84,
                "citation_coverage": 0.94 if is_high else 0.75
            },
            "risk_signals": {
                "hallucination_probability": 0.03 if is_high else 0.17,
                "model_uncertainty": 0.04 if is_high else 0.19
            }
        },
        "overall_confidence": 0.93 if is_high else 0.75
    }

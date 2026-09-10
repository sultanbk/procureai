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
        "procedure_id": "proc_sop_overcharge_001",
        "name": "Enterprise Overcharge & SLA Penalty Recovery Playbook",
        "intent": "Standard operating procedure to formalize invoice overcharges, apply contractual credits, and initiate vendor dispute resolution.",
        "version": "2.1",
        "steps": [
            {
                "step_id": "step_1",
                "title": "Evidence Verification & Delta Reconciliation",
                "description": "Cross-reference invoice line item against governing Contract Schedule / Amendment and extract verbatim clause text.",
                "order": 1,
                "required_role": "Procurement Auditor",
                "status": "COMPLETED"
            },
            {
                "step_id": "step_2",
                "title": "Draft Formal Dispute Notice",
                "description": "Generate formal Notice of Dispute specifying invoice ID, overcharge delta, clause citation, and 14-day cure deadline.",
                "order": 2,
                "required_role": "Procurement Auditor",
                "status": "IN_PROGRESS"
            },
            {
                "step_id": "step_3",
                "title": "Escrow / Payment Withholding Authorization",
                "description": "Notify Accounts Payable to withhold disputed balance while releasing undisputed charges per Section 12.3.",
                "order": 3,
                "required_role": "Finance Director",
                "status": "PENDING"
            },
            {
                "step_id": "step_4",
                "title": "Vendor Account Remediation Meeting",
                "description": "Convene formal review with Vendor Account Director to secure credit memo or revised billing invoice.",
                "order": 4,
                "required_role": "Head of Strategic Sourcing",
                "status": "PENDING"
            },
            {
                "step_id": "step_5",
                "title": "Credit Memo Execution & Ledger Reconciliation",
                "description": "Validate receipt of signed credit note and verify credit application against the subsequent billing cycle.",
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

# Master graph of entities, concepts, clauses, and amendments
SAMPLE_KNOWLEDGE_GRAPH: Dict[str, Any] = {
    "nodes": [
        {
            "id": "node_org_apex",
            "label": "Apex Telecom Ltd",
            "type": "Entity",
            "properties": {"category": "Vendor", "description": "Global tier-1 telecommunications and cloud provider"},
            "is_anchor": False
        },
        {
            "id": "node_org_procure",
            "label": "ProcureAI Enterprise",
            "type": "Entity",
            "properties": {"category": "Customer", "description": "Contracting enterprise customer"},
            "is_anchor": False
        },
        {
            "id": "node_doc_msa",
            "label": "Master Services Agreement (MSA-2024)",
            "type": "Document",
            "properties": {"effective_date": "2024-01-01", "status": "Active"},
            "is_anchor": False
        },
        {
            "id": "node_doc_amend_1",
            "label": "Amendment 1 (Rate Reduction & Bandwidth)",
            "type": "Document",
            "properties": {"effective_date": "2024-06-01", "status": "Active", "priority": 1},
            "is_anchor": False
        },
        {
            "id": "node_concept_mrc",
            "label": "Monthly Recurring Charge (MRC)",
            "type": "Concept",
            "properties": {"definition": "Fixed recurring baseline fee billed on the first day of each calendar billing cycle", "aliases": ["Monthly Fee", "Base Charge"]},
            "is_anchor": False
        },
        {
            "id": "node_rule_sec_4_1",
            "label": "Clause 4.1: Base Circuit Bandwidth Rate ($1,200/mo)",
            "type": "Rule",
            "properties": {"rate": "$1,200/mo", "superseded_by": "node_rule_amend_1_sec_2", "clause_ref": "Section 4.1"},
            "is_anchor": False
        },
        {
            "id": "node_rule_amend_1_sec_2",
            "label": "Amendment 1 - Section 2: Revised Rate ($950/mo)",
            "type": "Rule",
            "properties": {"rate": "$950/mo", "effective_date": "2024-06-01", "clause_ref": "Amend 1, Sec 2"},
            "is_anchor": True
        },
        {
            "id": "node_rule_sla_penalty",
            "label": "Schedule B: SLA Uptime & 10% Outage Credit",
            "type": "Rule",
            "properties": {"uptime_threshold": "99.9%", "penalty": "10% invoice credit for monthly availability < 99.5%"},
            "is_anchor": False
        },
        {
            "id": "node_entity_circuit_448",
            "label": "Dedicated DIA Link (CID-44821)",
            "type": "Entity",
            "properties": {"bandwidth": "100Mbps", "carrier": "Apex Telecom", "datacenter": "LON-CE-01"},
            "is_anchor": True
        },
        {
            "id": "node_chunk_sec_4_1",
            "label": "Chunk: Section 4.1 Original Rate Table",
            "type": "Chunk",
            "properties": {"tokens": 142, "text": "Customer shall pay a Monthly Recurring Charge of $1,200.00 for each dedicated 100Mbps DIA port installed."},
            "is_anchor": False
        },
        {
            "id": "node_chunk_amend_1",
            "label": "Chunk: Amendment 1 Superseding Schedule",
            "type": "Chunk",
            "properties": {"tokens": 185, "text": "Effective June 1, 2024, Section 4.1 of the Master Agreement is hereby superseded. The revised Monthly Recurring Charge for 100Mbps DIA ports shall be $950.00."},
            "is_anchor": True
        }
    ],
    "edges": [
        {"source": "node_doc_msa", "target": "node_org_apex", "type": "GOVERNED_BY"},
        {"source": "node_doc_msa", "target": "node_doc_amend_1", "type": "SUPERSEDES"},
        {"source": "node_rule_amend_1_sec_2", "target": "node_rule_sec_4_1", "type": "SUPERSEDES"},
        {"source": "node_doc_amend_1", "target": "node_rule_amend_1_sec_2", "type": "CONTAINS"},
        {"source": "node_doc_msa", "target": "node_rule_sec_4_1", "type": "CONTAINS"},
        {"source": "node_doc_msa", "target": "node_rule_sla_penalty", "type": "CONTAINS"},
        {"source": "node_rule_amend_1_sec_2", "target": "node_concept_mrc", "type": "DEFINES"},
        {"source": "node_entity_circuit_448", "target": "node_rule_amend_1_sec_2", "type": "BILLED_ON"},
        {"source": "node_chunk_sec_4_1", "target": "node_rule_sec_4_1", "type": "MENTIONS"},
        {"source": "node_chunk_amend_1", "target": "node_rule_amend_1_sec_2", "type": "ASSERTS"},
        {"source": "node_chunk_amend_1", "target": "node_chunk_sec_4_1", "type": "SUPERSEDES"}
    ]
}

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

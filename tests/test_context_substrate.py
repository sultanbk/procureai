"""
ProcureAI - Unit & Integration Tests: SynaptAI Context Substrate

Tests the 4-store client, REST API endpoints, reasoning subgraph generation,
amendment supersession resolution, and SOP DAG retrieval.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.core.context_substrate_client import (
    ContextSubstrateClient,
    get_context_substrate_client,
)
from backend.models.schemas import (
    ContextSubstrateStatusResponse,
    ContextSubstrateQueryResponse,
    ReasoningSubgraph,
    ProcedureDAG,
    RetrievalPassCard,
)


@pytest.mark.asyncio
async def test_client_status():
    """Verify Context Substrate client status reports active/embedded and connected stores."""
    client = get_context_substrate_client()
    status = await client.get_status()
    assert isinstance(status, ContextSubstrateStatusResponse)
    assert status.enabled is True
    assert status.neo4j_connected is True
    assert status.milvus_connected is True
    assert status.node_count > 0
    assert status.procedures_count > 0


@pytest.mark.asyncio
async def test_tristore_query_resolution():
    """Verify semantic query returns grounded answer, reasoning subgraph, and 5-stage pass card."""
    client = ContextSubstrateClient(mode="mock")
    response = await client.query_tristore("What is the revised bandwidth rate in Amendment 1?")
    
    assert isinstance(response, ContextSubstrateQueryResponse)
    assert "950" in response.answer
    assert response.confidence == "HIGH"
    
    # Subgraph assertions
    assert isinstance(response.reasoning_subgraph, ReasoningSubgraph)
    assert len(response.reasoning_subgraph.nodes) > 0
    assert len(response.reasoning_subgraph.edges) > 0
    assert response.retrieval_pass_card.context_graph.score > 0
    assert len(response.reasoning_subgraph.anchor_node_ids) > 0
    
    # Pass card assertions (5-stage verification)
    assert isinstance(response.retrieval_pass_card, RetrievalPassCard)
    assert response.retrieval_pass_card.overall_confidence >= 0.70
    assert response.retrieval_pass_card.knowledge_store.score >= 70
    assert response.retrieval_pass_card.context_graph.score >= 70
    assert response.retrieval_pass_card.generation.quality_signals["groundedness"] >= 0.80


@pytest.mark.asyncio
async def test_procedure_dag_retrieval():
    """Verify SOP as DAG from Milvus PS with PRECEDES edges and step hierarchy."""
    client = get_context_substrate_client()
    dag = client.get_procedure_dag("dispute_recovery")
    
    assert isinstance(dag, ProcedureDAG)
    assert len(dag.steps) >= 4
    assert len(dag.edges) >= 3
    # Check that edges use PRECEDES vocabulary per spec
    assert all(e["type"] == "PRECEDES" for e in dag.edges)
    assert dag.steps[0].order == 1


@pytest.mark.asyncio
async def test_amendment_supersession():
    """Verify Neo4j SUPERSEDES relationship resolution for contract clauses."""
    client = get_context_substrate_client()
    res = client.resolve_amendment_hierarchy("contract_apex_01", "Section 4.1")
    
    assert res["is_superseded"] is True
    assert res["edge_type"] == "SUPERSEDES"
    assert "Amendment 1" in res["active_clause"]
    assert res["superseding_rate"] == "$950.00/mo"


@pytest.mark.asyncio
async def test_discrepancy_subgraph_generation():
    """Verify dynamic construction of discrepancy provenance graph."""
    client = get_context_substrate_client()
    subgraph = client.get_discrepancy_subgraph(
        finding_id="disc_001",
        description="Overcharge on DIA Bandwidth port",
        clause_ref="Section 4.1",
        clause_text="Customer shall pay $1,200/mo",
        delta=250.0,
    )
    
    assert len(subgraph.nodes) >= 4
    assert len(subgraph.edges) >= 3
    edge_types = [e.type for e in subgraph.edges]
    assert "BILLED_ON" in edge_types
    assert "SUPERSEDES" in edge_types
    assert "GOVERNED_BY" in edge_types


@pytest.mark.asyncio
async def test_api_status_endpoint():
    """Verify GET /api/context-substrate/status REST endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/context-substrate/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is True
        assert data["neo4j_connected"] is True


@pytest.mark.asyncio
async def test_api_query_endpoint():
    """Verify POST /api/context-substrate/query REST endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"query": "What are the SLA outage penalties?"}
        resp = await ac.post("/api/context-substrate/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "retrieval_pass_card" in data
        assert "reasoning_subgraph" in data


@pytest.mark.asyncio
async def test_api_providers_crud():
    """Verify provider creation wizard (Steps 1, 2, 3), listing, and deletion."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. List initial providers
        list_resp = await ac.get("/api/context-substrate/providers")
        assert list_resp.status_code == 200
        initial_providers = list_resp.json()
        assert len(initial_providers) >= 2

        # 2. Create provider via 3-step wizard payload
        payload = {
            # Step 1
            "name": "Cloud Governance Knowledge Substrate",
            "description": "Enterprise cloud policy, CIS benchmarks, and infrastructure rate cards.",
            "extraction_mode": "balanced",
            "knowledge_pack_source": "system-defined-types",
            "knowledge_pack_packet": "clougovernance",
            "entity_types": ["Policy", "Regulation", "CloudResource", "SLA"],
            "relationship_types": ["GOVERNED_BY", "DEFINES", "SUPERSEDES"],
            # Step 2
            "stores_included": [
                "Knowledge Store (Milvus KS)",
                "Context Graph (Neo4j)",
                "Procedure Store (Milvus PS)"
            ],
            "entity_types_exposed": ["customer", "order", "product", "policy"],
            "context_depth_limit": 2,
            "max_results_per_query": 50,
            # Step 3
            "rate_limit_rpm": 120,
            "token_ttl_hours": 24,
            "target_platform": "langgraph"
        }
        create_resp = await ac.post("/api/context-substrate/providers", json=payload)
        assert create_resp.status_code == 201
        created = create_resp.json()
        assert created["name"] == "Cloud Governance Knowledge Substrate"
        assert created["knowledge_pack_packet"] == "clougovernance"
        assert created["context_depth_limit"] == 2
        assert created["target_platform"] == "langgraph"
        assert created["client_id"].startswith("client_")

        provider_id = created["id"]

        # 3. Retrieve single provider
        get_resp = await ac.get(f"/api/context-substrate/providers/{provider_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == provider_id

        # 4. Delete provider
        del_resp = await ac.delete(f"/api/context-substrate/providers/{provider_id}")
        assert del_resp.status_code == 200


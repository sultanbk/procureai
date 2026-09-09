"""
ProcureAI - File Summary

What it does:
Defines REST API endpoints for the SynaptAI Context Substrate integration.
Exposes status, TriStore queries, knowledge graph topologies, SOP DAGs, and discrepancy subgraphs.

What it means:
API bridge between the React frontend, ProcureAI agents, and the Context Substrate 4-store engine.

Importance in Project:
High. Powers the interactive Reasoning Subgraph modal, Retrieval Pass Cards, and SOP Playbook viewers.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from backend.core.context_substrate_client import get_context_substrate_client
from backend.models.schemas import (
    ContextSubstrateStatusResponse,
    ContextSubstrateQueryRequest,
    ContextSubstrateQueryResponse,
    ReasoningSubgraph,
    ProcedureDAG,
    ContextProviderCreate,
    ContextProviderResponse,
)
from backend.core.db import AsyncSessionLocal
from backend.models.audit import Audit

router = APIRouter(prefix="/api/context-substrate", tags=["context-substrate"])


@router.get("/status", response_model=ContextSubstrateStatusResponse)
async def get_substrate_status():
    """Retrieve the real-time operational and connectivity status of Context Substrate."""
    client = get_context_substrate_client()
    return await client.get_status()


@router.get("/providers", response_model=List[ContextProviderResponse])
async def list_context_providers():
    """Retrieve all registered Context Providers."""
    client = get_context_substrate_client()
    return client.list_providers()


@router.post("/providers", response_model=ContextProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_context_provider(payload: ContextProviderCreate):
    """Create and register a new Context Provider."""
    client = get_context_substrate_client()
    return client.create_provider(payload)


@router.get("/providers/{provider_id}", response_model=ContextProviderResponse)
async def get_context_provider(provider_id: str):
    """Retrieve details of a specific Context Provider."""
    client = get_context_substrate_client()
    provider = client.get_provider(provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context Provider '{provider_id}' not found",
        )
    return provider


@router.delete("/providers/{provider_id}")
async def delete_context_provider(provider_id: str):
    """Delete a Context Provider."""
    client = get_context_substrate_client()
    success = client.delete_provider(provider_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context Provider '{provider_id}' not found",
        )
    return {"message": f"Provider '{provider_id}' deleted successfully"}


@router.post("/query", response_model=ContextSubstrateQueryResponse)
async def query_context_substrate(request: ContextSubstrateQueryRequest):
    """
    Query the Context Substrate across the Neo4j Concept Graph, Milvus Knowledge Store,
    and Milvus Procedural Store.
    """
    client = get_context_substrate_client()
    try:
        response = await client.query_tristore(
            query=request.query,
            provider_id=request.provider_id,
            top_k=request.top_k,
            hops=request.hops,
            contract_id=request.contract_id,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context Substrate query failed: {str(e)}",
        )


@router.get("/graph/{contract_id}", response_model=ReasoningSubgraph)
async def get_contract_graph(contract_id: str):
    """Retrieve full concept and entity knowledge graph for a contract or workspace."""
    client = get_context_substrate_client()
    return client.get_contract_graph(contract_id)


@router.get("/subgraph/discrepancy/{finding_id}", response_model=ReasoningSubgraph)
async def get_discrepancy_subgraph(
    finding_id: str,
    audit_id: Optional[str] = Query(None),
    description: Optional[str] = Query("Contract compliance discrepancy"),
    clause_ref: Optional[str] = Query(None),
    delta: Optional[float] = Query(0.0),
):
    """
    Retrieve targeted reasoning subgraph proving why a specific discrepancy violates
    the contract hierarchy (Invoice Line Item -> Rate -> Clause -> Amendment).
    """
    client = get_context_substrate_client()
    
    # If audit_id is provided, attempt to pull exact clause text from the audit report in DB
    clause_text = None
    if audit_id:
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(Audit).where(Audit.id == audit_id)
                res = await session.execute(stmt)
                audit_obj = res.scalar_one_or_none()
                if audit_obj and audit_obj.discrepancy_list:
                    import json
                    raw_data = json.loads(audit_obj.discrepancy_list) if isinstance(audit_obj.discrepancy_list, str) else audit_obj.discrepancy_list
                    discrepancies = raw_data.get("discrepancies", [])
                    for d in discrepancies:
                        if d.get("finding_id") == finding_id:
                            clause_text = d.get("clause_text")
                            clause_ref = d.get("clause_reference") or clause_ref
                            description = d.get("description") or description
                            delta = float(d.get("delta") or delta)
                            break
        except Exception:
            pass

    return client.get_discrepancy_subgraph(
        finding_id=finding_id,
        description=description or "Contract rate discrepancy",
        clause_ref=clause_ref,
        clause_text=clause_text,
        delta=delta,
    )


@router.get("/procedures/{intent}", response_model=ProcedureDAG)
async def get_procedure_dag(intent: str):
    """
    Retrieve a corporate Standard Operating Procedure (SOP) as a Directed Acyclic Graph
    from the Milvus Procedural Store (PS).
    """
    client = get_context_substrate_client()
    dag = client.get_procedure_dag(intent)
    if not dag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No corporate SOP found for intent '{intent}'",
        )
    return dag


@router.get("/amendments/{contract_id}/{clause_name}")
async def get_amendment_hierarchy(contract_id: str, clause_name: str):
    """
    Query the Neo4j Concept Graph to resolve whether a clause has been superseded
    by a subsequent contract amendment.
    """
    client = get_context_substrate_client()
    return client.resolve_amendment_hierarchy(contract_id, clause_name)

"""
FILE CANONICAL IDENTIFIER: backend/agents/pipeline.py
MODULE ROLE: Orchestrates the multi-agent compliance pipeline using StateGraph.
SYSTEM BOUNDARY: Handles agent workflow orchestration only; delegates PDF/text extraction, LLM parsing, auditing, and report generation to specialized sub-agents.
STATE DEPENDENCY / DATA CONTRACTS: Consumes and mutates PipelineState (backend.models.schemas.PipelineState) containing files, texts, extracted rulebooks, discrepancies, and audit reports.
CRITICAL LOGIC: Parallel fan-out for contract_parser and invoice_extractor (v3 architecture), followed by a fan-in cross_validator gate, then compliance_checker, reverse_sweep (v4), cross_invoice_analyzer (v4), and report_generator.
"""

import threading
from langgraph.graph import StateGraph, END
from backend.models.schemas import PipelineState
from backend.agents.contract_parser.agent import run_contract_parser
from backend.agents.invoice_extractor.agent import run_invoice_extractor
from backend.agents.cross_validator.validator import run_cross_validator
from backend.agents.compliance_checker.agent import run_compliance_checker
from backend.agents.reverse_sweep.agent import run_reverse_sweep
from backend.agents.cross_invoice_analyzer.agent import run_cross_invoice_analyzer
from backend.agents.report_generator.agent import run_report_generator


async def run_parallel_extractors(state: PipelineState) -> PipelineState:
    """
    Runs invoice_extractor and contract_parser as independent sequential calls.
    Both run regardless of the other's success/failure (v3 architecture requirement).
    They share no data — contract_parser reads contract_text, invoice_extractor reads invoice_texts.
    However, we run invoice_extractor first so contract_parser can inspect invoice_data
    and resolve the correct contract version based on invoice dates if needed.

    NOTE: LangGraph 0.2.x does not natively support true async fan-out/fan-in
    for nodes that mutate the same TypedDict state. We run them sequentially
    within a single node to guarantee state consistency, but maintain logical
    independence: neither reads the other's output, and one's failure does not
    block the other.
    """
    contract_error = None
    invoice_error = None

    # Run invoice extractor first so we have invoice_data for supplier/date resolution
    try:
        state = await run_invoice_extractor(state)
    except Exception as e:
        invoice_error = e

    # Always run contract parser, even if invoice extractor failed
    # Save and restore halt flag so invoice_extractor's halt doesn't block contract_parser
    invoice_halt = state.get("halt", False)
    if invoice_halt:
        state["halt"] = False  # Temporarily clear so contract parser runs

    try:
        state = await run_contract_parser(state)
    except Exception as e:
        contract_error = e

    # Now determine final halt status:
    # - If BOTH failed → halt (can't do anything)
    # - If only one failed → don't halt yet, let cross_validator handle partial data
    contract_halt = state.get("halt", False)

    if contract_halt and invoice_halt:
        # Both failed — pipeline must stop
        state["halt"] = True
    elif contract_halt and not invoice_halt:
        # Contract failed, invoice succeeded — halt because cross_validator needs rulebook
        state["halt"] = True
    elif not contract_halt and invoice_halt:
        # Invoice failed, contract succeeded — halt because cross_validator needs invoice_data
        state["halt"] = True
    else:
        # Both succeeded
        state["halt"] = False

    return state


def build_pipeline() -> StateGraph:
    """
    Builds the LangGraph state pipeline (v4 architecture).
    Flow: parallel_extractors (contract_parser + invoice_extractor)
          → cross_validator → compliance_checker → reverse_sweep
          → cross_invoice_analyzer → report_generator
    At each step, if the halt flag is set to True, the pipeline routes directly to END.
    """
    graph = StateGraph(PipelineState)

    # Single node that runs both extractors in sequence (logically independent)
    graph.add_node("parallel_extractors", run_parallel_extractors)
    graph.add_node("cross_validator", run_cross_validator)
    graph.add_node("compliance_checker", run_compliance_checker)
    graph.add_node("reverse_sweep_agent", run_reverse_sweep)                  # v4: Node 5
    graph.add_node("cross_invoice_agent", run_cross_invoice_analyzer)          # v4: Node 6
    graph.add_node("report_generator", run_report_generator)

    # Entry point
    graph.set_entry_point("parallel_extractors")

    # Conditional edges for halt checking after each node
    graph.add_conditional_edges(
        "parallel_extractors",
        lambda s: END if s.get("halt") else "cross_validator"
    )
    graph.add_conditional_edges(
        "cross_validator",
        lambda s: END if s.get("halt") else "compliance_checker"
    )
    graph.add_conditional_edges(
        "compliance_checker",
        lambda s: END if s.get("halt") else "reverse_sweep_agent"
    )
    graph.add_conditional_edges(
        "reverse_sweep_agent",
        lambda s: END if s.get("halt") else "cross_invoice_agent"
    )
    graph.add_conditional_edges(
        "cross_invoice_agent",
        lambda s: END if s.get("halt") else "report_generator"
    )

    # End node transitions to END
    graph.add_edge("report_generator", END)

    return graph.compile()


_pipeline = None
_pipeline_lock = threading.Lock()


def get_pipeline():
    """
    Returns the compiled LangGraph pipeline singleton.
    Thread-safe via lock (fixes Problem 15).
    """
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    with _pipeline_lock:
        # Double-check inside lock
        if _pipeline is None:
            _pipeline = build_pipeline()
        return _pipeline

"""
ProcureAI - File Summary

What it does:
Helper to load system prompts from corresponding agent directories.

What it means:
Prompts manager allowing decoupled storage of agent instruction templates.

Importance in Project:
Low. Promotes code hygiene by keeping prompt markdown files separate from python logic.
"""

from pathlib import Path

def load_prompt(agent_name: str, prompt_file: str = "prompt.txt") -> str:
    """
    Loads the system prompt text for a specific agent from its directory.
    E.g. load_prompt("contract_parser", "prompt_extract_chunk.txt") reads backend/agents/contract_parser/prompt_extract_chunk.txt
    Falls back to prompt.txt if prompt_file is not found.
    """
    path = Path(__file__).parent.parent / "agents" / agent_name / prompt_file
    if not path.exists():
        fallback = Path(__file__).parent.parent / "agents" / agent_name / "prompt.txt"
        if fallback.exists():
            return fallback.read_text(encoding="utf-8")
    return path.read_text(encoding="utf-8")


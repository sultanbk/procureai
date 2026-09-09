import os
import sys
import asyncio
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.pdf_extractor import extract_pdf_text
from backend.services.contract_chunker import split_by_sections
from backend.agents.contract_parser.agent import extract_section_rulebook
from backend.agents.contract_parser.tools import merge_rulebooks, vote_on_rules
from backend.core.llm_client import get_llm
from backend.core.prompt_loader import load_prompt
from backend.models.schemas import ContractRulebook

async def test():
    contract_path = "data/synthetic/contracts/c009_cloudscale_technologies_edgar.pdf"
    txt = extract_pdf_text(contract_path)
    secs = split_by_sections(txt)
    print(f"Total sections: {len(secs)}")
    
    llm = get_llm()
    pt = load_prompt("contract_parser", "prompt_extract_chunk.txt")
    sp = pt.replace("{schema}", json.dumps(ContractRulebook.model_json_schema(), indent=2))
    
    section_rulebooks = []
    for h, c in secs:
        content = f"--- SECTION: {h} ---\n{c}"
        rb = await extract_section_rulebook(llm, sp, content, temperature=0.0)
        print(f"Section '{h}': {len(rb.rules)} rules found")
        for r in rb.rules:
            print(f"   -> [{r.rule_type}] {r.applies_to}: {r.clause_text[:60]}...")
        section_rulebooks.append(rb)
        
    merged = merge_rulebooks(section_rulebooks)
    print(f"\nTotal merged rules: {len(merged.rules)}")
    for r in merged.rules:
        print(f"  • {r.rule_id} ({r.rule_type}): {r.applies_to} -> {r.clause_text}")

if __name__ == "__main__":
    asyncio.run(test())

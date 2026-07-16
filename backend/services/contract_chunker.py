"""
ProcureAI - File Summary

What it does:
Splits long contract text into distinct chunks.

What it means:
Document chunker and processor supporting Vector QA.

Importance in Project:
Medium. Prevents LLM context overflow during semantic contract QA.
"""

import json
import os
import re
import asyncio
from typing import Any

from rank_bm25 import BM25Okapi
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.pdf_extractor import extract_pdf_text
from backend.models.audit import Audit, ContractChunk


HEADER_PATTERN = re.compile(
    r"^\s*((?:Section|Clause|Schedule)\s+[A-Za-z0-9][A-Za-z0-9.\-_]*)(?:\s*[-:—]\s*(.*))?$",
    re.IGNORECASE,
)
TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text or "")]


def split_by_sections(contract_text: str) -> list[tuple[str, str]]:
    """
    Split contract text into logical sections.

    Headers include "Section X", "Clause X", "Schedule X", and short lines
    ending with ":".
    """
    lines = (contract_text or "").splitlines()
    sections: list[tuple[str, str]] = []
    current_header = "Full Contract"
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        is_header = bool(HEADER_PATTERN.match(stripped))
        if stripped.endswith(":") and len(stripped) < 60:
            is_header = True

        if is_header:
            if current_lines:
                section_text = "\n".join(current_lines).strip()
                if section_text:
                    sections.append((current_header, section_text))
            current_header = stripped.rstrip(":")
            current_lines = []
            continue

        current_lines.append(line)

    if current_lines:
        section_text = "\n".join(current_lines).strip()
        if section_text:
            sections.append((current_header, section_text))

    if not sections and contract_text.strip():
        return [("Full Contract", contract_text.strip())]
    return sections


def split_with_overlap(text: str, max_chars: int = 500, overlap: int = 50) -> list[str]:
    if not text:
        return []
    if len(text) <= max_chars:
        return [text.strip()]

    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + max_chars, text_len)
        if end < text_len:
            boundary = max(
                text.rfind("\n", start, end),
                text.rfind(". ", start, end),
                text.rfind(" ", start, end),
            )
            if boundary > start + max_chars // 2:
                end = boundary + (1 if text[boundary] == "." else 0)

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_len:
            break
        start = max(0, end - overlap)

    return chunks


async def chunk_contract(contract_text: str, audit_id: str, db: AsyncSession, contract_id: str = None) -> None:
    """
    Split contract text into overlapping chunks and store them for BM25 retrieval.
    Safe to call more than once for the same audit/contract.
    """
    await db.execute(delete(ContractChunk).where(ContractChunk.audit_id == audit_id))
    if contract_id:
        await db.execute(delete(ContractChunk).where(ContractChunk.contract_id == contract_id))

    chunks: list[ContractChunk] = []
    for section_header, section_text in split_by_sections(contract_text):
        for chunk_text in split_with_overlap(section_text, max_chars=500, overlap=50):
            chunks.append(
                ContractChunk(
                    audit_id=audit_id,
                    contract_id=contract_id,
                    chunk_index=len(chunks),
                    chunk_text=chunk_text,
                    section_header=section_header,
                )
            )

    if chunks:
        db.add_all(chunks)
    await db.commit()


async def ensure_contract_chunks(audit_id: str, db: AsyncSession) -> list[ContractChunk]:
    from backend.models.audit import Contract
    import hashlib

    # 1. Fetch Audit details
    audit_result = await db.execute(select(Audit).where(Audit.id == audit_id))
    audit = audit_result.scalar_one_or_none()
    
    if not audit or not audit.contract_file or not os.path.exists(audit.contract_file):
        # Fallback to querying by audit_id directly
        cc_stmt = select(ContractChunk).where(ContractChunk.audit_id == audit_id).order_by(ContractChunk.chunk_index.asc())
        cc_res = await db.execute(cc_stmt)
        return list(cc_res.scalars().all())

    # 2. Get file hash of contract
    try:
        def _read_file():
            with open(audit.contract_file, "rb") as f:
                return f.read()
        file_bytes = await asyncio.to_thread(_read_file)
        file_hash = hashlib.sha256(file_bytes).hexdigest()
    except Exception:
        file_hash = None

    contract = None
    if file_hash:
        contract_stmt = select(Contract).where(Contract.file_hash == file_hash)
        contract_res = await db.execute(contract_stmt)
        contract = contract_res.scalar_one_or_none()

    # 3. Retrieve chunks by contract_id if available
    if contract:
        cc_stmt = select(ContractChunk).where(ContractChunk.contract_id == contract.id).order_by(ContractChunk.chunk_index.asc())
        cc_res = await db.execute(cc_stmt)
        chunks = list(cc_res.scalars().all())
        if chunks:
            return chunks

    # 4. Fallback to audit_id lookup
    cc_stmt = select(ContractChunk).where(ContractChunk.audit_id == audit_id).order_by(ContractChunk.chunk_index.asc())
    cc_res = await db.execute(cc_stmt)
    chunks = list(cc_res.scalars().all())
    if chunks:
        # Backfill contract_id to these chunks for future lookups
        if contract:
            for c in chunks:
                c.contract_id = contract.id
            await db.commit()
        return chunks

    # 5. Extract text and chunk if not found
    contract_text = await asyncio.to_thread(extract_pdf_text, audit.contract_file)
    await chunk_contract(contract_text, audit_id, db, contract_id=contract.id if contract else None)

    cc_stmt = select(ContractChunk).where(
        (ContractChunk.audit_id == audit_id) | 
        (ContractChunk.contract_id == (contract.id if contract else None))
    ).order_by(ContractChunk.chunk_index.asc())
    cc_res = await db.execute(cc_stmt)
    return list(cc_res.scalars().all())


async def retrieve_relevant_chunks(
    query: str,
    audit_id: str,
    db: AsyncSession,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    chunks = await ensure_contract_chunks(audit_id, db)
    if not chunks:
        return []

    corpus = [tokenize((chunk.section_header or "") + " " + (chunk.chunk_text or "")) for chunk in chunks]
    query_tokens = tokenize(query)
    if not query_tokens or not any(corpus):
        return []

    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query_tokens)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    return [
        {
            "chunk_text": chunks[i].chunk_text,
            "section_header": chunks[i].section_header,
            "relevance_score": float(scores[i]),
        }
        for i in top_indices
        if scores[i] > 0.0
    ]


def _iter_rules(rulebook: Any) -> list[Any]:
    if isinstance(rulebook, dict):
        return rulebook.get("rules", []) or []
    return list(getattr(rulebook, "rules", []) or [])


def _rule_value(rule: Any, key: str, default: Any = "") -> Any:
    if isinstance(rule, dict):
        return rule.get(key, default)
    return getattr(rule, key, default)


def _dump_tiers(tiers: Any) -> str:
    if not tiers:
        return ""
    serializable = [
        tier.model_dump(mode="json") if hasattr(tier, "model_dump") else tier
        for tier in tiers
    ]
    return json.dumps(serializable, default=str)


def _rulebook_value(rulebook: Any, key: str, default: Any = "") -> Any:
    if isinstance(rulebook, dict):
        return rulebook.get(key, default)
    return getattr(rulebook, key, default)


def _numeric_query_value(query: str) -> int | None:
    matches = re.findall(r"\d[\d,]*", query or "")
    if not matches:
        return None
    try:
        return int(matches[0].replace(",", ""))
    except ValueError:
        return None


def _tier_value(tier: Any, key: str, default: Any = None) -> Any:
    if isinstance(tier, dict):
        return tier.get(key, default)
    return getattr(tier, key, default)


def build_pricing_hints(query: str, rulebook: Any) -> str:
    quantity = _numeric_query_value(query)
    if quantity is None:
        return ""

    query_lower = (query or "").lower()
    if not any(word in query_lower for word in ("price", "rate", "unit", "tier", "cost", "charge")):
        return ""

    hints: list[str] = []
    currency = _rulebook_value(rulebook, "contract_currency", "INR") or "INR"
    for rule in _iter_rules(rulebook):
        tiers = _rule_value(rule, "tiers", None)
        if not tiers:
            continue

        for index, tier in enumerate(tiers, start=1):
            min_units = _tier_value(tier, "min_units", 0)
            max_units = _tier_value(tier, "max_units", None)
            unit_price = _tier_value(tier, "unit_price", None)
            if unit_price is None:
                continue

            if quantity >= int(min_units) and (max_units is None or quantity <= int(max_units)):
                total = quantity * float(unit_price)
                ceiling = f"{max_units} units" if max_units is not None else "and above"
                hints.append(
                    "For {qty} units: {rule_id} tier {tier_no} applies "
                    "({min_units}-{ceiling}) -> {qty} x {currency} {unit_price} = "
                    "{currency} {total:,.2f}. Clause: {clause}.".format(
                        qty=quantity,
                        rule_id=_rule_value(rule, "rule_id", "Unknown"),
                        tier_no=index,
                        min_units=min_units,
                        ceiling=ceiling,
                        currency=currency,
                        unit_price=unit_price,
                        total=total,
                        clause=_rule_value(rule, "clause_reference", ""),
                    )
                )
                break

    if not hints:
        return ""
    return "\nQUERY-SPECIFIC PRICING CALCULATIONS:\n" + "\n".join(hints) + "\n"


async def build_rag_context(
    query: str,
    audit_id: str,
    rulebook: Any,
    db: AsyncSession,
) -> str:
    rules_context = (
        "CONTRACT METADATA:\n"
        f"Supplier: {_rulebook_value(rulebook, 'supplier_name', 'Unknown')}\n"
        f"Contract ID: {_rulebook_value(rulebook, 'contract_id', 'Unknown')}\n"
        f"Currency: {_rulebook_value(rulebook, 'contract_currency', 'INR')}\n\n"
        "CONTRACT PRICING RULES (structured):\n"
    )
    allowed_refs: list[str] = []

    for rule in _iter_rules(rulebook):
        rule_id = _rule_value(rule, "rule_id", "Unknown")
        clause_reference = _rule_value(rule, "clause_reference", "")
        tiers = _rule_value(rule, "tiers", None)
        if clause_reference:
            allowed_refs.append(str(clause_reference))

        rules_context += (
            f"\n[{rule_id}] {_rule_value(rule, 'description', '')}\n"
            f"Clause: {clause_reference}\n"
            f"Text: {_rule_value(rule, 'clause_text', '')}\n"
        )
        tiers_text = _dump_tiers(tiers)
        if tiers_text:
            rules_context += f"Tiers: {tiers_text}\n"

    if allowed_refs:
        rules_context += "\nALLOWED CLAUSE REFERENCES:\n" + "\n".join(
            f"- {ref}" for ref in sorted(set(allowed_refs))
        ) + "\n"

    pricing_hints = build_pricing_hints(query, rulebook)

    chunks = await retrieve_relevant_chunks(query, audit_id, db, top_k=4)
    chunks_context = "\nRELEVANT CONTRACT SECTIONS:\n"
    for chunk in chunks:
        chunks_context += f"\n[{chunk['section_header']}]\n{chunk['chunk_text']}\n"

    return rules_context + pricing_hints + chunks_context

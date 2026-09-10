# -*- coding: utf-8 -*-
"""The query agent: a registered identity plus a line to the context provider.

    async with QueryAgent.from_env() as agent:
        print(await agent.answer("what are the main procedures here?"))

The agent holds no domain knowledge. It exchanges its registry credential for a
session token (or uses one pasted in), then calls the Trident MCP tools. Every
answer comes back from the context substrate; its job is authentication plus
transport.
"""
from __future__ import annotations

from typing import Any
import httpx

from .config import AgentConfig
from .mcp_client import MCPError, SynaptMCP
from .s2s import SecretTokenSource, StaticTokenSource


class QueryAgent:
    def __init__(self, cfg: AgentConfig) -> None:
        self.cfg = cfg
        self.tokens: SecretTokenSource | StaticTokenSource
        if cfg.auth_mode == "static":
            self.tokens = StaticTokenSource(cfg.static_token, client_id=cfg.client_id)
        else:
            self.tokens = SecretTokenSource(
                token_url=cfg.token_url,
                client_id=cfg.client_id,
                client_secret=cfg.client_secret,
                verify=cfg.verify,
                timeout=min(cfg.timeout, 60.0),
            )
        self.mcp = SynaptMCP(
            mcp_url=cfg.mcp_url,
            provider_id=cfg.provider_id,
            token_source=self.tokens,
            verify=cfg.verify,
            timeout=cfg.timeout,
        )

    @classmethod
    def from_env(cls, **overrides: Any) -> "QueryAgent":
        return cls(AgentConfig.from_env(**overrides))

    async def __aenter__(self) -> "QueryAgent":
        await self.mcp.connect()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.mcp.aclose()

    async def aclose(self) -> None:
        await self.mcp.aclose()

    # ── the substrate surface (only the granted tools) ───────────────────
    async def ask(self, question: str, *, top_k: int = 5, graph_hops: int = 2) -> Any:
        """Retrieval-augmented answer with confidence + sources (trident_query)."""
        try:
            res = await self.mcp.call_tool(
                "trident_query", question=question, top_k=top_k, graph_hops=graph_hops
            )
            if isinstance(res, str) and "No agent_id was supplied" in res:
                return await self._rest_ask(question, top_k=top_k)
            return res
        except Exception:
            return await self._rest_ask(question, top_k=top_k)

    async def _rest_ask(self, question: str, top_k: int = 5) -> Any:
        token = await self.tokens.token()
        base = self.cfg.mcp_url.replace("/api/mcp", "")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"question": question, "provider_id": self.cfg.provider_id, "top_k": top_k}
        async with httpx.AsyncClient(timeout=60.0, verify=self.cfg.verify) as client:
            resp = await client.post(f"{base}/api/query", json=payload, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            return f"HTTP {resp.status_code}: {resp.text[:300]}"

    async def answer(self, question: str, **kw: Any) -> str:
        """`ask`, reduced to just the answer text."""
        result = await self.ask(question, **kw)
        if isinstance(result, dict) and result.get("answer"):
            return str(result["answer"])
        return str(result)

    async def search(self, query: str, node_type: str | None = None, top_k: int = 10) -> Any:
        return await self.mcp.call_tool(
            "trident_search", query=query, node_type=node_type, top_k=top_k
        )

    async def traverse(
        self,
        node_id: str,
        *,
        edge_types: Any = None,
        node_types: Any = None,
        direction: str | None = None,
        depth: int | None = None,
    ) -> Any:
        return await self.mcp.call_tool(
            "trident_traverse",
            node_id=node_id,
            edge_types=edge_types,
            node_types=node_types,
            direction=direction,
            depth=depth,
        )

    async def chunks(self, query: str, top_k: int = 5) -> Any:
        """Raw document text, not a synthesised answer."""
        return await self.mcp.call_tool("trident_get_chunks", query=query, top_k=top_k)

    async def procedures(self, query: str | None = None) -> Any:
        return await self.mcp.call_tool("trident_get_procedures", query=query)

    async def stats(self) -> Any:
        try:
            res = await self.mcp.call_tool("trident_get_stats")
            if isinstance(res, str) and "No agent_id was supplied" in res:
                return await self._rest_stats()
            return res
        except Exception:
            return await self._rest_stats()

    async def _rest_stats(self) -> Any:
        token = await self.tokens.token()
        base = self.cfg.mcp_url.replace("/api/mcp", "")
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=10.0, verify=self.cfg.verify) as client:
            resp = await client.get(f"{base}/api/providers", headers=headers)
            if resp.status_code == 200:
                providers = resp.json()
                active = [p for p in providers if (p.get("id") or p.get("provider_id")) == self.cfg.provider_id]
                return active[0] if active else {"providers_count": len(providers)}
            return f"HTTP {resp.status_code}: {resp.text[:300]}"

    async def feedback(
        self,
        feedback_id: str,
        *,
        caller_type: str | None = None,
        verdict: Any = None,
        post_action: Any = None,
        score: Any = None,
        reason: str | None = None,
    ) -> Any:
        return await self.mcp.call_tool(
            "trident_feedback",
            feedback_id=feedback_id,
            caller_type=caller_type,
            verdict=verdict,
            post_action=post_action,
            score=score,
            reason=reason,
        )

    async def tools(self) -> list[dict]:
        """What the substrate actually exposes - introspected, not hard-coded."""
        return await self.mcp.list_tools()

    # ── self-check ───────────────────────────────────────────────────────
    async def whoami(self) -> dict:
        """Prove the identity end to end: mint a token, then reach the substrate."""
        token = await self.tokens.token()
        out: dict[str, Any] = {
            "client_id": self.cfg.client_id,
            "auth_mode": self.cfg.auth_mode,
            "provider_id": self.cfg.provider_id,
            "mcp_url": self.cfg.mcp_url,
            "token_url": self.cfg.token_url,
            "token_acquired": bool(token),
        }
        # In the registered-agent flow the token carries the authoritative grant.
        grant = getattr(self.tokens, "scope", None)
        if grant is not None:
            out["granted_scope"] = grant
        try:
            out["mcp_tools"] = [t["name"] for t in await self.tools()]
        except MCPError as exc:
            out["mcp_error"] = str(exc)
        return out

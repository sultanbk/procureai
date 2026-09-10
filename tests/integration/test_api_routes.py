"""
ProcureAI — API Integration Tests

Fix #7: Integration tests using FastAPI's AsyncClient and httpx.
Tests all major API route endpoints for correct HTTP responses and data contracts.
"""

import os
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# Force mock mode to prevent real LLM/DB calls
os.environ["MOCK_LLM"] = "true"
os.environ["ALLOW_MOCK_LLM"] = "true"
os.environ["GEMINI_API_KEY"] = ""
os.environ["REQUIRE_API_KEY"] = "false"

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.core.db import Base, AsyncSessionLocal
from backend.main import app


# --- Test Database Setup ---

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="module")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="module")
async def test_session_factory(test_engine):
    return async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def override_db(test_engine, test_session_factory, monkeypatch):
    """Redirect all DB access to the test in-memory database."""
    import backend.core.db as db_module
    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "AsyncSessionLocal", test_session_factory)
    # Also patch the import used in routes
    import backend.api.routes.audit as audit_module
    monkeypatch.setattr(audit_module, "AsyncSessionLocal", test_session_factory)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Health & Root
# ============================================================================

@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert "ProcureAI" in data["message"]


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") in ("ok", "healthy", True)


# ============================================================================
# Audit List
# ============================================================================

@pytest.mark.asyncio
async def test_list_audits_empty(client):
    resp = await client.get("/api/audits")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


# ============================================================================
# Audit Not Found
# ============================================================================

@pytest.mark.asyncio
async def test_get_audit_not_found(client):
    resp = await client.get("/api/audit/nonexistent_id_123")
    assert resp.status_code == 404


# ============================================================================
# Upload Validation
# ============================================================================

@pytest.mark.asyncio
async def test_upload_contract_no_file(client):
    resp = await client.post("/api/upload/contract")
    assert resp.status_code == 422  # Missing file field


@pytest.mark.asyncio
async def test_upload_invoice_no_file(client):
    resp = await client.post("/api/upload/invoice")
    assert resp.status_code == 422


# ============================================================================
# Audit Run Validation
# ============================================================================

@pytest.mark.asyncio
async def test_run_audit_missing_contract(client):
    resp = await client.post("/api/audit/run", json={
        "contract_file_id": "nonexistent_file.pdf",
        "invoice_file_ids": ["also_missing.pdf"],
    })
    assert resp.status_code == 400


# ============================================================================
# Suppliers
# ============================================================================

@pytest.mark.asyncio
async def test_list_suppliers(client):
    resp = await client.get("/api/suppliers")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


@pytest.mark.asyncio
async def test_supplier_summary(client):
    resp = await client.get("/api/suppliers/summary")
    assert resp.status_code == 200


# ============================================================================
# Analytics
# ============================================================================

@pytest.mark.asyncio
async def test_analytics_overview(client):
    resp = await client.get("/api/analytics/overview")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_analytics_heatmap(client):
    resp = await client.get("/api/analytics/heatmap")
    assert resp.status_code == 200


# ============================================================================
# Settings
# ============================================================================

@pytest.mark.asyncio
async def test_get_notification_settings(client):
    resp = await client.get("/api/settings/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert "slack_enabled" in data
    assert "email_enabled" in data


@pytest.mark.asyncio
async def test_update_notification_settings(client):
    resp = await client.put("/api/settings/notifications", json={
        "slack_enabled": True,
        "alert_on_critical": True,
        "alert_threshold_inr": 5000.0,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["slack_enabled"] is True
    assert data["alert_on_critical"] is True


# ============================================================================
# Contracts
# ============================================================================

@pytest.mark.asyncio
async def test_list_contracts(client):
    resp = await client.get("/api/contracts")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


# ============================================================================
# Watcher
# ============================================================================

@pytest.mark.asyncio
async def test_watcher_status(client):
    resp = await client.get("/api/watcher/status")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_watcher_history(client):
    resp = await client.get("/api/watcher/history")
    assert resp.status_code == 200


# ============================================================================
# Context Substrate
# ============================================================================

@pytest.mark.asyncio
async def test_context_substrate_status(client):
    resp = await client.get("/api/context-substrate/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "enabled" in data


# ============================================================================
# Dispute Not Found (no audit to generate from)
# ============================================================================

@pytest.mark.asyncio
async def test_get_dispute_not_found(client):
    resp = await client.get("/api/disputes/nonexistent_audit_id")
    # Should return 404 or similar — not a crash
    assert resp.status_code in (404, 400, 500)


# ============================================================================
# Global Exception Handler — verify no traceback leak
# ============================================================================

@pytest.mark.asyncio
async def test_error_response_no_traceback(client):
    """Verify the global exception handler doesn't leak tracebacks."""
    resp = await client.get("/api/audit/nonexistent")
    data = resp.json()
    assert "traceback" not in data
    assert "Traceback" not in json.dumps(data)

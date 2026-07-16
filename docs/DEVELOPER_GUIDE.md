# Developer Guide

**Audience:** Developers contributing to SupplierGuard.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
python -m scripts.seed_db

cd frontend
npm install
Copy-Item .env.example .env
```

Start services:

```powershell
# Terminal 1
python backend\main.py

# Terminal 2
cd frontend
npm run dev
```

## Project Structure

| Path | Notes |
|---|---|
| `backend/main.py` | FastAPI app and lifespan hook |
| `backend/api/routes/` | Route modules grouped by domain |
| `backend/agents/` | Pipeline agents and prompts |
| `backend/services/` | Domain services reused by routes and agents |
| `backend/core/` | Configuration, DB, LLM, PDF, logging, prompt loading |
| `backend/models/` | SQLAlchemy and Pydantic models |
| `backend/eval/` | Evaluation harness |
| `frontend/src/api.js` | Frontend API client |
| `frontend/src/pages/` | Top-level views |
| `frontend/src/components/` | Reusable UI and feature components |
| `scripts/` | Operational and synthetic-data scripts |
| `tests/` | Backend tests |

## Development Workflow

1. Read the route, service, schema, and frontend API client before changing behavior.
2. Keep API request/response schemas synchronized with `frontend/src/api.js`.
3. Use deterministic Python for money and date calculations.
4. Keep prompts in `.txt` files under agent folders.
5. Keep new docs linked from `README.md` or `docs/DOCUMENTATION_COVERAGE.md`.

## Database Initialization

```powershell
python -m scripts.seed_db
python -m scripts.migrate_db
```

`seed_db.py` creates all ORM tables registered on `Base.metadata`. `migrate_db.py` currently adds contract-library columns and contract chunk indexes for older SQLite databases.

## Common Commands

```powershell
npm run install:all
npm run dev
python -m pytest
cd frontend
npm run test
npm run lint
npm run build
```

## Adding an API Endpoint

1. Add or update Pydantic schemas in `backend/models/schemas.py` when the payload is shared.
2. Add the route to the appropriate module in `backend/api/routes/`.
3. Register a new router in `backend/main.py` if you create a new route module.
4. Add a frontend wrapper in `frontend/src/api.js` when the UI will use it.
5. Add tests for behavior with database, file, or pipeline side effects.
6. Update [API Reference](API.md).

## Adding an Agent or Pipeline Stage

1. Define state inputs and outputs in `PipelineState`.
2. Keep prompts in the agent directory.
3. Validate outputs with Pydantic models.
4. Add halt/error behavior.
5. Wire the node in `backend/agents/pipeline.py`.
6. Update architecture, schema, and testing docs.

## Current Technical Debt

- `backend/api/middleware.py` is not mounted by `backend/main.py`.
- `CORS_ALLOW_ORIGINS` is parsed but not used in `backend/main.py`.
- PostgreSQL deployment notes require adding an async PostgreSQL driver before use.
- Frontend view state is not URL-addressable.
- Some root-level historical documents remain for context and may overlap with current docs.

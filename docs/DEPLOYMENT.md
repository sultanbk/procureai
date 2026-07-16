# Deployment Guide

**Audience:** Developers and operators.

## Current Deployment Assets

The repository contains local development scripts and configuration examples. It does not contain Dockerfiles, Kubernetes manifests, GitHub Actions workflows, or other CI/CD deployment definitions.

## Local Deployment

Backend:

```powershell
.\.venv\Scripts\Activate.ps1
python -m scripts.seed_db
python backend\main.py
```

Frontend:

```powershell
cd frontend
npm run dev
```

Or use:

```powershell
.\run_dev.ps1
```

## Production-Oriented Backend Notes

Run FastAPI with an ASGI server such as Uvicorn:

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Recommended production work before exposing the API:

- Register API-key and rate-limit middleware or add stronger authentication.
- Restrict CORS origins.
- Use a managed database and add the required async driver.
- Store uploads on durable storage.
- Protect `.env` and cloud credentials.
- Run behind TLS and a reverse proxy or managed ingress.
- Add background task supervision if audit workload grows beyond in-process background tasks.

## Frontend Build

```powershell
cd frontend
npm run build
```

The build output is produced by Vite in `frontend/dist/`.

## Database

Default verified configuration:

```ini
DATABASE_URL=sqlite:///./data/procureai.db
```

PostgreSQL-style URLs are accepted by the configuration shape, but `backend/requirements.txt` currently does not include `asyncpg`. Add and validate a driver before deploying with PostgreSQL.

## File Storage

Runtime file paths:

| Path | Purpose |
|---|---|
| `data/uploads` | Uploaded PDFs |
| `watched_invoices` | Incoming auto-audit PDFs |
| `watched_invoices/processed` | Completed watched invoices |
| `watched_invoices/unmatched` | Invoices without matched contracts |
| `logs` | Optional local logs |

Production deployments should mount these paths on persistent storage or move file handling to object storage with corresponding code changes.

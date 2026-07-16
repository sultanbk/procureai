# Documentation Coverage Checklist

**Audience:** Documentation maintainers and developers.

## Coverage Status

| Area | Status | Covered by |
|---|---|---|
| Project purpose | Covered | `README.md`, `ARCHITECTURE.md` |
| Architecture | Covered | `ARCHITECTURE.md` |
| Request flow | Covered | `ARCHITECTURE.md`, `docs/API.md` |
| Data flow | Covered | `ARCHITECTURE.md` |
| API endpoints | Covered | `docs/API.md` |
| Database schema | Covered | `DATA_SCHEMAS.md`, `docs/DATABASE.md` |
| Environment variables | Covered | `docs/CONFIGURATION.md` |
| Local setup | Covered | `README.md`, `docs/DEVELOPER_GUIDE.md` |
| Frontend setup | Covered | `frontend/README.md` |
| Testing | Covered | `TESTING.md` |
| Deployment | Partially covered | `docs/DEPLOYMENT.md` |
| Security | Covered with caveats | `docs/SECURITY.md` |
| User workflows | Covered | `docs/USER_GUIDE.md` |
| Troubleshooting | Covered | `docs/TROUBLESHOOTING.md` |
| Auto-audit watcher | Covered | `docs/USER_GUIDE.md`, `docs/API.md`, `ARCHITECTURE.md` |
| Contract library | Covered | `docs/USER_GUIDE.md`, `docs/API.md` |
| Contract comparison | Covered | `docs/API.md`, `docs/USER_GUIDE.md` |
| Dispute letters | Covered | `docs/API.md`, `docs/USER_GUIDE.md` |
| Human review loop | Covered | `docs/USER_GUIDE.md`, existing human review guides |
| CI/CD | Not present | No workflow files found |
| Docker/Kubernetes | Not present | No Docker/Kubernetes files found |

## Important Assumptions

- SQLite is the only database configuration verified directly from dependencies.
- API-key/rate-limit middleware behavior is documented as implemented but inactive because it is not mounted in `backend/main.py`.
- Production deployment guidance is advisory because no production deployment manifests exist.
- Historical docs under `docs/archive/` are not current references.

## Maintenance Checklist

Before merging documentation changes:

- [ ] Confirm endpoints against `backend/api/routes/`.
- [ ] Confirm schemas against `backend/models/schemas.py`.
- [ ] Confirm tables against `backend/models/audit.py`.
- [ ] Confirm frontend workflows against `frontend/src/App.jsx` and `frontend/src/api.js`.
- [ ] Confirm commands against `package.json`, `frontend/package.json`, and `pytest.ini`.
- [ ] Confirm environment variables against `backend/core/config.py`, `backend/.env.example`, and `frontend/.env.example`.
- [ ] Run Markdown link checks manually or with a link-checking tool if available.

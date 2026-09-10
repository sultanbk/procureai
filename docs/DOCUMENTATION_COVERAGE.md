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
| Guardrails & Safety | Covered | `docs/GUARDRAILS.md` |
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

## Required Versus Optional Documents

The following documents are the maintained documentation set and should remain linked from `README.md`:

| Document | Keep? | Reason |
|---|---|---|
| `README.md` | Required | Entry point, documentation map, quick start, and current capability summary |
| `ARCHITECTURE.md` | Required | Runtime components and pipeline ownership |
| `DATA_SCHEMAS.md` | Required | Pydantic contracts and persistence reference |
| `docs/API.md` | Required | Integration contract for frontend and API consumers |
| `docs/CONFIGURATION.md` | Required | Runtime environment and feature switches |
| `docs/DEVELOPER_GUIDE.md` | Required | Contributor setup and extension workflow |
| `docs/USER_GUIDE.md` | Required | User-facing workflows and limitations |
| `docs/DATABASE.md` | Required | Local database lifecycle and retention behavior |
| `docs/SECURITY.md` | Required | Security boundary and production caveats |
| `docs/GUARDRAILS.md` | Required | 6-layer defense-in-depth safety architecture and operational guide |
| `docs/TROUBLESHOOTING.md` | Required | Recovery guidance for common failures |
| `docs/DEPLOYMENT.md` | Required | Local deployment and explicit production gaps |
| `TESTING.md` | Required | Backend, frontend, and evaluation commands |
| `frontend/README.md` | Required | Frontend-specific setup and scripts |
| `PROJECT_CONVENTIONS.md` | Required | Code and documentation conventions |
| `PROGRESS_TRACKER.md` | Optional history | Useful build/session log, but not an architecture specification |
| `ONE_PAGER.md`, `ARCHITECTURE_PITCH.md`, `CONTEST_PITCH.md`, `DEMO_PITCH.md`, and `pcf_demo_package.md` | Optional | Contest, approval, demo, or presentation material rather than operating documentation |
| `architecture_v4.md` | Optional planning note | Retain only as design history; the implemented workflow is documented in `ARCHITECTURE.md` |
| `PROMPTS.md` | Optional reference | Prompt/design reference; source prompt files under `backend/agents/` are authoritative |
| `docs/human_review_guide.md` and `docs/needs_human_review_guide.md` | Optional | Keep only if the team actively uses the longer human-review process; otherwise consolidate into `docs/USER_GUIDE.md` |
| `docs/archive/` | Archive only | Historical plans and audits; do not link as current behavior |
| `docs/visuals/` | Optional artifacts | Generated visuals, not required for setup or operation |

No current operational document is redundant enough to delete. The clearest consolidation candidate is the pair of human-review guides, but that should be done only after confirming which one the team uses.

## Maintenance Checklist

Before merging documentation changes:

- [ ] Confirm endpoints against `backend/api/routes/`.
- [ ] Confirm schemas against `backend/models/schemas.py`.
- [ ] Confirm tables against `backend/models/audit.py`.
- [ ] Confirm frontend workflows against `frontend/src/App.jsx` and `frontend/src/api.js`.
- [ ] Confirm commands against `package.json`, `frontend/package.json`, and `pytest.ini`.
- [ ] Confirm environment variables against `backend/core/config.py`, `backend/.env.example`, and `frontend/.env.example`.
- [ ] Run Markdown link checks manually or with a link-checking tool if available.

# SupplierGuard Frontend

**Audience:** Frontend developers.

This is the React/Vite client for SupplierGuard / ProcureAI. It renders the audit portal, calls the FastAPI backend through `src/api.js`, and uses Tailwind CSS, Lucide icons, Recharts, jsPDF, and local component primitives.

## Setup

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

Default development URL:

```text
http://localhost:5173
```

## Environment

| Variable | Purpose | Default behavior |
|---|---|---|
| `VITE_API_URL` | Backend origin | Falls back to `http://127.0.0.1:8000` in `src/api.js` |
| `VITE_API_KEY` | Optional API key sent as `X-API-Key` | Not set by default |

Example:

```ini
VITE_API_URL=http://localhost:8000
VITE_API_KEY=
```

## Scripts

```powershell
npm run dev
npm run test
npm run lint
npm run build
npm run preview
```

## Application Structure

| Path | Purpose |
|---|---|
| `src/App.jsx` | State-based view routing and top-level page orchestration |
| `src/api.js` | Centralized backend API client |
| `src/pages/` | Main application views |
| `src/components/` | Report, audit, drawer, modal, layout, and reusable UI components |
| `src/components/ui/` | Shared design primitives |
| `src/components/layout/` | Sidebar and page shell |
| `src/utils/chartTheme.js` | Chart styling helpers |

## Implemented Views

- Audit list
- Upload and risk prediction
- Audit progress and logs
- Audit report with evidence, dispute letter, Q&A, and feedback loop
- Supplier scorecard
- Supplier history and negotiation briefs
- Analytics and clause heatmap
- Contract library
- Auto-audit watcher
- Contract comparison
- Notification settings

Navigation is currently stored in React state rather than a URL router. Direct deep links to specific views are not implemented in `src/App.jsx`.

# ProcureAI Testing Architecture

**Audience:** Developers.

SupplierGuard uses pytest for backend tests and Vitest with React Testing Library for frontend tests.

## Backend Tests

Run from the repository root:

```powershell
python -m pytest
```

`pytest.ini` configures:

- `testpaths = tests`
- `python_files = test_*.py`
- `asyncio_mode = auto`
- verbose output and short tracebacks

`tests/conftest.py` forces:

```python
MOCK_LLM=true
ALLOW_MOCK_LLM=true
GEMINI_API_KEY=
```

This prevents routine tests from calling live Gemini or Vertex AI APIs.

## Test Layout

| Path | Current purpose |
|---|---|
| `tests/unit/test_billing_regressions.py` | Unit regression coverage for billing/rule behavior |
| `tests/integration/test_contract_library.py` | Integration coverage for contract library behavior |
| `tests/conftest.py` | Async in-memory SQLite fixtures and mock LLM safety |
| `scripts/test_real_ippb_parser.py` | Script-style real parser check for IPPB sample data |
| `scripts/test_real_ippb_pipeline.py` | Script-style real pipeline check for IPPB sample data |

## Frontend Tests

Run from `frontend/`:

```powershell
npm run test
```

The frontend uses Vitest. `frontend/src/setupTests.js` configures test setup.

## Frontend Lint and Build

```powershell
cd frontend
npm run lint
npm run build
```

## Evaluation Harness

The repository includes `backend/eval/harness.py` and `data/eval/test_cases.json`. Run from the repository root:

```powershell
$env:PYTHONPATH="."
python -m backend.eval.harness
```

Assumption: evaluation behavior depends on local data and LLM/mock configuration. Treat generated metrics as local run artifacts rather than stable documentation unless the report is committed and reviewed.

## Suggested Validation Before Documentation or Release Changes

```powershell
python -m pytest
cd frontend
npm run test
npm run lint
npm run build
```

If live LLM behavior is being changed, run targeted real-data scripts only after confirming credentials, billing expectations, and `MOCK_LLM` settings.

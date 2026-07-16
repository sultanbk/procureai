# Troubleshooting

**Audience:** Developers and users.

## Backend Fails to Start

Check Python dependencies:

```powershell
pip install -r backend\requirements.txt
```

Check database initialization:

```powershell
python -m scripts.seed_db
```

Check `.env` path. The backend loads root `.env` and `backend/.env`.

## Frontend Cannot Reach Backend

Confirm backend is running:

```text
http://localhost:8000/api/health
```

Confirm `frontend/.env`:

```ini
VITE_API_URL=http://localhost:8000
```

Restart Vite after changing environment variables.

## PDF Extraction Fails

The extractor uses `pdfplumber` first and `pypdf` as fallback. Scanned image-only PDFs usually fail because they have no embedded text.

Use text-based PDFs or add OCR before ingestion.

## Audit Stays Pending or Fails

Check:

- `/api/audit/{audit_id}/logs`
- Backend console logs
- LLM configuration
- PDF text extractability
- Database writability

For local mock mode, ensure both are set:

```ini
MOCK_LLM=true
ALLOW_MOCK_LLM=true
```

## Live LLM Calls Fail

For Gemini Developer API, verify `GEMINI_API_KEY`.

For Vertex AI, verify:

- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- application default credentials or `GOOGLE_APPLICATION_CREDENTIALS`
- Vertex AI API permissions

## Auto-Audit Does Not Process Files

Check watcher status:

```text
GET /api/watcher/status
```

Make sure:

- The backend is running.
- Files are placed directly in `watched_invoices/`, not a subdirectory.
- Files have `.pdf` extension.
- The watcher is not paused.
- Matching contracts exist and are active in the Contract Library.

Unmatched files move to `watched_invoices/unmatched/`.

## Contract Q&A Returns Not Found

Possible causes:

- Audit ID does not exist.
- Rulebook or chunks are unavailable.
- Contract text did not contain the requested topic.
- LLM/mock response could not cite the relevant clause.

Registering a contract in the library can prebuild a baseline rulebook and chunks.

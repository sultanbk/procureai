import time
import vertexai
from vertexai.generative_models import GenerativeModel
from backend.models.schemas import InvoiceData
from backend.core.schema_utils import clean_vertex_schema

models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-3.7-flash",
    "gemini-3.7-flash-preview",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.8-flash",
]

locations = ["global", "us-central1"]

for loc in locations:
    print(f"\n==========================================")
    print(f"Testing Location: {loc} on project 'supplierguard'")
    print(f"==========================================")
    try:
        vertexai.init(project="supplierguard", location=loc)
    except Exception as init_err:
        print(f"Failed to init location {loc}: {init_err}")
        continue

    for model_name in models_to_test:
        print(f"\n--- Model: {model_name} ({loc}) ---")
        start = time.time()
        try:
            m = GenerativeModel(model_name)
            resp = m.generate_content("Say OK in one word", generation_config={"temperature": 0.0})
            elapsed = time.time() - start
            print(f"  [Simple Prompt]: SUCCESS in {elapsed:.2f}s -> Response: {resp.text.strip()[:60]}")
            
            # Now test structured JSON generation with invoice schema
            schema = clean_vertex_schema(InvoiceData.model_json_schema())
            config = {
                "response_mime_type": "application/json",
                "response_schema": schema,
                "temperature": 0.0,
            }
            start_schema = time.time()
            schema_resp = m.generate_content(
                "Extract invoice: Invoice ID INV-001, Date 2026-06-01, Total $500, Item: Produce Box, Qty 100, Rate 5.00",
                generation_config=config
            )
            elapsed_schema = time.time() - start_schema
            print(f"  [Structured Schema]: SUCCESS in {elapsed_schema:.2f}s")
        except Exception as e:
            elapsed = time.time() - start
            err_msg = str(e)
            print(f"  [FAILED in {elapsed:.2f}s]: {err_msg[:200]}")

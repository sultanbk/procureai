"""
FILE CANONICAL IDENTIFIER: backend/core/llm_client.py
MODULE ROLE: Interfaces with Google Gemini via Vertex AI API or returns local mock data if enabled.
SYSTEM BOUNDARY: The cognitive LLM driver for all contract parsing, invoice extraction, and compliance checking.
STATE DEPENDENCY / DATA CONTRACTS: Imports get_mock_response from backend.core.mock_router and clean_vertex_schema from backend.core.schema_utils.
CRITICAL LOGIC: Manages LLM client initialization, rate limits, retries, and test mock configurations.
"""

import os
import time
import google.generativeai as genai
import structlog
from backend.core.config import LLM_RETRY_ATTEMPTS, LLM_RETRY_DELAY_SECONDS
from backend.core.mock_router import get_mock_response
from backend.core.schema_utils import clean_vertex_schema

logger = structlog.get_logger()


def is_mock_llm_enabled() -> bool:
    mock_requested = os.getenv("MOCK_LLM", "false").strip().lower() in {"1", "true", "yes", "on"}
    mock_allowed = os.getenv("ALLOW_MOCK_LLM", "false").strip().lower() in {"1", "true", "yes", "on"}
    return mock_requested and mock_allowed


class SmartGenerativeModel:
    def __init__(self, real_model, provider="mock", model_name=None, project=None, location=None):
        self.real_model = real_model
        self.provider = provider
        self.model_name = model_name
        self.project = project
        self.location = location

    def status_label(self) -> str:
        if is_mock_llm_enabled():
            return "Mock LLM"
        if self.real_model:
            if self.provider == "vertex":
                return f"Vertex AI Gemini ({self.model_name}, project={self.project}, location={self.location})"
            return f"Gemini Developer API ({self.model_name})"
        return "No live LLM configured"

    def generate_content(self, contents, generation_config=None):
        try:
            if is_mock_llm_enabled():
                logger.info("MOCK_LLM is set to true. Forcing mock LLM response.")
                return get_mock_response(contents, generation_config)
                
            if self.real_model:
                # If generation_config is a google.generativeai.GenerationConfig, convert it to a dictionary
                # to prevent type mismatch issues when using the Vertex SDK client.
                if generation_config is not None and not isinstance(generation_config, dict):
                    config_dict = {}
                    for key in ["response_mime_type", "response_schema", "temperature", "max_output_tokens", "top_p", "top_k", "candidate_count", "stop_sequences"]:
                        val = getattr(generation_config, key, None)
                        if val is not None:
                            config_dict[key] = val
                    generation_config = config_dict
                
                if isinstance(generation_config, dict) and "response_schema" in generation_config:
                    generation_config["response_schema"] = clean_vertex_schema(generation_config["response_schema"])
                    
                last_error = None
                for attempt in range(1, max(LLM_RETRY_ATTEMPTS, 1) + 1):
                    try:
                        return self.real_model.generate_content(contents, generation_config=generation_config)
                    except Exception as exc:
                        last_error = exc
                        if attempt >= max(LLM_RETRY_ATTEMPTS, 1):
                            raise
                        logger.warning(
                            "GenerativeModel call failed; retrying.",
                            attempt=attempt,
                            max_attempts=LLM_RETRY_ATTEMPTS,
                            error=str(exc),
                        )
                        time.sleep(LLM_RETRY_DELAY_SECONDS)
                raise last_error
            else:
                if not is_mock_llm_enabled():
                    raise RuntimeError("No real generative model initialized. Check Vertex AI / API credentials.")
                logger.warning("No real generative model initialized. Falling back to mock generator.")
                return get_mock_response(contents, generation_config)
        except Exception as e:
            if not is_mock_llm_enabled():
                logger.error("GenerativeModel call failed.", error=str(e))
                raise e
            logger.warning("GenerativeModel call failed. Falling back to mock response.", error=str(e))
            return get_mock_response(contents, generation_config)

    async def async_generate_content(self, contents, generation_config=None):
        """
        Non-blocking async wrapper around generate_content with timeout.
        Runs the synchronous LLM API call in a thread pool to avoid blocking
        the asyncio event loop (critical for FastAPI concurrent request handling).
        Raises asyncio.TimeoutError if the call exceeds LLM_CALL_TIMEOUT_SECONDS.
        """
        import asyncio
        from backend.core.config import LLM_CALL_TIMEOUT_SECONDS
        return await asyncio.wait_for(
            asyncio.to_thread(self.generate_content, contents, generation_config),
            timeout=LLM_CALL_TIMEOUT_SECONDS
        )

    def generate_content_stream(self, contents, generation_config=None):
        try:
            if is_mock_llm_enabled():
                logger.info("MOCK_LLM is set to true. Forcing mock streaming response.")
                return self._mock_stream(contents, generation_config)
                
            if self.real_model:
                config = generation_config
                if config is not None and not isinstance(config, dict):
                    config_dict = {}
                    for key in ["response_mime_type", "response_schema", "temperature", "max_output_tokens", "top_p", "top_k", "candidate_count", "stop_sequences"]:
                        val = getattr(config, key, None)
                        if val is not None:
                            config_dict[key] = val
                    config = config_dict
                
                if isinstance(config, dict) and "response_schema" in config:
                    config["response_schema"] = clean_vertex_schema(config["response_schema"])
                
                if hasattr(self.real_model, "generate_content_stream"):
                    return self.real_model.generate_content_stream(contents, generation_config=config)
                else:
                    return self.real_model.generate_content(contents, generation_config=config, stream=True)
            else:
                if not is_mock_llm_enabled():
                    raise RuntimeError("No real generative model initialized. Check Vertex AI / API credentials.")
                logger.warning("No real generative model initialized. Falling back to mock stream.")
                return self._mock_stream(contents, generation_config)
        except Exception as e:
            if not is_mock_llm_enabled():
                logger.error("GenerativeModel streaming call failed.", error=str(e))
                raise e
            logger.warning("GenerativeModel streaming call failed. Falling back to mock stream.", error=str(e))
            return self._mock_stream(contents, generation_config)

    def _mock_stream(self, contents, generation_config=None):
        import time
        mock_resp = get_mock_response(contents, generation_config)
        text = mock_resp.text
        words = text.split(" ")
        class MockChunk:
            def __init__(self, text):
                self.text = text
        for i in range(0, len(words), 3):
            chunk_text = " ".join(words[i:i+3]) + (" " if i+3 < len(words) else "")
            yield MockChunk(chunk_text)
            time.sleep(0.02)


    def create_document_part(self, data: bytes, mime_type: str):
        if self.provider == "vertex":
            from vertexai.generative_models import Part
            return Part.from_data(data=data, mime_type=mime_type)
        elif self.provider == "developer_api":
            return {"mime_type": mime_type, "data": data}
        else:
            class MockPart:
                def __init__(self, data, mime_type):
                    self.data = data
                    self.mime_type = mime_type
            return MockPart(data, mime_type)

# --- Singleton Provider ---

_llm_instance = None


def get_llm():
    """
    Returns a configured SmartGenerativeModel client instance (singleton).
    Attempts standard SDK or Vertex AI. Mock mode requires MOCK_LLM=true and ALLOW_MOCK_LLM=true.
    """
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    api_key = os.getenv("GEMINI_API_KEY")
    real_model = None
    provider = "mock"
    project = None
    location = None

    if api_key:
        logger.info("Initializing developer Gemini SDK", model=model_name)
        try:
            genai.configure(api_key=api_key)
            real_model = genai.GenerativeModel(model_name)
            provider = "developer_api"
        except Exception as e:
            logger.error("Failed to initialize developer SDK", error=str(e))
    else:
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "procureai")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        logger.info("GEMINI_API_KEY not found. Attempting Vertex AI initialization...", project=project, location=location)
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            vertexai.init(project=project, location=location)
            real_model = GenerativeModel(model_name)
            provider = "vertex"
            logger.info("Vertex AI initialized successfully", model=model_name)
        except Exception as e:
            logger.warning("Failed to initialize Vertex AI client", error=str(e))

    _llm_instance = SmartGenerativeModel(
        real_model,
        provider=provider,
        model_name=model_name,
        project=project,
        location=location,
    )
    return _llm_instance

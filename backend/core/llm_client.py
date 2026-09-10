"""
FILE CANONICAL IDENTIFIER: backend/core/llm_client.py
MODULE ROLE: Interfaces with LLM providers (Google Gemini, Groq, etc.) for all contract parsing, invoice extraction, and compliance checking.
SYSTEM BOUNDARY: The cognitive LLM driver for all contract parsing, invoice extraction, and compliance checking.
STATE DEPENDENCY / DATA CONTRACTS: Imports get_mock_response from backend.core.mock_router and clean_vertex_schema from backend.core.schema_utils.
CRITICAL LOGIC: Manages LLM client initialization, rate limits, retries, and test mock configurations. Supports multiple providers: gemini (Vertex/GCP), groq (free/fast), and mock mode.
"""

import os
import time
import json
import structlog
from dataclasses import dataclass, field
from typing import Optional, List

import google.generativeai as genai

from backend.core.config import LLM_RETRY_ATTEMPTS, LLM_RETRY_DELAY_SECONDS
from backend.core.mock_router import get_mock_response
from backend.core.schema_utils import clean_vertex_schema
from backend.core.token_budget import TokenBudget
from backend.core.llm_rate_limiter import get_rate_limiter

logger = structlog.get_logger()


# --- Fix #13: Proper response wrapper dataclasses (replaces dynamic type() objects) ---

@dataclass
class StreamDelta:
    content: str = ""

@dataclass
class StreamChoice:
    delta: StreamDelta = field(default_factory=StreamDelta)

@dataclass
class StreamChunk:
    choices: List[StreamChoice] = field(default_factory=list)

@dataclass
class ResponseMessage:
    content: str = ""

@dataclass
class ResponseChoice:
    message: ResponseMessage = field(default_factory=ResponseMessage)

@dataclass
class ResponseUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    candidates_token_count: int = 0

@dataclass
class CompatibleResponse:
    choices: List[ResponseChoice] = field(default_factory=list)
    usage: ResponseUsage = field(default_factory=ResponseUsage)

@dataclass
class MockChunkObj:
    text: str = ""


class OpenAICompatibleClient:
    """Lightweight HTTP client for standard OpenAI-compatible endpoints (OmniRoute, vLLM, Ollama, etc.)."""
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        url = base_url.rstrip("/")
        if not url.endswith("/v1"):
            url = f"{url}/v1"
        self.base_url = url
        self.chat = self.Chat(self)

    class Chat:
        def __init__(self, client):
            self.completions = self.Completions(client)

        class Completions:
            def __init__(self, client):
                self.client = client

            def create(self, **kwargs):
                import httpx
                endpoint = f"{self.client.base_url}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.client.api_key}",
                    "Content-Type": "application/json",
                }
                stream = kwargs.get("stream", False)
                timeout = kwargs.get("timeout", 120.0)

                payload = {k: v for k, v in kwargs.items() if k not in ("timeout",) and v is not None}

                if stream:
                    def stream_generator():
                        with httpx.Client(timeout=timeout) as client:
                            with client.stream("POST", endpoint, headers=headers, json=payload) as resp:
                                resp.raise_for_status()
                                for line in resp.iter_lines():
                                    if line.startswith("data: "):
                                        data_str = line[6:].strip()
                                        if data_str == "[DONE]":
                                            break
                                        try:
                                            chunk_data = json.loads(data_str)
                                            choices = chunk_data.get("choices", [])
                                            if choices:
                                                delta = choices[0].get("delta", {})
                                                content = delta.get("content", "")
                                                if content:
                                                    yield StreamChunk(choices=[StreamChoice(delta=StreamDelta(content=content))])
                                        except Exception:
                                            continue
                    return stream_generator()
                else:
                    with httpx.Client(timeout=timeout) as client:
                        resp = client.post(endpoint, headers=headers, json=payload)
                        resp.raise_for_status()
                        raw_text = resp.text.strip() if resp.text else ""
                        if not raw_text:
                            raise RuntimeError(f"Empty HTTP response received from OmniRoute/LLM server (HTTP {resp.status_code})")

                        # If response is SSE stream (text/event-stream or contains data: prefixes)
                        if "data:" in raw_text:
                            full_content = ""
                            prompt_tokens = 0
                            completion_tokens = 0
                            for line in raw_text.splitlines():
                                line = line.strip()
                                if line.startswith("data: "):
                                    data_str = line[6:].strip()
                                    if data_str == "[DONE]":
                                        break
                                    try:
                                        chunk = json.loads(data_str)
                                        choices = chunk.get("choices", [])
                                        if choices:
                                            delta = choices[0].get("delta", {})
                                            content = delta.get("content", "")
                                            if content:
                                                full_content += content
                                        usage = chunk.get("usage")
                                        if usage:
                                            prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
                                            completion_tokens = usage.get("completion_tokens", completion_tokens)
                                    except Exception:
                                        continue

                            return CompatibleResponse(
                                choices=[ResponseChoice(message=ResponseMessage(content=full_content))],
                                usage=ResponseUsage(
                                    prompt_tokens=prompt_tokens,
                                    completion_tokens=completion_tokens,
                                    candidates_token_count=completion_tokens,
                                ),
                            )

                        # Otherwise standard JSON response
                        try:
                            data = json.loads(raw_text)
                        except Exception as exc:
                            raise RuntimeError(f"OmniRoute returned non-JSON payload: {raw_text[:200]}") from exc

                        raw_choices = data.get("choices", [])
                        msg_content = raw_choices[0].get("message", {}).get("content", "") if raw_choices else ""
                        raw_usage = data.get("usage", {})
                        return CompatibleResponse(
                            choices=[ResponseChoice(message=ResponseMessage(content=msg_content))],
                            usage=ResponseUsage(
                                prompt_tokens=raw_usage.get("prompt_tokens", 0),
                                completion_tokens=raw_usage.get("completion_tokens", 0),
                                total_tokens=raw_usage.get("total_tokens", 0),
                            ),
                        )


class GroqResponseWrapper:
    """Wrapper to make Groq / OpenAI response compatible with Gemini response format."""
    def __init__(self, response):
        self._response = response

    @property
    def text(self) -> str:
        """Extract text content from Groq/OpenAI response."""
        if self._response and hasattr(self._response, 'choices') and self._response.choices:
            return self._response.choices[0].message.content or "{}"
        return "{}"

    @property
    def usage_metadata(self):
        """Extract usage metadata from Groq/OpenAI response."""
        class UsageMetadata:
            def __init__(self, prompt_tokens, response_tokens):
                self.prompt_token_count = prompt_tokens
                self.candidates_token_count = response_tokens
        if hasattr(self._response, 'usage'):
            return UsageMetadata(
                self._response.usage.prompt_tokens,
                self._response.usage.completion_tokens
            )
        return None


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
        self.rate_limiter = get_rate_limiter()

    def _record_tokens(self, response, budget: Optional[TokenBudget] = None):
        """Helper to extract token usage and update TokenBudget and LLMRateLimiter."""
        if response is None:
            return response
        prompt_tok = 0
        comp_tok = 0
        um = getattr(response, "usage_metadata", None)
        if um:
            prompt_tok = getattr(um, "prompt_token_count", 0) or 0
            comp_tok = getattr(um, "candidates_token_count", 0) or 0
        elif hasattr(response, "usage") and response.usage:
            prompt_tok = getattr(response.usage, "prompt_tokens", 0) or 0
            comp_tok = getattr(response.usage, "completion_tokens", 0) or 0

        # Approximate if usage metadata missing
        if prompt_tok == 0 and comp_tok == 0 and hasattr(response, "text") and response.text:
            comp_tok = max(1, len(response.text) // 4)
            prompt_tok = 100

        if budget is not None:
            budget.record(prompt_tokens=prompt_tok, completion_tokens=comp_tok, agent=self.model_name or "llm")
        if self.rate_limiter is not None:
            self.rate_limiter.record_usage(prompt_tok + comp_tok)
        return response

    def status_label(self) -> str:
        if is_mock_llm_enabled():
            return "Mock LLM"
        if self.real_model:
            if self.provider == "vertex":
                return f"Vertex AI Gemini ({self.model_name}, project={self.project}, location={self.location})"
            elif self.provider in ("groq", "omniroute"):
                return f"OmniRoute / Groq ({self.model_name})"
            return f"Gemini Developer API ({self.model_name})"
        return "No live LLM configured"

    def generate_content(self, contents, generation_config=None, budget: Optional[TokenBudget] = None):
        try:
            if is_mock_llm_enabled():
                logger.info("MOCK_LLM is set to true. Forcing mock LLM response.")
                return self._record_tokens(get_mock_response(contents, generation_config), budget=budget)

            if self.real_model:
                # Handle Groq provider (OpenAI-compatible API)
                if self.provider == "groq":
                    return self._record_tokens(self._groq_generate_content(contents, generation_config), budget=budget)

                # Handle Google providers
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
                        return self._record_tokens(self.real_model.generate_content(contents, generation_config=generation_config), budget=budget)
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
                return self._record_tokens(get_mock_response(contents, generation_config), budget=budget)
        except Exception as e:
            if not is_mock_llm_enabled():
                logger.error("GenerativeModel call failed.", error=str(e))
                raise e
            logger.warning("GenerativeModel call failed. Falling back to mock response.", error=str(e))
            return self._record_tokens(get_mock_response(contents, generation_config), budget=budget)

    def _groq_generate_content(self, contents, generation_config=None):
        """Generate content using Groq's OpenAI-compatible API."""
        # Build messages from contents
        messages = self._build_groq_messages(contents)

        # Build Groq parameters
        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.0,
        }

        # Map generation_config to Groq parameters
        response_schema = None
        if generation_config:
            if isinstance(generation_config, dict):
                if "temperature" in generation_config:
                    params["temperature"] = generation_config["temperature"]
                if "max_output_tokens" in generation_config:
                    params["max_tokens"] = generation_config["max_output_tokens"]
                if "top_p" in generation_config:
                    params["top_p"] = generation_config["top_p"]
                response_schema = generation_config.get("response_schema")
            else:
                # Handle GenerationConfig object
                for key in ["temperature", "max_output_tokens", "top_p"]:
                    val = getattr(generation_config, key, None)
                    if val is not None:
                        if key == "max_output_tokens":
                            params["max_tokens"] = val
                        else:
                            params[key] = val
                response_schema = getattr(generation_config, "response_schema", None)

        # Make the API call
        last_error = None
        for attempt in range(1, max(LLM_RETRY_ATTEMPTS, 1) + 1):
            try:
                # For structured JSON output, Groq expects response_format
                if response_schema:
                    # Use JSON mode for structured output
                    params["response_format"] = {"type": "json_object"}

                response = self.real_model.chat.completions.create(**params)
                return GroqResponseWrapper(response)
            except Exception as exc:
                last_error = exc
                if attempt >= max(LLM_RETRY_ATTEMPTS, 1):
                    raise
                logger.warning(
                    "Groq API call failed; retrying.",
                    attempt=attempt,
                    max_attempts=LLM_RETRY_ATTEMPTS,
                    error=str(exc),
                )
                time.sleep(LLM_RETRY_DELAY_SECONDS)
        raise last_error

    def _build_groq_messages(self, contents):
        """Convert contents to Groq/OpenAI message format."""
        messages = []
        system_prompt = None
        user_content = None

        for content in contents:
            if hasattr(content, 'parts'):
                # Handle Gemini-style content objects with parts
                for part in content.parts:
                    if hasattr(part, 'text'):
                        if system_prompt is None:
                            system_prompt = part.text
                        else:
                            if user_content:
                                user_content += part.text
                            else:
                                user_content = part.text
            elif isinstance(content, str):
                if system_prompt is None and not messages:
                    # First string is likely the system prompt
                    system_prompt = content
                else:
                    # Subsequent strings are user content
                    if user_content:
                        user_content += "\n" + content
                    else:
                        user_content = content
            elif isinstance(content, dict) and "mime_type" in content:
                # Handle inline document parts - just note them
                pass

        # Build messages list
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if user_content:
            messages.append({"role": "user", "content": user_content})

        # Ensure we have at least one message
        if not messages:
            messages.append({"role": "user", "content": ""})

        return messages

    async def async_generate_content(self, contents, generation_config=None, budget: Optional[TokenBudget] = None):
        """
        Non-blocking async wrapper around generate_content with rate limiting and timeout.
        Runs the synchronous LLM API call in a thread pool to avoid blocking
        the asyncio event loop (critical for FastAPI concurrent request handling).
        Raises asyncio.TimeoutError if the call exceeds LLM_CALL_TIMEOUT_SECONDS.
        """
        import asyncio
        from backend.core.config import LLM_CALL_TIMEOUT_SECONDS
        if self.rate_limiter is not None:
            try:
                await self.rate_limiter.acquire(estimated_tokens=1000)
            except Exception as exc:
                logger.warning("LLM rate limiter warning", error=str(exc))
        return await asyncio.wait_for(
            asyncio.to_thread(self.generate_content, contents, generation_config, budget),
            timeout=LLM_CALL_TIMEOUT_SECONDS
        )

    def generate_content_stream(self, contents, generation_config=None):
        try:
            if is_mock_llm_enabled():
                logger.info("MOCK_LLM is set to true. Forcing mock streaming response.")
                return self._mock_stream(contents, generation_config)

            if self.real_model:
                # Handle Groq streaming
                if self.provider == "groq":
                    return self._groq_stream(contents, generation_config)

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

    def _groq_stream(self, contents, generation_config=None):
        """Stream response from Groq API."""
        messages = self._build_groq_messages(contents)
        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.0,
            "stream": True,
        }

        if generation_config:
            if isinstance(generation_config, dict):
                if "temperature" in generation_config:
                    params["temperature"] = generation_config["temperature"]
                if "max_output_tokens" in generation_config:
                    params["max_tokens"] = generation_config["max_output_tokens"]
                if "top_p" in generation_config:
                    params["top_p"] = generation_config["top_p"]

        response = self.real_model.chat.completions.create(**params)
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield MockChunkObj(text=chunk.choices[0].delta.content)

    def _mock_stream(self, contents, generation_config=None):
        import time
        mock_resp = get_mock_response(contents, generation_config)
        text = mock_resp.text
        words = text.split(" ")
        for i in range(0, len(words), 3):
            chunk_text = " ".join(words[i:i+3]) + (" " if i+3 < len(words) else "")
            yield MockChunkObj(text=chunk_text)
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
    Supports multiple providers: vertex (GCP), omniroute, groq, gemini (Developer API).
    Mock mode requires MOCK_LLM=true and ALLOW_MOCK_LLM=true.
    """
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    provider_pref = os.getenv("LLM_PROVIDER", "").strip().lower()

    # 1. Prioritize Vertex AI if requested explicitly (e.g. LLM_PROVIDER=vertex, vertexai, gcp)
    if provider_pref in {"vertex", "vertexai", "gcp"}:
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "supplierguard")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        model_name = os.getenv("VERTEX_MODEL") or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

        logger.info("Initializing Vertex AI client (GCP)", project=project, location=location, model=model_name)
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            vertexai.init(project=project, location=location)
            real_model = GenerativeModel(model_name)
            _llm_instance = SmartGenerativeModel(
                real_model,
                provider="vertex",
                model_name=model_name,
                project=project,
                location=location,
            )
            logger.info("Vertex AI initialized successfully", project=project, location=location, model=model_name)
            return _llm_instance
        except Exception as e:
            logger.error("Failed to initialize Vertex AI client", error=str(e), project=project, location=location)
            raise RuntimeError(f"Vertex AI initialization failed for project '{project}': {e}") from e

    # 2. Prioritize OmniRoute / Groq if requested explicitly
    if provider_pref in {"omniroute", "groq", "openai"} or (not provider_pref and os.getenv("GROQ_API_KEY") and not os.getenv("GEMINI_API_KEY")):
        groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
        if groq_api_key:
            model_name = os.getenv("GROQ_MODEL") or os.getenv("ANTHROPIC_DEFAULT_OPUS_MODEL", "oc/nemotron-3-ultra-free")
            base_url = os.getenv("GROQ_BASE_URL") or os.getenv("ANTHROPIC_BASE_URL", "http://localhost:20128/v1")
            logger.info("Initializing OmniRoute/OpenAI client", model=model_name, base_url=base_url)
            try:
                if base_url:
                    real_model = OpenAICompatibleClient(api_key=groq_api_key, base_url=base_url)
                else:
                    from groq import Groq as GroqClient
                    real_model = GroqClient(api_key=groq_api_key)

                _llm_instance = SmartGenerativeModel(
                    real_model,
                    provider="groq",
                    model_name=model_name,
                )
                logger.info("OmniRoute/OpenAI client initialized successfully", model=model_name, base_url=base_url)
                return _llm_instance
            except Exception as e:
                logger.error("Failed to initialize Groq/OmniRoute client", error=str(e))

    # 3. Check for Google AI Studio API key
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if gemini_api_key and provider_pref not in {"omniroute", "groq"}:
        logger.info("Initializing Google AI Studio Gemini SDK", model=gemini_model)
        try:
            genai.configure(api_key=gemini_api_key)
            real_model = genai.GenerativeModel(gemini_model)
            _llm_instance = SmartGenerativeModel(
                real_model,
                provider="developer_api",
                model_name=gemini_model,
            )
            logger.info("Google AI Studio Gemini initialized successfully", model=gemini_model)
            return _llm_instance
        except Exception as e:
            logger.error("Failed to initialize Google AI Studio Gemini SDK", error=str(e))

    # 4. Fallback to Groq / OmniRoute if available
    groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
    if groq_api_key and not provider_pref:
        model_name = os.getenv("GROQ_MODEL") or os.getenv("ANTHROPIC_DEFAULT_OPUS_MODEL", "oc/nemotron-3-ultra-free")
        base_url = os.getenv("GROQ_BASE_URL") or os.getenv("ANTHROPIC_BASE_URL", "http://localhost:20128/v1")
        logger.info("Initializing fallback Groq/OmniRoute client", model=model_name, base_url=base_url)
        try:
            if base_url:
                real_model = OpenAICompatibleClient(api_key=groq_api_key, base_url=base_url)
            else:
                from groq import Groq as GroqClient
                real_model = GroqClient(api_key=groq_api_key)

            _llm_instance = SmartGenerativeModel(
                real_model,
                provider="groq",
                model_name=model_name,
            )
            logger.info("Groq/OmniRoute client initialized successfully", model=model_name, base_url=base_url)
            return _llm_instance
        except Exception as e:
            logger.error("Failed to initialize Groq client", error=str(e))

    # 5. Fallback to Vertex AI / GCP
    model_name = gemini_model
    real_model = None
    provider = "mock"
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "supplierguard")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    logger.info("Attempting Vertex AI initialization...", project=project, location=location)
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


def reset_llm() -> None:
    """
    Fix #14: Clears the cached LLM singleton so the next call to get_llm()
    re-initializes with current environment settings. Call this when LLM
    provider configuration changes at runtime (e.g. via the Settings page).
    """
    global _llm_instance
    _llm_instance = None
    logger.info("LLM client singleton cleared. Next get_llm() call will re-initialize.")
"""LLM client wrapper for agent decision making."""

import hashlib
import logging
import time
from dataclasses import dataclass

from hamlet.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from an LLM call."""

    content: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    cached: bool = False
    latency_ms: float = 0


class ResponseCache:
    """Simple in-memory cache for LLM responses."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[LLMResponse, float]] = {}

    def _make_key(self, prompt: str, model: str) -> str:
        """Create cache key from prompt and model."""
        content = f"{model}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, prompt: str, model: str) -> LLMResponse | None:
        """Get cached response if available and not expired."""
        key = self._make_key(prompt, model)
        if key in self._cache:
            response, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                response.cached = True
                return response
            else:
                del self._cache[key]
        return None

    def set(self, prompt: str, model: str, response: LLMResponse) -> None:
        """Cache a response."""
        if len(self._cache) >= self.max_size:
            # Remove oldest entries
            sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][1])
            for key in sorted_keys[: len(sorted_keys) // 4]:
                del self._cache[key]

        key = self._make_key(prompt, model)
        self._cache[key] = (response, time.time())

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()


class LLMClient:
    """Client for making LLM API calls."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        use_cache: bool = True,
    ):
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.llm_model
        self.cache = ResponseCache() if use_cache else None
        self._client = None

    @property
    def client(self):
        """Lazy-load the Anthropic client."""
        if self._client is None:
            try:
                import anthropic

                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                logger.error("anthropic package not installed")
                raise
        return self._client

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        use_cache: bool = True,
    ) -> LLMResponse:
        """Make a completion request to the LLM."""
        # Check cache first
        if use_cache and self.cache:
            cached = self.cache.get(prompt, self.model)
            if cached:
                logger.debug("Cache hit for LLM request")
                return cached

        # Make API call
        start_time = time.time()

        try:
            messages = [{"role": "user", "content": prompt}]

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system or "You are a helpful assistant.",
                messages=messages,
            )

            latency_ms = (time.time() - start_time) * 1000

            result = LLMResponse(
                content=response.content[0].text,
                model=self.model,
                tokens_in=response.usage.input_tokens,
                tokens_out=response.usage.output_tokens,
                cached=False,
                latency_ms=latency_ms,
            )

            # Cache the response
            if use_cache and self.cache:
                self.cache.set(prompt, self.model, result)

            logger.debug(
                f"LLM call: {result.tokens_in} in, {result.tokens_out} out, {latency_ms:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"LLM API error: {e}")
            # Return fallback response
            return LLMResponse(
                content="I'll wait and observe.",
                model=self.model,
                tokens_in=0,
                tokens_out=0,
                cached=False,
                latency_ms=(time.time() - start_time) * 1000,
            )


class MockLLMClient(LLMClient):
    """Mock LLM client for testing without API calls."""

    def __init__(self, responses: list[str] | None = None):
        super().__init__(api_key="mock", use_cache=False)
        self.responses = responses or ["wait"]
        self.call_count = 0
        self.last_prompt = ""

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        use_cache: bool = True,
    ) -> LLMResponse:
        """Return mock response."""
        self.last_prompt = prompt
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1

        return LLMResponse(
            content=response,
            model="mock",
            tokens_in=len(prompt.split()),
            tokens_out=len(response.split()),
            cached=False,
            latency_ms=10,
        )


# Global client instance
_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get or create the global LLM client."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


def set_llm_client(client: LLMClient) -> None:
    """Set the global LLM client (useful for testing)."""
    global _client
    _client = client

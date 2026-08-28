import json
from abc import ABC, abstractmethod
from .config import settings


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    def __init__(self):
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        from google import genai
        self.client = genai.Client(api_key=settings.gemini_api_key)

    async def generate(self, prompt: str) -> str:
        # google-genai is synchronous; run it in a worker thread so FastAPI stays responsive.
        import asyncio
        def call():
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
            )
            return response.text or ""
        return await asyncio.to_thread(call)


class AnthropicProvider(LLMProvider):
    def __init__(self):
        if not settings.anthropic_auth_token:
            raise RuntimeError("ANTHROPIC_AUTH_TOKEN is not configured")
        from anthropic import AsyncAnthropic
        kwargs = {"api_key": settings.anthropic_auth_token}
        if settings.anthropic_base_url:
            kwargs["base_url"] = settings.anthropic_base_url
        self.client = AsyncAnthropic(**kwargs)

    async def generate(self, prompt: str) -> str:
        response = await self.client.messages.create(
            model=settings.anthropic_model,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )


class MockProvider(LLMProvider):
    async def generate(self, prompt: str) -> str:
        return "MOCK RESPONSE\n\nThis is deterministic local test content."


def get_provider() -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "gemini":
        return GeminiProvider()
    if provider == "anthropic":
        return AnthropicProvider()
    if provider == "mock":
        return MockProvider()
    raise RuntimeError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")

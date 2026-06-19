from app.core.config import get_settings
from app.llm.api_client import APIClient
from app.llm.base import BaseLLMClient
from app.llm.mock_client import MockLLMClient
from app.llm.ollama_client import OllamaClient


def get_llm_client() -> BaseLLMClient:
    provider = get_settings().llm_provider.lower()
    if provider == "mock":
        return MockLLMClient()
    if provider == "ollama":
        return OllamaClient()
    if provider == "api":
        return APIClient()
    raise ValueError(f"unsupported LLM_PROVIDER: {provider}")

import requests
from requests import RequestException

from app.core.config import get_settings
from app.llm.base import BaseLLMClient


class OllamaClient(BaseLLMClient):
    def generate(self, prompt: str, *, context: str, query: str) -> str:
        settings = get_settings()
        try:
            response = requests.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/generate",
                json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            answer = data.get("response", "")
            if not answer:
                raise RuntimeError(f"Ollama 返回为空：{data}")
            return answer
        except RequestException as exc:
            detail = getattr(exc.response, "text", "") if getattr(exc, "response", None) else ""
            raise RuntimeError(
                f"Ollama 调用失败：请确认服务已启动、模型 {settings.ollama_model} 已拉取。{exc}. {detail}"
            ) from exc

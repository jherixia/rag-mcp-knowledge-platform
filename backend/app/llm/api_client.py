import requests
from requests import RequestException

from app.core.config import get_settings
from app.llm.base import BaseLLMClient


class APIClient(BaseLLMClient):
    def generate(self, prompt: str, *, context: str, query: str) -> str:
        settings = get_settings()
        if not settings.api_model_base_url or not settings.api_model_api_key:
            raise RuntimeError(
                "API 模式缺少配置：请设置 API_MODEL_BASE_URL 和 API_MODEL_API_KEY。"
            )

        endpoint = _chat_completions_endpoint(settings.api_model_base_url)
        try:
            response = requests.post(
                endpoint,
                headers={"Authorization": f"Bearer {settings.api_model_api_key}"},
                json={
                    "model": settings.api_model_name or settings.model_id,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except RequestException as exc:
            detail = getattr(exc.response, "text", "") if getattr(exc, "response", None) else ""
            raise RuntimeError(f"API 模型调用失败：{exc}. {detail}".strip()) from exc
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"API 模型返回格式异常：{exc}") from exc


def _chat_completions_endpoint(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"

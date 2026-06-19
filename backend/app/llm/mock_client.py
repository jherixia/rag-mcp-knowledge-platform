from app.llm.base import BaseLLMClient


class MockLLMClient(BaseLLMClient):
    def generate(self, prompt: str, *, context: str, query: str) -> str:
        excerpts = [line.strip() for line in context.splitlines() if line.strip()]
        preview = "\n".join(f"- {line[:220]}" for line in excerpts[:3])
        if not preview:
            preview = "- 知识库中未找到足够相关信息"
        return (
            f"[mock 模式回答] 问题：{query}\n\n"
            "根据当前检索到的知识库片段，可以参考以下内容：\n"
            f"{preview}\n\n"
            "这是本地 mock LLM 生成的回答，用于在没有 Ollama、本地模型或 API Key 的环境中验证 RAG 流程。"
        )

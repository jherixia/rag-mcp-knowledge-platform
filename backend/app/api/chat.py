import json
import time

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.rag.chain import RAGChain

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


@router.post("/api/chat")
def chat(request: ChatRequest) -> dict:
    result = RAGChain().answer(request.query, request.top_k)
    return {"query": request.query, **result}


@router.get("/v1/models")
def list_models() -> dict:
    settings = get_settings()
    return {
        "object": "list",
        "data": [
            {
                "id": settings.model_id,
                "object": "model",
                "created": 0,
                "owned_by": settings.app_name,
            }
        ],
    }


@router.post("/v1/chat/completions")
def openai_chat_completions(request: dict) -> dict:
    settings = get_settings()
    messages = request.get("messages") or []
    query = _last_user_message(messages)
    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="messages 不能为空，并且必须包含至少一条 role=user 的消息。",
        )
    top_k = int(request.get("top_k") or settings.default_top_k)
    result = RAGChain().answer(query, top_k)
    created = int(time.time())
    payload = {
        "id": f"chatcmpl-rag-{created}",
        "object": "chat.completion",
        "created": created,
        "model": request.get("model") or settings.model_id,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": result["answer"]},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(query),
            "completion_tokens": len(result["answer"]),
            "total_tokens": len(query) + len(result["answer"]),
        },
        "sources": result["sources"],
    }
    if request.get("stream"):
        return StreamingResponse(_stream_openai_answer(payload), media_type="text/event-stream")
    return payload


def _last_user_message(messages: list[dict]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


def _stream_openai_answer(payload: dict):
    content = payload["choices"][0]["message"]["content"]
    model = payload["model"]
    start = {
        "id": payload["id"],
        "object": "chat.completion.chunk",
        "created": 0,
        "model": model,
        "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
    }
    yield f"data: {json.dumps(start, ensure_ascii=False)}\n\n"
    chunk = {
        "id": payload["id"],
        "object": "chat.completion.chunk",
        "created": 0,
        "model": model,
        "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
    }
    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
    end = {
        "id": payload["id"],
        "object": "chat.completion.chunk",
        "created": 0,
        "model": model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(end, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"

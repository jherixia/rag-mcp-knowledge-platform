import json
import mimetypes
import sys
import uuid
from pathlib import Path
from urllib import error, request


BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
SAMPLE_FILE = Path("data/samples/ai_intern_job_requirements.txt")


def main() -> None:
    print(f"Testing API: {BASE_URL}")
    check_health()
    doc_id = check_upload()
    check_documents()
    check_build(doc_id)
    check_stats()
    check_chat()
    check_models()
    check_completion()
    check_clear()


def check_health() -> None:
    status, data = call("GET", "/health")
    assert_ok(status, data)
    print("[OK] health check passed")


def check_upload() -> str:
    status, data = upload_file("/api/documents/upload", SAMPLE_FILE)
    assert_ok(status, data)
    doc_id = data["document"]["id"]
    print(f"[OK] document uploaded: {doc_id}")
    return doc_id


def check_documents() -> None:
    status, data = call("GET", "/api/documents")
    assert_ok(status, data)
    print(f"[OK] document list returned {len(data.get('documents', []))} documents")


def check_build(doc_id: str) -> None:
    status, data = call("POST", "/api/knowledge/build", {"doc_ids": [doc_id]})
    assert_ok(status, data)
    print(f"[OK] knowledge base built, chunk_count={data.get('chunk_count')}")


def check_stats() -> None:
    status, data = call("GET", "/api/knowledge/stats")
    assert_ok(status, data)
    print(f"[OK] stats returned chunks={data.get('chunk_count')}, vectors={data.get('vector_count')}")


def check_chat() -> None:
    status, data = call(
        "POST",
        "/api/chat",
        {
            "query": "根据人工智能实习生岗位要求，我需要掌握哪些技术栈？",
            "top_k": 5,
        },
    )
    assert_ok(status, data)
    sources = data.get("sources", [])
    if not data.get("answer") or not sources:
        raise AssertionError(preview(data))
    print(f"[OK] chat returned answer and {len(sources)} sources")


def check_models() -> None:
    status, data = call("GET", "/v1/models")
    assert_ok(status, data)
    print(f"[OK] models returned {data['data'][0]['id']}")


def check_completion() -> None:
    status, data = call(
        "POST",
        "/v1/chat/completions",
        {
            "model": "rag-mcp-knowledge-platform",
            "messages": [{"role": "user", "content": "RAG 和普通大模型问答有什么区别？"}],
        },
    )
    assert_ok(status, data)
    print("[OK] OpenAI-compatible chat completions returned answer")


def check_clear() -> None:
    status, data = call("DELETE", "/api/knowledge/clear")
    assert_ok(status, data)
    print(f"[OK] knowledge base cleared, deleted_chunks={data['data']['deleted_chunks']}")


def call(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{BASE_URL}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=60) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="ignore")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"error": text}
        return exc.code, data


def upload_file(path: str, file_path: Path) -> tuple[int, dict]:
    boundary = f"----ragboundary{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    file_bytes = file_path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = request.Request(
        f"{BASE_URL}{path}",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with request.urlopen(req, timeout=60) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def assert_ok(status: int, data: dict) -> None:
    if not 200 <= status < 300:
        raise AssertionError(f"HTTP {status}: {preview(data)}")


def preview(data: dict) -> str:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    return text if len(text) <= 1000 else f"{text[:1000]}\n..."


if __name__ == "__main__":
    main()

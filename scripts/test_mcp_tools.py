import json
import sys
from urllib import error, request


BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:9000"


def main() -> None:
    stats = call("GET", "/tools/get_kb_stats")
    print(
        f"[OK] get_kb_stats returned document_count={stats.get('document_count')}, "
        f"chunk_count={stats.get('chunk_count')}"
    )

    file_result = call("POST", "/tools/read_project_file", {"path": "README.md"})
    if not file_result.get("content"):
        raise AssertionError(file_result)
    print("[OK] read_project_file returned README.md content")

    notes = call("POST", "/tools/query_notes", {"keyword": "RAG"}).get("results", [])
    print(f"[OK] query_notes returned {len(notes)} notes")

    search = call(
        "POST",
        "/tools/search_kb",
        {"query": "RAG 和普通大模型问答有什么区别？", "top_k": 5},
    )
    print(f"[OK] search_kb returned {len(search.get('results', []))} retrieved chunks")


def call(method: str, path: str, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{BASE_URL}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code}: {text}") from exc


if __name__ == "__main__":
    main()

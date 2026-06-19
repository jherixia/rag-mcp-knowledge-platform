from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings
from app.db.session import db, init_db
from app.rag.vector_store import similarity_search


ALLOWED_SUFFIXES = {".md", ".txt", ".json"}
MAX_FILE_CHARS = 8000


def get_kb_stats() -> dict:
    settings = get_settings()
    try:
        init_db()
        with db() as conn:
            document_count = conn.execute("SELECT COUNT(*) AS count FROM documents").fetchone()["count"]
            chunk_count = conn.execute("SELECT COUNT(*) AS count FROM chunks").fetchone()["count"]
    except Exception as exc:
        return {"error": f"failed to read knowledge base stats: {exc}"}

    return {
        "document_count": int(document_count),
        "chunk_count": int(chunk_count),
        "vector_store": settings.vector_store_type,
        "embedding_backend": settings.embedding_backend,
        "embedding_model": settings.embedding_model_name,
    }


def read_project_file(path: str) -> dict:
    try:
        safe_path = _resolve_project_path(path)
    except ValueError as exc:
        return {"error": str(exc)}

    if safe_path.suffix.lower() not in ALLOWED_SUFFIXES:
        return {"error": "only .md, .txt and .json files are allowed"}
    if not safe_path.exists() or not safe_path.is_file():
        return {"error": f"file not found: {path}"}

    content = safe_path.read_text(encoding="utf-8", errors="ignore")
    truncated = len(content) > MAX_FILE_CHARS
    if truncated:
        content = content[:MAX_FILE_CHARS]
    return {
        "path": str(safe_path.relative_to(ROOT_DIR)),
        "content": content,
        "truncated": truncated,
        "max_chars": MAX_FILE_CHARS,
    }


def query_notes(keyword: str = "") -> list[dict]:
    init_db()
    keyword = keyword.strip()
    with db() as conn:
        if keyword:
            like = f"%{keyword}%"
            rows = conn.execute(
                """
                SELECT title, content, tags
                FROM notes
                WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
                ORDER BY created_at DESC
                """,
                (like, like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT title, content, tags FROM notes ORDER BY created_at DESC"
            ).fetchall()
    return [dict(row) for row in rows]


def search_kb(query: str, top_k: int = 5) -> dict:
    init_db()
    results = similarity_search(query, top_k)
    return {
        "query": query,
        "results": [
            {
                "filename": item.filename,
                "chunk_id": item.chunk_id,
                "doc_id": item.doc_id,
                "chunk_index": item.chunk_index,
                "score": round(item.score, 4),
                "text": item.text[:500],
            }
            for item in results
        ],
    }


def _resolve_project_path(path: str) -> Path:
    if not path:
        raise ValueError("path is required")
    candidate = (ROOT_DIR / path).resolve()
    try:
        candidate.relative_to(ROOT_DIR)
    except ValueError as exc:
        raise ValueError("path traversal is not allowed") from exc
    return candidate

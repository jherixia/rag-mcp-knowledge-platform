from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.db.session import db
from app.rag.loader import load_document
from app.rag.splitter import split_document
from app.rag import vector_store

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class BuildKnowledgeRequest(BaseModel):
    doc_ids: list[str] = Field(default_factory=list)


@router.post("/build")
def build_knowledge(request: BuildKnowledgeRequest) -> dict:
    query = "SELECT id, filename, content_type, saved_path FROM documents"
    params: tuple = ()
    if request.doc_ids:
        placeholders = ",".join("?" for _ in request.doc_ids)
        query += f" WHERE id IN ({placeholders})"
        params = tuple(request.doc_ids)

    with db() as conn:
        docs = conn.execute(query, params).fetchall()

    if not docs:
        raise HTTPException(status_code=404, detail="no documents found")

    total_chunks = 0
    built_docs = []
    for doc in docs:
        count = _rebuild_doc(dict(doc))
        total_chunks += count
        built_docs.append({"doc_id": doc["id"], "filename": doc["filename"], "chunk_count": count})

    return {
        "message": "knowledge base built successfully",
        "document_count": len(built_docs),
        "chunk_count": total_chunks,
        "documents": built_docs,
    }


@router.get("/stats")
def knowledge_stats() -> dict:
    with db() as conn:
        document_count = conn.execute("SELECT COUNT(*) AS count FROM documents").fetchone()["count"]
        chunk_count = conn.execute("SELECT COUNT(*) AS count FROM chunks").fetchone()["count"]
    return {
        "document_count": document_count,
        "chunk_count": chunk_count,
        "vector_count": vector_store.count(),
    }


@router.delete("/clear")
def clear_knowledge() -> dict:
    before = knowledge_stats()
    vector_store.clear()
    with db() as conn:
        conn.execute("DELETE FROM chunks")
    after = knowledge_stats()
    return {
        "code": 0,
        "message": "knowledge base cleared successfully",
        "data": {
            "deleted_chunks": before["chunk_count"],
            "before": before,
            "after": after,
        },
    }


@router.post("/rebuild")
def rebuild_knowledge(request: BuildKnowledgeRequest) -> dict:
    if not request.doc_ids:
        raise HTTPException(status_code=400, detail="doc_ids is required")
    placeholders = ",".join("?" for _ in request.doc_ids)
    with db() as conn:
        docs = conn.execute(
            f"SELECT id, filename, content_type, saved_path FROM documents WHERE id IN ({placeholders})",
            tuple(request.doc_ids),
        ).fetchall()
    if not docs:
        raise HTTPException(status_code=404, detail="no documents found")

    total_chunks = 0
    rebuilt = []
    for doc in docs:
        count = _rebuild_doc(dict(doc))
        total_chunks += count
        rebuilt.append({"doc_id": doc["id"], "filename": doc["filename"], "chunk_count": count})
    return {
        "code": 0,
        "message": "knowledge base rebuilt successfully",
        "data": {"chunk_count": total_chunks, "documents": rebuilt},
    }


def _rebuild_doc(doc: dict) -> int:
    text = load_document(doc["saved_path"])
    chunks = split_document(
        doc_id=doc["id"],
        filename=doc["filename"],
        file_type=doc.get("content_type"),
        text=text,
    )
    return vector_store.replace_document_chunks(doc["id"], chunks)

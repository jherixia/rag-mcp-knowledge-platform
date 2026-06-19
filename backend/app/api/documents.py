import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.db.session import db
from app.rag import vector_store

router = APIRouter(prefix="/api/documents", tags=["documents"])

SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".docx"}


@router.post("/upload")
def upload_document(file: UploadFile = File(...)) -> dict:
    settings = get_settings()
    original_name = Path(file.filename or "uploaded.txt").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"unsupported file type: {suffix}")

    doc_id = str(uuid.uuid4())
    saved_path = settings.raw_docs_dir / f"{doc_id}_{original_name}"
    with saved_path.open("wb") as output:
        shutil.copyfileobj(file.file, output)

    size = saved_path.stat().st_size
    with db() as conn:
        conn.execute(
            """
            INSERT INTO documents (id, filename, content_type, saved_path, size)
            VALUES (?, ?, ?, ?, ?)
            """,
            (doc_id, original_name, file.content_type, str(saved_path), size),
        )

    return {
        "message": "document uploaded successfully",
        "document": {
            "id": doc_id,
            "filename": original_name,
            "content_type": file.content_type,
            "saved_path": str(saved_path),
            "size": size,
        },
    }


@router.get("")
def list_documents() -> dict:
    with db() as conn:
        rows = conn.execute(
            """
            SELECT id, filename, content_type, saved_path, size, created_at
            FROM documents
            ORDER BY created_at DESC
            """
        ).fetchall()
    return {"documents": [dict(row) for row in rows]}


@router.delete("/{doc_id}")
def delete_document(doc_id: str) -> dict:
    with db() as conn:
        doc = conn.execute(
            "SELECT id, filename, saved_path FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="document not found")

        chunk_row = conn.execute(
            "SELECT COUNT(*) AS count FROM chunks WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        sqlite_chunks = int(chunk_row["count"])
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

    vector_deleted = vector_store.delete_by_doc_id(doc_id)
    saved_path = Path(doc["saved_path"])
    file_deleted = False
    if saved_path.exists():
        saved_path.unlink()
        file_deleted = True

    return {
        "code": 0,
        "message": "document deleted successfully",
        "data": {
            "doc_id": doc_id,
            "filename": doc["filename"],
            "deleted_chunks": max(sqlite_chunks, vector_deleted),
            "raw_file_deleted": file_deleted,
        },
    }

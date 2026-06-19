import json
from abc import ABC, abstractmethod
from pathlib import Path
import shutil

from app.core.config import get_settings
from app.db.models import RetrievedChunk, SourceChunk
from app.db.session import db
from app.rag.embeddings import get_embedding_model, vector_cosine
from app.rag.splitter import Chunk


COLLECTION_NAME = "knowledge_chunks"


class BaseVectorStore(ABC):
    @abstractmethod
    def add_chunks(self, chunks: list[Chunk]) -> int:
        raise NotImplementedError

    @abstractmethod
    def similarity_search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        raise NotImplementedError

    @abstractmethod
    def delete_by_doc_id(self, doc_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        raise NotImplementedError


class ChromaVectorStore(BaseVectorStore):
    def __init__(self) -> None:
        settings = get_settings()
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError(
                "chromadb 未安装，无法使用 Chroma 向量库。请执行 pip install -r requirements.txt。"
            ) from exc

        self.client = chromadb.PersistentClient(path=str(settings.vector_db_dir))
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)

    def add_chunks(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        embeddings = get_embedding_model().embed_documents([chunk.text for chunk in chunks])
        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[_metadata(chunk) for chunk in chunks],
        )
        return len(chunks)

    def similarity_search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        embedding = get_embedding_model().embed_query(query)
        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        return _from_chroma_result(result)

    def delete_by_doc_id(self, doc_id: str) -> int:
        before = self.count()
        self.collection.delete(where={"doc_id": doc_id})
        after = self.count()
        return max(before - after, 0)

    def clear(self) -> None:
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)

    def count(self) -> int:
        return int(self.collection.count())


class FaissVectorStore(BaseVectorStore):
    def __init__(self) -> None:
        raise NotImplementedError("FAISS vector store will be implemented later.")


class LocalVectorStore(BaseVectorStore):
    """Offline fallback with persisted JSON vectors when Chroma is unavailable."""

    def __init__(self) -> None:
        settings = get_settings()
        self.path = settings.vector_db_dir / "local_vector_store.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add_chunks(self, chunks: list[Chunk]) -> int:
        records = self._load()
        embeddings = get_embedding_model().embed_documents([chunk.text for chunk in chunks])
        for chunk, embedding in zip(chunks, embeddings):
            records[chunk.chunk_id] = {
                "id": chunk.chunk_id,
                "text": chunk.text,
                "embedding": embedding,
                "metadata": _metadata(chunk),
            }
        self._save(records)
        return len(chunks)

    def similarity_search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        query_embedding = get_embedding_model().embed_query(query)
        results = []
        for record in self._load().values():
            score = round(vector_cosine(query_embedding, record["embedding"]), 4)
            if score <= 0:
                continue
            metadata = record["metadata"]
            results.append(
                RetrievedChunk(
                    text=_truncate(record["text"]),
                    score=score,
                    chunk_id=record["id"],
                    doc_id=metadata["doc_id"],
                    filename=metadata["filename"],
                    chunk_index=int(metadata["chunk_index"]),
                    metadata=metadata,
                )
            )
        results.sort(key=lambda item: item.score, reverse=True)
        return _dedupe(results)[:top_k]

    def delete_by_doc_id(self, doc_id: str) -> int:
        records = self._load()
        delete_ids = [chunk_id for chunk_id, record in records.items() if record["metadata"]["doc_id"] == doc_id]
        for chunk_id in delete_ids:
            records.pop(chunk_id, None)
        self._save(records)
        return len(delete_ids)

    def clear(self) -> None:
        self._save({})

    def count(self) -> int:
        return len(self._load())

    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, records: dict) -> None:
        self.path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")


def get_vector_store() -> BaseVectorStore:
    settings = get_settings()
    if settings.vector_store_type == "chroma":
        try:
            return ChromaVectorStore()
        except RuntimeError:
            return LocalVectorStore()
    if settings.vector_store_type == "faiss":
        return FaissVectorStore()
    if settings.vector_store_type in {"local", "lightweight"}:
        return LocalVectorStore()
    raise ValueError(f"unsupported VECTOR_STORE_TYPE: {settings.vector_store_type}")


def add_chunks(chunks: list[Chunk]) -> int:
    return get_vector_store().add_chunks(chunks)


def similarity_search(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    return get_vector_store().similarity_search(query, top_k)


def delete_by_doc_id(doc_id: str) -> int:
    return get_vector_store().delete_by_doc_id(doc_id)


def clear() -> None:
    get_vector_store().clear()


def count() -> int:
    return get_vector_store().count()


def replace_document_chunks(doc_id: str, chunks: list[str] | list[Chunk]) -> int:
    if chunks and isinstance(chunks[0], str):
        with db() as conn:
            doc = conn.execute(
                "SELECT filename, content_type FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
        filename = doc["filename"] if doc else "unknown"
        file_type = doc["content_type"] if doc else Path(filename).suffix.lower().lstrip(".")
        from app.rag.splitter import split_document

        chunk_objects = split_document(
            doc_id=doc_id,
            filename=filename,
            file_type=file_type,
            text="\n".join(chunks),
        )
    else:
        chunk_objects = chunks  # type: ignore[assignment]

    deleted = delete_by_doc_id(doc_id)
    with db() as conn:
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        for chunk in chunk_objects:
            conn.execute(
                """
                INSERT INTO chunks
                (id, doc_id, chunk_index, text, token_count, embedding_json, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.chunk_id,
                    chunk.doc_id,
                    chunk.chunk_index,
                    chunk.text,
                    len(chunk.text.split()),
                    "[]",
                    json.dumps(_metadata(chunk), ensure_ascii=False),
                    chunk.created_at,
                ),
            )
    _ = deleted
    return add_chunks(chunk_objects)


def search(query: str, top_k: int = 5) -> list[SourceChunk]:
    return [
        SourceChunk(
            chunk_id=item.chunk_id,
            doc_id=item.doc_id,
            filename=item.filename,
            score=item.score,
            text=item.text,
            chunk_index=item.chunk_index,
            metadata=item.metadata,
        )
        for item in similarity_search(query, top_k)
    ]


def chunk_count() -> int:
    with db() as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM chunks").fetchone()
    return int(row["count"])


def clear_storage_dir() -> None:
    settings = get_settings()
    if settings.vector_db_dir.exists():
        shutil.rmtree(settings.vector_db_dir)
    settings.vector_db_dir.mkdir(parents=True, exist_ok=True)


def _metadata(chunk: Chunk) -> dict:
    metadata = {
        "chunk_id": chunk.chunk_id,
        "doc_id": chunk.doc_id,
        "filename": chunk.filename,
        "file_type": chunk.file_type,
        "chunk_index": chunk.chunk_index,
        "created_at": chunk.created_at,
    }
    metadata.update(chunk.metadata or {})
    return metadata


def _from_chroma_result(result: dict) -> list[RetrievedChunk]:
    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    chunks: list[RetrievedChunk] = []
    for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
        score = round(1 / (1 + float(distance)), 4)
        chunks.append(
            RetrievedChunk(
                text=_truncate(text or ""),
                score=score,
                chunk_id=chunk_id,
                doc_id=metadata.get("doc_id", ""),
                filename=metadata.get("filename", ""),
                chunk_index=int(metadata.get("chunk_index", 0)),
                metadata=metadata,
            )
        )
    chunks.sort(key=lambda item: item.score, reverse=True)
    return _dedupe(chunks)


def _dedupe(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    seen = set()
    result = []
    for chunk in chunks:
        if chunk.chunk_id in seen:
            continue
        seen.add(chunk.chunk_id)
        result.append(chunk)
    return result


def _truncate(text: str, limit: int = 500) -> str:
    return text if len(text) <= limit else f"{text[:limit]}..."

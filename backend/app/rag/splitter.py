from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import re

from app.core.config import get_settings


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    filename: str
    file_type: str
    chunk_index: int
    text: str
    created_at: str
    metadata: dict = field(default_factory=dict)


def split_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    settings = get_settings()
    size = chunk_size or settings.chunk_size
    chunk_overlap = overlap if overlap is not None else settings.chunk_overlap
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    chunks = _recursive_split(normalized, size, chunk_overlap)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def split_document(
    *,
    doc_id: str,
    filename: str,
    text: str,
    file_type: str | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Chunk]:
    now = datetime.now(timezone.utc).isoformat()
    suffix = file_type or Path(filename).suffix.lower().lstrip(".") or "unknown"
    chunks = split_text(text, chunk_size, chunk_overlap)
    result: list[Chunk] = []
    for index, chunk_text in enumerate(chunks):
        metadata = {
            "doc_id": doc_id,
            "filename": filename,
            "file_type": suffix,
            "chunk_index": index,
        }
        result.append(
            Chunk(
                chunk_id=f"{doc_id}_chunk_{index}",
                doc_id=doc_id,
                filename=filename,
                file_type=suffix,
                chunk_index=index,
                text=chunk_text,
                created_at=now,
                metadata=metadata,
            )
        )
    return result


def _recursive_split(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        return _fallback_split(text, chunk_size, chunk_overlap)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", "；", ";", "，", ",", " ", ""],
    )
    return splitter.split_text(text)


def _fallback_split(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if chunk_size <= chunk_overlap:
        raise ValueError("chunk_size must be greater than chunk_overlap")
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - chunk_overlap
    return chunks

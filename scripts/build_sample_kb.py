import mimetypes
import shutil
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.db.session import db, init_db
from app.rag.loader import load_document
from app.rag.splitter import split_document
from app.rag.vector_store import replace_document_chunks


SAMPLE_DIR = Path("data/samples")
SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf", ".docx"}


def main() -> None:
    init_db()
    settings = get_settings()
    total_docs = 0
    total_chunks = 0

    for sample in sorted(SAMPLE_DIR.iterdir()):
        if not sample.is_file() or sample.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        doc_id = str(uuid.uuid4())
        target = settings.raw_docs_dir / f"{doc_id}_{sample.name}"
        shutil.copyfile(sample, target)
        with db() as conn:
            conn.execute(
                """
                INSERT INTO documents (id, filename, content_type, saved_path, size)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    sample.name,
                    mimetypes.guess_type(sample.name)[0],
                    str(target),
                    target.stat().st_size,
                ),
            )

        chunks = split_document(
            doc_id=doc_id,
            filename=sample.name,
            file_type=mimetypes.guess_type(sample.name)[0],
            text=load_document(target),
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        chunk_count = replace_document_chunks(doc_id, chunks)
        total_docs += 1
        total_chunks += chunk_count
        print(f"[OK] {sample.name}: {chunk_count} chunks")

    print(f"Done. documents={total_docs}, chunks={total_chunks}")


if __name__ == "__main__":
    main()

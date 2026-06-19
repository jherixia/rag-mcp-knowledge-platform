from pathlib import Path
from uuid import uuid4

from app.api.knowledge import build_knowledge, clear_knowledge, knowledge_stats, rebuild_knowledge
from app.db.session import db, init_db
from app.rag.chain import RAGChain


class Request:
    def __init__(self, doc_ids):
        self.doc_ids = doc_ids


def test_build_rebuild_clear_knowledge(tmp_path) -> None:
    init_db()
    sample = tmp_path / "job.txt"
    sample.write_text("人工智能实习生需要掌握 RAG、LangChain、OpenWebUI 和 Transformer。", encoding="utf-8")
    doc_id = str(uuid4())
    with db() as conn:
        conn.execute(
            """
            INSERT INTO documents (id, filename, content_type, saved_path, size)
            VALUES (?, ?, ?, ?, ?)
            """,
            (doc_id, sample.name, "text/plain", str(sample), sample.stat().st_size),
        )

    built = build_knowledge(Request([doc_id]))
    assert built["chunk_count"] > 0
    assert knowledge_stats()["chunk_count"] > 0

    answer = RAGChain().answer("人工智能实习生需要掌握什么？", 3)
    assert answer["sources"]
    assert "参考来源" in answer["answer"]

    rebuilt = rebuild_knowledge(Request([doc_id]))
    assert rebuilt["data"]["chunk_count"] > 0

    cleared = clear_knowledge()
    assert cleared["code"] == 0
    assert knowledge_stats()["chunk_count"] == 0

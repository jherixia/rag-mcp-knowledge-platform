from pathlib import Path
from uuid import uuid4

from app.api.chat import list_models, openai_chat_completions
from app.db.session import db, init_db
from app.rag.chain import RAGChain
from app.rag.loader import load_document
from app.rag.splitter import split_text
from app.rag.vector_store import replace_document_chunks


def test_mock_rag_core_flow() -> None:
    init_db()
    sample = Path("data/samples/rag_intro.txt")
    doc_id = str(uuid4())
    with db() as conn:
        conn.execute(
            """
            INSERT INTO documents (id, filename, content_type, saved_path, size)
            VALUES (?, ?, ?, ?, ?)
            """,
            (doc_id, sample.name, "text/plain", str(sample), sample.stat().st_size),
        )

    chunks = split_text(load_document(sample), 800, 120)
    assert replace_document_chunks(doc_id, chunks) > 0

    result = RAGChain().answer("RAG 和普通大模型问答有什么区别？", 3)
    assert "mock 模式回答" in result["answer"]
    assert result["sources"]
    assert result["sources"][0]["filename"] == "rag_intro.txt"


def test_openai_compatible_handlers() -> None:
    assert list_models()["data"][0]["id"] == "rag-mcp-knowledge-platform"
    completion = openai_chat_completions(
        {
            "model": "rag-mcp-knowledge-platform",
            "messages": [{"role": "user", "content": "什么是 RAG？"}],
        }
    )
    assert completion["choices"][0]["message"]["content"]

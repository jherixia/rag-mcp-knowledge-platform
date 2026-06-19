from pathlib import Path

from app.db.session import init_db
from app.rag.splitter import split_document
from app.rag.vector_store import replace_document_chunks
from mcp_server.tools import get_kb_stats, query_notes, read_project_file, search_kb


def test_get_kb_stats_basic_return() -> None:
    init_db()
    stats = get_kb_stats()
    assert "document_count" in stats
    assert "chunk_count" in stats
    assert stats["vector_store"] == "local"


def test_read_project_file_blocks_path_traversal() -> None:
    result = read_project_file("../../etc/passwd")
    assert "error" in result
    assert "path traversal" in result["error"]


def test_query_notes_returns_list() -> None:
    init_db()
    results = query_notes("RAG")
    assert isinstance(results, list)
    assert results


def test_search_kb_returns_structured_results(tmp_path) -> None:
    init_db()
    chunks = split_document(
        doc_id="mcp_doc",
        filename="rag_intro.txt",
        file_type="txt",
        text="RAG 会先检索知识库，再结合上下文回答。普通大模型问答主要依赖模型参数。",
    )
    assert replace_document_chunks("mcp_doc", chunks) > 0
    result = search_kb("RAG 和普通大模型问答有什么区别？", 5)
    assert result["query"]
    assert result["results"]
    first = result["results"][0]
    assert {"filename", "chunk_id", "score", "text"}.issubset(first.keys())

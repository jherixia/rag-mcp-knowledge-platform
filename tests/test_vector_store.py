from app.db.session import init_db
from app.rag.splitter import split_document
from app.rag.vector_store import clear, count, delete_by_doc_id, replace_document_chunks, similarity_search


def test_local_vector_store_add_search_delete() -> None:
    init_db()
    chunks = split_document(
        doc_id="doc1",
        filename="rag.md",
        file_type="md",
        text="RAG 会先检索知识库，再结合上下文回答问题。OpenWebUI 可以接入 OpenAI-compatible API。",
    )
    assert replace_document_chunks("doc1", chunks) == len(chunks)
    assert count() == len(chunks)

    results = similarity_search("RAG 如何回答问题", 3)
    assert results
    assert results[0].doc_id == "doc1"
    assert results[0].score >= 0

    assert delete_by_doc_id("doc1") >= 1
    clear()
    assert count() == 0

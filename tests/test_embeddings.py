from app.rag.embeddings import EmbeddingModel, LightweightEmbeddingModel


def test_lightweight_embedding_shapes() -> None:
    model = LightweightEmbeddingModel()
    vectors = model.embed_documents(["什么是 RAG", "OpenWebUI 接入 API"])
    assert len(vectors) == 2
    assert len(vectors[0]) == model.dimensions
    assert len(model.embed_query("RAG")) == model.dimensions


def test_real_embedding_class_exists() -> None:
    assert hasattr(EmbeddingModel, "embed_documents")
    assert hasattr(EmbeddingModel, "embed_query")

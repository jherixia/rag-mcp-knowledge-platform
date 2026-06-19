import os
from pathlib import Path
import sys

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("RAW_DOCS_DIR", str(tmp_path / "data" / "raw_docs"))
    monkeypatch.setenv("VECTOR_DB_DIR", str(tmp_path / "data" / "vector_db"))
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "data" / "sqlite" / "app.db"))
    monkeypatch.setenv("VECTOR_STORE_TYPE", "local")
    monkeypatch.setenv("EMBEDDING_BACKEND", "lightweight")
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    from app.core.config import get_settings
    from app.rag.embeddings import get_embedding_model

    get_settings.cache_clear()
    get_embedding_model.cache_clear()
    yield
    get_settings.cache_clear()
    get_embedding_model.cache_clear()

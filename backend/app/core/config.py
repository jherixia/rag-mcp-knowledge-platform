from functools import lru_cache
import os
from pathlib import Path


class Settings:
    def __init__(self) -> None:
        env_file = _load_env_file(Path(".env"))
        self.app_name = _env("APP_NAME", "RAG MCP Knowledge Platform", env_file)
        self.app_env = _env("APP_ENV", "dev", env_file)
        self.data_dir = Path(_env("DATA_DIR", "data", env_file))
        self.sqlite_path = Path(
            _env("SQLITE_DB_PATH", _env("SQLITE_PATH", "data/sqlite/app.db", env_file), env_file)
        )
        self.raw_docs_dir = Path(_env("RAW_DOCS_DIR", str(self.data_dir / "raw_docs"), env_file))
        self.vector_db_dir = Path(_env("VECTOR_DB_DIR", str(self.data_dir / "vector_db"), env_file))
        self.vector_store_type = _env("VECTOR_STORE_TYPE", "chroma", env_file).lower()
        self.embedding_model_name = _env(
            "EMBEDDING_MODEL_NAME", "BAAI/bge-small-zh-v1.5", env_file
        )
        self.embedding_backend = _env("EMBEDDING_BACKEND", "sentence-transformers", env_file).lower()
        self.chunk_size = int(_env("CHUNK_SIZE", "800", env_file))
        self.chunk_overlap = int(_env("CHUNK_OVERLAP", "120", env_file))
        self.default_top_k = int(_env("TOP_K", _env("DEFAULT_TOP_K", "5", env_file), env_file))
        self.model_id = _env("MODEL_ID", "rag-mcp-knowledge-platform", env_file)

        self.llm_provider = _env("LLM_PROVIDER", "mock", env_file)
        self.ollama_base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434", env_file)
        self.ollama_model = _env("OLLAMA_MODEL", "qwen2.5:7b", env_file)
        self.api_model_base_url = _env_optional("API_MODEL_BASE_URL", env_file) or _env_optional("API_BASE_URL", env_file)
        self.api_model_api_key = _env_optional("API_MODEL_API_KEY", env_file) or _env_optional("API_KEY", env_file)
        self.api_model_name = _env_optional("API_MODEL_NAME", env_file) or _env_optional("API_MODEL", env_file)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.raw_docs_dir.mkdir(parents=True, exist_ok=True)
    settings.vector_db_dir.mkdir(parents=True, exist_ok=True)
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return settings


def _env(key: str, default: str, env_file: dict[str, str]) -> str:
    return os.getenv(key) or env_file.get(key) or default


def _env_optional(key: str, env_file: dict[str, str]) -> str | None:
    value = os.getenv(key) or env_file.get(key)
    return value or None


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values

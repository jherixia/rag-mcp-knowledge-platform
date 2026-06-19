import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.core.config import get_settings


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_settings().sqlite_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                content_type TEXT,
                saved_path TEXT NOT NULL,
                size INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                token_count INTEGER NOT NULL,
                embedding_json TEXT NOT NULL,
                metadata_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(doc_id) REFERENCES documents(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);

            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        _ensure_column(conn, "chunks", "metadata_json", "TEXT DEFAULT '{}'")
        _seed_notes(conn)


def _seed_notes(conn: sqlite3.Connection) -> None:
    notes = [
        (
            "note_rag",
            "RAG 学习笔记",
            "RAG 是 Retrieval-Augmented Generation，会先检索外部知识库，再结合上下文生成回答。",
            "rag,llm,knowledge-base",
        ),
        (
            "note_langchain",
            "LangChain 学习笔记",
            "LangChain 可以连接 Loader、Splitter、Retriever、Prompt 和 LLM Chain，常用于构建 RAG 应用。",
            "langchain,rag,retriever",
        ),
        (
            "note_mcp",
            "MCP 工具调用笔记",
            "MCP Server 可以把文件读取、数据库查询、知识库检索等外部工具暴露给智能体或客户端。",
            "mcp,tools,agent",
        ),
        (
            "note_openwebui",
            "OpenWebUI 接入笔记",
            "OpenWebUI 可以通过 OpenAI-compatible API 调用自研 RAG 后端，例如 /v1/models 和 /v1/chat/completions。",
            "openwebui,openai-compatible,api",
        ),
        (
            "note_ai_intern",
            "AI 实习技术栈笔记",
            "人工智能实习生应掌握 Python、FastAPI、RAG、Embedding、LangChain、OpenWebUI、MCP 和基础模型部署。",
            "ai-intern,rag,langchain,mcp",
        ),
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO notes (id, title, content, tags)
        VALUES (?, ?, ?, ?)
        """,
        notes,
    )


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    if column not in {row["name"] for row in rows}:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

import argparse
import json
from pathlib import Path

from app.db.session import db, init_db


def knowledge_stats() -> dict:
    init_db()
    with db() as conn:
        docs = conn.execute("SELECT COUNT(*) AS count FROM documents").fetchone()["count"]
        chunks = conn.execute("SELECT COUNT(*) AS count FROM chunks").fetchone()["count"]
    return {"document_count": docs, "chunk_count": chunks}


def read_local_file(path: str) -> dict:
    file_path = Path(path).resolve()
    return {"path": str(file_path), "content": file_path.read_text(encoding="utf-8", errors="ignore")}


def sqlite_query(sql: str) -> dict:
    init_db()
    if not sql.strip().lower().startswith("select"):
        raise ValueError("only SELECT queries are allowed")
    with db() as conn:
        rows = conn.execute(sql).fetchall()
    return {"rows": [dict(row) for row in rows]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple MCP-like utility tools")
    parser.add_argument("tool", choices=["knowledge_stats", "read_local_file", "sqlite_query"])
    parser.add_argument("arg", nargs="?")
    args = parser.parse_args()
    if args.tool == "knowledge_stats":
        result = knowledge_stats()
    elif args.tool == "read_local_file":
        result = read_local_file(args.arg or "")
    else:
        result = sqlite_query(args.arg or "SELECT name FROM sqlite_master")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

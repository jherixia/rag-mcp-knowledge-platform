from pathlib import Path
import sys

from fastapi import FastAPI
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from mcp_server.tools import get_kb_stats, query_notes, read_project_file, search_kb


app = FastAPI(title="RAG MCP Tool Server")


class ReadProjectFileRequest(BaseModel):
    path: str


class QueryNotesRequest(BaseModel):
    keyword: str = ""


class SearchKbRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "server": "mcp-http-fallback"}


@app.get("/tools")
def list_tools() -> dict:
    return {
        "tools": [
            "get_kb_stats",
            "read_project_file",
            "query_notes",
            "search_kb",
        ],
        "mode": "http-fallback",
    }


@app.get("/tools/get_kb_stats")
def get_kb_stats_endpoint() -> dict:
    return get_kb_stats()


@app.post("/tools/read_project_file")
def read_project_file_endpoint(request: ReadProjectFileRequest) -> dict:
    return read_project_file(request.path)


@app.post("/tools/query_notes")
def query_notes_endpoint(request: QueryNotesRequest) -> dict:
    return {"results": query_notes(request.keyword)}


@app.post("/tools/search_kb")
def search_kb_endpoint(request: SearchKbRequest) -> dict:
    return search_kb(request.query, request.top_k)

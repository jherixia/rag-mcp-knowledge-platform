from pydantic import BaseModel, Field


class DocumentRecord(BaseModel):
    id: str
    filename: str
    content_type: str | None = None
    saved_path: str
    size: int
    created_at: str


class SourceChunk(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    score: float
    text: str
    chunk_index: int = 0
    metadata: dict = Field(default_factory=dict)


class RetrievedChunk(SourceChunk):
    pass

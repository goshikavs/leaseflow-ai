from pydantic import BaseModel, Field


class PreparedChunk(BaseModel):
    ordinal: int
    section_heading: str
    start_page: int
    end_page: int
    source_text: str
    content_hash: str
    token_count: int


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    lease_id: str | None
    organization_id: str
    property_id: str
    document_version: int
    document_type: str
    section_heading: str
    start_page: int
    end_page: int
    source_text: str
    score: float


class RagSearchResponse(BaseModel):
    items: list[RetrievedChunk] = Field(default_factory=list)


class RagAskResponse(BaseModel):
    answer: str
    insufficient_evidence: bool
    citations: list[RetrievedChunk] = Field(default_factory=list)
    provider: str
    model_name: str

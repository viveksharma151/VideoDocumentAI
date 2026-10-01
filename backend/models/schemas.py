from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class YoutubeIngestRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL")
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200

class PdfUrlIngestRequest(BaseModel):
    url: str = Field(..., description="Direct PDF file URL")
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200

class QueryRequest(BaseModel):
    query: str = Field(..., description="User question / prompt")
    llm_provider: Optional[str] = "gemini" # gemini, openai
    llm_model: Optional[str] = "gemini-1.5-flash"
    embedding_provider: Optional[str] = "huggingface" # huggingface, gemini, openai
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    top_k: Optional[int] = 4

class ConfigUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    llm_provider: Optional[str] = None
    embedding_provider: Optional[str] = None

class DocumentSourceSchema(BaseModel):
    source_id: str
    source_type: str # youtube, pdf_upload, pdf_url
    title: str
    chunks_count: int
    created_at: str

class CitationSchema(BaseModel):
    content: str
    source_type: str
    source_name: str
    page: Optional[int] = None
    timestamp: Optional[str] = None
    score: Optional[float] = None

class QueryResponse(BaseModel):
    answer: str
    citations: List[CitationSchema]
    llm_used: str

class IngestResponse(BaseModel):
    status: str
    message: str
    source_id: str
    source_title: str
    total_chunks: int

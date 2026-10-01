import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional

from backend.config import config
from backend.models.schemas import (
    YoutubeIngestRequest,
    PdfUrlIngestRequest,
    QueryRequest,
    QueryResponse,
    IngestResponse,
    ConfigUpdateRequest
)
from backend.services.document_processor import DocumentProcessor
from backend.services.vector_store import vector_store_manager
from backend.services.rag_chain import RAGChainService

app = FastAPI(
    title="Multimodal RAG Platform (YouTube + PDF)",
    description="RAG System supporting YouTube links, PDF uploads, and PDF URLs using FastAPI & Multi-Provider LLMs",
    version="1.0.0"
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ingest YouTube Endpoint
@app.post("/api/ingest/youtube", response_model=IngestResponse)
async def ingest_youtube(
    payload: YoutubeIngestRequest,
    embedding_provider: str = "huggingface",
    gemini_key: Optional[str] = None,
    openai_key: Optional[str] = None
):
    try:
        docs = DocumentProcessor.process_youtube(
            url=payload.url,
            chunk_size=payload.chunk_size or config.CHUNK_SIZE,
            chunk_overlap=payload.chunk_overlap or config.CHUNK_OVERLAP
        )
        res = vector_store_manager.add_documents(
            docs=docs,
            embedding_provider=embedding_provider,
            gemini_key=gemini_key or config.GEMINI_API_KEY,
            openai_key=openai_key or config.OPENAI_API_KEY
        )
        return IngestResponse(
            status="success",
            message=f"Successfully processed YouTube video with {res['total_chunks']} transcript chunks!",
            source_id=res["source_id"],
            source_title=res["source_title"],
            total_chunks=res["total_chunks"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Ingest PDF Upload Endpoint
@app.post("/api/ingest/pdf-upload", response_model=IngestResponse)
async def ingest_pdf_upload(
    file: UploadFile = File(...),
    embedding_provider: str = Form("huggingface"),
    gemini_key: Optional[str] = Form(None),
    openai_key: Optional[str] = Form(None),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200)
):
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise ValueError("Uploaded file must be a PDF document.")
        
        content = await file.read()
        docs = DocumentProcessor.process_pdf_bytes(
            file_bytes=content,
            filename=file.filename,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        res = vector_store_manager.add_documents(
            docs=docs,
            embedding_provider=embedding_provider,
            gemini_key=gemini_key or config.GEMINI_API_KEY,
            openai_key=openai_key or config.OPENAI_API_KEY
        )
        return IngestResponse(
            status="success",
            message=f"Successfully indexed PDF '{file.filename}' into vector store ({res['total_chunks']} chunks).",
            source_id=res["source_id"],
            source_title=res["source_title"],
            total_chunks=res["total_chunks"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Ingest PDF Link Endpoint
@app.post("/api/ingest/pdf-url", response_model=IngestResponse)
async def ingest_pdf_url(
    payload: PdfUrlIngestRequest,
    embedding_provider: str = "huggingface",
    gemini_key: Optional[str] = None,
    openai_key: Optional[str] = None
):
    try:
        docs = await DocumentProcessor.process_pdf_url(
            url=payload.url,
            chunk_size=payload.chunk_size or config.CHUNK_SIZE,
            chunk_overlap=payload.chunk_overlap or config.CHUNK_OVERLAP
        )
        res = vector_store_manager.add_documents(
            docs=docs,
            embedding_provider=embedding_provider,
            gemini_key=gemini_key or config.GEMINI_API_KEY,
            openai_key=openai_key or config.OPENAI_API_KEY
        )
        return IngestResponse(
            status="success",
            message=f"Successfully downloaded and indexed PDF URL into vector store ({res['total_chunks']} chunks).",
            source_id=res["source_id"],
            source_title=res["source_title"],
            total_chunks=res["total_chunks"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# RAG Query Endpoint
@app.post("/api/query", response_model=QueryResponse)
async def query_rag(payload: QueryRequest):
    try:
        res = RAGChainService.answer_query(
            query=payload.query,
            llm_provider=payload.llm_provider or config.DEFAULT_LLM_PROVIDER,
            llm_model=payload.llm_model or config.DEFAULT_LLM_MODEL,
            embedding_provider=payload.embedding_provider or config.DEFAULT_EMBEDDING_PROVIDER,
            gemini_api_key=payload.gemini_api_key or config.GEMINI_API_KEY,
            openai_api_key=payload.openai_api_key or config.OPENAI_API_KEY,
            top_k=payload.top_k or 4
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# List Indexed Documents
@app.get("/api/documents")
async def get_documents():
    return {
        "sources": vector_store_manager.get_sources_list(),
        "total_documents": len(vector_store_manager.indexed_sources),
        "embedding_provider": vector_store_manager.current_embedding_provider
    }

# Clear Vector Store
@app.delete("/api/documents")
async def clear_documents():
    vector_store_manager.clear_vector_store()
    return {"status": "success", "message": "Vector store and document index cleared successfully."}

# Config Settings Endpoint
@app.post("/api/config")
async def update_config(payload: ConfigUpdateRequest):
    if payload.gemini_api_key is not None:
        config.GEMINI_API_KEY = payload.gemini_api_key
    if payload.openai_api_key is not None:
        config.OPENAI_API_KEY = payload.openai_api_key
    if payload.llm_provider is not None:
        config.DEFAULT_LLM_PROVIDER = payload.llm_provider
    if payload.embedding_provider is not None:
        config.DEFAULT_EMBEDDING_PROVIDER = payload.embedding_provider
    return {"status": "success", "message": "Settings updated successfully."}

# Serve Frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

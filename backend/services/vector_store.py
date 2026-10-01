import os
import datetime
from typing import List, Dict, Any, Optional, Tuple
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from backend.services.llm_factory import LLMFactory

class VectorStoreManager:
    def __init__(self):
        self.vector_store: Optional[FAISS] = None
        self.current_embedding_provider: str = "huggingface"
        self.indexed_sources: Dict[str, Dict[str, Any]] = {}

    def add_documents(
        self,
        docs: List[Document],
        embedding_provider: str = "huggingface",
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None
    ) -> Dict[str, Any]:
        if not docs:
            raise ValueError("No documents provided to index.")

        # Check embedding provider consistency
        if self.vector_store is not None and self.current_embedding_provider != embedding_provider:
            # Re-indexing required if provider changed
            self.clear_vector_store()

        embeddings = LLMFactory.get_embeddings(
            provider=embedding_provider,
            gemini_key=gemini_key,
            openai_key=openai_key
        )
        self.current_embedding_provider = embedding_provider

        # Extract source metadata
        first_doc = docs[0]
        source_id = first_doc.metadata.get("source_id", "doc_unknown")
        source_name = first_doc.metadata.get("source_name", "Untitled Document")
        source_type = first_doc.metadata.get("source_type", "unknown")

        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(documents=docs, embedding=embeddings)
        else:
            self.vector_store.add_documents(documents=docs)

        # Track metadata
        if source_id in self.indexed_sources:
            self.indexed_sources[source_id]["chunks_count"] += len(docs)
        else:
            self.indexed_sources[source_id] = {
                "source_id": source_id,
                "title": source_name,
                "source_type": source_type,
                "chunks_count": len(docs),
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        return {
            "source_id": source_id,
            "source_title": source_name,
            "total_chunks": len(docs)
        }

    def search_similar(
        self,
        query: str,
        k: int = 4,
        embedding_provider: str = "huggingface",
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None
    ) -> List[Tuple[Document, float]]:
        if self.vector_store is None:
            return []

        # If user queries with different embedding provider than active index, re-embed or search
        embeddings = LLMFactory.get_embeddings(
            provider=embedding_provider,
            gemini_key=gemini_key,
            openai_key=openai_key
        )

        results = self.vector_store.similarity_search_with_score(query, k=k)
        return results

    def get_sources_list(self) -> List[Dict[str, Any]]:
        return list(self.indexed_sources.values())

    def clear_vector_store(self):
        self.vector_store = None
        self.indexed_sources = {}
        return True

# Singleton instance
vector_store_manager = VectorStoreManager()

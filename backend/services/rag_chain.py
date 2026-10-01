from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from backend.services.vector_store import vector_store_manager
from backend.services.llm_factory import LLMFactory
from backend.models.schemas import CitationSchema, QueryResponse

RAG_SYSTEM_PROMPT = """You are an intelligent, helpful AI Assistant trained on Retrieval-Augmented Generation (RAG).
Answer the user's question accurately based ONLY on the provided context passages retrieved from YouTube transcripts and PDF documents.

Guidelines:
1. Rely strictly on the context provided. If the context does not contain enough information to answer the question, state politely: "I couldn't find enough relevant information in the uploaded documents/video transcripts to answer your question."
2. Be comprehensive, direct, and well-structured. Use markdown formatting (bullet points, bold text) for clarity.
3. If referring to specific information, mention the source (e.g., PDF page number or YouTube timestamp) in your response if helpful.
4. Respond in the same language as the user's question (Hindi, English, Hinglish, etc.).
"""

class RAGChainService:
    @staticmethod
    def answer_query(
        query: str,
        llm_provider: str = "gemini",
        llm_model: str = "gemini-1.5-flash",
        embedding_provider: str = "huggingface",
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        top_k: int = 4
    ) -> QueryResponse:
        # Retrieve context from vector DB
        results = vector_store_manager.search_similar(
            query=query,
            k=top_k,
            embedding_provider=embedding_provider,
            gemini_key=gemini_api_key,
            openai_key=openai_api_key
        )

        if not results:
            return QueryResponse(
                answer="No documents or YouTube transcripts have been added to the knowledge base yet. Please add a YouTube URL or upload a PDF first!",
                citations=[],
                llm_used=f"{llm_provider.capitalize()} ({llm_model})"
            )

        # Build context & citations
        context_parts = []
        citations: List[CitationSchema] = []

        for idx, (doc, score) in enumerate(results, start=1):
            content = doc.page_content
            meta = doc.metadata
            source_type = meta.get("source_type", "Document")
            source_name = meta.get("source_name", "Unknown Source")
            page = meta.get("page")
            timestamp = meta.get("timestamp")

            source_info = f"Source {idx} [{source_name}]"
            if timestamp:
                source_info += f" (Timestamp: {timestamp})"
            elif page:
                source_info += f" (Page: {page})"

            context_parts.append(f"--- {source_info} ---\n{content}\n")

            citations.append(CitationSchema(
                content=content,
                source_type=source_type,
                source_name=source_name,
                page=page,
                timestamp=timestamp,
                score=float(score) if score is not None else None
            ))

        formatted_context = "\n".join(context_parts)
        user_prompt = f"Context Passages:\n{formatted_context}\n\nUser Question:\n{query}"

        # Instantiate LLM
        llm = LLMFactory.get_llm(
            provider=llm_provider,
            model_name=llm_model,
            gemini_key=gemini_api_key,
            openai_key=openai_api_key
        )

        messages = [
            SystemMessage(content=RAG_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        answer_text = response.content

        return QueryResponse(
            answer=str(answer_text),
            citations=citations,
            llm_used=f"{llm_provider.capitalize()} ({llm_model})"
        )

import os
from typing import Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from backend.config import config

class LLMFactory:
    _hf_embeddings_instance = None

    @classmethod
    def get_embeddings(cls, provider: str = "huggingface", gemini_key: Optional[str] = None, openai_key: Optional[str] = None):
        provider = (provider or "huggingface").lower()
        
        if provider == "huggingface":
            if cls._hf_embeddings_instance is None:
                cls._hf_embeddings_instance = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={'device': 'cpu'}
                )
            return cls._hf_embeddings_instance

        elif provider == "gemini":
            key = gemini_key or config.GEMINI_API_KEY
            if not key:
                raise ValueError("Google Gemini API Key is required for Gemini Embeddings.")
            return GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=key
            )

        elif provider == "openai":
            key = openai_key or config.OPENAI_API_KEY
            if not key:
                raise ValueError("OpenAI API Key is required for OpenAI Embeddings.")
            return OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=key
            )

        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

    @classmethod
    def get_llm(cls, provider: str = "gemini", model_name: Optional[str] = None, gemini_key: Optional[str] = None, openai_key: Optional[str] = None):
        provider = (provider or "gemini").lower()

        if provider == "gemini":
            key = gemini_key or config.GEMINI_API_KEY
            if not key:
                raise ValueError("Google Gemini API Key is missing. Please provide a valid GEMINI_API_KEY.")
            model = model_name or "gemini-1.5-flash"
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=key,
                temperature=0.3
            )

        elif provider == "openai":
            key = openai_key or config.OPENAI_API_KEY
            if not key:
                raise ValueError("OpenAI API Key is missing. Please provide a valid OPENAI_API_KEY.")
            model = model_name or "gpt-4o-mini"
            return ChatOpenAI(
                model=model,
                openai_api_key=key,
                temperature=0.3
            )

        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

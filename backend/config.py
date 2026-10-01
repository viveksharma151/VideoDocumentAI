import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 8000))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 200))
    DEFAULT_EMBEDDING_PROVIDER: str = "huggingface" # 'huggingface' (free/local), 'gemini', 'openai'
    DEFAULT_LLM_PROVIDER: str = "gemini"            # 'gemini', 'openai'
    DEFAULT_LLM_MODEL: str = "gemini-1.5-flash"

config = Config()

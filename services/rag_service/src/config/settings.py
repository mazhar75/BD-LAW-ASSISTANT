"""
Application Settings and Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "BD Law Assistant RAG Service"
    VERSION: str = "1.0.0"
    APP_VERSION: str = "1.0.0"  # Alias for VERSION
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_HOST: str = "0.0.0.0"  # Alias for HOST
    API_PORT: int = 8000  # Alias for PORT
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list = ["*"]  # CORS origins

    # ChromaDB Configuration
    CHROMA_PERSIST_DIR: str = "./data/chroma_data"
    CHROMA_COLLECTION_NAME: str = "bd_laws_v1"
    CHROMA_DISTANCE_METRIC: str = "cosine"  # Options: cosine, l2, ip

    # Embedding Configuration
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_DEVICE: Optional[str] = None  # None = auto-detect, "cuda", "cpu"

    # PostgreSQL Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "bdlaw"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""  # Must be set in .env file
    DB_POOL_MIN: int = 1
    DB_POOL_MAX: int = 10

    # Search Configuration
    SEARCH_DEFAULT_TOP_K: int = 5
    SEARCH_MAX_TOP_K: int = 20
    SEARCH_DEFAULT_THRESHOLD: float = 0.5

    # LLM Configuration
    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"  # Free tier model
    GEMINI_TEMPERATURE: float = 0.1
    GEMINI_MAX_OUTPUT_TOKENS: int = 2048
    GEMINI_TOP_P: float = 0.95
    GEMINI_TOP_K: int = 40

    # OpenAI (fallback)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE: float = 0.1
    OPENAI_MAX_TOKENS: int = 2048

    # RAG Configuration
    RAG_CONTEXT_TOP_K: int = 5  # Number of chunks to retrieve for context
    RAG_CONTEXT_MAX_TOKENS: int = 4000  # Max tokens for context
    RAG_MIN_SIMILARITY_SCORE: float = 0.3  # Minimum similarity for inclusion
    RAG_ENABLE_RERANKING: bool = True  # Enable context reranking

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Create necessary directories
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)

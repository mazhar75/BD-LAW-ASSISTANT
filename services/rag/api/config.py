"""
Configuration for RAG API
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "BD Law RAG Service"
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # API
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5000"],
        env="CORS_ORIGINS"
    )

    # Database
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="bdlaw", env="DB_NAME")
    db_user: str = Field(default="bdlaw", env="DB_USER")
    db_password: str = Field(default="bdlaw123", env="DB_PASSWORD")

    # Redis
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")

    # Embedding Model
    embedding_model: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        env="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=384, env="EMBEDDING_DIMENSION")

    # Vector Store
    vector_store_path: str = Field(default="vector_store.faiss", env="VECTOR_STORE_PATH")
    vector_index_type: str = Field(default="Flat", env="VECTOR_INDEX_TYPE")

    # LLM Configuration
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    llm_model: str = Field(default="gpt-3.5-turbo", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=1000, env="LLM_MAX_TOKENS")

    # Search Configuration
    search_top_k: int = Field(default=5, env="SEARCH_TOP_K")
    search_threshold: float = Field(default=0.5, env="SEARCH_THRESHOLD")

    # Chunking Configuration
    chunk_size: int = Field(default=512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
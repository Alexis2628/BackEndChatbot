"""
Application Configuration using Pydantic Settings.
"""

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_name: str = Field(default="Enterprise RAG System", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_workers: int = Field(default=4, alias="API_WORKERS")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="CORS_ORIGINS",
    )
    
    # Database (PostgreSQL - Optional)
    database_url: Optional[str] = Field(
        default=None, alias="DATABASE_URL"
    )
    database_pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")
    
    # Qdrant
    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_collection_name: str = Field(
        default="rag_documents", alias="QDRANT_COLLECTION_NAME"
    )
    qdrant_vector_size: int = Field(default=1536, alias="QDRANT_VECTOR_SIZE")
    
    # LLM
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_MODEL")
    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )
    ollama_model: str = Field(default="llama2", alias="OLLAMA_MODEL")
    
    # Embeddings
    embedding_provider: str = Field(default="openai", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(
        default="text-embedding-3-small", alias="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=1536, alias="EMBEDDING_DIMENSION")
    
    # LangSmith (Optional)
    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: Optional[str] = Field(default=None, alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="rag-system", alias="LANGCHAIN_PROJECT")
    
    # MCP
    mcp_enabled: bool = Field(default=True, alias="MCP_ENABLED")
    mcp_server_url: str = Field(
        default="http://localhost:8001", alias="MCP_SERVER_URL"
    )
    
    # Document Processing
    docling_max_file_size: int = Field(default=52428800, alias="DOCLING_MAX_FILE_SIZE")
    docling_supported_formats: List[str] = Field(
        default=["pdf", "docx", "txt", "md", "html"],
        alias="DOCLING_SUPPORTED_FORMATS",
    )
    docling_chunk_size: int = Field(default=1000, alias="DOCLING_CHUNK_SIZE")
    docling_chunk_overlap: int = Field(default=200, alias="DOCLING_CHUNK_OVERLAP")
    
    # RAG
    rag_top_k: int = Field(default=5, alias="RAG_TOP_K")
    rag_score_threshold: float = Field(default=0.7, alias="RAG_SCORE_THRESHOLD")
    rag_max_tokens: int = Field(default=4000, alias="RAG_MAX_TOKENS")
    
    # Agent
    agent_max_iterations: int = Field(default=10, alias="AGENT_MAX_ITERATIONS")
    agent_timeout: int = Field(default=300, alias="AGENT_TIMEOUT")
    
    # Redis (Optional)
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    cache_ttl: int = Field(default=3600, alias="CACHE_TTL")
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production", alias="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )


# Global settings instance
settings = Settings()

"""
Dependency Injection Container.
Manages service instantiation and lifecycle.
"""

import logging
from functools import lru_cache
from typing import Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.config import settings
from src.repositories.qdrant_repository import QdrantRepository
from src.services.indexing_service import IndexingService
from src.services.rag_service import RAGService

logger = logging.getLogger(__name__)

# Global instances (singleton pattern)
_qdrant_repository: Optional[QdrantRepository] = None
_indexing_service: Optional[IndexingService] = None
_rag_service: Optional[RAGService] = None


@lru_cache()
def get_embedding_model() -> OpenAIEmbeddings:
    """Get embedding model instance."""
    if settings.embedding_provider == "openai":
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )
    else:
        # Fallback or other providers
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )


@lru_cache()
def get_llm() -> ChatOpenAI:
    """Get LLM instance."""
    if settings.llm_provider == "openai":
        return ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            temperature=0.7,
        )
    elif settings.llm_provider == "ollama":
        return ChatOpenAI(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.7,
        )
    else:
        # Default to OpenAI
        return ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
        )


def get_qdrant_repository() -> QdrantRepository:
    """Get Qdrant repository instance."""
    global _qdrant_repository
    
    if _qdrant_repository is None:
        _qdrant_repository = QdrantRepository(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key,
            collection_name=settings.qdrant_collection_name,
        )
        logger.info("Created QdrantRepository instance")
    
    return _qdrant_repository


def get_indexing_service_instance() -> IndexingService:
    """Get IndexingService instance."""
    global _indexing_service
    
    if _indexing_service is None:
        # Note: In production, implement proper repository instances
        # For now, using mock repositories
        from src.repositories.mock_repositories import (
            MockDocumentRepository,
            MockIndexingJobRepository,
        )
        
        _indexing_service = IndexingService(
            document_repository=MockDocumentRepository(),
            vector_repository=get_qdrant_repository(),
            indexing_job_repository=MockIndexingJobRepository(),
            embedding_model=get_embedding_model(),
            config={
                "chunk_size": settings.docling_chunk_size,
                "chunk_overlap": settings.docling_chunk_overlap,
            },
        )
        logger.info("Created IndexingService instance")
    
    return _indexing_service


def get_rag_service_instance() -> RAGService:
    """Get RAGService instance."""
    global _rag_service
    
    if _rag_service is None:
        from src.repositories.mock_repositories import MockQueryRepository
        
        _rag_service = RAGService(
            vector_repository=get_qdrant_repository(),
            query_repository=MockQueryRepository(),
            embedding_model=get_embedding_model(),
            llm=get_llm(),
            config={
                "top_k": settings.rag_top_k,
                "score_threshold": settings.rag_score_threshold,
                "max_iterations": settings.agent_max_iterations,
            },
        )
        logger.info("Created RAGService instance")
    
    return _rag_service


async def initialize_services() -> None:
    """Initialize all services on startup."""
    logger.info("Initializing services...")
    
    # Initialize Qdrant collection
    qdrant_repo = get_qdrant_repository()
    await qdrant_repo.create_collection(
        collection_name=settings.qdrant_collection_name,
        vector_size=settings.qdrant_vector_size,
    )
    
    # Initialize other services
    get_indexing_service_instance()
    get_rag_service_instance()
    
    logger.info("Services initialized successfully")


async def shutdown_services() -> None:
    """Cleanup on shutdown."""
    logger.info("Shutting down services...")
    # Add cleanup logic here if needed
    logger.info("Services shut down successfully")

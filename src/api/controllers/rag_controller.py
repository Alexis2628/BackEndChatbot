"""
RAG API Controller (Router).
Handles HTTP requests for RAG queries.
"""

import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dtos import QueryRequest, QueryResponse
from src.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])


def get_rag_service() -> RAGService:
    """Dependency injection for RAG service."""
    # This will be implemented in main.py with proper DI
    from src.dependencies import get_rag_service_instance
    return get_rag_service_instance()


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute RAG Query",
    description="Process a query using the RAG system with optional multi-agent workflow.",
)
async def query(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> QueryResponse:
    """
    Execute a RAG query.
    
    - **query**: The user's question (required)
    - **filters**: Optional filters for document search
    - **top_k**: Number of top results to retrieve (1-20)
    - **score_threshold**: Minimum similarity score (0.0-1.0)
    - **use_agent**: Whether to use multi-agent system (default: true)
    """
    try:
        logger.info(f"Received query request: {request.query}")
        response = await rag_service.query(request)
        return response
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}",
        )


@router.get(
    "/query/{query_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Query by ID",
)
async def get_query(
    query_id: UUID,
    rag_service: RAGService = Depends(get_rag_service),
) -> Dict[str, Any]:
    """Get a query by its ID."""
    try:
        query = await rag_service.get_query_by_id(query_id)
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query {query_id} not found",
            )
        return query.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/queries/recent",
    response_model=list,
    status_code=status.HTTP_200_OK,
    summary="Get Recent Queries",
)
async def get_recent_queries(
    limit: int = 10,
    rag_service: RAGService = Depends(get_rag_service),
) -> list:
    """Get recent queries."""
    try:
        queries = await rag_service.get_recent_queries(limit)
        return [q.model_dump() for q in queries]
    except Exception as e:
        logger.error(f"Error getting recent queries: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

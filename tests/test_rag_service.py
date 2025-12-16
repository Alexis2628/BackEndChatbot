"""
Test RAG Service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.api.dtos import QueryRequest
from src.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_rag_query_simple():
    """Test simple RAG query without agents."""
    # Mock dependencies
    vector_repo = AsyncMock()
    query_repo = AsyncMock()
    embedding_model = AsyncMock()
    llm = AsyncMock()
    
    # Mock search results
    vector_repo.search.return_value = []
    
    # Mock query creation
    from src.domain.models import Query
    mock_query = Query(text="test query")
    query_repo.create.return_value = mock_query
    
    # Mock LLM response
    llm.ainvoke.return_value = MagicMock(content="Test answer")
    
    # Create service
    service = RAGService(
        vector_repository=vector_repo,
        query_repository=query_repo,
        embedding_model=embedding_model,
        llm=llm,
        config={"top_k": 5, "score_threshold": 0.7, "max_iterations": 10},
    )
    
    # Execute query
    request = QueryRequest(query="test query", use_agent=False)
    response = await service.query(request)
    
    # Assertions
    assert response.query == "test query"
    assert response.answer == "Test answer"
    assert vector_repo.search.called
    assert query_repo.create.called


@pytest.mark.asyncio
async def test_rag_query_with_agent():
    """Test RAG query with multi-agent system."""
    # This would test the agent workflow
    # Implementation depends on more complex mocking
    pass


def test_confidence_calculation():
    """Test confidence score calculation."""
    from src.services.rag_service import RAGService
    
    service = RAGService(
        vector_repository=AsyncMock(),
        query_repository=AsyncMock(),
        embedding_model=AsyncMock(),
        llm=AsyncMock(),
        config={},
    )
    
    # Test with sources
    sources = [
        {"score": 0.9},
        {"score": 0.8},
        {"score": 0.7},
    ]
    
    confidence = service._calculate_confidence(sources)
    assert confidence == pytest.approx(0.8667, abs=0.01)
    
    # Test with no sources
    confidence = service._calculate_confidence([])
    assert confidence == 0.0

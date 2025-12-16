"""
RAG Service - Core business logic for RAG operations.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.agents.multi_agent_system import MultiAgentRAGSystem
from src.api.dtos import QueryRequest, QueryResponse, SearchResultDTO
from src.domain.models import AgentType, Query, RAGResponse, SearchResult
from src.repositories.interfaces import IQueryRepository, IVectorRepository

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG query operations."""

    def __init__(
        self,
        vector_repository: IVectorRepository,
        query_repository: IQueryRepository,
        embedding_model: OpenAIEmbeddings,
        llm: ChatOpenAI,
        config: Dict[str, Any],
    ):
        """Initialize RAG service."""
        self.vector_repo = vector_repository
        self.query_repo = query_repository
        self.embedding_model = embedding_model
        self.llm = llm
        self.config = config
        
        # Initialize multi-agent system
        self.agent_system = MultiAgentRAGSystem(
            llm=llm,
            vector_search_func=self._vector_search,
            max_iterations=config.get("max_iterations", 10),
        )
        
        logger.info("Initialized RAGService")

    async def _vector_search(self, query: str) -> List[SearchResult]:
        """Internal method for vector search."""
        # Generate embedding for query
        query_embedding = await self.embedding_model.aembed_query(query)
        
        # Search in vector DB
        results = await self.vector_repo.search(
            query_embedding=query_embedding,
            top_k=self.config.get("top_k", 5),
            score_threshold=self.config.get("score_threshold", 0.7),
        )
        
        return results

    async def query(self, request: QueryRequest) -> QueryResponse:
        """Process a RAG query."""
        start_time = time.time()
        
        logger.info(f"Processing query: {request.query}")
        
        try:
            # Save query to repository
            query_domain = Query(
                text=request.query,
                filters=request.filters,
                top_k=request.top_k,
                score_threshold=request.score_threshold,
            )
            saved_query = await self.query_repo.create(query_domain)
            
            if request.use_agent:
                # Use multi-agent system
                result = await self.agent_system.execute(request.query)
                
                answer = result["answer"]
                sources = result["sources"]
                agent_type = AgentType.ROUTER
                metadata = result["metadata"]
            else:
                # Simple RAG without agents
                search_results = await self._vector_search(request.query)
                
                # Generate answer using LLM
                context = "\n\n".join([
                    f"[Source {i+1}]\n{r.content}"
                    for i, r in enumerate(search_results[:request.top_k])
                ])
                
                prompt = f"""Context:\n{context}\n\nQuery: {request.query}\n\nAnswer:"""
                response = await self.llm.ainvoke(prompt)
                
                answer = response.content
                sources = [
                    {
                        "chunk_id": str(r.chunk_id),
                        "document_id": str(r.document_id),
                        "content": r.content,
                        "score": r.score,
                        "metadata": r.metadata,
                    }
                    for r in search_results
                ]
                agent_type = AgentType.QUERY
                metadata = {}
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Build response
            response = QueryResponse(
                query_id=saved_query.id,
                query=request.query,
                answer=answer,
                sources=[
                    SearchResultDTO(
                        chunk_id=UUID(s["chunk_id"]) if isinstance(s["chunk_id"], str) else s["chunk_id"],
                        document_id=UUID(s["document_id"]) if isinstance(s["document_id"], str) else s["document_id"],
                        content=s["content"],
                        score=s["score"],
                        metadata=s["metadata"],
                    )
                    for s in sources
                ],
                confidence=self._calculate_confidence(sources),
                agent_type=agent_type,
                processing_time_ms=processing_time_ms,
                metadata=metadata,
            )
            
            logger.info(
                f"Query processed successfully in {processing_time_ms:.2f}ms"
            )
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            raise

    def _calculate_confidence(self, sources: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on search results."""
        if not sources:
            return 0.0
        
        # Average of top-3 scores
        top_scores = sorted([s["score"] for s in sources], reverse=True)[:3]
        return sum(top_scores) / len(top_scores) if top_scores else 0.0

    async def get_query_by_id(self, query_id: UUID) -> Optional[Query]:
        """Get query by ID."""
        return await self.query_repo.get_by_id(query_id)

    async def get_recent_queries(self, limit: int = 10) -> List[Query]:
        """Get recent queries."""
        return await self.query_repo.get_recent_queries(limit)

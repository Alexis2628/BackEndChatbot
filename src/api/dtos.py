"""
Data Transfer Objects (DTOs) for API requests and responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.models import AgentType, DocumentStatus


# ============ Document DTOs ============

class DocumentUploadRequest(BaseModel):
    """Request DTO for document upload."""
    filename: str
    content_type: str
    metadata: Optional[Dict[str, Any]] = None


class DocumentUploadResponse(BaseModel):
    """Response DTO for document upload."""
    document_id: UUID
    filename: str
    status: DocumentStatus
    message: str


class DocumentResponse(BaseModel):
    """Response DTO for document details."""
    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]


class DocumentListResponse(BaseModel):
    """Response DTO for document list."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


# ============ Indexing DTOs ============

class IndexingRequest(BaseModel):
    """Request DTO for indexing job."""
    document_ids: List[UUID]
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200


class IndexingJobResponse(BaseModel):
    """Response DTO for indexing job."""
    job_id: UUID
    document_ids: List[UUID]
    status: DocumentStatus
    total_chunks: int
    processed_chunks: int
    created_at: datetime


# ============ Query DTOs ============

class QueryRequest(BaseModel):
    """Request DTO for RAG query."""
    query: str = Field(..., min_length=1, max_length=1000)
    filters: Optional[Dict[str, Any]] = None
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    use_agent: bool = Field(default=True, description="Use multi-agent system")


class SearchResultDTO(BaseModel):
    """DTO for search result."""
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    metadata: Dict[str, Any]


class QueryResponse(BaseModel):
    """Response DTO for RAG query."""
    query_id: UUID
    query: str
    answer: str
    sources: List[SearchResultDTO]
    confidence: float
    agent_type: AgentType
    processing_time_ms: float
    metadata: Dict[str, Any]


# ============ Agent DTOs ============

class AgentExecutionRequest(BaseModel):
    """Request DTO for agent execution."""
    query: str
    agent_type: AgentType
    additional_context: Optional[Dict[str, Any]] = None


class AgentExecutionResponse(BaseModel):
    """Response DTO for agent execution."""
    execution_id: UUID
    agent_type: AgentType
    status: str
    result: Dict[str, Any]
    execution_time_ms: float


# ============ MCP DTOs ============

class MCPContextRequest(BaseModel):
    """Request DTO for MCP context."""
    query: str
    max_tokens: int = 4000


class MCPContextResponse(BaseModel):
    """Response DTO for MCP context."""
    context: str
    tokens_used: int
    sources: List[str]


# ============ Health & Status DTOs ============

class HealthResponse(BaseModel):
    """Response DTO for health check."""
    status: str
    timestamp: datetime
    services: Dict[str, str]


class MetricsResponse(BaseModel):
    """Response DTO for system metrics."""
    total_documents: int
    total_chunks: int
    total_queries: int
    avg_query_time_ms: float
    cache_hit_rate: float

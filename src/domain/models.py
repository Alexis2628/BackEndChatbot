"""
Domain Models for the RAG System.
These represent the core business entities.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(str, Enum):
    """Types of agents in the system."""
    ROUTER = "router"
    INDEXING = "indexing"
    QUERY = "query"
    EVALUATION = "evaluation"


class Document(BaseModel):
    """Domain model for a document."""
    id: UUID = Field(default_factory=uuid4)
    filename: str
    file_path: str
    content_type: str
    size_bytes: int
    status: DocumentStatus = DocumentStatus.PENDING
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class Chunk(BaseModel):
    """Domain model for a document chunk."""
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    content: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class Query(BaseModel):
    """Domain model for a user query."""
    id: UUID = Field(default_factory=uuid4)
    text: str
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 5
    score_threshold: float = 0.7
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    """Domain model for a search result."""
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    metadata: Dict[str, Any]


class RAGResponse(BaseModel):
    """Domain model for RAG system response."""
    id: UUID = Field(default_factory=uuid4)
    query_id: UUID
    answer: str
    sources: List[SearchResult]
    confidence: float
    agent_type: AgentType
    processing_time_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class AgentState(BaseModel):
    """State model for LangGraph agents."""
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    query: Optional[str] = None
    documents: List[Document] = Field(default_factory=list)
    chunks: List[Chunk] = Field(default_factory=list)
    search_results: List[SearchResult] = Field(default_factory=list)
    answer: Optional[str] = None
    current_agent: Optional[AgentType] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    iteration: int = 0
    max_iterations: int = 10


class IndexingJob(BaseModel):
    """Domain model for an indexing job."""
    id: UUID = Field(default_factory=uuid4)
    document_ids: List[UUID]
    status: DocumentStatus = DocumentStatus.PENDING
    total_chunks: int = 0
    processed_chunks: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

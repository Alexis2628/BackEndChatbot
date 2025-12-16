"""
Repository interfaces (Abstract Base Classes).
These define the contracts for data access.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.models import Chunk, Document, IndexingJob, Query, SearchResult


class IDocumentRepository(ABC):
    """Interface for document repository."""

    @abstractmethod
    async def create(self, document: Document) -> Document:
        """Create a new document."""
        pass

    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID."""
        pass

    @abstractmethod
    async def get_all(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[Document]:
        """Get all documents with pagination."""
        pass

    @abstractmethod
    async def update(self, document: Document) -> Document:
        """Update an existing document."""
        pass

    @abstractmethod
    async def delete(self, document_id: UUID) -> bool:
        """Delete a document."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total documents."""
        pass


class IVectorRepository(ABC):
    """Interface for vector database repository (Qdrant)."""

    @abstractmethod
    async def create_collection(self, collection_name: str, vector_size: int) -> bool:
        """Create a collection."""
        pass

    @abstractmethod
    async def upsert_chunks(self, chunks: List[Chunk]) -> bool:
        """Upsert document chunks with embeddings."""
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        score_threshold: float = 0.7,
        filters: Optional[dict] = None,
    ) -> List[SearchResult]:
        """Search for similar chunks."""
        pass

    @abstractmethod
    async def delete_by_document_id(self, document_id: UUID) -> bool:
        """Delete all chunks for a document."""
        pass

    @abstractmethod
    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[Chunk]:
        """Get chunk by ID."""
        pass

    @abstractmethod
    async def count_chunks(self) -> int:
        """Count total chunks."""
        pass


class IIndexingJobRepository(ABC):
    """Interface for indexing job repository."""

    @abstractmethod
    async def create(self, job: IndexingJob) -> IndexingJob:
        """Create a new indexing job."""
        pass

    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> Optional[IndexingJob]:
        """Get job by ID."""
        pass

    @abstractmethod
    async def update(self, job: IndexingJob) -> IndexingJob:
        """Update job status."""
        pass

    @abstractmethod
    async def get_pending_jobs(self) -> List[IndexingJob]:
        """Get all pending jobs."""
        pass


class IQueryRepository(ABC):
    """Interface for query repository."""

    @abstractmethod
    async def create(self, query: Query) -> Query:
        """Save a query."""
        pass

    @abstractmethod
    async def get_by_id(self, query_id: UUID) -> Optional[Query]:
        """Get query by ID."""
        pass

    @abstractmethod
    async def get_recent_queries(self, limit: int = 10) -> List[Query]:
        """Get recent queries."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total queries."""
        pass

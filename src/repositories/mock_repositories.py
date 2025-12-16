"""
Mock Repository Implementations.
For development/testing purposes until database layer is fully implemented.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from src.domain.models import Document, IndexingJob, Query
from src.repositories.interfaces import (
    IDocumentRepository,
    IIndexingJobRepository,
    IQueryRepository,
)

logger = logging.getLogger(__name__)


class MockDocumentRepository(IDocumentRepository):
    """In-memory document repository for development."""

    def __init__(self) -> None:
        self.documents: Dict[UUID, Document] = {}

    async def create(self, document: Document) -> Document:
        self.documents[document.id] = document
        return document

    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        return self.documents.get(document_id)

    async def get_all(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[Document]:
        docs = list(self.documents.values())
        if status:
            docs = [d for d in docs if d.status == status]
        return docs[skip : skip + limit]

    async def update(self, document: Document) -> Document:
        self.documents[document.id] = document
        return document

    async def delete(self, document_id: UUID) -> bool:
        if document_id in self.documents:
            del self.documents[document_id]
            return True
        return False

    async def count(self) -> int:
        return len(self.documents)


class MockIndexingJobRepository(IIndexingJobRepository):
    """In-memory indexing job repository for development."""

    def __init__(self) -> None:
        self.jobs: Dict[UUID, IndexingJob] = {}

    async def create(self, job: IndexingJob) -> IndexingJob:
        self.jobs[job.id] = job
        return job

    async def get_by_id(self, job_id: UUID) -> Optional[IndexingJob]:
        return self.jobs.get(job_id)

    async def update(self, job: IndexingJob) -> IndexingJob:
        self.jobs[job.id] = job
        return job

    async def get_pending_jobs(self) -> List[IndexingJob]:
        return [j for j in self.jobs.values() if j.status == "pending"]


class MockQueryRepository(IQueryRepository):
    """In-memory query repository for development."""

    def __init__(self) -> None:
        self.queries: Dict[UUID, Query] = {}

    async def create(self, query: Query) -> Query:
        self.queries[query.id] = query
        return query

    async def get_by_id(self, query_id: UUID) -> Optional[Query]:
        return self.queries.get(query_id)

    async def get_recent_queries(self, limit: int = 10) -> List[Query]:
        queries = sorted(
            self.queries.values(),
            key=lambda q: q.created_at,
            reverse=True,
        )
        return queries[:limit]

    async def count(self) -> int:
        return len(self.queries)

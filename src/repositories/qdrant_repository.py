"""
Qdrant Vector Database Repository Implementation.
"""

import logging
from typing import List, Optional
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from src.domain.models import Chunk, SearchResult
from src.repositories.interfaces import IVectorRepository

logger = logging.getLogger(__name__)


class QdrantRepository(IVectorRepository):
    """Qdrant implementation of vector repository."""

    def __init__(
        self,
        host: str,
        port: int,
        api_key: Optional[str] = None,
        collection_name: str = "rag_documents",
    ):
        """Initialize Qdrant client."""
        self.client = QdrantClient(host=host, port=port, api_key=api_key)
        self.collection_name = collection_name
        logger.info(f"Initialized QdrantRepository with collection: {collection_name}")

    async def create_collection(self, collection_name: str, vector_size: int) -> bool:
        """Create a collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            if any(c.name == collection_name for c in collections):
                logger.info(f"Collection {collection_name} already exists")
                return True

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info(f"Created collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False

    async def upsert_chunks(self, chunks: List[Chunk]) -> bool:
        """Upsert document chunks with embeddings."""
        try:
            points = []
            for chunk in chunks:
                if chunk.embedding is None:
                    logger.warning(f"Chunk {chunk.id} has no embedding, skipping")
                    continue

                point = models.PointStruct(
                    id=str(chunk.id),
                    vector=chunk.embedding,
                    payload={
                        "document_id": str(chunk.document_id),
                        "content": chunk.content,
                        "chunk_index": chunk.chunk_index,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                        "metadata": chunk.metadata,
                        "created_at": chunk.created_at.isoformat(),
                    },
                )
                points.append(point)

            if not points:
                logger.warning("No valid points to upsert")
                return False

            self.client.upsert(collection_name=self.collection_name, points=points)
            logger.info(f"Upserted {len(points)} chunks to Qdrant")
            return True
        except Exception as e:
            logger.error(f"Error upserting chunks: {e}")
            return False

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        score_threshold: float = 0.7,
        filters: Optional[dict] = None,
    ) -> List[SearchResult]:
        """Search for similar chunks."""
        try:
            query_filter = None
            if filters:
                # Convert filters to Qdrant filter format
                query_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value),
                        )
                        for key, value in filters.items()
                    ]
                )

            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=query_filter,
            )

            results = []
            for hit in search_result:
                result = SearchResult(
                    chunk_id=UUID(hit.id),
                    document_id=UUID(hit.payload["document_id"]),
                    content=hit.payload["content"],
                    score=hit.score,
                    metadata=hit.payload.get("metadata", {}),
                )
                results.append(result)

            logger.info(f"Found {len(results)} similar chunks")
            return results
        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
            return []

    async def delete_by_document_id(self, document_id: UUID) -> bool:
        """Delete all chunks for a document."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=str(document_id)),
                            )
                        ]
                    )
                ),
            )
            logger.info(f"Deleted chunks for document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            return False

    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[Chunk]:
        """Get chunk by ID."""
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[str(chunk_id)],
            )
            if not result:
                return None

            point = result[0]
            chunk = Chunk(
                id=UUID(point.id),
                document_id=UUID(point.payload["document_id"]),
                content=point.payload["content"],
                chunk_index=point.payload["chunk_index"],
                start_char=point.payload["start_char"],
                end_char=point.payload["end_char"],
                metadata=point.payload.get("metadata", {}),
                embedding=point.vector if hasattr(point, "vector") else None,
            )
            return chunk
        except Exception as e:
            logger.error(f"Error getting chunk: {e}")
            return None

    async def count_chunks(self) -> int:
        """Count total chunks."""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return collection_info.points_count
        except UnexpectedResponse:
            logger.warning(f"Collection {self.collection_name} does not exist")
            return 0
        except Exception as e:
            logger.error(f"Error counting chunks: {e}")
            return 0

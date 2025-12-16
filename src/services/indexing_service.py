"""
Indexing Service - Handles document processing and indexing.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from docling.document_converter import DocumentConverter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from src.domain.models import Chunk, Document, DocumentStatus, IndexingJob
from src.repositories.interfaces import (
    IDocumentRepository,
    IIndexingJobRepository,
    IVectorRepository,
)

logger = logging.getLogger(__name__)


class IndexingService:
    """Service for document indexing operations."""

    def __init__(
        self,
        document_repository: IDocumentRepository,
        vector_repository: IVectorRepository,
        indexing_job_repository: IIndexingJobRepository,
        embedding_model: OpenAIEmbeddings,
        config: Dict[str, Any],
    ):
        """Initialize indexing service."""
        self.doc_repo = document_repository
        self.vector_repo = vector_repository
        self.job_repo = indexing_job_repository
        self.embedding_model = embedding_model
        self.config = config
        
        # Initialize Docling converter
        self.doc_converter = DocumentConverter()
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.get("chunk_size", 1000),
            chunk_overlap=config.get("chunk_overlap", 200),
            length_function=len,
        )
        
        logger.info("Initialized IndexingService")

    async def create_document(
        self,
        filename: str,
        file_path: str,
        content_type: str,
        size_bytes: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """Create a new document record."""
        logger.info(f"Creating document: {filename}")
        
        document = Document(
            filename=filename,
            file_path=file_path,
            content_type=content_type,
            size_bytes=size_bytes,
            status=DocumentStatus.PENDING,
            metadata=metadata or {},
        )
        
        saved_doc = await self.doc_repo.create(document)
        logger.info(f"Document created: {saved_doc.id}")
        return saved_doc

    async def process_document(self, document_id: UUID) -> IndexingJob:
        """Process a document: parse, chunk, embed, and index."""
        logger.info(f"Processing document: {document_id}")
        
        try:
            # Get document
            document = await self.doc_repo.get_by_id(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            await self.doc_repo.update(document)
            
            # Create indexing job
            job = IndexingJob(document_ids=[document_id])
            saved_job = await self.job_repo.create(job)
            
            # Parse document using Docling
            logger.info(f"Parsing document with Docling: {document.file_path}")
            parsed_content = await self._parse_document(document.file_path)
            
            # Split into chunks
            logger.info("Splitting document into chunks")
            text_chunks = self.text_splitter.split_text(parsed_content)
            
            # Create chunk objects with embeddings
            chunks: List[Chunk] = []
            for idx, text in enumerate(text_chunks):
                # Generate embedding
                embedding = await self.embedding_model.aembed_query(text)
                
                chunk = Chunk(
                    document_id=document_id,
                    content=text,
                    chunk_index=idx,
                    start_char=idx * self.config.get("chunk_size", 1000),
                    end_char=(idx + 1) * self.config.get("chunk_size", 1000),
                    metadata=document.metadata,
                    embedding=embedding,
                )
                chunks.append(chunk)
            
            logger.info(f"Created {len(chunks)} chunks with embeddings")
            
            # Store chunks in vector DB
            success = await self.vector_repo.upsert_chunks(chunks)
            if not success:
                raise Exception("Failed to store chunks in vector DB")
            
            # Update document status
            document.status = DocumentStatus.COMPLETED
            await self.doc_repo.update(document)
            
            # Update job
            job.status = DocumentStatus.COMPLETED
            job.total_chunks = len(chunks)
            job.processed_chunks = len(chunks)
            await self.job_repo.update(job)
            
            logger.info(f"Document {document_id} processed successfully")
            return job
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
            
            # Update statuses to failed
            if document:
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)
                await self.doc_repo.update(document)
            
            if saved_job:
                saved_job.status = DocumentStatus.FAILED
                saved_job.error_message = str(e)
                await self.job_repo.update(saved_job)
            
            raise

    async def _parse_document(self, file_path: str) -> str:
        """Parse document using Docling."""
        try:
            # Convert document
            result = self.doc_converter.convert(file_path)
            
            # Extract text content
            # Note: Actual implementation depends on Docling API
            # This is a simplified version
            text_content = result.document.export_to_markdown()
            
            return text_content
        except Exception as e:
            logger.error(f"Error parsing document with Docling: {e}")
            # Fallback to simple text extraction
            return Path(file_path).read_text(encoding="utf-8")

    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document and its chunks."""
        logger.info(f"Deleting document: {document_id}")
        
        try:
            # Delete from vector DB
            await self.vector_repo.delete_by_document_id(document_id)
            
            # Delete from document repo
            success = await self.doc_repo.delete(document_id)
            
            logger.info(f"Document {document_id} deleted successfully")
            return success
        except Exception as e:
            logger.error(f"Error deleting document: {e}", exc_info=True)
            return False

    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID."""
        return await self.doc_repo.get_by_id(document_id)

    async def list_documents(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[Document]:
        """List documents with pagination."""
        return await self.doc_repo.get_all(skip=skip, limit=limit, status=status)

    async def get_indexing_job(self, job_id: UUID) -> Optional[IndexingJob]:
        """Get indexing job by ID."""
        return await self.job_repo.get_by_id(job_id)

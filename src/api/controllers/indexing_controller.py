"""
Indexing API Controller (Router).
Handles HTTP requests for document indexing.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from src.api.dtos import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
    IndexingJobResponse,
    IndexingRequest,
)
from src.domain.models import DocumentStatus
from src.services.indexing_service import IndexingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


def get_indexing_service() -> IndexingService:
    """Dependency injection for indexing service."""
    from src.dependencies import get_indexing_service_instance
    return get_indexing_service_instance()


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Document",
    description="Upload a document for indexing.",
)
async def upload_document(
    file: UploadFile = File(...),
    indexing_service: IndexingService = Depends(get_indexing_service),
) -> DocumentUploadResponse:
    """
    Upload a document.
    
    - **file**: The document file to upload
    """
    try:
        logger.info(f"Uploading document: {file.filename}")
        
        # Save file temporarily
        import aiofiles
        from pathlib import Path
        
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        # Create document record
        document = await indexing_service.create_document(
            filename=file.filename,
            file_path=str(file_path),
            content_type=file.content_type or "application/octet-stream",
            size_bytes=len(content),
        )
        
        return DocumentUploadResponse(
            document_id=document.id,
            filename=document.filename,
            status=document.status,
            message="Document uploaded successfully",
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}",
        )


@router.post(
    "/index",
    response_model=IndexingJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Index Documents",
    description="Start indexing job for documents.",
)
async def index_documents(
    request: IndexingRequest,
    indexing_service: IndexingService = Depends(get_indexing_service),
) -> IndexingJobResponse:
    """
    Index documents.
    
    - **document_ids**: List of document IDs to index
    - **chunk_size**: Size of document chunks (optional)
    - **chunk_overlap**: Overlap between chunks (optional)
    """
    try:
        logger.info(f"Starting indexing for {len(request.document_ids)} documents")
        
        # Process first document (in production, use background tasks)
        job = await indexing_service.process_document(request.document_ids[0])
        
        return IndexingJobResponse(
            job_id=job.id,
            document_ids=job.document_ids,
            status=job.status,
            total_chunks=job.total_chunks,
            processed_chunks=job.processed_chunks,
            created_at=job.created_at,
        )
        
    except Exception as e:
        logger.error(f"Error indexing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error indexing documents: {str(e)}",
        )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Document",
)
async def get_document(
    document_id: UUID,
    indexing_service: IndexingService = Depends(get_indexing_service),
) -> DocumentResponse:
    """Get document by ID."""
    try:
        document = await indexing_service.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            status=document.status,
            metadata=document.metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
            processed_at=document.processed_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Documents",
)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    indexing_service: IndexingService = Depends(get_indexing_service),
) -> DocumentListResponse:
    """List documents with pagination."""
    try:
        documents = await indexing_service.list_documents(
            skip=skip, limit=limit, status=status_filter
        )
        
        return DocumentListResponse(
            documents=[
                DocumentResponse(
                    id=doc.id,
                    filename=doc.filename,
                    content_type=doc.content_type,
                    size_bytes=doc.size_bytes,
                    status=doc.status,
                    metadata=doc.metadata,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    processed_at=doc.processed_at,
                )
                for doc in documents
            ],
            total=len(documents),
            page=skip // limit + 1,
            page_size=limit,
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Document",
)
async def delete_document(
    document_id: UUID,
    indexing_service: IndexingService = Depends(get_indexing_service),
) -> None:
    """Delete a document."""
    try:
        success = await indexing_service.delete_document(document_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

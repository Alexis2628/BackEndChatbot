"""
Main FastAPI Application.
Entry point for the Enterprise RAG System.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.controllers import indexing_controller, rag_controller
from src.config import settings
from src.dependencies import initialize_services, shutdown_services

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    logger.info("Starting application...")
    
    # Startup
    await initialize_services()
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await shutdown_services()
    logger.info("Application shut down successfully")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Enterprise RAG System with Multi-Agent Architecture
    
    ## Features
    * 🤖 Multi-agent workflow using LangGraph
    * 📄 Advanced document processing with Docling
    * 🔍 Vector search with Qdrant
    * 🧠 LLM-powered responses
    * 📊 MCP (Model Context Protocol) support
    
    ## Architecture
    * **Repository Pattern** for clean data access
    * **Domain-Driven Design** principles
    * **Dependency Injection** for modularity
    * **Type-safe** with strict type hints
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rag_controller.router)
app.include_router(indexing_controller.router)


# Health check endpoint
@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Health Check",
)
async def health_check() -> JSONResponse:
    """Check if the API is running."""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app_version,
            "environment": settings.app_env,
        }
    )


# Root endpoint
@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    tags=["Root"],
)
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Welcome to Enterprise RAG System",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )

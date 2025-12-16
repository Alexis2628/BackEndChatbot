"""
MCP (Model Context Protocol) Implementation.
Provides standardized context access for the RAG system.
"""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MCPContext(BaseModel):
    """MCP Context structure."""
    query: str
    context_documents: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    max_tokens: int = 4000


class MCPProvider:
    """MCP Provider for context management."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize MCP provider."""
        self.config = config
        self.enabled = config.get("enabled", True)
        logger.info(f"Initialized MCPProvider (enabled: {self.enabled})")

    async def get_context(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        max_tokens: int = 4000,
    ) -> MCPContext:
        """
        Get context for a query following MCP protocol.
        
        Args:
            query: User query
            documents: Retrieved documents
            max_tokens: Maximum tokens for context
            
        Returns:
            MCPContext with structured context
        """
        if not self.enabled:
            logger.warning("MCP is disabled")
            return MCPContext(
                query=query,
                context_documents=[],
                metadata={"enabled": False},
                max_tokens=max_tokens,
            )

        # Filter and structure documents
        context_docs = []
        current_tokens = 0
        
        for doc in documents:
            # Simplified token counting (use tiktoken for production)
            doc_tokens = len(doc.get("content", "")) // 4
            
            if current_tokens + doc_tokens > max_tokens:
                break
            
            context_docs.append({
                "id": doc.get("id"),
                "content": doc.get("content"),
                "score": doc.get("score", 0.0),
                "metadata": doc.get("metadata", {}),
            })
            current_tokens += doc_tokens

        mcp_context = MCPContext(
            query=query,
            context_documents=context_docs,
            metadata={
                "total_documents": len(documents),
                "included_documents": len(context_docs),
                "estimated_tokens": current_tokens,
            },
            max_tokens=max_tokens,
        )

        logger.info(
            f"Generated MCP context: {len(context_docs)} docs, ~{current_tokens} tokens"
        )
        return mcp_context

    async def format_for_llm(self, context: MCPContext) -> str:
        """Format MCP context for LLM consumption."""
        formatted = f"Query: {context.query}\n\n"
        formatted += "Context Documents:\n\n"
        
        for i, doc in enumerate(context.context_documents, 1):
            formatted += f"[Document {i}] (Relevance: {doc['score']:.2f})\n"
            formatted += f"{doc['content']}\n\n"
        
        return formatted


# Singleton instance
_mcp_provider: Optional[MCPProvider] = None


def get_mcp_provider(config: Optional[Dict[str, Any]] = None) -> MCPProvider:
    """Get or create MCP provider instance."""
    global _mcp_provider
    
    if _mcp_provider is None:
        if config is None:
            from src.config import settings
            config = {
                "enabled": settings.mcp_enabled,
                "server_url": settings.mcp_server_url,
            }
        _mcp_provider = MCPProvider(config)
    
    return _mcp_provider

"""Main MCP server implementation for advanced RAG capabilities."""

# 1. Standard library imports
import asyncio
import json
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime, date
import decimal

# 2. Third-party imports
from fastmcp import FastMCP
from fastmcp import Context
from pydantic import BaseModel

# 3. Local application imports  
from src.llm_models import get_chat_model
from src.embeddings import get_openai_embeddings
from src.vectorstore_setup import get_main_vectorstore, BASELINE_COLLECTION_NAME
from src.retriever_factory import create_retriever
from src.chain_factory import create_rag_chain
from src.logging_config import setup_logging


def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def safe_json_dumps(data, **kwargs):
    """Safely serialize data to JSON, handling datetime and other non-serializable objects."""
    return json.dumps(data, default=json_serializer, **kwargs)


# Request/Response models
class SemanticSearchRequest(BaseModel):
    """Request model for semantic search tool."""
    query: str
    top_k: int = 5
    retrieval_type: str = "hybrid"


class DocumentQueryRequest(BaseModel):
    """Request model for document-specific queries."""
    question: str
    document_filter: Optional[dict] = None


# Initialize logging and logger
import logging
logger = logging.getLogger(__name__)

# Global state for MCP server
server_state = {}


@asynccontextmanager
async def lifespan(app):
    """MCP server lifespan management with resource setup/cleanup."""
    # Setup logging first
    if not logging.getLogger().hasHandlers():
        setup_logging()
    
    logger.info("Initializing MCP server resources")
    
    try:
        # Initialize embeddings and LLM
        embeddings = get_openai_embeddings()
        llm = get_chat_model()
        
        # Setup vector store
        vectorstore = get_main_vectorstore()
        
        # Create retriever and chain
        retriever = create_retriever("hybrid", vectorstore)
        rag_chain = create_rag_chain(retriever)
        
        # Store in global state
        server_state.update({
            "vectorstore": vectorstore,
            "retriever": retriever,
            "rag_chain": rag_chain,
            "embeddings": embeddings,
            "llm": llm
        })
        
        logger.info("MCP server initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP server: {e}")
        raise
    finally:
        logger.info("Shutting down MCP server")
        # Cleanup resources if needed
        server_state.clear()


# Initialize FastMCP server following v2.8.0 best practices
mcp = FastMCP(
    name="Advanced RAG Server",
    instructions="""
    This server provides advanced retrieval-augmented generation (RAG) capabilities.
    
    Available tools:
    - semantic_search: Find relevant documents using hybrid search (vector + BM25)
    - document_query: Ask natural language questions about the document collection
    - get_collection_stats: Get metadata about the document collection
    
    Available resources:
    - rag://collections/{collection_name}: Get detailed collection information
    """,
    lifespan=lifespan,
    # Use include_tags to expose only components with these tags
    include_tags={"rag", "search", "retrieval", "qa"}
)


@mcp.tool(tags={"search", "retrieval"})
async def semantic_search(
    query: str, 
    ctx: Context,
    top_k: int = 5, 
    retrieval_type: str = "hybrid"
) -> str:
    """
    Perform semantic search across the document collection.
    
    Returns relevant documents based on the query using hybrid search
    combining vector similarity and BM25 keyword matching.
    """
    try:
        # Use FastMCP 2.0 logging context
        await ctx.info(f"Semantic search request: {query[:100]}...")
        
        # Get retriever from state
        if retrieval_type == "hybrid":
            retriever = server_state["retriever"]  # Already hybrid
        else:
            vectorstore = server_state["vectorstore"]
            retriever = create_retriever(retrieval_type, vectorstore)
        
        # Retrieve documents
        docs = retriever.get_relevant_documents(query)[:top_k]
        
        # Format response
        results = []
        for i, doc in enumerate(docs):
            results.append({
                "rank": i + 1,
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": getattr(doc, 'score', None)
            })
        
        await ctx.info(f"Retrieved {len(results)} documents for query")
        return safe_json_dumps(results)
        
    except Exception as e:
        await ctx.error(f"Semantic search failed: {e}")
        return f"Error performing semantic search: {str(e)}"


@mcp.tool(tags={"qa", "rag"})
async def document_query(question: str, document_filter: dict = None) -> str:
    """
    Query the document collection with a natural language question.
    
    Uses the full RAG pipeline to provide comprehensive answers
    based on retrieved relevant documents.
    """
    try:
        logger.info(f"Document query request: {question[:100]}...")
        
        # Get RAG chain from state
        rag_chain = server_state["rag_chain"]
        
        # Process query
        response = await rag_chain.ainvoke({"question": question})
        
        logger.info("Document query processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Document query failed: {e}")
        return f"Error processing document query: {str(e)}"


@mcp.tool
async def get_collection_stats() -> str:
    """
    Get statistics about the document collection.
    
    Returns information about the number of documents, collection health,
    and other metadata useful for understanding the knowledge base.
    """
    try:
        vectorstore = server_state["vectorstore"]
        
        # Get collection information (implementation depends on your vectorstore)
        stats = {
            "collection_name": BASELINE_COLLECTION_NAME,
            "status": "healthy",
            "last_updated": "N/A",  # Implement based on your tracking
            "approximate_document_count": "N/A"  # Implement based on vectorstore
        }
        
        return safe_json_dumps(stats)
        
    except Exception as e:
        logger.error(f"Failed to get collection stats: {e}")
        return f"Error getting collection statistics: {str(e)}"


@mcp.resource("rag://collections/{collection_name}")
async def get_collection_info(collection_name: str) -> str:
    """
    MCP Resource: Get detailed information about a specific collection.
    
    Provides metadata, configuration, and status information for
    the specified document collection.
    """
    try:
        if collection_name != BASELINE_COLLECTION_NAME:
            return f"Collection '{collection_name}' not found"
        
        vectorstore = server_state["vectorstore"]
        
        info = {
            "name": collection_name,
            "type": "qdrant_vector_store",
            "status": "active",
            "configuration": {
                "embedding_model": "text-embedding-3-small",
                "vector_size": 1536,  # text-embedding-3-small dimension
                "distance_metric": "cosine"
            },
            "capabilities": [
                "semantic_search",
                "hybrid_search", 
                "mmr_search",
                "metadata_filtering"
            ]
        }
        
        return safe_json_dumps(info)
        
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        return f"Error getting collection information: {str(e)}"


def main():
    """Entry point for MCP server - Run in stdio mode for Claude Desktop integration."""
    import sys
    import logging
    
    # Add debug output for Inspector
    print("Starting Advanced RAG MCP Server...", file=sys.stderr)
    print("Transport: stdio", file=sys.stderr)
    
    try:
        # FastMCP 2.0 recommended run pattern
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("Server interrupted by user", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main() 
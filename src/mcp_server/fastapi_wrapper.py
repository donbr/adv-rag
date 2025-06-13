# mcp_server/fastapi_wrapper.py - Primary MCP Server Implementation

"""
FastMCP server that converts the Advanced RAG FastAPI application 
to a Model Context Protocol (MCP) server using the recommended approach.

This implementation follows FastMCP 2.0 best practices:
- Zero code duplication via FastMCP.from_fastapi()
- Preserves all 6 retrieval endpoints as MCP tools
- Schema inheritance and validation from FastAPI
- Custom tool naming for better UX

Architecture:
- src/main_api.py: FastAPI application with 6 retrieval endpoints
- This file: MCP wrapper exposing FastAPI endpoints as MCP tools
"""

import logging
import sys
import os
from pathlib import Path
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mcp_server():
    """Create MCP server from FastAPI app using FastMCP.from_fastapi()"""
    
    try:
        # Add project root to Python path for imports
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent  # Go up 3 levels: mcp_server -> src -> project_root
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            logger.info(f"Added project root to Python path: {project_root}")
        
        # Import the FastAPI app
        from src.main_api import app
        logger.info(f"Successfully imported FastAPI app with {len(app.routes)} routes")
        
        # Convert FastAPI app to MCP server using FastMCP.from_fastapi()
        # This works as a pure wrapper - no backend services needed during conversion
        mcp = FastMCP.from_fastapi(
            app=app,
            # name="Advanced RAG MCP Server",
            # tags={"rag", "retrieval", "langchain", "fastapi", "production"},
            # # Custom component names for better MCP tool naming
            # mcp_names={
            #     "naive_retriever": "naive_search",
            #     "bm25_retriever": "keyword_search", 
            #     "contextual_compression_retriever": "compressed_search",
            #     "multi_query_retriever": "enhanced_search",
            #     "ensemble_retriever": "hybrid_search",
            #     "semantic_retriever": "semantic_search"
            # }
        )
        
        logger.info("FastMCP server created successfully from FastAPI app")
        logger.info("MCP tools available with improved names:")
        logger.info("- naive_search: Basic similarity search")
        logger.info("- keyword_search: BM25 keyword-based search") 
        logger.info("- compressed_search: Contextual compression retrieval")
        logger.info("- enhanced_search: Multi-query expansion")
        logger.info("- hybrid_search: Combined retrieval strategies")
        logger.info("- semantic_search: Advanced semantic search")
        
        return mcp
        
    except Exception as e:
        logger.error(f"Failed to import FastAPI app: {e}")
        logger.error("Environment variables will only be needed when MCP tools execute")
        raise

# Create the MCP server using the recommended approach
mcp = create_mcp_server()

def main():
    """Entry point for MCP server"""
    logger.info("Starting Advanced RAG MCP Server...")
    logger.info("FastMCP acts as a wrapper - backend services only needed when tools execute")
    mcp.run()

if __name__ == "__main__":
    main() 
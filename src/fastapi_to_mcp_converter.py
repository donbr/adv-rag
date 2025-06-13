#!/usr/bin/env python3
"""
FastAPI to MCP Converter using FastMCP v2.8.0 built-in features.

This demonstrates the simple conversion process documented at:
https://github.com/jlowin/fastmcp?tab=readme-ov-file#openapi--fastapi-generation
"""

from fastapi import FastAPI
from fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing components
from src.llm_models import get_chat_model
from src.embeddings import get_openai_embeddings
from src.vectorstore_setup import get_main_vectorstore
from src.retriever_factory import create_retriever
from src.chain_factory import create_rag_chain

class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str
    top_k: int = 5
    retrieval_type: str = "hybrid"

class DocumentQueryRequest(BaseModel):
    """Request model for document queries."""
    question: str
    document_filter: Optional[dict] = None

# Method 1: Convert existing FastAPI app to MCP
def create_fastapi_app() -> FastAPI:
    """Create a FastAPI app with your existing endpoints."""
    app = FastAPI(title="Advanced RAG API", version="1.0.0")
    
    @app.post("/semantic_search")
    async def semantic_search(request: SemanticSearchRequest):
        """Perform semantic search across the document collection."""
        try:
            # Initialize components (in production, these would be dependencies)
            vectorstore = get_main_vectorstore()
            retriever = create_retriever(request.retrieval_type, vectorstore)
            
            # Retrieve documents
            docs = retriever.get_relevant_documents(request.query)[:request.top_k]
            
            # Format response
            results = []
            for i, doc in enumerate(docs):
                results.append({
                    "rank": i + 1,
                    "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": getattr(doc, 'score', None)
                })
            
            return {"results": results, "count": len(results)}
            
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    @app.post("/document_query")
    async def document_query(request: DocumentQueryRequest):
        """Query the document collection with a natural language question."""
        try:
            # Initialize RAG chain
            vectorstore = get_main_vectorstore()
            retriever = create_retriever("hybrid", vectorstore)
            rag_chain = create_rag_chain(retriever)
            
            # Process query
            response = await rag_chain.ainvoke({"question": request.question})
            
            return {"answer": response, "question": request.question}
            
        except Exception as e:
            return {"error": f"Query failed: {str(e)}"}
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "Advanced RAG API"}
    
    return app

# Method 2: Automatic FastAPI to MCP conversion
def convert_fastapi_to_mcp():
    """Convert FastAPI app to MCP server automatically."""
    print("🔄 Converting FastAPI to MCP using FastMCP.from_fastapi()")
    
    # Create your existing FastAPI app
    fastapi_app = create_fastapi_app()
    
    # Convert to MCP automatically
    mcp_server = FastMCP.from_fastapi(
        fastapi_app,
        name="Advanced RAG MCP Server",
        description="Automatically converted from FastAPI"
    )
    
    return mcp_server

# Method 3: Manual conversion with FastMCP decorators
def create_native_mcp_server():
    """Create MCP server using native FastMCP decorators."""
    print("🛠️ Creating native MCP server with FastMCP decorators")
    
    mcp = FastMCP("Advanced RAG Server - Native")
    
    @mcp.tool
    async def semantic_search(query: str, top_k: int = 5, retrieval_type: str = "hybrid") -> str:
        """Perform semantic search across the document collection."""
        try:
            vectorstore = get_main_vectorstore()
            retriever = create_retriever(retrieval_type, vectorstore)
            docs = retriever.get_relevant_documents(query)[:top_k]
            
            results = []
            for i, doc in enumerate(docs):
                results.append({
                    "rank": i + 1,
                    "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": getattr(doc, 'score', None)
                })
            
            import json
            from src.mcp_server.main import safe_json_dumps
            return safe_json_dumps({"results": results, "count": len(results)})
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    @mcp.tool
    async def document_query(question: str) -> str:
        """Query the document collection with a natural language question."""
        try:
            vectorstore = get_main_vectorstore()
            retriever = create_retriever("hybrid", vectorstore)
            rag_chain = create_rag_chain(retriever)
            
            response = await rag_chain.ainvoke({"question": question})
            
            import json
            return json.dumps({"answer": response, "question": question})
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    return mcp

def main():
    """Main function to demonstrate different conversion methods."""
    import sys
    
    method = sys.argv[1] if len(sys.argv) > 1 else "auto"
    
    if method == "fastapi":
        print("🌐 Running original FastAPI server")
        import uvicorn
        app = create_fastapi_app()
        uvicorn.run(app, host="127.0.0.1", port=8000)
        
    elif method == "auto":
        print("🔄 Running auto-converted FastAPI to MCP")
        try:
            mcp_server = convert_fastapi_to_mcp()
            mcp_server.run(transport="stdio")
        except Exception as e:
            print(f"Auto-conversion failed: {e}")
            print("This feature may not be available in your FastMCP version")
            print("Falling back to native MCP server...")
            mcp_server = create_native_mcp_server()
            mcp_server.run(transport="stdio")
        
    elif method == "native":
        print("🛠️ Running native MCP server")
        mcp_server = create_native_mcp_server()
        mcp_server.run(transport="stdio")
        
    else:
        print("Usage: python fastapi_to_mcp_converter.py [fastapi|auto|native]")
        print("  fastapi - Run original FastAPI server")
        print("  auto    - Auto-convert FastAPI to MCP (default)")
        print("  native  - Native MCP server with decorators")

if __name__ == "__main__":
    main() 
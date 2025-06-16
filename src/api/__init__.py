"""
FastAPI implementation components for the Advanced RAG project.

This package contains all FastAPI-related functionality:
- API routes and endpoints (app.py) - 6 retrieval strategies exposed as HTTP endpoints
- Request/response models with Pydantic validation
- Health monitoring and cache statistics endpoints
- Middleware configuration and error handling

Educational Note: This separation allows learners to understand FastAPI
concepts independently before seeing how they integrate with RAG and MCP.
The API layer serves as the HTTP interface to the underlying RAG system,
providing RESTful access to all retrieval strategies (naive, BM25, 
contextual compression, multi-query, ensemble, and semantic).
"""

__version__ = "1.0.0" 
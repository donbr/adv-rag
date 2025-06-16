"""
Advanced RAG with FastAPI → MCP Integration - Source Package

This is the main source package for the Advanced RAG project, implementing
a sophisticated domain-organized architecture that demonstrates:

Domain Organization:
- core/         - Shared infrastructure (settings, logging, exceptions)
- api/          - FastAPI web layer with 6 retrieval strategies  
- rag/          - RAG pipeline components (embeddings, vectorstore, retrievers, chains)
- mcp/          - MCP server implementation (FastMCP.from_fastapi conversion)
- integrations/ - External service clients (LLM, Redis, telemetry)

Key Architectural Patterns:
- Zero-duplication MCP integration using FastMCP.from_fastapi()
- Domain-driven design with clear separation of concerns
- Centralized configuration management with environment variable support
- Comprehensive observability with Phoenix tracing
- Production-ready features (caching, error handling, validation)

Educational Value:
This project serves as a comprehensive example of how to build production-ready
RAG systems with proper architecture, testing, and MCP integration for AI assistants.
Each domain can be studied independently to understand specific concepts before
seeing how they integrate into a complete system.

For detailed architecture documentation, see docs/project-structure.md
"""

__version__ = "1.0.0" 
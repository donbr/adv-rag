"""
Model Context Protocol (MCP) server implementation for the Advanced RAG project.

This package contains all MCP-related functionality:
- Main MCP server implementation (server.py) - FastMCP.from_fastapi() conversion
- Enhanced MCP resources for data exposure (resources.py) - Advanced resource handlers
- Transport support for stdio (Claude Desktop) and HTTP (programmatic access)
- Phoenix tracing integration for observability

Educational Note: This separation allows learners to understand MCP
architecture independently - how servers expose resources and tools
to AI assistants through the Model Context Protocol. The server.py
demonstrates the zero-duplication pattern using FastMCP.from_fastapi()
to convert existing FastAPI endpoints into MCP tools without code replication.
MCP provides a standardized way for AI systems to access external
data and functionality, including our sophisticated RAG system.
"""

__version__ = "1.0.0" 
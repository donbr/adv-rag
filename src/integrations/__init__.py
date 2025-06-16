"""
External service integrations for the Advanced RAG project.

This package contains integrations with external services and systems:
- Redis client for caching and session management (redis_client.py)
- LLM model clients and abstractions (llm_models.py)
- Database connections (if needed)
- Third-party API clients (if needed)

Educational Note: This separation allows learners to understand how
modern applications integrate with external services. Each integration
is isolated and can be studied independently, showing patterns like
connection pooling, error handling, and service abstraction.
The integrations support both the RAG system and MCP server functionality.
"""

__version__ = "1.0.0" 
"""
Global exception classes for the Advanced RAG project.

This module defines custom exception classes that can be used across
all components (RAG, MCP, API, integrations). Having centralized
exceptions improves error handling consistency and makes debugging easier.

Educational Note: This demonstrates how to create a hierarchy of custom
exceptions in Python, showing proper inheritance patterns and how to
organize application-specific errors in a maintainable way.
"""


class RAGException(Exception):
    """Base exception class for all RAG application errors."""
    
    def __init__(self, message: str, component: str = None, details: dict = None):
        self.message = message
        self.component = component
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.component:
            return f"[{self.component}] {self.message}"
        return self.message


class ConfigurationError(RAGException):
    """Raised when there's a configuration error (missing env vars, invalid settings)."""
    pass


class RAGError(RAGException):
    """Base exception for RAG-related errors."""
    pass


class EmbeddingError(RAGError):
    """Raised when embedding operations fail."""
    pass


class VectorStoreError(RAGError):
    """Raised when vector store operations fail."""
    pass


class RetrievalError(RAGError):
    """Raised when document retrieval fails."""
    pass


class ChainExecutionError(RAGError):
    """Raised when RAG chain execution fails."""
    pass


class MCPError(RAGException):
    """Base exception for MCP-related errors."""
    pass


class MCPServerError(MCPError):
    """Raised when MCP server operations fail."""
    pass


class MCPTransportError(MCPError):
    """Raised when MCP transport layer fails."""
    pass


class MCPResourceError(MCPError):
    """Raised when MCP resource operations fail."""
    pass


class IntegrationError(RAGException):
    """Base exception for external service integration errors."""
    pass


class RedisError(IntegrationError):
    """Raised when Redis operations fail."""
    pass


class LLMError(IntegrationError):
    """Raised when LLM API calls fail."""
    pass


# Convenience functions for common error scenarios
def raise_config_error(message: str, missing_var: str = None):
    """Raise a configuration error with optional missing variable info."""
    details = {"missing_variable": missing_var} if missing_var else {}
    raise ConfigurationError(message, component="Configuration", details=details)


def raise_rag_error(message: str, operation: str = None, chain_name: str = None):
    """Raise a RAG error with optional operation and chain details."""
    details = {}
    if operation:
        details["operation"] = operation
    if chain_name:
        details["chain_name"] = chain_name
    raise RAGError(message, component="RAG", details=details)


def raise_mcp_error(message: str, server_type: str = None):
    """Raise an MCP error with optional server type info."""
    details = {"server_type": server_type} if server_type else {}
    raise MCPError(message, component="MCP", details=details) 
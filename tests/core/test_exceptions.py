"""
Test exceptions module for core shared components.

Tests the custom exception classes including:
- Exception hierarchy and inheritance
- Custom exception behavior and attributes
- Convenience functions for raising errors
- Component and details tracking
"""
import pytest
from src.core.exceptions import (
    RAGException,
    ConfigurationError,
    RAGError,
    EmbeddingError,
    VectorStoreError,
    RetrievalError,
    ChainExecutionError,
    MCPError,
    MCPServerError,
    MCPTransportError,
    MCPResourceError,
    IntegrationError,
    RedisError,
    LLMError,
    raise_config_error,
    raise_rag_error,
    raise_mcp_error
)


@pytest.mark.unit
class TestRAGException:
    """Test the base RAGException class."""
    
    def test_basic_exception_creation(self):
        """Test creating a basic exception with just a message."""
        exc = RAGException("Test error message")
        assert str(exc) == "Test error message"
        assert exc.message == "Test error message"
        assert exc.component is None
        assert exc.details == {}
    
    def test_exception_with_component(self):
        """Test creating an exception with component information."""
        exc = RAGException("Test error", component="TestComponent")
        assert str(exc) == "[TestComponent] Test error"
        assert exc.component == "TestComponent"
    
    def test_exception_with_details(self):
        """Test creating an exception with details dictionary."""
        details = {"error_code": "TEST001", "retry_count": 3}
        exc = RAGException("Test error", details=details)
        assert exc.details == details
    
    def test_exception_with_all_parameters(self):
        """Test creating an exception with all parameters."""
        details = {"operation": "test_op"}
        exc = RAGException("Test error", component="Test", details=details)
        assert str(exc) == "[Test] Test error"
        assert exc.component == "Test"
        assert exc.details == details
    
    def test_exception_inheritance(self):
        """Test that RAGException inherits from Exception."""
        exc = RAGException("Test error")
        assert isinstance(exc, Exception)


@pytest.mark.unit
class TestConfigurationError:
    """Test ConfigurationError exception class."""
    
    def test_configuration_error_inheritance(self):
        """Test that ConfigurationError inherits from RAGException."""
        exc = ConfigurationError("Config error")
        assert isinstance(exc, RAGException)
        assert isinstance(exc, Exception)
    
    def test_configuration_error_with_component(self):
        """Test ConfigurationError with component information."""
        exc = ConfigurationError("Missing API key", component="Settings")
        assert str(exc) == "[Settings] Missing API key"


@pytest.mark.unit
class TestRAGErrors:
    """Test RAG-related exception classes."""
    
    def test_rag_error_inheritance(self):
        """Test that RAGError inherits from RAGException."""
        exc = RAGError("RAG error")
        assert isinstance(exc, RAGException)
    
    def test_embedding_error_inheritance(self):
        """Test that EmbeddingError inherits from RAGError."""
        exc = EmbeddingError("Embedding failed")
        assert isinstance(exc, RAGError)
        assert isinstance(exc, RAGException)
    
    def test_vectorstore_error_inheritance(self):
        """Test that VectorStoreError inherits from RAGError."""
        exc = VectorStoreError("Vector store failed")
        assert isinstance(exc, RAGError)
        assert isinstance(exc, RAGException)
    
    def test_retrieval_error_inheritance(self):
        """Test that RetrievalError inherits from RAGError."""
        exc = RetrievalError("Retrieval failed")
        assert isinstance(exc, RAGError)
        assert isinstance(exc, RAGException)
    
    def test_chain_execution_error_inheritance(self):
        """Test that ChainExecutionError inherits from RAGError."""
        exc = ChainExecutionError("Chain execution failed")
        assert isinstance(exc, RAGError)
        assert isinstance(exc, RAGException)


@pytest.mark.unit
class TestMCPErrors:
    """Test MCP-related exception classes."""
    
    def test_mcp_error_inheritance(self):
        """Test that MCPError inherits from RAGException."""
        exc = MCPError("MCP error")
        assert isinstance(exc, RAGException)
    
    def test_mcp_server_error_inheritance(self):
        """Test that MCPServerError inherits from MCPError."""
        exc = MCPServerError("Server error")
        assert isinstance(exc, MCPError)
        assert isinstance(exc, RAGException)
    
    def test_mcp_transport_error_inheritance(self):
        """Test that MCPTransportError inherits from MCPError."""
        exc = MCPTransportError("Transport error")
        assert isinstance(exc, MCPError)
        assert isinstance(exc, RAGException)
    
    def test_mcp_resource_error_inheritance(self):
        """Test that MCPResourceError inherits from MCPError."""
        exc = MCPResourceError("Resource error")
        assert isinstance(exc, MCPError)
        assert isinstance(exc, RAGException)


@pytest.mark.unit
class TestIntegrationErrors:
    """Test integration-related exception classes."""
    
    def test_integration_error_inheritance(self):
        """Test that IntegrationError inherits from RAGException."""
        exc = IntegrationError("Integration error")
        assert isinstance(exc, RAGException)
    
    def test_redis_error_inheritance(self):
        """Test that RedisError inherits from IntegrationError."""
        exc = RedisError("Redis connection failed")
        assert isinstance(exc, IntegrationError)
        assert isinstance(exc, RAGException)
    
    def test_llm_error_inheritance(self):
        """Test that LLMError inherits from IntegrationError."""
        exc = LLMError("LLM API failed")
        assert isinstance(exc, IntegrationError)
        assert isinstance(exc, RAGException)


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test convenience functions for raising errors."""
    
    def test_raise_config_error_basic(self):
        """Test raise_config_error with basic message."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise_config_error("Test config error")
        
        exc = exc_info.value
        assert str(exc) == "[Configuration] Test config error"
        assert exc.component == "Configuration"
    
    def test_raise_config_error_with_missing_var(self):
        """Test raise_config_error with missing variable info."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise_config_error("API key missing", missing_var="OPENAI_API_KEY")
        
        exc = exc_info.value
        assert exc.details["missing_variable"] == "OPENAI_API_KEY"
    
    def test_raise_rag_error_basic(self):
        """Test raise_rag_error with basic message."""
        with pytest.raises(RAGError) as exc_info:
            raise_rag_error("Test RAG error")
        
        exc = exc_info.value
        assert str(exc) == "[RAG] Test RAG error"
        assert exc.component == "RAG"
    
    def test_raise_rag_error_with_operation(self):
        """Test raise_rag_error with operation details."""
        with pytest.raises(RAGError) as exc_info:
            raise_rag_error("Embedding failed", operation="create_embeddings")
        
        exc = exc_info.value
        assert exc.details["operation"] == "create_embeddings"
    
    def test_raise_rag_error_with_chain_name(self):
        """Test raise_rag_error with chain name details."""
        with pytest.raises(RAGError) as exc_info:
            raise_rag_error("Chain failed", chain_name="semantic_retriever")
        
        exc = exc_info.value
        assert exc.details["chain_name"] == "semantic_retriever"
    
    def test_raise_rag_error_with_all_details(self):
        """Test raise_rag_error with all details."""
        with pytest.raises(RAGError) as exc_info:
            raise_rag_error(
                "Operation failed", 
                operation="retrieval", 
                chain_name="ensemble_retriever"
            )
        
        exc = exc_info.value
        assert exc.details["operation"] == "retrieval"
        assert exc.details["chain_name"] == "ensemble_retriever"
    
    def test_raise_mcp_error_basic(self):
        """Test raise_mcp_error with basic message."""
        with pytest.raises(MCPError) as exc_info:
            raise_mcp_error("Test MCP error")
        
        exc = exc_info.value
        assert str(exc) == "[MCP] Test MCP error"
        assert exc.component == "MCP"
    
    def test_raise_mcp_error_with_server_type(self):
        """Test raise_mcp_error with server type details."""
        with pytest.raises(MCPError) as exc_info:
            raise_mcp_error("Server failed", server_type="FastAPI")
        
        exc = exc_info.value
        assert exc.details["server_type"] == "FastAPI"


@pytest.mark.unit
class TestExceptionIntegration:
    """Integration tests for exception behavior."""
    
    def test_exception_can_be_caught_as_base_type(self):
        """Test that specific exceptions can be caught as base types."""
        try:
            raise EmbeddingError("Test embedding error")
        except RAGError:
            # Should be caught as RAGError
            pass
        except Exception:
            pytest.fail("Should have been caught as RAGError")
    
    def test_exception_can_be_caught_as_advanced_rag_exception(self):
        """Test that all custom exceptions can be caught as RAGException."""
        exceptions_to_test = [
            ConfigurationError("Config error"),
            EmbeddingError("Embedding error"),
            MCPServerError("MCP error"),
            RedisError("Redis error")
        ]
        
        for exc in exceptions_to_test:
            try:
                raise exc
            except RAGException:
                # Should be caught as RAGException
                pass
            except Exception:
                pytest.fail(f"{type(exc).__name__} should be caught as RAGException")
    
    def test_exception_details_preserved(self):
        """Test that exception details are preserved when caught."""
        details = {"operation": "test", "retry_count": 3}
        
        try:
            raise RAGError("Test error", component="Test", details=details)
        except RAGException as exc:
            assert exc.component == "Test"
            assert exc.details == details
            assert exc.message == "Test error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
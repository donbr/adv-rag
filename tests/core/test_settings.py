"""
Test settings module for core shared components.

Tests the configuration management functionality including:
- Settings instance creation and singleton behavior
- Required configuration fields
- Environment variable handling
- Default values and validation
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from src.core.settings import Settings, get_settings, get_env_variable, setup_env_vars


@pytest.mark.unit
class TestSettings:
    """Test settings functionality and configuration management."""
    
    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)
    
    def test_settings_has_required_fields(self):
        """Test that settings has all required configuration fields."""
        settings = get_settings()
        
        # Core API configuration
        assert hasattr(settings, 'openai_api_key')
        assert hasattr(settings, 'openai_model_name')
        assert hasattr(settings, 'cohere_api_key')
        
        # LLM configuration
        assert hasattr(settings, 'openai_temperature')
        assert hasattr(settings, 'openai_max_retries')
        assert hasattr(settings, 'openai_request_timeout')
        
        # Embedding configuration
        assert hasattr(settings, 'embedding_model_name')
        
        # Cohere configuration
        assert hasattr(settings, 'cohere_rerank_model')
        
        # External service endpoints
        assert hasattr(settings, 'phoenix_endpoint')
        assert hasattr(settings, 'qdrant_url')
        
        # Redis configuration
        assert hasattr(settings, 'redis_url')
        assert hasattr(settings, 'redis_cache_ttl')
        assert hasattr(settings, 'redis_max_connections')
        assert hasattr(settings, 'redis_socket_keepalive')
        assert hasattr(settings, 'redis_health_check_interval')
        
        # MCP configuration
        assert hasattr(settings, 'mcp_request_timeout')
        assert hasattr(settings, 'max_snippets')
    
    def test_settings_default_values(self):
        """Test that settings has correct default values."""
        settings = get_settings()
        
        assert settings.openai_model_name == "gpt-4.1-mini"
        assert settings.openai_temperature == 0.0
        assert settings.openai_max_retries == 3
        assert settings.openai_request_timeout == 60
        assert settings.embedding_model_name == "text-embedding-3-small"
        assert settings.cohere_rerank_model == "rerank-english-v3.0"
        assert settings.phoenix_endpoint == "http://localhost:6006"
        assert settings.qdrant_url == "http://localhost:6333"
        assert settings.redis_url == "redis://localhost:6379"
        assert settings.redis_cache_ttl == 300
        assert settings.redis_max_connections == 20
        assert settings.redis_socket_keepalive is True
        assert settings.redis_health_check_interval == 30
        assert settings.mcp_request_timeout == 30
        assert settings.max_snippets == 5
    
    def test_settings_singleton_behavior(self):
        """Test that get_settings returns the same instance (singleton pattern)."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
    
    def test_get_env_variable_success(self):
        """Test successful environment variable retrieval."""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            result = get_env_variable('TEST_VAR')
            assert result == 'test_value'
    
    def test_get_env_variable_missing_with_default(self):
        """Test environment variable retrieval with default value."""
        # Ensure the variable doesn't exist
        with patch.dict(os.environ, {}, clear=True):
            result = get_env_variable('MISSING_VAR', default_value='default')
            assert result == 'default'
    
    def test_get_env_variable_missing_no_default(self):
        """Test environment variable retrieval when missing and no default."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env_variable('MISSING_VAR')
            assert result is None
    
    @patch('src.core.settings.logging')
    def test_get_env_variable_logging(self, mock_logging):
        """Test that get_env_variable logs appropriately."""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            get_env_variable('TEST_VAR')
            mock_logging.info.assert_called_with("Environment variable 'TEST_VAR' was accessed.")
    
    @patch('src.core.settings.logging')
    def test_get_env_variable_missing_logging(self, mock_logging):
        """Test that get_env_variable logs errors for missing variables."""
        with patch.dict(os.environ, {}, clear=True):
            get_env_variable('MISSING_VAR')
            mock_logging.error.assert_called_with(
                "Environment variable 'MISSING_VAR' not found. Please set it in your .env file or system environment."
            )
    
    @patch('src.core.settings.logging')
    @patch('src.core.settings.get_env_variable')
    def test_setup_env_vars_success(self, mock_get_env, mock_logging):
        """Test successful environment variables setup."""
        mock_get_env.side_effect = lambda var, **kwargs: {
            'OPENAI_API_KEY': 'test_openai_key',
            'COHERE_API_KEY': 'test_cohere_key'
        }.get(var)
        
        setup_env_vars()
        
        assert mock_get_env.call_count == 2
        mock_logging.info.assert_any_call("Setting up application environment variables...")
        mock_logging.info.assert_any_call("OPENAI_API_KEY is set.")
        mock_logging.info.assert_any_call("COHERE_API_KEY is set.")
    
    @patch('src.core.settings.logging')
    @patch('src.core.settings.get_env_variable')
    def test_setup_env_vars_missing_openai_key(self, mock_get_env, mock_logging):
        """Test setup when OPENAI_API_KEY is missing."""
        mock_get_env.side_effect = lambda var, **kwargs: {
            'OPENAI_API_KEY': None,
            'COHERE_API_KEY': 'test_cohere_key'
        }.get(var)
        
        setup_env_vars()
        
        mock_logging.error.assert_called_with(
            "CRITICAL: OPENAI_API_KEY is not set. Core functionality will be impacted."
        )
    
    @patch('src.core.settings.logging')
    @patch('src.core.settings.get_env_variable')
    def test_setup_env_vars_missing_cohere_key(self, mock_get_env, mock_logging):
        """Test setup when COHERE_API_KEY is missing."""
        mock_get_env.side_effect = lambda var, **kwargs: {
            'OPENAI_API_KEY': 'test_openai_key',
            'COHERE_API_KEY': None
        }.get(var)
        
        setup_env_vars()
        
        mock_logging.warning.assert_called_with(
            "COHERE_API_KEY is not set. Contextual Compression Retriever (CohereRerank) will not function."
        )
    
    def test_settings_with_env_override(self):
        """Test that environment variables override default settings."""
        with patch.dict(os.environ, {
            'OPENAI_MODEL_NAME': 'gpt-4.1-nano',
            'REDIS_CACHE_TTL': '600',
            'MAX_SNIPPETS': '10'
        }):
            # Create new settings instance to pick up env vars
            settings = Settings()
            assert settings.openai_model_name == 'gpt-4.1-nano'
            assert settings.redis_cache_ttl == 600
            assert settings.max_snippets == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
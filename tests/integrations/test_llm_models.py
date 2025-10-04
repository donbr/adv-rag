import pytest
from unittest.mock import patch, MagicMock
from langchain_openai import ChatOpenAI
from src.integrations.llm_models import get_chat_openai, get_chat_model

@pytest.fixture
def mock_settings():
    """Fixture to mock get_settings()"""
    with patch('src.integrations.llm_models.get_settings') as mock:
        settings = MagicMock()
        settings.openai_model_name = "test-gpt-model"
        settings.openai_temperature = 0.5
        settings.openai_api_key = "test_api_key"
        settings.openai_max_retries = 2
        settings.openai_request_timeout = 45
        settings.redis_url = "redis://mock-redis:6379"
        mock.return_value = settings
        yield mock

@pytest.mark.requires_llm
@patch('src.integrations.llm_models.RedisCache')
@patch('src.integrations.llm_models.set_llm_cache')
def test_get_chat_openai_initialization(mock_set_llm_cache, mock_redis_cache, mock_settings):
    """Test that ChatOpenAI is initialized with settings and Redis cache."""
    chat_model = get_chat_openai()

    # Check if RedisCache and set_llm_cache were called
    mock_redis_cache.assert_called_once_with(redis_url="redis://mock-redis:6379")
    mock_set_llm_cache.assert_called_once_with(mock_redis_cache.return_value)

    # Check model instance and parameters
    assert isinstance(chat_model, ChatOpenAI)
    assert chat_model.model_name == "test-gpt-model"
    assert chat_model.temperature == 0.5

@pytest.mark.requires_llm
@patch('src.integrations.llm_models.ChatOpenAI')
@patch('src.integrations.llm_models.set_llm_cache')
def test_get_chat_openai_parameters_passed(mock_set_cache, mock_chat_openai, mock_settings):
    """Test that correct parameters are passed to ChatOpenAI constructor."""
    get_chat_openai()
    
    mock_chat_openai.assert_called_once_with(
        model="test-gpt-model",
        temperature=0.5,
        openai_api_key="test_api_key",
        max_retries=2,
        request_timeout=45,
    )

@pytest.mark.requires_llm
def test_get_chat_model_alias(mock_settings):
    """Test the backward compatibility alias get_chat_model."""
    with patch('src.integrations.llm_models.get_chat_openai') as mock_get_chat:
        get_chat_model()
        mock_get_chat.assert_called_once()

@pytest.mark.requires_llm
@patch('src.integrations.llm_models.set_llm_cache', side_effect=Exception("Redis connection failed"))
def test_get_chat_openai_cache_failure(mock_set_cache, mock_settings, caplog):
    """Test that the function handles Redis cache initialization failure gracefully."""
    import logging
    caplog.set_level(logging.WARNING)
    
    chat_model = get_chat_openai()
    
    assert chat_model is not None
    assert "Failed to initialize Redis cache" in caplog.text
    assert "LLM caching disabled" in caplog.text 
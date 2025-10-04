import pytest
from unittest.mock import patch, MagicMock
from langchain_openai import OpenAIEmbeddings
from src.rag.embeddings import get_openai_embeddings

@pytest.fixture
def mock_settings():
    """Fixture to mock get_settings() for embeddings."""
    with patch('src.rag.embeddings.get_settings') as mock:
        settings = MagicMock()
        settings.embedding_model_name = "test-embedding-model"
        mock.return_value = settings
        yield mock

@pytest.mark.unit
@patch('src.rag.embeddings.OpenAIEmbeddings')
def test_get_openai_embeddings_success(mock_openai_embeddings, mock_settings):
    """Test successful initialization of OpenAIEmbeddings."""
    mock_instance = MagicMock(spec=OpenAIEmbeddings)
    mock_openai_embeddings.return_value = mock_instance
    
    embeddings = get_openai_embeddings()
    
    mock_openai_embeddings.assert_called_once_with(model="test-embedding-model")
    assert embeddings == mock_instance

@pytest.mark.unit
@patch('src.rag.embeddings.OpenAIEmbeddings', side_effect=Exception("API Key Error"))
def test_get_openai_embeddings_failure(mock_openai_embeddings, mock_settings, caplog):
    """Test failure during OpenAIEmbeddings initialization."""
    with pytest.raises(Exception, match="API Key Error"):
        get_openai_embeddings()
    
    assert "Failed to initialize OpenAIEmbeddings model" in caplog.text 
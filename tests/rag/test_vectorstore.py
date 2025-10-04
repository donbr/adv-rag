import pytest
from unittest.mock import patch, MagicMock
from src.rag.vectorstore import get_main_vectorstore, get_semantic_vectorstore

@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock dependencies for all vector store tests."""
    with patch('src.rag.vectorstore.load_documents') as mock_load_docs, \
         patch('src.rag.vectorstore.get_openai_embeddings') as mock_embeddings, \
         patch('src.rag.vectorstore.QdrantClient') as mock_qdrant_client, \
         patch('src.rag.vectorstore.QdrantVectorStore') as mock_qdrant_vs, \
         patch('src.rag.vectorstore.QDRANT_API_URL', "http://mock-qdrant:6333"):
        
        yield {
            "load_docs": mock_load_docs,
            "embeddings": mock_embeddings,
            "qdrant_client": mock_qdrant_client,
            "qdrant_vs": mock_qdrant_vs
        }

@pytest.mark.requires_vectordb
def test_get_main_vectorstore_success(mock_dependencies):
    """Test successful creation of the main vector store."""
    vs = get_main_vectorstore()
    
    mock_dependencies["qdrant_client"].assert_called_once_with(url="http://mock-qdrant:6333", prefer_grpc=True)
    mock_dependencies["qdrant_vs"].assert_called_once()
    assert vs is not None
    
    args, kwargs = mock_dependencies["qdrant_vs"].call_args
    assert kwargs["collection_name"] == "johnwick_baseline"

@pytest.mark.requires_vectordb
def test_get_semantic_vectorstore_success(mock_dependencies):
    """Test successful creation of the semantic vector store."""
    vs = get_semantic_vectorstore()
    
    mock_dependencies["qdrant_client"].assert_called_once_with(url="http://mock-qdrant:6333", prefer_grpc=True)
    mock_dependencies["qdrant_vs"].assert_called_once()
    assert vs is not None
    
    args, kwargs = mock_dependencies["qdrant_vs"].call_args
    assert kwargs["collection_name"] == "johnwick_semantic"

@pytest.mark.requires_vectordb
def test_vectorstore_creation_failure(mock_dependencies, caplog):
    """Test graceful failure of vector store creation."""
    mock_dependencies["qdrant_client"].side_effect = Exception("Qdrant connection failed")
    
    with pytest.raises(Exception, match="Qdrant connection failed"):
        get_main_vectorstore()
    
    assert "Failed to create main vector store" in caplog.text 
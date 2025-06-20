import pytest
from unittest.mock import patch, MagicMock
from langchain_core.retrievers import BaseRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_cohere import CohereRerank
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever

# We need to import the module to be tested *after* the mocks are in place.
# The fixtures will handle the mocking, and the tests will handle the import.

@pytest.fixture
def mock_retriever_dependencies():
    """Mocks all dependencies for the retriever module."""
    with patch('src.rag.retriever.load_documents', return_value=[MagicMock()]) as mock_load_docs, \
         patch('src.rag.retriever.get_chat_model', return_value=MagicMock()) as mock_chat_model, \
         patch('src.rag.retriever.get_main_vectorstore') as mock_main_vs, \
         patch('src.rag.retriever.get_semantic_vectorstore') as mock_semantic_vs:
        
        mock_main_vs.return_value.as_retriever.return_value = MagicMock(spec=BaseRetriever)
        mock_semantic_vs.return_value.as_retriever.return_value = MagicMock(spec=BaseRetriever)
        
        yield

def test_get_retrievers(mock_retriever_dependencies):
    """Test that each retriever factory function returns the correct type of object."""
    from src.rag.retriever import (
        get_naive_retriever, get_bm25_retriever, get_ensemble_retriever,
        get_semantic_retriever, get_contextual_compression_retriever
    )
    
    assert isinstance(get_naive_retriever(), BaseRetriever)
    assert isinstance(get_bm25_retriever(), BM25Retriever)
    assert isinstance(get_ensemble_retriever(), EnsembleRetriever)
    assert isinstance(get_semantic_retriever(), BaseRetriever)
    with patch('os.getenv', return_value="fake_key"):
        assert isinstance(get_contextual_compression_retriever(), ContextualCompressionRetriever)

def test_create_retriever_factory(mock_retriever_dependencies):
    """Test the main create_retriever factory function."""
    from src.rag.retriever import create_retriever
    
    assert isinstance(create_retriever("naive"), BaseRetriever)
    assert isinstance(create_retriever("bm25"), BM25Retriever)
    assert isinstance(create_retriever("ensemble"), EnsembleRetriever)
    assert isinstance(create_retriever("semantic"), BaseRetriever)
    
    # Test fallback
    assert isinstance(create_retriever("unknown"), BaseRetriever)
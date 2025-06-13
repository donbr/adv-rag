"""Unit tests for essential retriever factory functionality."""

import pytest
from unittest.mock import Mock
from src.retriever_factory import create_retriever


class TestRetrieverFactory:
    """Test suite for essential retriever factory patterns."""
    
    def test_similarity_retriever_creation(self):
        """Test creation of similarity retriever."""
        retriever = create_retriever("similarity")
        
        assert retriever is not None
        assert hasattr(retriever, 'get_relevant_documents')
        
        # Test basic retrieval functionality
        docs = retriever.get_relevant_documents("test query")
        assert len(docs) > 0
        assert hasattr(docs[0], 'page_content')
        assert hasattr(docs[0], 'metadata')
    
    def test_hybrid_retriever_creation(self):
        """Test creation of hybrid retriever."""
        retriever = create_retriever("hybrid")
        
        assert retriever is not None
        assert hasattr(retriever, 'get_relevant_documents')
    
    def test_mmr_retriever_creation(self):
        """Test creation of MMR retriever."""
        retriever = create_retriever("mmr")
        
        assert retriever is not None
        assert hasattr(retriever, 'get_relevant_documents')
    
    def test_invalid_retriever_type(self):
        """Test handling of invalid retriever types."""
        with pytest.raises(ValueError, match="Unknown retrieval type"):
            create_retriever("invalid_type")
    
    def test_retriever_with_search_kwargs(self):
        """Test retriever creation with custom search parameters."""
        search_kwargs = {"k": 5, "fetch_k": 20}
        
        retriever = create_retriever("similarity", search_kwargs=search_kwargs)
        
        assert retriever is not None
        # Basic functionality should still work
        docs = retriever.get_relevant_documents("test query")
        assert len(docs) > 0
        
    def test_all_supported_retriever_types(self):
        """Test that all documented retriever types can be created."""
        supported_types = ["similarity", "hybrid", "mmr", "contextual", "naive", "bm25", "semantic"]
        
        for retriever_type in supported_types:
            retriever = create_retriever(retriever_type)
            assert retriever is not None, f"Failed to create {retriever_type} retriever"
            assert hasattr(retriever, 'get_relevant_documents'), f"{retriever_type} retriever missing get_relevant_documents method" 
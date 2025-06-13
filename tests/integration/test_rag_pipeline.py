"""Essential integration tests for RAG pipeline."""

import pytest
from unittest.mock import Mock
from src.retriever_factory import create_retriever, create_rag_chain


class TestRAGPipeline:
    """Essential tests for RAG pipeline integration."""
    
    def test_basic_rag_pipeline(self):
        """Test basic RAG pipeline creation and execution."""
        # Setup retriever
        retriever = create_retriever("similarity")
        
        # Setup chain
        chain = create_rag_chain(retriever)
        
        # Test basic functionality
        assert chain is not None
        assert hasattr(chain, 'invoke')
        
        # Test query processing
        response = chain.invoke({"question": "What is the test content?"})
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_retrieval_functionality(self):
        """Test basic retrieval functionality."""
        retriever = create_retriever("similarity")
        
        # Test retrieval
        docs = retriever.get_relevant_documents("test query")
        
        assert len(docs) > 0
        assert all(hasattr(doc, 'page_content') for doc in docs)
        assert all(hasattr(doc, 'metadata') for doc in docs)
        
        # Verify document content
        assert docs[0].page_content == "Test document content"
        assert docs[0].metadata == {"source": "test.txt"}
    
    def test_different_retriever_types(self):
        """Test RAG pipeline with different retriever types."""
        retriever_types = ["similarity", "hybrid", "mmr"]
        
        for retriever_type in retriever_types:
            retriever = create_retriever(retriever_type)
            chain = create_rag_chain(retriever)
            
            assert chain is not None, f"Failed to create chain with {retriever_type} retriever"
            
            response = chain.invoke({"question": f"Test question for {retriever_type}"})
            assert response is not None
            assert isinstance(response, str)
    
    def test_chain_with_none_retriever(self):
        """Test chain creation with None retriever."""
        chain = create_rag_chain(None)
        
        assert chain is None
    
    @pytest.mark.asyncio
    async def test_async_retrieval(self):
        """Test async retrieval functionality."""
        retriever = create_retriever("hybrid")
        
        # Test async retrieval
        docs = await retriever.aget_relevant_documents("async test query")
        
        assert len(docs) > 0
        assert all(hasattr(doc, 'page_content') for doc in docs)
    
    @pytest.mark.asyncio 
    async def test_async_chain_execution(self):
        """Test async chain execution."""
        retriever = create_retriever("similarity")
        chain = create_rag_chain(retriever)
        
        # Test async execution
        response = await chain.ainvoke({"question": "async test question"})
        
        assert response is not None
        assert isinstance(response, str)
    
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test batch query processing."""
        retriever = create_retriever("hybrid")
        chain = create_rag_chain(retriever)
        
        queries = [
            {"question": "Query 1"},
            {"question": "Query 2"},
            {"question": "Query 3"}
        ]
        
        results = await chain.abatch(queries)
        
        assert len(results) == len(queries)
        assert all(isinstance(result, str) for result in results)
        assert results == ["Test answer 1", "Test answer 2", "Test answer 3"] 
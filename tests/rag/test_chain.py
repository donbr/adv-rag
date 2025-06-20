import pytest
from unittest.mock import patch, MagicMock
from langchain_core.runnables import Runnable

# Mock dependencies before importing the module under test
@pytest.fixture(autouse=True)
def mock_chain_dependencies():
    """Mock dependencies for the chain module."""
    with patch('src.rag.chain.get_chat_model') as mock_chat_model, \
         patch('src.rag.chain.get_naive_retriever') as mock_naive_ret, \
         patch('src.rag.chain.get_bm25_retriever') as mock_bm25_ret, \
         patch('src.rag.chain.get_contextual_compression_retriever') as mock_cc_ret, \
         patch('src.rag.chain.get_multi_query_retriever') as mock_mq_ret, \
         patch('src.rag.chain.get_ensemble_retriever') as mock_ensemble_ret, \
         patch('src.rag.chain.get_semantic_retriever') as mock_semantic_ret:
        
        mocks = {
            "chat_model": mock_chat_model,
            "naive": mock_naive_ret,
            "bm25": mock_bm25_ret,
            "contextual": mock_cc_ret,
            "multiquery": mock_mq_ret,
            "ensemble": mock_ensemble_ret,
            "semantic": mock_semantic_ret
        }
        for name, mock_ret in mocks.items():
            if name != "chat_model":
                mock_ret.return_value = MagicMock(spec=Runnable) if "ret" in name else MagicMock()

        yield mocks


# Now import the module
from src.rag.chain import create_rag_chain, NAIVE_RETRIEVAL_CHAIN, BM25_RETRIEVAL_CHAIN

def test_create_rag_chain_success():
    """Test successful creation of a RAG chain."""
    mock_retriever = MagicMock(spec=Runnable)
    chain = create_rag_chain(mock_retriever)
    assert chain is not None
    assert isinstance(chain, Runnable)

def test_create_rag_chain_with_none_retriever(caplog):
    """Test that chain creation returns None if the retriever is None."""
    chain = create_rag_chain(None)
    assert chain is None

def test_chains_are_initialized(mock_chain_dependencies):
    """Test that global chain instances are created."""
    # The module-level code in chain.py should create these.
    # We just need to assert they are not None.
    assert NAIVE_RETRIEVAL_CHAIN is not None
    assert BM25_RETRIEVAL_CHAIN is not None
    # Add asserts for other chains as needed

def test_chain_initialization_failure(caplog):
    """Test that chain creation logs an error if it fails."""
    with patch('src.rag.chain.RunnablePassthrough.assign', side_effect=Exception("LCEL error")):
        chain = create_rag_chain(MagicMock(spec=Runnable))
        assert chain is None
        assert "Failed to create RAG chain" in caplog.text 
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from src.api.app import app, get_redis

@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock external dependencies for all tests in this module."""
    with patch('src.api.app.NAIVE_RETRIEVAL_CHAIN') as mock_naive_chain, \
         patch('src.api.app.BM25_RETRIEVAL_CHAIN') as mock_bm25_chain, \
         patch('src.api.app.CONTEXTUAL_COMPRESSION_CHAIN') as mock_cc_chain, \
         patch('src.api.app.MULTI_QUERY_CHAIN') as mock_mq_chain, \
         patch('src.api.app.ENSEMBLE_CHAIN') as mock_ensemble_chain, \
         patch('src.api.app.SEMANTIC_CHAIN') as mock_semantic_chain, \
         patch('src.api.app.redis_client') as mock_redis_client:
        
        # Mock Redis client connection for lifespan manager
        mock_redis_client.connect = AsyncMock(return_value=None)
        mock_redis_client.disconnect = AsyncMock(return_value=None)
        
        # Mock all chains
        mock_chains = {
            "naive": mock_naive_chain,
            "bm25": mock_bm25_chain,
            "contextual": mock_cc_chain,
            "multiquery": mock_mq_chain,
            "ensemble": mock_ensemble_chain,
            "semantic": mock_semantic_chain
        }
        
        for name, mock_chain in mock_chains.items():
            if mock_chain:
                mock_chain.ainvoke = AsyncMock(return_value={
                    "response": MagicMock(content=f"Answer from {name} chain"),
                    "context": [MagicMock()] * 2
                })
        
        yield { "chains": mock_chains }

def test_health_check():
    """Test the /health endpoint."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

def test_invoke_naive_retriever_endpoint(mock_dependencies):
    """Test the /invoke/naive_retriever endpoint."""
    with patch('src.api.app.get_cached_response', AsyncMock(return_value=None)), \
         patch('src.api.app.cache_response', AsyncMock()):
        with TestClient(app) as client:
            response = client.post("/invoke/naive_retriever", json={"question": "What is John Wick?"})
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["answer"] == "Answer from naive chain"
        assert json_response["context_document_count"] == 2
        mock_dependencies["chains"]["naive"].ainvoke.assert_awaited_once_with({"question": "What is John Wick?"})

@patch('src.api.app.get_cached_response', new_callable=AsyncMock)
def test_invoke_endpoint_with_cache_hit(mock_get_cached, mock_dependencies):
    """Test an invoke endpoint with a cache hit."""
    cached_data = {"answer": "Cached answer", "context_document_count": 5}
    mock_get_cached.return_value = cached_data
    
    with TestClient(app) as client:
        response = client.post("/invoke/bm25_retriever", json={"question": "A cached question"})
    
    assert response.status_code == 200
    assert response.json() == cached_data
    mock_dependencies["chains"]["bm25"].ainvoke.assert_not_awaited()

@patch('src.api.app.cache_response', new_callable=AsyncMock)
@patch('src.api.app.get_cached_response', new_callable=AsyncMock, return_value=None)
def test_invoke_endpoint_with_cache_miss(mock_get_cached, mock_cache_resp, mock_dependencies):
    """Test an invoke endpoint with a cache miss and subsequent caching."""
    with TestClient(app) as client:
        response = client.post("/invoke/semantic_retriever", json={"question": "An uncached question"})
    
    assert response.status_code == 200
    mock_dependencies["chains"]["semantic"].ainvoke.assert_awaited_once()
    mock_cache_resp.assert_awaited_once()

def test_invoke_unavailable_chain():
    """Test invoking a chain that is None (unavailable)."""
    with patch('src.api.app.ENSEMBLE_CHAIN', None):
        with TestClient(app) as client:
            response = client.post("/invoke/ensemble_retriever", json={"question": "This should fail"})
            assert response.status_code == 503
            assert "unavailable" in response.json()["detail"]

def test_cache_stats_endpoint():
    """Test the /cache/stats endpoint with a mocked redis via dependency_overrides."""
    mock_redis = AsyncMock()
    mock_redis.info.return_value = {
        "redis_version": "6.2.5",
        "connected_clients": 1,
        "used_memory_human": "1.23M"
    }
    mock_redis.dbsize.return_value = 10
    
    app.dependency_overrides[get_redis] = lambda: mock_redis
    
    with TestClient(app) as client:
        response = client.get("/cache/stats")
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["total_keys"] == 10
    assert json_response["redis_version"] == "6.2.5" 
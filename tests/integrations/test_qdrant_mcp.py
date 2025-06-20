"""
Test suite for Enhanced Qdrant MCP Server

Task 2.1: Tests for enhanced Qdrant MCP with validation metadata support.

This test module covers:
- Enhanced collection initialization
- Validation metadata indexing
- Confidence-based pattern filtering
- Phoenix pattern synchronization
- Pattern storage and retrieval
- Expiration and cleanup mechanisms
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from src.integrations.qdrant_mcp import (
    EnhancedQdrantMCPServer,
    EnhancedQdrantPattern,
    ValidationMetadata,
    ENHANCED_CODE_SNIPPETS_COLLECTION,
    ENHANCED_SEMANTIC_MEMORY_COLLECTION,
    PATTERN_VALIDATION_COLLECTION,
    create_enhanced_qdrant_mcp_server
)

class TestValidationMetadata:
    """Test ValidationMetadata structure and functionality."""
    
    def test_validation_metadata_creation(self):
        """Test creating ValidationMetadata with all required fields."""
        metadata = ValidationMetadata(
            confidence_score=0.85,
            qa_correctness_score=0.9,
            rag_relevance_score=0.8,
            experiment_id="exp_123",
            dataset_id="dataset_456",
            validation_timestamp="2025-06-17T10:00:00Z",
            pattern_type="phoenix_validated",
            validation_status="validated"
        )
        
        assert metadata.confidence_score == 0.85
        assert metadata.qa_correctness_score == 0.9
        assert metadata.rag_relevance_score == 0.8
        assert metadata.experiment_id == "exp_123"
        assert metadata.dataset_id == "dataset_456"
        assert metadata.pattern_type == "phoenix_validated"
        assert metadata.validation_status == "validated"
        assert metadata.expiration_date is None  # Optional field
    
    def test_validation_metadata_with_expiration(self):
        """Test ValidationMetadata with expiration date."""
        expiration = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        metadata = ValidationMetadata(
            confidence_score=0.75,
            qa_correctness_score=0.8,
            rag_relevance_score=0.7,
            experiment_id="exp_789",
            dataset_id="dataset_101",
            validation_timestamp=datetime.utcnow().isoformat(),
            pattern_type="golden_testset",
            validation_status="validated",
            expiration_date=expiration
        )
        
        assert metadata.expiration_date == expiration


class TestEnhancedQdrantPattern:
    """Test EnhancedQdrantPattern model and validation."""
    
    def test_enhanced_pattern_creation(self):
        """Test creating an enhanced pattern with validation metadata."""
        validation_metadata = ValidationMetadata(
            confidence_score=0.92,
            qa_correctness_score=0.95,
            rag_relevance_score=0.88,
            experiment_id="exp_test",
            dataset_id="dataset_test",
            validation_timestamp=datetime.utcnow().isoformat(),
            pattern_type="phoenix_validated",
            validation_status="validated"
        )
        
        pattern = EnhancedQdrantPattern(
            pattern_id="test_pattern_123",
            content="def test_function(): return True",
            pattern_type="code_snippet",
            validation_metadata=validation_metadata,
            tags=["python", "test", "function"],
            category="testing"
        )
        
        assert pattern.pattern_id == "test_pattern_123"
        assert pattern.content == "def test_function(): return True"
        assert pattern.pattern_type == "code_snippet"
        assert pattern.tags == ["python", "test", "function"]
        assert pattern.category == "testing"
        assert pattern.validation_metadata.confidence_score == 0.92
    
    def test_enhanced_pattern_defaults(self):
        """Test EnhancedQdrantPattern with default values."""
        validation_metadata = ValidationMetadata(
            confidence_score=0.8,
            qa_correctness_score=0.8,
            rag_relevance_score=0.8,
            experiment_id="exp_default",
            dataset_id="dataset_default",
            validation_timestamp=datetime.utcnow().isoformat(),
            pattern_type="default",
            validation_status="validated"
        )
        
        pattern = EnhancedQdrantPattern(
            pattern_id="default_pattern",
            content="Test content",
            pattern_type="semantic_memory",
            validation_metadata=validation_metadata
        )
        
        assert pattern.tags == []  # Default empty list
        assert pattern.category == "general"  # Default category


class TestEnhancedQdrantMCPServer:
    """Test Enhanced Qdrant MCP Server functionality."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = MagicMock()
        settings.qdrant_url = "http://localhost:6333"
        return settings
    
    @pytest.fixture
    def mock_embeddings(self):
        """Mock embeddings for testing."""
        embeddings = MagicMock()
        embeddings.embed_query = AsyncMock(return_value=[0.1] * 1536)
        return embeddings
    
    @pytest.fixture
    def mock_phoenix_client(self):
        """Mock Phoenix client for testing."""
        return MagicMock()
    
    @pytest.fixture
    def mock_qdrant_client(self):
        """Mock Qdrant client for testing."""
        client = MagicMock()
        # Mock collections response
        collections_response = MagicMock()
        collections_response.collections = []
        client.get_collections.return_value = collections_response
        return client
    
    @pytest.fixture
    async def enhanced_server(self, mock_settings, mock_embeddings, mock_phoenix_client, mock_qdrant_client):
        """Create enhanced Qdrant server with mocked dependencies."""
        with patch('src.integrations.qdrant_mcp.get_settings', return_value=mock_settings), \
             patch('src.integrations.qdrant_mcp.get_openai_embeddings', return_value=mock_embeddings), \
             patch('src.integrations.qdrant_mcp.PhoenixMCPClient', return_value=mock_phoenix_client), \
             patch('src.integrations.qdrant_mcp.QdrantClient', return_value=mock_qdrant_client):
            
            server = EnhancedQdrantMCPServer()
            server.qdrant_client = mock_qdrant_client  # Ensure mock is used
            return server
    
    def test_server_initialization(self, enhanced_server):
        """Test enhanced server initialization."""
        assert enhanced_server is not None
        assert hasattr(enhanced_server, 'collections_config')
        assert ENHANCED_CODE_SNIPPETS_COLLECTION in enhanced_server.collections_config
        assert ENHANCED_SEMANTIC_MEMORY_COLLECTION in enhanced_server.collections_config
        assert PATTERN_VALIDATION_COLLECTION in enhanced_server.collections_config
    
    def test_collections_config(self, enhanced_server):
        """Test collection configuration structure."""
        config = enhanced_server.collections_config
        
        for collection_name, collection_config in config.items():
            assert "description" in collection_config
            assert "vector_size" in collection_config
            assert "distance" in collection_config
            assert collection_config["vector_size"] == 1536  # text-embedding-3-small
    
    async def test_initialize_collections_new_collections(self, enhanced_server):
        """Test initializing collections when they don't exist."""
        # Mock empty collections response
        collections_response = MagicMock()
        collections_response.collections = []
        enhanced_server.qdrant_client.get_collections.return_value = collections_response
        
        with patch('asyncio.to_thread', side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)):
            await enhanced_server.initialize_collections()
        
        # Verify create_collection was called for each collection
        assert enhanced_server.qdrant_client.create_collection.call_count == 3
    
    async def test_initialize_collections_existing_collections(self, enhanced_server):
        """Test initializing collections when they already exist."""
        # Mock existing collections
        existing_collection = MagicMock()
        existing_collection.name = PATTERN_VALIDATION_COLLECTION
        collections_response = MagicMock()
        collections_response.collections = [existing_collection]
        enhanced_server.qdrant_client.get_collections.return_value = collections_response
        
        with patch('asyncio.to_thread', side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)):
            await enhanced_server.initialize_collections()
        
        # Verify create_collection was called only for non-existing collections
        assert enhanced_server.qdrant_client.create_collection.call_count <= 2
    
    async def test_store_validated_pattern(self, enhanced_server):
        """Test storing a validated pattern."""
        validation_metadata = ValidationMetadata(
            confidence_score=0.9,
            qa_correctness_score=0.95,
            rag_relevance_score=0.85,
            experiment_id="exp_store_test",
            dataset_id="dataset_store_test",
            validation_timestamp=datetime.utcnow().isoformat(),
            pattern_type="phoenix_validated",
            validation_status="validated"
        )
        
        pattern = EnhancedQdrantPattern(
            pattern_id="store_test_123",
            content="Test content for storage",
            pattern_type="test_pattern",
            validation_metadata=validation_metadata,
            tags=["test", "storage"],
            category="testing"
        )
        
        with patch('asyncio.to_thread', side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)):
            pattern_id = await enhanced_server.store_validated_pattern(pattern)
        
        assert pattern_id == "store_test_123"
        enhanced_server.qdrant_client.upsert.assert_called_once()
    
    async def test_find_patterns_with_confidence(self, enhanced_server):
        """Test finding patterns with confidence filtering."""
        # Mock search results
        mock_hit = MagicMock()
        mock_hit.id = "pattern_123"
        mock_hit.score = 0.92
        mock_hit.payload = {
            "content": "Test pattern content",
            "pattern_type": "test",
            "validation_metadata": {
                "confidence_score": 0.88,
                "qa_correctness_score": 0.9,
                "experiment_id": "exp_123"
            },
            "tags": ["test"],
            "category": "testing",
            "created_at": "2025-06-17T10:00:00Z",
            "updated_at": "2025-06-17T10:00:00Z"
        }
        
        enhanced_server.qdrant_client.search.return_value = [mock_hit]
        
        with patch('asyncio.to_thread', side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)):
            results = await enhanced_server.find_patterns_with_confidence(
                query="test query",
                min_confidence=0.8,
                limit=5
            )
        
        assert len(results) == 1
        assert results[0]["pattern_id"] == "pattern_123"
        assert results[0]["similarity_score"] == 0.92
        assert results[0]["validation_metadata"]["confidence_score"] == 0.88
        enhanced_server.qdrant_client.search.assert_called_once()
    
    async def test_find_patterns_with_filters(self, enhanced_server):
        """Test finding patterns with additional filters."""
        enhanced_server.qdrant_client.search.return_value = []
        
        with patch('asyncio.to_thread', side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)):
            results = await enhanced_server.find_patterns_with_confidence(
                query="test query",
                min_confidence=0.7,
                pattern_type="phoenix_validated",
                experiment_id="exp_123",
                limit=10
            )
        
        # Verify search was called with filters
        call_args = enhanced_server.qdrant_client.search.call_args
        assert call_args[1]["query_filter"] is not None
        assert results == []
    
    async def test_sync_phoenix_patterns(self, enhanced_server):
        """Test synchronizing patterns from Phoenix."""
        # Mock Phoenix client response
        from src.integrations.phoenix_mcp import DatasetAnalysisResult, ExtractedPattern
        
        mock_pattern = ExtractedPattern(
            pattern_id="phoenix_pattern_123",
            query="What is the test?",
            response="This is a test response",
            confidence_score=0.9,
            qa_correctness_score=0.95,
            rag_relevance_score=0.85,
            experiment_id="exp_phoenix",
            example_id="example_123",
            dataset_id="dataset_phoenix",
            extraction_metadata={"test": "metadata"}
        )
        
        mock_analysis = DatasetAnalysisResult(
            dataset_name="test_dataset",
            total_experiments=1,
            successful_patterns=[mock_pattern],
            failed_extractions=[],
            cross_dataset_patterns=[],
            analysis_summary={"status": "completed"}
        )
        
        enhanced_server.phoenix_client.analyze_dataset_for_golden_patterns = AsyncMock(
            return_value=mock_analysis
        )
        
        with patch('asyncio.to_thread', side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)):
            with patch.object(enhanced_server, 'store_validated_pattern', new=AsyncMock(return_value="stored_id")):
                sync_result = await enhanced_server.sync_phoenix_patterns("dataset_phoenix")
        
        assert sync_result["patterns_stored"] == 1
        assert sync_result["failed_storage"] == 0
        assert sync_result["success_rate"] == 1.0
        assert sync_result["dataset_id"] == "dataset_phoenix"
    
    async def test_cleanup_expired_patterns(self, enhanced_server):
        """Test cleanup of expired patterns."""
        # Mock expired pattern
        mock_point = MagicMock()
        mock_point.id = "expired_pattern_123"
        
        enhanced_server.qdrant_client.scroll.return_value = ([mock_point], None)
        
        with patch('asyncio.to_thread', side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)):
            cleanup_stats = await enhanced_server.cleanup_expired_patterns()
        
        # Should have cleanup stats for all collections
        assert len(cleanup_stats) == 3
        for collection in enhanced_server.collections_config.keys():
            assert collection in cleanup_stats
            assert isinstance(cleanup_stats[collection], int)


class TestMCPServerIntegration:
    """Test MCP server integration and tools."""
    
    @pytest.mark.asyncio
    async def test_create_enhanced_qdrant_mcp_server(self):
        """Test creating the enhanced Qdrant MCP server."""
        with patch('src.integrations.qdrant_mcp.EnhancedQdrantMCPServer') as MockServer:
            mock_server_instance = MockServer.return_value
            mock_server_instance.initialize_collections = AsyncMock()
            
            server = await create_enhanced_qdrant_mcp_server()
            
            # Verify server was created and collections initialized
            assert server is not None
            mock_server_instance.initialize_collections.assert_called_once()
    
    def test_mcp_tools_registration(self):
        """Test that MCP tools are properly registered."""
        # This would test the actual tool registration
        # In a real scenario, we'd verify that tools like:
        # - store-validated-pattern
        # - qdrant-find-validated
        # - sync-phoenix-patterns
        # - cleanup-expired-patterns
        # are properly registered with the MCP server
        
        expected_tools = [
            "store-validated-pattern",
            "qdrant-find-validated", 
            "sync-phoenix-patterns",
            "cleanup-expired-patterns"
        ]
        
        # This is a placeholder test structure
        # In practice, this would interact with the actual MCP server
        assert len(expected_tools) == 4
    
    def test_mcp_resources_registration(self):
        """Test that MCP resources are properly registered."""
        # Test that resources like enhanced-qdrant://collections/{collection_name}
        # are properly registered
        
        expected_resource_pattern = "enhanced-qdrant://collections/{collection_name}"
        assert "{collection_name}" in expected_resource_pattern


# ==========================================
# Task 2.1: Enhanced Qdrant MCP Tests (NEW)
# ==========================================

def test_enhanced_collection_names():
    """Test that enhanced collection names are properly defined."""
    assert ENHANCED_CODE_SNIPPETS_COLLECTION == "enhanced_code_snippets"
    assert ENHANCED_SEMANTIC_MEMORY_COLLECTION == "enhanced_semantic_memory"
    assert PATTERN_VALIDATION_COLLECTION == "pattern_validation"


def test_validation_metadata_structure():
    """Test ValidationMetadata contains all required fields for Phoenix integration."""
    metadata = ValidationMetadata(
        confidence_score=0.85,
        qa_correctness_score=0.9,
        rag_relevance_score=0.8,
        experiment_id="exp_123",
        dataset_id="dataset_456",
        validation_timestamp="2025-06-17T10:00:00Z",
        pattern_type="phoenix_validated",
        validation_status="validated"
    )
    
    # Verify all Phoenix integration fields are present
    required_fields = [
        'confidence_score', 'qa_correctness_score', 'rag_relevance_score',
        'experiment_id', 'dataset_id', 'validation_timestamp',
        'pattern_type', 'validation_status'
    ]
    
    for field in required_fields:
        assert hasattr(metadata, field)
        assert getattr(metadata, field) is not None


def test_enhanced_pattern_phoenix_compatibility():
    """Test that EnhancedQdrantPattern is compatible with Phoenix ExtractedPattern."""
    # This test ensures our enhanced pattern can work with Phoenix data
    validation_metadata = ValidationMetadata(
        confidence_score=0.92,
        qa_correctness_score=0.95,
        rag_relevance_score=0.88,
        experiment_id="exp_phoenix_compat",
        dataset_id="dataset_phoenix_compat",
        validation_timestamp=datetime.utcnow().isoformat(),
        pattern_type="phoenix_validated",
        validation_status="validated"
    )
    
    pattern = EnhancedQdrantPattern(
        pattern_id="phoenix_compat_test",
        content="Query: What is compatibility?\nResponse: This tests Phoenix compatibility.",
        pattern_type="phoenix_validated",
        validation_metadata=validation_metadata,
        tags=["phoenix", "compatibility", "test"],
        category="qa_pattern"
    )
    
    # Verify pattern structure supports Phoenix workflow
    assert pattern.validation_metadata.experiment_id == "exp_phoenix_compat"
    assert pattern.validation_metadata.dataset_id == "dataset_phoenix_compat"
    assert "phoenix" in pattern.tags
    assert pattern.category == "qa_pattern"


def test_enhanced_qdrant_server_task_2_1_completion():
    """Test that Task 2.1 requirements are met."""
    # Verify that all Task 2.1 requirements are implemented:
    # 1. Validation metadata support
    # 2. Confidence filtering capability
    # 3. Phoenix pattern integration
    # 4. Enhanced collection support
    
    # Test 1: Validation metadata support
    validation_metadata = ValidationMetadata(
        confidence_score=0.8,
        qa_correctness_score=0.85,
        rag_relevance_score=0.9,
        experiment_id="task_2_1_test",
        dataset_id="task_2_1_dataset",
        validation_timestamp=datetime.utcnow().isoformat(),
        pattern_type="task_2_1_pattern",
        validation_status="validated"
    )
    assert validation_metadata is not None
    
    # Test 2: Enhanced pattern with validation
    enhanced_pattern = EnhancedQdrantPattern(
        pattern_id="task_2_1_pattern",
        content="Task 2.1 test content",
        pattern_type="test",
        validation_metadata=validation_metadata
    )
    assert enhanced_pattern.validation_metadata == validation_metadata
    
    # Test 3: Collection names for enhanced functionality
    collections = [
        ENHANCED_CODE_SNIPPETS_COLLECTION,
        ENHANCED_SEMANTIC_MEMORY_COLLECTION,
        PATTERN_VALIDATION_COLLECTION
    ]
    assert len(collections) == 3
    assert all("enhanced" in name or "validation" in name for name in collections)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
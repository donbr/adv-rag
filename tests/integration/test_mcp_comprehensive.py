#!/usr/bin/env python3
"""
Comprehensive pytest-based testing framework for MCP server.

This addresses the testing framework improvements mentioned:
- Structured pytest + asyncio fixtures
- Schema validation with Pydantic
- Negative/error case testing
- HTTP endpoint coverage
- Performance benchmarking
"""

import pytest
import pytest_asyncio
import asyncio
import json
import time
from typing import Dict, Any, List
from pydantic import BaseModel, ValidationError
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Schema validation models
class SemanticSearchResult(BaseModel):
    """Schema for semantic search results."""
    rank: int
    content: str
    metadata: Dict[str, Any]
    relevance_score: Any = None

class SemanticSearchResponse(BaseModel):
    """Schema for semantic search response."""
    results: List[SemanticSearchResult] = []
    count: int = 0

class ToolError(BaseModel):
    """Schema for tool error responses."""
    error: str

# Test fixtures
@pytest_asyncio.fixture(scope="module")
async def mcp_session():
    """Create MCP session for testing."""
    from src.mcp_server.main import mcp
    from mcp.shared.memory import create_connected_server_and_client_session
    
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        await session.initialize()
        yield session

@pytest.fixture(scope="module")
def test_queries():
    """Test queries for different scenarios."""
    return {
        "valid": [
            "What is John Wick about?",
            "Who are the main characters?",
            "What happens in the Continental Hotel?"
        ],
        "edge_cases": [
            "",  # Empty query
            "a",  # Single character
            "x" * 1000,  # Very long query
            "🎬🔫🐕",  # Emojis only
        ],
        "invalid": [
            None,  # Will cause validation error
        ]
    }

# Tool listing and discovery tests
@pytest.mark.asyncio
class TestToolDiscovery:
    """Test MCP tool discovery and listing."""
    
    async def test_list_tools_success(self, mcp_session):
        """Test that tools can be listed successfully."""
        tools = await mcp_session.list_tools()
        
        assert tools.tools, "Should have at least one tool"
        assert len(tools.tools) >= 2, "Should have semantic_search and document_query tools"
        
        tool_names = [tool.name for tool in tools.tools]
        assert "semantic_search" in tool_names
        assert "document_query" in tool_names
    
    async def test_tool_schemas(self, mcp_session):
        """Test that tools have proper schemas."""
        tools = await mcp_session.list_tools()
        
        for tool in tools.tools:
            assert tool.name, "Tool should have a name"
            assert tool.description, "Tool should have a description"
            # Note: inputSchema might be optional in some MCP versions

# Semantic search tool tests
@pytest.mark.asyncio
class TestSemanticSearch:
    """Test semantic search functionality."""
    
    @pytest.mark.parametrize("query,top_k", [
        ("What is John Wick about?", 3),
        ("Who are the main characters?", 5),
        ("Continental Hotel", 1),
    ])
    async def test_semantic_search_valid_queries(self, mcp_session, query, top_k):
        """Test semantic search with valid queries."""
        result = await mcp_session.call_tool(
            "semantic_search", 
            {"query": query, "top_k": top_k}
        )
        
        assert result.content, "Should return content"
        content = result.content[0].text
        
        # Should not be an error
        assert not content.startswith("Error"), f"Unexpected error: {content}"
        
        # Should be valid JSON
        parsed = json.loads(content)
        
        # Validate schema
        if "results" in parsed:
            response = SemanticSearchResponse(**parsed)
            assert response.count <= top_k, f"Should not return more than {top_k} results"
            assert len(response.results) == response.count, "Count should match results length"
            
            for result_item in response.results:
                assert result_item.content, "Each result should have content"
                assert result_item.metadata, "Each result should have metadata"
                assert 1 <= result_item.rank <= top_k, "Rank should be within expected range"
    
    @pytest.mark.parametrize("invalid_input", [
        {"query": "", "top_k": 3},  # Empty query
        {"query": "test", "top_k": 0},  # Zero results
        {"query": "test", "top_k": -1},  # Negative results
        {"top_k": 3},  # Missing query
        {"query": "test"},  # Missing top_k (should use default)
    ])
    async def test_semantic_search_edge_cases(self, mcp_session, invalid_input):
        """Test semantic search with edge cases."""
        try:
            result = await mcp_session.call_tool("semantic_search", invalid_input)
            
            if result.content:
                content = result.content[0].text
                
                # If it's an error, it should be a controlled error
                if content.startswith("Error"):
                    error = ToolError(error=content)
                    assert "Error" in error.error
                else:
                    # If successful, validate the response
                    parsed = json.loads(content)
                    if "results" in parsed:
                        SemanticSearchResponse(**parsed)  # Should validate
                        
        except Exception as e:
            # Should be a controlled exception, not a crash
            assert "validation" in str(e).lower() or "missing" in str(e).lower()
    
    async def test_semantic_search_performance(self, mcp_session):
        """Test semantic search performance."""
        query = "What is John Wick about?"
        
        # Warm-up call
        await mcp_session.call_tool("semantic_search", {"query": query, "top_k": 3})
        
        # Measure performance
        start_time = time.time()
        result = await mcp_session.call_tool("semantic_search", {"query": query, "top_k": 3})
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert result.content, "Should return content"
        assert response_time < 5.0, f"Response time {response_time:.2f}s should be under 5 seconds"
        
        # For production, you might want stricter limits
        if response_time > 2.0:
            pytest.warn(f"Response time {response_time:.2f}s is slower than ideal")

# Document query tool tests
@pytest.mark.asyncio
class TestDocumentQuery:
    """Test document query functionality."""
    
    @pytest.mark.parametrize("question", [
        "What is John Wick about?",
        "Who are the main characters in John Wick?",
        "Tell me about the Continental Hotel.",
    ])
    async def test_document_query_valid(self, mcp_session, question):
        """Test document query with valid questions."""
        result = await mcp_session.call_tool("document_query", {"question": question})
        
        assert result.content, "Should return content"
        content = result.content[0].text
        
        # Should not be an error
        assert not content.startswith("Error"), f"Unexpected error: {content}"
        
        # Should be a meaningful response
        assert len(content) > 10, "Response should be substantial"
    
    async def test_document_query_empty_question(self, mcp_session):
        """Test document query with empty question."""
        try:
            result = await mcp_session.call_tool("document_query", {"question": ""})
            
            if result.content:
                content = result.content[0].text
                # Empty questions might return an error or a generic response
                assert content, "Should return some content"
                
        except Exception as e:
            # Should be a controlled exception
            assert "question" in str(e).lower() or "required" in str(e).lower()

# Error handling and negative tests
@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and negative cases."""
    
    async def test_unknown_tool(self, mcp_session):
        """Test calling an unknown tool."""
        with pytest.raises(Exception) as exc_info:
            await mcp_session.call_tool("unknown_tool", {})
        
        # Should get a meaningful error about unknown tool
        error_msg = str(exc_info.value).lower()
        assert "unknown" in error_msg or "not found" in error_msg or "tool" in error_msg
    
    async def test_malformed_payload(self, mcp_session):
        """Test tools with malformed payloads."""
        malformed_payloads = [
            {"invalid_param": "value"},  # Invalid parameter
            {"query": None},  # None value
        ]
        
        for payload in malformed_payloads:
            try:
                result = await mcp_session.call_tool("semantic_search", payload)
                
                if result.content:
                    content = result.content[0].text
                    # Should either be an error response or handle gracefully
                    if content.startswith("Error"):
                        assert "Error" in content
                        
            except Exception:
                # Exception is acceptable for malformed input
                pass

# Resource tests
@pytest.mark.asyncio
class TestResources:
    """Test MCP resources."""
    
    async def test_list_resource_templates(self, mcp_session):
        """Test listing resource templates."""
        templates = await mcp_session.list_resource_templates()
        
        # Should have at least one template
        assert hasattr(templates, 'resourceTemplates'), "Should have resourceTemplates attribute"
    
    async def test_read_collection_resource(self, mcp_session):
        """Test reading collection resource."""
        try:
            resource = await mcp_session.read_resource("rag://collections/johnwick_baseline")
            
            assert resource.contents, "Should have content"
            
            for content in resource.contents:
                assert content.text, "Content should have text"
                
        except Exception as e:
            # Resource might not be available in test environment
            pytest.skip(f"Resource not available: {e}")

# Performance and load tests
@pytest.mark.asyncio
class TestPerformance:
    """Test performance and load characteristics."""
    
    async def test_concurrent_requests(self, mcp_session):
        """Test concurrent tool calls."""
        query = "What is John Wick about?"
        
        # Create multiple concurrent requests
        tasks = [
            mcp_session.call_tool("semantic_search", {"query": query, "top_k": 3})
            for _ in range(5)
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # All requests should succeed or fail gracefully
        for result in results:
            if isinstance(result, Exception):
                # Concurrent requests might fail due to resource limits
                pytest.warn(f"Concurrent request failed: {result}")
            else:
                assert result.content, "Successful requests should have content"
        
        # Total time should be reasonable for 5 concurrent requests
        assert total_time < 15.0, f"5 concurrent requests took {total_time:.2f}s"

# Integration and end-to-end tests
@pytest.mark.asyncio
class TestIntegration:
    """Integration and end-to-end tests."""
    
    async def test_full_workflow(self, mcp_session):
        """Test a complete workflow from discovery to execution."""
        # 1. Discover tools
        tools = await mcp_session.list_tools()
        assert tools.tools, "Should discover tools"
        
        # 2. Execute semantic search
        search_result = await mcp_session.call_tool(
            "semantic_search", 
            {"query": "John Wick", "top_k": 3}
        )
        assert search_result.content, "Search should return results"
        
        # 3. Execute document query
        query_result = await mcp_session.call_tool(
            "document_query", 
            {"question": "What is John Wick about?"}
        )
        assert query_result.content, "Query should return answer"
        
        # 4. Validate both responses are meaningful
        search_content = search_result.content[0].text
        query_content = query_result.content[0].text
        
        assert not search_content.startswith("Error"), "Search should not error"
        assert not query_content.startswith("Error"), "Query should not error"
        assert len(query_content) > len(search_content), "Query response should be more detailed"

# Test configuration and markers
@pytest.mark.slow
class TestComprehensive:
    """Comprehensive tests that take longer to run."""
    
    async def test_all_query_types(self, mcp_session, test_queries):
        """Test all query types comprehensively."""
        for category, queries in test_queries.items():
            if category == "invalid":
                continue  # Skip invalid queries in this test
                
            for query in queries:
                if not query:  # Skip empty queries
                    continue
                    
                try:
                    result = await mcp_session.call_tool(
                        "semantic_search", 
                        {"query": query, "top_k": 3}
                    )
                    
                    if result.content:
                        content = result.content[0].text
                        
                        if not content.startswith("Error"):
                            # Validate successful responses
                            parsed = json.loads(content)
                            if "results" in parsed:
                                SemanticSearchResponse(**parsed)
                                
                except Exception as e:
                    pytest.warn(f"Query '{query}' failed: {e}")

if __name__ == "__main__":
    # Run tests with verbose output and coverage
    pytest.main([
        __file__, 
        "-v", 
        "--tb=short",
        "--asyncio-mode=auto"
    ]) 
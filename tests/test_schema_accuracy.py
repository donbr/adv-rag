"""
Test schema accuracy for FastAPI → MCP conversion.

Ensures that FastAPI endpoint parameters map correctly to MCP tool schemas.
This addresses accuracy issues like "semantic_search" vs "semantic_retriever" 
and "top_k" vs "question" parameter mismatches.
"""
import asyncio
import pytest
from fastmcp import Client
from src.mcp.server import mcp


class TestSchemaAccuracy:
    """Test accurate mapping of FastAPI schemas to MCP tools."""
    
    @pytest.fixture
    async def mcp_client(self):
        """Create MCP client for testing."""
        async with Client(mcp) as client:
            yield client
    
    async def test_tool_names_match_fastapi_operations(self, mcp_client):
        """Verify MCP tool names match FastAPI operation IDs exactly."""
        tools = await mcp_client.list_tools()
        tool_names = {tool.name for tool in tools}
        
        # Expected tool names should match FastAPI endpoint operation_ids
        expected_tools = {
            'naive_retriever',
            'bm25_retriever', 
            'contextual_compression_retriever',
            'multi_query_retriever',
            'ensemble_retriever',
            'semantic_retriever'
        }
        
        assert expected_tools.issubset(tool_names), (
            f"Missing expected tools: {expected_tools - tool_names}"
        )
        
        # Verify NO incorrect tool names exist
        incorrect_names = {'semantic_search', 'naive_search', 'bm25_search'}
        assert not incorrect_names.intersection(tool_names), (
            f"Found incorrect tool names: {incorrect_names.intersection(tool_names)}"
        )
    
    async def test_parameter_schemas_match_fastapi(self, mcp_client):
        """Verify MCP tool parameters match FastAPI request schemas."""
        tools = await mcp_client.list_tools()
        
        for tool in tools:
            if tool.name.endswith('_retriever'):
                # All retriever tools should use QuestionRequest schema
                input_schema = tool.inputSchema
                
                assert input_schema is not None, f"Tool {tool.name} missing input schema"
                assert input_schema.get('type') == 'object', f"Tool {tool.name} schema not object type"
                
                properties = input_schema.get('properties', {})
                
                # Should have 'question' parameter, not 'query', 'top_k', etc.
                assert 'question' in properties, (
                    f"Tool {tool.name} missing 'question' parameter. Has: {list(properties.keys())}"
                )
                
                # Should NOT have incorrect parameters
                incorrect_params = {'query', 'top_k', 'limit', 'k'}
                found_incorrect = incorrect_params.intersection(properties.keys())
                assert not found_incorrect, (
                    f"Tool {tool.name} has incorrect parameters: {found_incorrect}"
                )
    
    async def test_parameter_types_are_correct(self, mcp_client):
        """Verify parameter types match expected FastAPI schema types."""
        tools = await mcp_client.list_tools()
        
        for tool in tools:
            if tool.name.endswith('_retriever'):
                input_schema = tool.inputSchema
                properties = input_schema.get('properties', {})
                
                if 'question' in properties:
                    question_prop = properties['question']
                    assert question_prop.get('type') == 'string', (
                        f"Tool {tool.name} 'question' parameter should be string, got {question_prop.get('type')}"
                    )
    
    async def test_tool_execution_with_correct_parameters(self, mcp_client):
        """Test that tools execute successfully with correct parameter names."""
        test_question = "What makes a good action movie?"
        
        # Test first two tools to verify they work with correct parameters
        tools = await mcp_client.list_tools()
        retriever_tools = [t for t in tools if t.name.endswith('_retriever')][:2]
        
        for tool in retriever_tools:
            try:
                result = await mcp_client.call_tool(tool.name, {"question": test_question})
                assert result is not None, f"Tool {tool.name} returned None"
                assert len(result) > 0, f"Tool {tool.name} returned empty result"
            except Exception as e:
                pytest.fail(f"Tool {tool.name} failed with correct parameters: {e}")
    
    async def test_incorrect_parameters_fail_gracefully(self, mcp_client):
        """Test that using incorrect parameter names fails gracefully."""
        tools = await mcp_client.list_tools()
        semantic_tool = next((t for t in tools if t.name == 'semantic_retriever'), None)
        
        if semantic_tool:
            # Test with old incorrect parameter names
            incorrect_params = [
                {"query": "test"},  # Should be 'question'
                {"top_k": 5},       # Should be 'question'
                {"search": "test"}   # Should be 'question'
            ]
            
            for params in incorrect_params:
                with pytest.raises(Exception):
                    await mcp_client.call_tool('semantic_retriever', params)


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"])) 
import pytest
from unittest.mock import AsyncMock, patch
from fastmcp import Client
from fastmcp.exceptions import ToolError

# The mcp_server_instance fixture is provided by conftest.py

class TestFastAPItoMCPConversion:
    """
    Verify that the FastMCP.from_fastapi() conversion works as expected
    using the recommended in-memory testing pattern from FastMCP documentation.
    """

    @pytest.mark.asyncio
    async def test_all_routes_are_converted_to_tools(self, mcp_server_instance):
        """Ensure all invokable routes are converted to MCP tools."""
        async with Client(mcp_server_instance) as client:
            tools_result = await client.list_tools()
            
            # Extract tool names from the tools result (it's already a list)
            tool_names = {tool.name for tool in tools_result}
            
            # Based on src/api/app.py, all HTTP methods become tools
            # POST endpoints get their operation_id, GET endpoints get auto-generated names
            expected_tools = {
                "naive_retriever",
                "bm25_retriever",
                "contextual_compression_retriever",
                "multi_query_retriever",
                "ensemble_retriever",
                "semantic_retriever",
                "health_check_health_get",  # GET /health
                "cache_stats_cache_stats_get",  # GET /cache/stats
            }
            
            assert tool_names == expected_tools

    @pytest.mark.asyncio
    @patch("src.api.app.NAIVE_RETRIEVAL_CHAIN")
    async def test_tool_execution_with_correct_parameters(self, mock_rag_chain, mcp_server_instance):
        """
        Verify a tool can be called with correct parameters, and that the call
        reaches the underlying (mocked) RAG chain.
        """
        # Mock the chain to return the structure expected by the FastAPI endpoint
        mock_response = {"response": type('MockResponse', (), {'content': 'mocked response'})()}
        mock_rag_chain.ainvoke = AsyncMock(return_value=mock_response)

        async with Client(mcp_server_instance) as client:
            # Call the MCP tool
            result = await client.call_tool(
                "naive_retriever", {"question": "test query"}
            )

            # According to FastMCP docs, result is a list of content objects
            # The actual response should be in the first item's text
            assert len(result) > 0
            # The response should contain the structured JSON response from FastAPI
            assert "mocked response" in result[0].text

    @pytest.mark.asyncio
    async def test_tool_execution_with_missing_parameter(self, mcp_server_instance):
        """
        Verify that calling a tool with a missing required parameter
        results in a specific ToolError, validating parameter schema conversion.
        """
        async with Client(mcp_server_instance) as client:
            with pytest.raises(ToolError) as excinfo:
                await client.call_tool("naive_retriever", {})  # Missing 'question'

            # Check for validation error
            error_message = str(excinfo.value).lower()
            assert "field required" in error_message or "missing" in error_message 
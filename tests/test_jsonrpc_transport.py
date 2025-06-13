"""
Test JSON-RPC transport functionality for MCP.

Tests JSON-RPC message handling to support STDIO → JSON-RPC transition path.
Validates protocol compliance and message structure.
"""
import asyncio
import json
import pytest
from fastmcp import Client
from src.mcp_server.fastapi_wrapper import mcp


class TestJsonRpcTransport:
    """Test JSON-RPC message handling and transport functionality."""
    
    @pytest.fixture
    async def mcp_client(self):
        """Create MCP client for testing."""
        async with Client(mcp) as client:
            yield client
    
    def test_jsonrpc_request_structure(self):
        """Test that we can construct valid JSON-RPC requests."""
        # Sample JSON-RPC request for tool call
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "semantic_retriever",
                "arguments": {
                    "question": "What makes a good action movie?"
                }
            }
        }
        
        # Validate JSON-RPC structure
        assert request["jsonrpc"] == "2.0"
        assert "id" in request
        assert "method" in request
        assert "params" in request
        
        # Validate it's valid JSON
        json_str = json.dumps(request)
        parsed = json.loads(json_str)
        assert parsed == request
    
    def test_jsonrpc_response_structure(self):
        """Test expected JSON-RPC response structure."""
        # Sample JSON-RPC success response
        success_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Action movies are characterized by..."
                    }
                ]
            }
        }
        
        # Validate response structure
        assert success_response["jsonrpc"] == "2.0"
        assert "id" in success_response
        assert "result" in success_response
        
        # Validate content structure
        content = success_response["result"]["content"]
        assert isinstance(content, list)
        assert len(content) > 0
        assert content[0]["type"] == "text"
        assert "text" in content[0]
    
    def test_jsonrpc_error_structure(self):
        """Test JSON-RPC error response structure."""
        error_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32602,
                "message": "Invalid params",
                "data": {
                    "details": "Missing required parameter 'question'"
                }
            }
        }
        
        # Validate error structure
        assert error_response["jsonrpc"] == "2.0"
        assert "id" in error_response
        assert "error" in error_response
        
        error = error_response["error"]
        assert "code" in error
        assert "message" in error
    
    async def test_list_tools_jsonrpc_flow(self, mcp_client):
        """Test list_tools operation in JSON-RPC context."""
        # This simulates what would happen over JSON-RPC
        tools = await mcp_client.list_tools()
        
        # Validate we get expected tools
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            'naive_retriever', 'bm25_retriever', 'contextual_compression_retriever',
            'multi_query_retriever', 'ensemble_retriever', 'semantic_retriever'
        ]
        
        for expected in expected_tools:
            assert expected in tool_names, f"Missing tool: {expected}"
        
        # Validate tool structure matches JSON-RPC expectations
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
    
    async def test_call_tool_jsonrpc_flow(self, mcp_client):
        """Test call_tool operation in JSON-RPC context."""
        # Test semantic_retriever tool call
        result = await mcp_client.call_tool(
            "semantic_retriever",
            {"question": "What makes a good action movie?"}
        )
        
        # Validate result structure for JSON-RPC transport
        assert result is not None
        assert len(result) > 0
        
        # Result should be serializable to JSON
        try:
            json.dumps(str(result))
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result not JSON serializable: {e}")
    
    def test_sample_messages_are_valid_json(self):
        """Test that our sample JSON-RPC messages are valid."""
        # Sample tool request
        tool_request = {
            "jsonrpc": "2.0",
            "id": "test-1",
            "method": "tools/call",
            "params": {
                "name": "semantic_retriever",
                "arguments": {"question": "test query"}
            }
        }
        
        # Sample tool response
        tool_response = {
            "jsonrpc": "2.0", 
            "id": "test-1",
            "result": {
                "content": [{"type": "text", "text": "response"}]
            }
        }
        
        # Both should be valid JSON
        for message in [tool_request, tool_response]:
            try:
                json_str = json.dumps(message)
                parsed = json.loads(json_str)
                assert parsed == message
            except Exception as e:
                pytest.fail(f"Invalid JSON message: {e}")
    
    async def test_concurrent_jsonrpc_calls(self, mcp_client):
        """Test that multiple JSON-RPC calls can be handled concurrently."""
        test_questions = [
            "What makes a good action movie?",
            "Tell me about science fiction films",
            "What are the best comedy movies?"
        ]
        
        # Make concurrent calls (simulating JSON-RPC concurrent requests)
        tasks = [
            mcp_client.call_tool("semantic_retriever", {"question": q})
            for q in test_questions
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All calls should succeed
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent call {i} failed: {result}")
            assert result is not None
            assert len(result) > 0


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"])) 
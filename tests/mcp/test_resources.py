import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.mcp.resources import format_rag_content, create_resource_handler, health_check, get_settings
import asyncio

@pytest.fixture
def mock_resource_dependencies():
    """Mock dependencies for the mcp.resources module."""
    with patch('src.mcp.resources.get_settings') as mock_settings, \
         patch('src.mcp.resources.get_chain_by_method') as mock_get_chain, \
         patch('src.mcp.resources.tracer') as mock_tracer:
        
        settings = MagicMock()
        settings.mcp_request_timeout = 30
        settings.max_snippets = 2
        mock_settings.return_value = settings
        
        mock_span = MagicMock()
        mock_span.get_span_context.return_value.trace_id = "mock_trace_id"
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

        yield {
            "settings": mock_settings,
            "get_chain": mock_get_chain,
            "tracer": mock_tracer,
            "span": mock_span,
        }

def test_format_rag_content():
    """Test the formatting of RAG results into a markdown string."""
    result = {
        "response": MagicMock(content="This is the answer."),
        "context": [
            MagicMock(page_content="Document 1 content", metadata={"source": "doc1.txt"}),
            MagicMock(page_content="Document 2 content", metadata={"source": "doc2.txt"}),
        ]
    }
    formatted_string = format_rag_content(result, "naive", "test query", "naive_retriever")
    
    assert "## Answer" in formatted_string
    assert "This is the answer." in formatted_string
    assert "## Context Documents" in formatted_string
    assert "Retrieved 2 relevant documents" in formatted_string
    assert "doc1.txt" in formatted_string
    assert "Operation ID**: naive\\_retriever" in formatted_string

@pytest.mark.asyncio
async def test_resource_handler_success(mock_resource_dependencies):
    """Test a resource handler's successful execution."""
    mock_chain = AsyncMock()
    mock_chain.ainvoke.return_value = {"response": MagicMock(content="Success"), "context": []}
    mock_resource_dependencies["get_chain"].return_value = mock_chain

    handler = create_resource_handler("naive")
    response = await handler("test query")
    
    mock_chain.ainvoke.assert_awaited_once_with({"question": "test query"})
    assert "Success" in response
    assert "MCP.resource.naive" in mock_resource_dependencies["tracer"].start_as_current_span.call_args[0][0]

@pytest.mark.asyncio
async def test_resource_handler_timeout(mock_resource_dependencies, caplog):
    """Test a resource handler's timeout behavior."""
    timeout = mock_resource_dependencies["settings"].return_value.mcp_request_timeout
    with patch('anyio.move_on_after', side_effect=asyncio.TimeoutError):
        handler = create_resource_handler("naive")
        response = await handler("test query")
        assert "# Timeout" in response
        assert f"Request timed out after {timeout} seconds" in response

@pytest.mark.asyncio
async def test_health_check_resource_success(mock_resource_dependencies):
    """Test the MCP health check resource."""
    response = await health_check()
    assert "System Health Check" in response
    assert "HEALTHY" in response
    assert "MCP.resource.health_check" in mock_resource_dependencies["tracer"].start_as_current_span.call_args[0][0]
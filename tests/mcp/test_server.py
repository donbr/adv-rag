import pytest
from unittest.mock import patch
from datetime import datetime
from src.mcp.server import create_mcp_server, get_server_health

@pytest.fixture
def mock_mcp_server_dependencies():
    """Mock dependencies for the mcp.server module."""
    with patch('src.mcp.server.FastMCP') as mock_fast_mcp, \
         patch('src.mcp.server.register') as mock_register:
        
        mock_fast_mcp.from_fastapi.return_value = "mcp_server_instance"
        
        yield {
            "fast_mcp": mock_fast_mcp,
            "register": mock_register,
        }

def test_create_mcp_server(mock_mcp_server_dependencies):
    """Test successful creation of the MCP server."""
    server = create_mcp_server()
    assert server == "mcp_server_instance"

    # Test failure case
    test_exception = ValueError("Failed to create")
    mock_mcp_server_dependencies["fast_mcp"].from_fastapi.side_effect = test_exception
    with pytest.raises(ValueError, match="Failed to create") as excinfo:
        create_mcp_server()
    assert excinfo.value == test_exception

@patch('src.mcp.server.datetime')
def test_get_server_health(mock_datetime):
    """Test the server health check function."""
    # Test success
    mock_datetime.now.return_value.isoformat.return_value = "2025-01-01T00:00:00"
    health = get_server_health()
    assert health["status"] == "healthy"
    assert health["timestamp"] == "2025-01-01T00:00:00"

    # Test failure
    mock_datetime.now.side_effect = ValueError("Time Error")
    with pytest.raises(ValueError, match="Time Error"):
        get_server_health() 
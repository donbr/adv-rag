#!/bin/bash

# MCP Server Test Script
# Tests the FastMCP server endpoints using command line tools

# Server entry point
MCP_SERVER_COMMAND="python -m src.mcp_server.main"

# Define test queries
QUERIES=(
    "What is John Wick about?"
    "Who are the main characters in John Wick?"
    "What happens in the Continental Hotel?"
    "Tell me about Keanu Reeves performance"
    "What is the plot of John Wick?"
)

# Create logs directory if it doesn't exist
LOGS_DIR="logs"
if [ ! -d "$LOGS_DIR" ]; then
    echo "Creating directory: ${LOGS_DIR}"
    mkdir -p "$LOGS_DIR"
fi

# Create a timestamped log file
LOG_FILE="${LOGS_DIR}/mcp_test_results_$(date +%Y%m%d_%H%M%S).log"

echo "Starting MCP server tests. Results will be logged to: ${LOG_FILE}"
echo "MCP Server Command: ${MCP_SERVER_COMMAND}" | tee -a "${LOG_FILE}"

# Function to test MCP server using Python client
test_mcp_tool() {
    local tool_name=$1
    local query_text=$2
    local top_k=${3:-5}

    echo "------------------------------------------------------------" | tee -a "${LOG_FILE}"
    echo "Testing MCP Tool: ${tool_name}" | tee -a "${LOG_FILE}"
    echo "Query: ${query_text}" | tee -a "${LOG_FILE}"
    echo "Top K: ${top_k}" | tee -a "${LOG_FILE}"
    echo "Timestamp: $(date)" | tee -a "${LOG_FILE}"
    echo "Response:" | tee -a "${LOG_FILE}"
    
    # Create a temporary Python test script
    cat > temp_mcp_test.py << EOF
#!/usr/bin/env python3
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_tool():
    try:
        from src.mcp_server.main import mcp
        from mcp.shared.memory import create_connected_server_and_client_session
        
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "${tool_name}", 
                {
                    "query": "${query_text}",
                    "top_k": ${top_k}
                }
            )
            
            if hasattr(result, 'content') and len(result.content) > 0:
                content = result.content[0].text
                print("SUCCESS")
                print(content)
            else:
                print("ERROR: No content returned")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_tool())
EOF

    # Run the test and capture output
    python temp_mcp_test.py 2>&1 | tee -a "${LOG_FILE}"
    
    # Clean up
    rm -f temp_mcp_test.py
    
    echo "------------------------------------------------------------" | tee -a "${LOG_FILE}"
    echo "" | tee -a "${LOG_FILE}"
}

# Function to test MCP server tools list
test_mcp_tools_list() {
    echo "------------------------------------------------------------" | tee -a "${LOG_FILE}"
    echo "Testing MCP Tools List" | tee -a "${LOG_FILE}"
    echo "Timestamp: $(date)" | tee -a "${LOG_FILE}"
    echo "Response:" | tee -a "${LOG_FILE}"
    
    cat > temp_list_tools.py << EOF
#!/usr/bin/env python3
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def list_tools():
    try:
        from src.mcp_server.main import mcp
        from mcp.shared.memory import create_connected_server_and_client_session
        
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            print("SUCCESS")
            print("Available tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(list_tools())
EOF

    python temp_list_tools.py 2>&1 | tee -a "${LOG_FILE}"
    rm -f temp_list_tools.py
    
    echo "------------------------------------------------------------" | tee -a "${LOG_FILE}"
    echo "" | tee -a "${LOG_FILE}"
}

# Function to test MCP server resources
test_mcp_resources() {
    echo "------------------------------------------------------------" | tee -a "${LOG_FILE}"
    echo "Testing MCP Resources" | tee -a "${LOG_FILE}"
    echo "Timestamp: $(date)" | tee -a "${LOG_FILE}"
    echo "Response:" | tee -a "${LOG_FILE}"
    
    cat > temp_test_resources.py << EOF
#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_resources():
    try:
        from src.mcp_server.main import mcp
        from mcp.shared.memory import create_connected_server_and_client_session
        
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            await session.initialize()
            
            # List resource templates
            templates = await session.list_resource_templates()
            print("SUCCESS")
            print("Available resource templates:")
            for template in templates.resourceTemplates:
                print(f"- {template.uriTemplate}: {template.description}")
            
            # Test reading a specific resource
            resource = await session.read_resource("rag://collections/johnwick_baseline")
            print("\nCollection info:")
            for content in resource.contents:
                print(content.text)
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_resources())
EOF

    python temp_test_resources.py 2>&1 | tee -a "${LOG_FILE}"
    rm -f temp_test_resources.py
    
    echo "------------------------------------------------------------" | tee -a "${LOG_FILE}"
    echo "" | tee -a "${LOG_FILE}"
}

# Function to test direct server startup
test_server_startup() {
    echo "------------------------------------------------------------" | tee -a "${LOG_FILE}"
    echo "Testing MCP Server Startup" | tee -a "${LOG_FILE}"
    echo "Timestamp: $(date)" | tee -a "${LOG_FILE}"
    
    # Test if server can start (timeout after 5 seconds)
    timeout 5s ${MCP_SERVER_COMMAND} > /dev/null 2>&1
    local exit_code=$?
    
    if [ $exit_code -eq 124 ]; then
        echo "SUCCESS: Server started and was running (timed out as expected)" | tee -a "${LOG_FILE}"
    elif [ $exit_code -eq 0 ]; then
        echo "SUCCESS: Server started and exited cleanly" | tee -a "${LOG_FILE}"
    else
        echo "ERROR: Server failed to start (exit code: $exit_code)" | tee -a "${LOG_FILE}"
    fi
    
    echo "------------------------------------------------------------" | tee -a "${LOG_FILE}"
    echo "" | tee -a "${LOG_FILE}"
}

# Main test execution
echo "=========================================="
echo "MCP SERVER COMPREHENSIVE TESTS"
echo "=========================================="

# Test 1: Server startup
echo "Test 1: Server Startup"
test_server_startup

# Test 2: List available tools
echo "Test 2: List Tools"
test_mcp_tools_list

# Test 3: Test resources
echo "Test 3: Test Resources"
test_mcp_resources

# Test 4: Test semantic search tool with different queries
echo "Test 4: Semantic Search Tests"
for query in "${QUERIES[@]}"; do
    test_mcp_tool "semantic_search" "${query}" 3
    sleep 2  # Small delay between tests
done

# Test 5: Test document query tool
echo "Test 5: Document Query Test"
test_mcp_tool "document_query" "What is John Wick about and who are the main characters?" 

# Test 6: Test collection stats
echo "Test 6: Collection Stats Test"
cat > temp_stats_test.py << EOF
#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_stats():
    try:
        from src.mcp_server.main import mcp
        from mcp.shared.memory import create_connected_server_and_client_session
        
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            await session.initialize()
            
            result = await session.call_tool("get_collection_stats", {})
            
            if hasattr(result, 'content') and len(result.content) > 0:
                content = result.content[0].text
                print("SUCCESS")
                print(content)
            else:
                print("ERROR: No content returned")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_stats())
EOF

echo "------------------------------------------------------------" | tee -a "${LOG_FILE}"
echo "Testing get_collection_stats tool" | tee -a "${LOG_FILE}"
python temp_stats_test.py 2>&1 | tee -a "${LOG_FILE}"
rm -f temp_stats_test.py
echo "------------------------------------------------------------" | tee -a "${LOG_FILE}"

echo ""
echo "=========================================="
echo "MCP server tests completed. Results logged to: ${LOG_FILE}"
echo "==========================================" 
# FastMCP with streamable HTTP transport testing

# Method 1: Test if MCP Inspector proxy can handle JSON-RPC via HTTP
# Based on the documentation, some setups expose MCP via HTTP
echo "Testing MCP via proxy server..."

# The proxy at 6277 might accept HTTP MCP requests
curl -X POST http://localhost:6277/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' \
  2>/dev/null || echo "❌ No HTTP MCP endpoint at 6277/mcp"

# Method 2: Test Inspector's internal API (if exposed)
curl -X POST http://localhost:6274/api/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' \
  2>/dev/null || echo "❌ No HTTP MCP endpoint at 6274/api/mcp"

# Method 3: Check if FastMCP server runs with streamable_http transport
# Your current setup uses stdio transport through Inspector
echo "ℹ️  Current setup: stdio transport via MCP Inspector"
echo "ℹ️  For direct HTTP JSON-RPC, you need streamable_http transport"

# Method 4: Verify current setup works via web UI
curl -s http://127.0.0.1:6274 | grep -q "MCP Inspector" && echo "✅ MCP Inspector UI is running at http://127.0.0.1:6274"

# Test resources
curl -X POST http://localhost:6274/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "resources/list"}'
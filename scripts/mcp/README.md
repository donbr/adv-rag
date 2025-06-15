# MCP Schema Export and Validation

This directory contains scripts for exporting and validating MCP (Model Context Protocol) server schemas from your FastAPI-based RAG application.

## Files

- **`export_mcp_schema.py`** - Exports MCP server definitions in both legacy and official formats
- **`validate_mcp_schema.py`** - Validates the official MCP schema against the specification
- **`README.md`** - This documentation

## Generated Files

- **`mcp_server_official.json`** - ✅ **RECOMMENDED** Official MCP-compliant schema
- **`mcp_server_schema.json`** - ❌ Legacy/community format (not MCP-compliant)

## Quick Start

```bash
# 1. Export MCP schemas
python scripts/mcp/export_mcp_schema.py

# 2. Validate official schema compliance
python scripts/mcp/validate_mcp_schema.py
```
# 3. streamable mode
```bash
python scripts/mcp/export_mcp_schema_http.py

python scripts/mcp/validate_mcp_schema.py
```

## Schema Formats

### Official MCP Format (`mcp_server_official.json`)

✅ **Use this for production!** This format follows the official MCP specification:

```json
{
  "$schema": "https://raw.githubusercontent.com/modelcontextprotocol/specification/main/schema/server.json",
  "$id": "https://github.com/donbr/advanced-rag/mcp-server.json",
  "name": "advanced-rag-fastapi",
  "version": "1.0.0",
  "capabilities": {
    "tools": { "listChanged": false },
    "resources": { "subscribe": false, "listChanged": false },
    "prompts": { "listChanged": false }
  },
  "protocolVersion": "2024-11-05",
  "tools": [
    {
      "name": "naive_retriever", 
      "description": "...",
      "inputSchema": { ... }  // ← camelCase
    }
  ]
}
```

**Key Features:**
- `$schema` and `$id` fields for JSON Schema validation
- `inputSchema` (camelCase) for tool parameters
- `capabilities` and `protocolVersion` fields
- Full MCP specification compliance

### Legacy Format (`mcp_server_schema.json`)

❌ **Don't use for production.** This is a legacy/community format:

```json
{
  "server_info": { ... },
  "tools": [
    {
      "name": "naive_retriever",
      "input_schema": { ... }  // ← snake_case (incorrect)
    }
  ]
}
```

**Issues:**
- Missing `$schema` and `$id` fields
- Uses `input_schema` (snake_case) instead of `inputSchema` (camelCase)
- Missing MCP-specific fields like `capabilities` and `protocolVersion`

## Key Differences

| Feature | Official MCP | Legacy Format |
|---------|-------------|---------------|
| JSON Schema validation | ✅ `$schema`, `$id` | ❌ Missing |
| Parameter field name | ✅ `inputSchema` | ❌ `input_schema` |
| MCP capabilities | ✅ Full support | ❌ Missing |
| Protocol version | ✅ Specified | ❌ Missing |
| Production ready | ✅ Yes | ❌ No |

## Validation Results

When you run the validation script, you'll see:

```
✅ Required Fields Check:
  • $schema: ✅ (JSON Schema reference)
  • $id: ✅ (Unique identifier)
  • capabilities: ✅ (MCP capabilities)
  • protocolVersion: ✅ (MCP protocol version)

✅ Field Format Check:
  • camelCase inputSchema: ✅ (Uses 'inputSchema' not 'input_schema')
  • Tools format: ✅ (All tools have name, description, inputSchema)

🎉 Schema is MCP-compliant!
   Ready for production deployment.
```

## Usage with MCP Clients

### Claude Desktop Integration

```bash
# Install the MCP server for Claude Desktop
fastmcp install src/mcp_server/fastapi_wrapper.py --name "Advanced RAG"
```

### Programmatic Access

```python
# Using the schema for validation or client generation
import json

with open("mcp_server_official.json") as f:
    schema = json.load(f)

# Validate client requests against tool schemas
for tool in schema["tools"]:
    print(f"Tool: {tool['name']}")
    print(f"Schema: {tool['inputSchema']}")
```

### JSON-RPC Discovery

The FastMCP server exposes these definitions via standard MCP methods:

```bash
# Get all tools
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# Get server capabilities  
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"capabilities/list","params":{}}'
```

## Official MCP Specification

- **Schema Reference**: https://raw.githubusercontent.com/modelcontextprotocol/specification/main/schema/server.json
- **Documentation**: https://modelcontextprotocol.io/
- **GitHub**: https://github.com/modelcontextprotocol/specification

## Best Practices

1. **Always use the official format** (`mcp_server_official.json`) for production
2. **Validate schemas** after any changes to your FastAPI endpoints
3. **Version your schemas** when you add/modify tools
4. **Test with real MCP clients** like Claude Desktop or custom implementations
5. **Monitor the official spec** for updates and new features

## Troubleshooting

### Schema Validation Fails

If validation fails, check:
- All tools have `inputSchema` (not `input_schema`)
- Required fields are present: `$schema`, `$id`, `capabilities`, `protocolVersion`
- Tool schemas have `properties` and `required` fields

### MCP Client Issues

If MCP clients can't discover your tools:
- Verify the server is running and accessible
- Check that tool names don't contain special characters
- Ensure input schemas are valid JSON Schema
- Test with `fastmcp dev` for debugging

### FastAPI Integration Issues

If tools aren't being exported:
- Verify FastAPI endpoints use POST methods for tools
- Check that request models use Pydantic with proper type hints
- Ensure the FastMCP wrapper is importing your app correctly 
# Essential Testing Guide for FastAPI → MCP Prototyping

## Quick Start

```bash
# Run essential tests
uv run bash tests/integration/test_api_endpoints.sh  # FastAPI baseline
uv run python tests/integration/verify_mcp.py       # MCP conversion

# Run accuracy tests  
uv run pytest tests/test_schema_accuracy.py -v     # Schema validation
uv run pytest tests/test_jsonrpc_transport.py -v   # JSON-RPC testing

# Run all tests
uv run pytest tests/ -v
```

## Test Structure

### ⭐ Essential Tests
1. **`tests/integration/test_api_endpoints.sh`** - FastAPI baseline validation
2. **`tests/integration/verify_mcp.py`** - MCP conversion verification

### 🎯 Accuracy Tests  
3. **`tests/test_schema_accuracy.py`** - Parameter mapping accuracy
4. **`tests/test_jsonrpc_transport.py`** - JSON-RPC message testing

### 📝 Sample Data
- **`tests/samples/tool_requests.json`** - Sample JSON-RPC requests
- **`tests/samples/tool_responses.json`** - Sample JSON-RPC responses

## Test Goals

### Accuracy First
- ✅ Tool names match FastAPI operation IDs exactly
- ✅ Parameters use correct schema (`question` not `query` or `top_k`)
- ✅ Response formats are consistent
- ✅ Error handling works correctly

### JSON-RPC Transition Support
- ✅ Valid JSON-RPC message structure
- ✅ Protocol compliance testing
- ✅ Concurrent request handling
- ✅ Error response formatting

## Running Individual Tests

```bash
# Test FastAPI endpoints directly
bash tests/integration/test_api_endpoints.sh

# Test MCP conversion
python tests/integration/verify_mcp.py

# Test schema accuracy
pytest tests/test_schema_accuracy.py::TestSchemaAccuracy::test_tool_names_match_fastapi_operations -v

# Test JSON-RPC transport
pytest tests/test_jsonrpc_transport.py::TestJsonRpcTransport::test_jsonrpc_request_structure -v
```

## Common Issues

### Schema Mismatches
- **Problem**: Tool using `query` parameter instead of `question`
- **Fix**: Update FastAPI endpoint to use `QuestionRequest` model
- **Test**: `test_schema_accuracy.py` will catch this

### Tool Name Errors  
- **Problem**: MCP tool named `semantic_search` instead of `semantic_retriever`
- **Fix**: Ensure FastAPI operation_id matches expected tool name
- **Test**: `test_schema_accuracy.py` validates tool names

### JSON-RPC Issues
- **Problem**: Response not JSON serializable
- **Fix**: Ensure all response objects can be converted to JSON
- **Test**: `test_jsonrpc_transport.py` validates serialization

## Environment Setup

```bash
# Activate environment
source .venv/bin/activate

# Install dependencies
uv sync

# Start FastAPI server (for endpoint tests)
python run.py  # or uvicorn src.main_api:app --reload
```

## Success Criteria

### All Tests Pass
```bash
✅ FastAPI endpoints respond correctly
✅ MCP conversion works without errors  
✅ Tool names and parameters are accurate
✅ JSON-RPC messages are well-formed
✅ Concurrent requests handled properly
```

This simplified structure focuses on **rapid, accurate FastAPI → MCP prototyping** without unnecessary complexity. 
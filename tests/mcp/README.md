# MCP JSON-RPC Testing Framework

## Overview
Test-Driven Development approach for MCP server validation with comprehensive JSON-RPC sample files and milestone tracking.

## Testing Milestones

### Milestone 1: Server Initialization & Capability Negotiation
- **Objective**: Verify server starts and properly negotiates capabilities
- **Success Criteria**: Server responds to initialization with correct capabilities
- **Sample Files**: `01-initialization/`

### Milestone 2: Tool Discovery & Validation
- **Objective**: Verify all tools are discoverable and have correct schemas
- **Success Criteria**: `list_tools` returns expected tool definitions
- **Sample Files**: `02-tools/`

### Milestone 3: Tool Execution
- **Objective**: Verify each tool executes correctly with sample inputs
- **Success Criteria**: All tools return expected outputs for valid inputs
- **Sample Files**: `03-tool-execution/`

### Milestone 4: Resource Discovery & Access
- **Objective**: Verify resources are discoverable and accessible
- **Success Criteria**: Resources return expected content
- **Sample Files**: `04-resources/`

### Milestone 5: Error Handling
- **Objective**: Verify proper error responses for invalid inputs
- **Success Criteria**: Appropriate error codes and messages returned
- **Sample Files**: `05-error-handling/`

### Milestone 6: Performance & Load Testing
- **Objective**: Verify server handles concurrent requests appropriately
- **Success Criteria**: Response times within acceptable limits
- **Sample Files**: `06-performance/`

## File Structure

```
tests/mcp_jsonrpc_samples/
├── README.md                          # This file
├── 01-initialization/
│   ├── request-initialize.json        # Client initialization request
│   ├── response-initialize.json       # Expected server response
│   └── test-initialize.py             # Automated test
├── 02-tools/
│   ├── request-list-tools.json        # Tool discovery request
│   ├── response-list-tools.json       # Expected tool list
│   └── test-tools-discovery.py        # Automated test
├── 03-tool-execution/
│   ├── semantic-search/
│   │   ├── request.json               # Sample tool call
│   │   ├── response.json              # Expected response
│   │   └── test.py                    # Test automation
│   ├── document-query/
│   │   ├── request.json
│   │   ├── response.json
│   │   └── test.py
│   └── collection-stats/
│       ├── request.json
│       ├── response.json
│       └── test.py
├── 04-resources/
│   ├── list-resources/
│   │   ├── request.json
│   │   ├── response.json
│   │   └── test.py
│   └── read-resource/
│       ├── request.json
│       ├── response.json
│       └── test.py
├── 05-error-handling/
│   ├── invalid-tool-call.json
│   ├── missing-parameters.json
│   ├── invalid-resource.json
│   └── test-error-handling.py
├── 06-performance/
│   ├── concurrent-requests.json
│   ├── load-test-config.json
│   └── test-performance.py
└── run-all-tests.py                   # Complete test suite runner
```

## Usage

### Run Individual Milestone Tests
```bash
# Milestone 1: Initialization
python tests/mcp_jsonrpc_samples/01-initialization/test-initialize.py

# Milestone 2: Tool Discovery  
python tests/mcp_jsonrpc_samples/02-tools/test-tools-discovery.py

# Milestone 3: Tool Execution
python tests/mcp_jsonrpc_samples/03-tool-execution/semantic-search/test.py
```

### Run Complete Test Suite
```bash
python tests/mcp_jsonrpc_samples/run-all-tests.py
```

### Validate Against Sample Files
Each test automatically compares actual responses against expected JSON-RPC samples, providing clear pass/fail validation.

## JSON-RPC Message Format

All sample files follow MCP specification (2025-03-26) using JSON-RPC 2.0:

### Request Format
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "method_name",
  "params": {
    "parameter_name": "value"
  }
}
```

### Response Format
```json
{
  "jsonrpc": "2.0", 
  "id": "matching-request-id",
  "result": {
    "response_data": "value"
  }
}
```

### Error Format
```json
{
  "jsonrpc": "2.0",
  "id": "matching-request-id", 
  "error": {
    "code": -32000,
    "message": "Error description",
    "data": "Additional error context"
  }
}
```

## Expected Outcomes by Milestone

### Milestone 1 Success Criteria
- Server responds with `serverInfo` containing name and version
- `capabilities` object includes supported features
- Response ID matches request ID

### Milestone 2 Success Criteria  
- `tools` array contains exactly 3 tools
- Each tool has `name`, `description`, and `inputSchema`
- Tool names match: `semantic_search`, `document_query`, `get_collection_stats`

### Milestone 3 Success Criteria
- `semantic_search` returns JSON array with search results
- `document_query` returns text response with RAG answer
- `get_collection_stats` returns JSON with collection metadata

### Milestone 4 Success Criteria
- `list_resources` returns available resource URIs
- `read_resource` returns resource content for valid URIs
- Resource schema matches expected format

### Milestone 5 Success Criteria
- Invalid tool calls return error code -32602 (Invalid params)
- Missing parameters return error code -32602 
- Unknown resources return error code -32001 (Invalid request)

### Milestone 6 Success Criteria
- Server handles 10 concurrent requests without errors
- Average response time < 500ms for tool calls
- No memory leaks during load testing 
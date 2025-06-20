# External MCP Services Documentation

## Overview

This document provides setup procedures, requirements, and testing results for external MCP services integrated with the Advanced RAG system. All services have been tested and validated as part of the MCP baseline validation process.

## Summary of External MCP Services

| Service | Status | Functionality | Performance Notes |
|---------|--------|---------------|-------------------|
| **Phoenix MCP** | ✅ Fully Functional | AI observability and experiment tracking | 16 tools available, all operations working |
| **Qdrant MCP (Semantic Memory)** | ✅ Fully Functional | Vector storage for contextual information | Complete store/find operations |
| **Qdrant MCP (Code Snippets)** | ⚠️ Initialization Issues | Vector storage for code snippets | Discovery works, execution hangs |
| **Redis MCP** | ✅ Fully Functional | High-performance caching layer | 546.9x average cache speedup |

---

## Phoenix MCP Integration

### Purpose
Phoenix MCP provides AI observability, experiment tracking, and dataset management capabilities for the RAG system.

### Requirements
- **Phoenix Server**: Must be running on localhost (typically port 6006)
- **Environment Variables**: None required (uses localhost defaults)
- **Command**: `uvx @arize-ai/phoenix-mcp`

### Available Tools (16 total)
- **Dataset Management**: `list-datasets`, `get-dataset-examples`, `add-dataset-examples`
- **Experiment Tracking**: `list-experiments-for-dataset`, `get-experiment-by-id`
- **Project Management**: `list-projects`
- **Prompt Management**: `list-prompts`, `get-latest-prompt`, `upsert-prompt`

### Setup Instructions
```bash
# 1. Install Phoenix (if not already installed)
pip install arize-phoenix

# 2. Start Phoenix server
python -m phoenix.server.main serve

# 3. Test Phoenix MCP connection
uvx @arize-ai/phoenix-mcp

# 4. Verify in Cursor MCP settings
# Add to ~/.cursor/mcp.json:
{
  "mcpServers": {
    "phoenix": {
      "command": "uvx",
      "args": ["@arize-ai/phoenix-mcp"]
    }
  }
}
```

### Validation Results
- ✅ **Connection**: Successful
- ✅ **Tool Discovery**: All 16 tools detected
- ✅ **Dataset Operations**: `list-datasets` returns real data (`johnwick_golden_testset`, `semantic_architecture_benchmark_20250616`)
- ✅ **Experiment Operations**: `list-experiments-for-dataset` works with real dataset IDs
- ✅ **Complete Request/Response**: All operations return full, structured data

---

## Qdrant MCP Integration

### Purpose
Qdrant MCP provides vector storage capabilities for semantic search and retrieval in two configurations:
1. **Semantic Memory**: Contextual information and project decisions
2. **Code Snippets**: Reusable code patterns and implementations

### Requirements
- **Qdrant Server**: Must be running on localhost:6333
- **Environment Variables**: 
  - `COLLECTION_NAME`: Collection identifier
  - `FASTMCP_PORT`: Unique port for each instance
- **Command**: `uvx mcp-server-qdrant`

### Configuration

#### Semantic Memory MCP (✅ WORKING)
```json
{
  "command": "uvx",
  "args": ["mcp-server-qdrant"],
  "env": {
    "COLLECTION_NAME": "semantic-memory",
    "FASTMCP_PORT": "8003",
    "TOOL_STORE_DESCRIPTION": "Store contextual information for semantic memory: conversation insights, project decisions, learned patterns, user preferences. Include descriptive information in the 'information' parameter and structured metadata for categorization and retrieval.",
    "TOOL_FIND_DESCRIPTION": "Search semantic memory for relevant context, decisions, and previously learned information. Use natural language queries to describe what type of information you're looking for."
  }
}
```

#### Code Snippets MCP (⚠️ ISSUES)
```json
{
  "command": "uvx",
  "args": ["mcp-server-qdrant"],
  "env": {
    "COLLECTION_NAME": "code-snippets",
    "FASTMCP_PORT": "8002",
    "TOOL_STORE_DESCRIPTION": "Store reusable code snippets for later retrieval. The 'information' parameter should contain a natural language description of what the code does, while the actual code should be included in the 'metadata' parameter as a 'code' property. The value of 'metadata' is a Python dictionary with strings as keys. Use this whenever you generate some code snippet.",
    "TOOL_FIND_DESCRIPTION": "Search for relevant code snippets based on natural language descriptions. The 'query' parameter should describe what you're looking for, and the tool will return the most relevant code snippets. Use this when you need to find existing code snippets for reuse or reference."
  }
}
```

### Available Tools (2 per instance)
- `qdrant-store`: Store vectors with metadata
- `qdrant-find`: Search for similar vectors

### Setup Instructions
```bash
# 1. Start Qdrant server
docker run -p 6333:6333 qdrant/qdrant

# 2. Install Qdrant MCP server
uvx install mcp-server-qdrant

# 3. Test connections
uvx mcp-server-qdrant  # Test basic installation

# 4. Configure in Cursor (see configurations above)
```

### Known Issues
- **Code Snippets MCP**: Hangs during session initialization/embedding provider setup
- **Semantic Memory MCP**: Works perfectly with all operations
- **Root Cause**: Likely embedding model initialization timeout or configuration mismatch in Code Snippets instance

### Troubleshooting
- Ensure Qdrant server is accessible at `localhost:6333`
- Verify collection names don't conflict between instances
- Check FastMCP ports are unique (8002 vs 8003)
- Monitor embedding model download/initialization

---

## Redis MCP Integration

### Purpose
Redis MCP provides high-performance caching layer for the RAG system with dramatic speed improvements.

### Requirements
- **Redis Server**: Must be running on localhost:6379
- **Environment Variables**: `REDIS_URL=redis://localhost:6379`
- **Command**: `uvx @modelcontextprotocol/server-redis`

### Performance Metrics
- **Average Cache Speedup**: 546.9x improvement
- **Individual Results**:
  - `semantic_retriever`: 788.6x speedup (7.024s → 0.009s)
  - `bm25_retriever`: 720.8x speedup (4.323s → 0.006s)
  - `ensemble_retriever`: 131.3x speedup (1.301s → 0.010s)

### Available Tools (4 total)
- `set`: Store key-value pairs with optional expiration
- `get`: Retrieve values by key
- `list`: Find keys matching patterns
- `delete`: Remove keys from storage

### Setup Instructions
```bash
# 1. Start Redis server
redis-server

# Or with Docker:
docker run -p 6379:6379 redis:alpine

# 2. Test Redis connection
redis-cli ping  # Should return PONG

# 3. Configure in Cursor MCP settings
{
  "mcpServers": {
    "redis-mcp": {
      "command": "uvx",
      "args": ["@modelcontextprotocol/server-redis"],
      "env": {
        "REDIS_URL": "redis://localhost:6379"
      }
    }
  }
}
```

### Validation Results
- ✅ **Connection**: Successful
- ✅ **Basic Operations**: All 4 CRUD operations working
- ✅ **Performance**: Exceptional cache hit performance
- ✅ **Integration**: Seamless with FastAPI MCP tools
- ✅ **Production Ready**: Suitable for high-load scenarios

---

## Docker Compose Setup (Recommended)

For consistent development environment, use the provided Docker Compose configuration:

```bash
# Start all services
docker-compose up -d

# Verify services
docker-compose ps

# Expected services:
# - qdrant (port 6333)
# - redis (port 6379)
# - phoenix (if included in compose)
```

## Testing and Validation

### Automated Testing
Each service includes comprehensive test scripts:

```bash
# Test all external MCP services
python tests/integrations/test_redis_mcp.py          # Redis integration
python tasks/temp-code/test_qdrant_semantic_memory_mcp.py  # Qdrant Semantic Memory
python tasks/temp-code/test_phoenix_mcp.py           # Phoenix integration
```

### Manual Validation
Use the MCP command-line tools for manual testing:

```bash
# Test tool discovery
uvx @arize-ai/phoenix-mcp

# Test specific operations
uvx mcp-server-qdrant  # For Qdrant
uvx @modelcontextprotocol/server-redis  # For Redis
```

## Security Considerations

### Network Security
- All services run on localhost by default
- No external network exposure required
- Use proper firewall rules in production

### Data Security
- Redis: Consider password authentication in production
- Qdrant: Review access controls for sensitive vector data
- Phoenix: Evaluate experiment data privacy requirements

### Authentication
- Current setup uses no authentication (development mode)
- Production deployments should implement proper auth mechanisms
- Consider API keys or token-based authentication

## Production Deployment Notes

### Performance Optimization
- **Redis**: Configure appropriate memory limits and persistence
- **Qdrant**: Optimize vector dimensions and indexing parameters
- **Phoenix**: Set up proper logging and metrics collection

### Monitoring
- Monitor service health endpoints
- Track cache hit rates (Redis)
- Monitor vector search performance (Qdrant)
- Review experiment metrics (Phoenix)

### Backup and Recovery
- Redis: Configure RDB/AOF persistence
- Qdrant: Implement collection backup strategies
- Phoenix: Back up experiment and dataset configurations

---

## Summary

The external MCP services provide significant value to the Advanced RAG system:

1. **Phoenix MCP**: Complete AI observability and experiment tracking
2. **Redis MCP**: Exceptional performance improvements through caching
3. **Qdrant MCP**: Vector storage with one fully functional instance

**Recommendation**: Deploy Redis MCP and Phoenix MCP immediately for production use. Monitor Qdrant Code Snippets MCP for resolution of initialization issues. 
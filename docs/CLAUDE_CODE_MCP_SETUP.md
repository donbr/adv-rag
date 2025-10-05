# Claude Code MCP Server Setup Guide

## Overview

This guide explains how to configure Claude Code to access the Advanced RAG system's MCP servers.

The system provides **two complementary MCP servers**:

1. **MCP Tools Server** (`adv-rag-tools`) - Full RAG pipeline with LLM synthesis
2. **MCP Resources Server** (`adv-rag-resources`) - Direct data access (3-5x faster)

## Prerequisites

✅ **Required**:
- Claude Code CLI installed and configured
- Python 3.13+ with virtual environment activated
- All system dependencies installed (`uv sync --dev`)
- Infrastructure running (`docker compose up -d`)
- Environment variables configured (`.env` file with API keys)

✅ **Verify System Status**:
```bash
# Check all services are running
python scripts/status.py

# Expected: All ✅ (Environment, Infrastructure, Application, MCP, Data)
```

## Configuration File

### Location

The MCP configuration file is provided at:
```
/home/donbr/ghcp/adv-rag/claude_mcp_config.json
```

### Usage with Claude Code

**Option 1: Project-Level Configuration** (Recommended)
```bash
# Use the configuration from this project
cd /home/donbr/ghcp/adv-rag

# Claude Code will automatically detect claude_mcp_config.json in the project root
# or you can specify it explicitly:
export CLAUDE_MCP_CONFIG=/home/donbr/ghcp/adv-rag/claude_mcp_config.json
```

**Option 2: User-Level Configuration**
```bash
# Copy to Claude Code's default config location
cp claude_mcp_config.json ~/.claude/mcp_servers.json

# Or merge with existing configuration
```

**Option 3: Inline Configuration**
```bash
# Use the --mcp-config flag with Claude Code
claude --mcp-config /home/donbr/ghcp/adv-rag/claude_mcp_config.json
```

## Configuration Details

### MCP Tools Server (`adv-rag-tools`)

**Purpose**: Complete RAG pipeline with LLM answer generation

**Configuration**:
```json
{
  "command": "python",
  "args": ["src/mcp/server.py"],
  "cwd": "/home/donbr/ghcp/adv-rag",
  "transport": "stdio"
}
```

**Available Tools** (6 retrieval strategies):
- `naive_retriever` - Fast baseline vector similarity
- `bm25_retriever` - Traditional keyword search
- `semantic_retriever` - Advanced semantic with context
- `contextual_compression_retriever` - AI reranking with filtering
- `multi_query_retriever` - Query expansion for coverage
- `ensemble_retriever` - Hybrid approach combining strategies

**Additional CQRS Qdrant Resources** (5 direct access patterns):
- `qdrant://collections` - List all Qdrant collections
- `qdrant://collections/{collection_name}` - Get collection info
- `qdrant://collections/{collection_name}/documents/{point_id}` - Retrieve specific document
- `qdrant://collections/{collection_name}/search?query={text}&limit={n}` - Direct search
- `qdrant://collections/{collection_name}/stats` - Collection statistics

**Performance**: ~20-30 seconds
**Output**: Formatted answer + context documents
**Logs**: `logs/mcp_tools.log`

**Example Usage**:
```python
# In Claude Code conversation
"Use the semantic_retriever tool to find information about John Wick action sequences"

# Result: Complete analysis with formatted answer and source attribution
```

### MCP Resources Server (`adv-rag-resources`)

**Purpose**: Direct data access bypassing LLM (Query Pattern - CQRS)

**Configuration**:
```json
{
  "command": "python",
  "args": ["src/mcp/resources.py"],
  "cwd": "/home/donbr/ghcp/adv-rag",
  "transport": "stdio"
}
```

**Available Resources** (6 retrieval strategies + 1 health):
- `retriever://naive_retriever/{query}` - Fast vector similarity results
- `retriever://bm25_retriever/{query}` - Keyword search results
- `retriever://semantic_retriever/{query}` - Semantic search results
- `retriever://contextual_compression_retriever/{query}` - Reranked results
- `retriever://multi_query_retriever/{query}` - Expanded query results
- `retriever://ensemble_retriever/{query}` - Hybrid results
- `system://health` - System health status

**Performance**: ~3-5 seconds ⚡ (3-5x faster than tools)
**Output**: Raw documents + metadata (LLM-friendly markdown)
**Logs**: `logs/mcp_resources.log`

**Example Usage**:
```python
# In Claude Code conversation
"Read the resource retriever://semantic_retriever/action movie fight scenes"

# Result: Raw documents for Claude to analyze and synthesize
```

## Development & Testing Tools

### MCP Inspector Helper Scripts

Two helper scripts are provided for easy testing with the MCP Inspector:

**Option 1: MCP Inspector (Standalone)**
```bash
# Interactive menu for testing either server
./scripts/dev_mcp_inspector.sh

# Opens inspector at: http://localhost:6274
# Provides step-by-step configuration instructions
```

**Option 2: FastMCP Dev Mode (Recommended)**
```bash
# Uses FastMCP's built-in dev command with hot reload
. /scripts/dev_mcp_fastmcp.sh

# Opens inspector automatically at: http://localhost:5173
# Includes hot reload on code changes
```

### Features of Helper Scripts

✅ **Automatic Infrastructure Checks** - Verifies Qdrant, Redis are running
✅ **Interactive Server Selection** - Choose Tools or Resources server
✅ **Pre-configured Commands** - All paths and settings ready to use
✅ **Browser Auto-Launch** - Opens inspector UI automatically
✅ **Example Queries** - Displays test queries for quick validation
✅ **Log Monitoring** - Shows where to tail server logs

## Testing the Configuration

### 1. Verify MCP Servers Start Correctly

**Test MCP Tools Server**:
```bash
# Terminal 1: Start the server
cd /home/donbr/ghcp/adv-rag
python src/mcp/server.py

# Expected output:
# ✅ MCP Server created successfully with Phoenix observability and CQRS Resources
# Starting MCP server 'Advanced RAG Retriever API' with transport 'stdio'

# Check logs
tail -f logs/mcp_tools.log
```

**Test MCP Resources Server**:
```bash
# Terminal 2: Start the server
cd /home/donbr/ghcp/adv-rag
python src/mcp/resources.py

# Expected output:
# Registered 6 RAG resource templates + 1 health endpoint with Phoenix tracing
# Starting Advanced RAG MCP Resource Server v2.2 with Enhanced Phoenix Tracing...

# Check logs
tail -f logs/mcp_resources.log
```

### 2. Test with Claude Code

**List Available MCP Servers**:
```bash
claude mcp list
# Should show: adv-rag-tools, adv-rag-resources
```

**Test Tool Invocation**:
```bash
# Using Claude Code interactively
claude

# In conversation:
"Use the naive_retriever tool to search for 'John Wick action scenes'"
```

**Test Resource Access**:
```bash
# In Claude Code conversation:
"Read the resource retriever://semantic_retriever/best action movies"
```

### 3. Verify Logs

Check that operations are being logged:
```bash
# MCP Tools Server logs
tail -f logs/mcp_tools.log

# MCP Resources Server logs
tail -f logs/mcp_resources.log

# Should see:
# - Server startup messages
# - Tool/resource invocations
# - Phoenix tracing information
# - Performance metrics
```

## When to Use Which Server?

### Use MCP Tools Server When:
- ✅ You need a **complete, ready-to-use answer**
- ✅ User-facing responses requiring synthesis
- ✅ Research and analysis workflows
- ✅ Question-answering systems

**Example**: "Analyze the themes in John Wick movies"
→ Returns: Formatted analysis with citations

### Use MCP Resources Server When:
- ⚡ You need **raw data for further processing** (3-5x faster)
- ⚡ Multi-step workflows where Claude processes data
- ⚡ Bulk data collection and analysis
- ⚡ Performance-critical applications

**Example**: "Gather data about action movies for trend analysis"
→ Returns: Raw documents for Claude's custom synthesis

## Architecture: Tools vs Resources (CQRS Pattern)

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code Client                        │
└─────────────────┬───────────────────────┬───────────────────┘
                  │                       │
         ┌────────▼────────┐     ┌───────▼────────┐
         │  MCP Tools      │     │  MCP Resources │
         │  Server         │     │  Server        │
         │  (Command)      │     │  (Query)       │
         └────────┬────────┘     └───────┬────────┘
                  │                       │
         ┌────────▼────────────────────────▼────────┐
         │         FastAPI Application              │
         │         (RAG Pipeline Core)              │
         └────────┬────────────────────┬────────────┘
                  │                    │
         ┌────────▼────────┐  ┌────────▼────────┐
         │   Qdrant        │  │   Redis Cache   │
         │   Vector DB     │  │                 │
         └─────────────────┘  └─────────────────┘
```

**Key Insight**:
- **Tools**: Full pipeline → Retrieval → LLM → Formatted answer (slower, complete)
- **Resources**: Direct retrieval → Raw documents (faster, requires Claude to synthesize)

## Troubleshooting

### Issue: "Server not found" or "Connection refused"

**Solution**: Ensure servers are running
```bash
# Check if servers are running
ps aux | grep -E "mcp/server.py|mcp/resources.py"

# Start servers if needed (in separate terminals)
python src/mcp/server.py
python src/mcp/resources.py
```

### Issue: "Import errors" or "Module not found"

**Solution**: Verify virtual environment and dependencies
```bash
# Activate virtual environment
source .venv/bin/activate

# Verify Python version
python --version  # Should be 3.13+

# Reinstall dependencies
uv sync --dev
```

### Issue: "API key not found" or "Authentication failed"

**Solution**: Check environment variables
```bash
# Verify .env file exists and has API keys
cat .env | grep -E "OPENAI_API_KEY|COHERE_API_KEY"

# Load environment if needed
source .env

# Test settings
python -c "from src.core.settings import get_settings; s=get_settings(); print(f'OpenAI: {bool(s.openai_api_key)}')"
```

### Issue: "Qdrant connection failed" or "Redis unavailable"

**Solution**: Ensure infrastructure services are running
```bash
# Check Docker services
docker compose ps

# Start services if down
docker compose up -d

# Verify connectivity
curl http://localhost:6333  # Qdrant
curl http://localhost:6379  # Redis (will return error but confirms port is open)
```

### Issue: Logs not appearing in `logs/` directory

**Solution**: Check log directory permissions
```bash
# Verify logs directory exists
ls -la logs/

# Create if missing
mkdir -p logs

# Check recent log entries
tail -20 logs/mcp_tools.log
tail -20 logs/mcp_resources.log
```

## Advanced Configuration

### Custom Environment Variables

Add to the MCP server configuration:
```json
{
  "adv-rag-tools": {
    "env": {
      "PYTHONUNBUFFERED": "1",
      "CACHE_ENABLED": "true",
      "MCP_REQUEST_TIMEOUT": "60",
      "LOG_LEVEL": "INFO"
    }
  }
}
```

### Performance Tuning

**For faster responses** (use Resources server):
```json
{
  "adv-rag-resources": {
    "env": {
      "MCP_REQUEST_TIMEOUT": "30",
      "MAX_SNIPPETS": "3"
    }
  }
}
```

**For comprehensive results** (use Tools server):
```json
{
  "adv-rag-tools": {
    "env": {
      "MCP_REQUEST_TIMEOUT": "120",
      "CACHE_ENABLED": "true"
    }
  }
}
```

## Phoenix Telemetry Integration

Both MCP servers are instrumented with Phoenix for comprehensive observability:

**View Traces**:
```bash
# Open Phoenix UI
open http://localhost:6006

# Filter by project:
# - Tools Server: "advanced-rag-system-{timestamp}"
# - Resources Server: "resource-wrapper-{timestamp}"
```

**Trace Information Includes**:
- Request/response timing
- Tool/resource invocations
- Cache hit rates
- Error tracking
- Span events and attributes

## Related Documentation

- **[CLAUDE.md](../CLAUDE.md)** - Main developer guide
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Essential commands
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture details
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

## Support

For issues or questions:
1. Check logs: `logs/mcp_tools.log` and `logs/mcp_resources.log`
2. Verify system status: `python scripts/status.py`
3. Review Phoenix traces: `http://localhost:6006`
4. Consult troubleshooting guide above

---

**Configuration Version**: 2.2.0
**Last Updated**: 2025-10-04
**Status**: ✅ Tested and Operational

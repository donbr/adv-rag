# mcp_server/fastapi_wrapper.py - Primary MCP Server Implementation

"""
🔗 FastAPI → MCP Server Integration - Complete Bootstrap Walkthrough

This script converts the Advanced RAG FastAPI application into a Model Context Protocol (MCP) 
server using FastMCP.from_fastapi() - enabling Claude Desktop and other MCP clients to access
your retrieval endpoints as native tools.

## 📋 STEP 1: Prerequisites (Must Complete First)

### FastAPI Foundation Required:
```bash
# MUST have FastAPI server working first
python run.py
# Test: curl http://localhost:8000/health

# Verify all 6 retrieval endpoints respond
bash tests/integration/test_api_endpoints.sh
```

### MCP Dependencies:
```bash
# Ensure MCP packages installed
uv sync
# Key packages: mcp[cli]>=1.9.3, fastmcp

# Environment variables (inherited from FastAPI)
echo $OPENAI_API_KEY    # Required when tools execute
echo $COHERE_API_KEY    # Required for compression retriever
```

## 🎯 STEP 2: FastMCP Architecture Pattern

### Zero-Duplication Conversion:
```python
from fastmcp import FastMCP
from src.main_api import app  # Existing FastAPI app

# Convert FastAPI → MCP with zero code duplication
mcp = FastMCP.from_fastapi(app=app)
```

### Automatic Tool Mapping:
```
FastAPI Endpoint                    →  MCP Tool
/invoke/naive_retriever            →  naive_retriever()
/invoke/bm25_retriever             →  bm25_retriever()  
/invoke/contextual_compression_*   →  contextual_compression_retriever()
/invoke/multi_query_retriever      →  multi_query_retriever()
/invoke/ensemble_retriever         →  ensemble_retriever()
/invoke/semantic_retriever         →  semantic_retriever()
```

### Schema Inheritance:
- **Input**: QuestionRequest {"question": str} → MCP tool parameters
- **Output**: FastAPI JSON responses → MCP tool results
- **Validation**: Pydantic models preserved across conversion

## 🔗 STEP 3: MCP Server Startup Process

### What Happens During Initialization:
1. **Path Resolution** - Adds project root to Python path
2. **FastAPI Import** - Loads existing app with all 6 endpoints
3. **Schema Conversion** - Maps FastAPI routes to MCP tools automatically
4. **Transport Setup** - Configures STDIO for Claude Desktop communication
5. **Tool Registration** - Makes retrieval endpoints available as MCP tools

### Manual Startup & Testing:
```bash
# Start MCP server (STDIO mode for Claude Desktop)
python src/mcp_server/fastapi_wrapper.py

# Test MCP protocol manually (alternative terminal)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python src/mcp_server/fastapi_wrapper.py

# Verify tools available
python tests/integration/verify_mcp.py
```

## 🖥️ STEP 4: Claude Desktop Integration

### Install for Claude Desktop:
```bash
# Option 1: Direct script reference
# Add to Claude Desktop MCP settings:
{
  "mcpServers": {
    "advanced-rag": {
      "command": "python",
      "args": ["/full/path/to/src/mcp_server/fastapi_wrapper.py"],
      "env": {
        "OPENAI_API_KEY": "your-key-here",
        "COHERE_API_KEY": "your-key-here"
      }
    }
  }
}

# Option 2: FastMCP CLI installation (when available)
fastmcp install src/mcp_server/fastapi_wrapper.py --name "Advanced RAG"
```

### Claude Desktop Usage:
```
User: "Use semantic_retriever to find information about John Wick action scenes"

Claude calls MCP tool:
{
  "tool": "semantic_retriever", 
  "parameters": {"question": "What makes John Wick action scenes special?"}
}

MCP server → FastAPI → RAG pipeline → Response
```

## 📊 STEP 5: Telemetry & Performance Monitoring

### Phoenix Integration (Inherited):
- **MCP tool calls** automatically traced in Phoenix
- **Compare MCP vs FastAPI** performance in same dashboard
- **Tool execution latency** measured end-to-end
- **Error tracking** across MCP protocol layer

### Logging Verbosity Control:
```python
# Reduce MCP protocol noise for production
logging.getLogger("mcp.server").setLevel(logging.WARNING)
logging.getLogger("fastmcp").setLevel(logging.INFO)
```

### Key Metrics for MCP vs FastAPI:
- **Protocol overhead** (JSON-RPC serialization)
- **Tool discovery latency** (tools/list performance)
- **Parameter validation** (schema conversion accuracy)
- **Transport efficiency** (STDIO vs HTTP comparison)

## 🎯 STEP 6: Development & Production Modes

### Development (STDIO - Claude Desktop):
```bash
# Single-user, in-process communication
python src/mcp_server/fastapi_wrapper.py
# → mcp.run() defaults to stdio transport
```

### Production (HTTP - Multi-user):
```python
# HTTP JSON-RPC for web applications
mcp.run(
    transport="streamable_http",
    host="0.0.0.0", 
    port=8001,  # Different from FastAPI port
    log_level="WARNING"
)
```

### Transport Performance Context:
- **STDIO**: No serialization overhead, perfect for Claude Desktop
- **JSON-RPC**: Network + serialization overhead, needed for multi-user scenarios
- **Performance focus**: RAG pipeline optimization matters more than MCP protocol

## 🚨 Troubleshooting

### Common MCP Integration Issues:
- **Import Errors**: Check `sys.path` resolution to project root
- **Tool Not Found**: Verify FastAPI endpoint exists and responds
- **Schema Mismatch**: Ensure QuestionRequest model is consistent
- **Claude Desktop**: Check MCP server logs for connection issues

### Debugging Commands:
```bash
# Test FastAPI directly first
curl -X POST "http://localhost:8000/invoke/semantic_retriever" \
     -H "Content-Type: application/json" \
     -d '{"question": "test"}'

# Then test MCP conversion
python tests/integration/verify_mcp.py

# Check tool schemas match
python -c "
from src.mcp_server.fastapi_wrapper import mcp
print([tool.name for tool in mcp.list_tools()])
"
```

### Recovery Steps:
```bash
# Reset and restart everything
docker-compose restart
python run.py                                    # Start FastAPI
python src/mcp_server/fastapi_wrapper.py        # Start MCP
```

## 🎯 Expected Outcomes

After successful MCP integration:
- ✅ 6 retrieval tools available in Claude Desktop
- ✅ FastAPI endpoints accessible via MCP protocol  
- ✅ Zero code duplication between HTTP and MCP interfaces
- ✅ Phoenix telemetry tracking both FastAPI and MCP calls
- ✅ Consistent parameter schemas across all interfaces

## 🔗 Next Steps

1. **Test in Claude Desktop** - Try semantic_retriever tool
2. **Compare performance** - FastAPI vs MCP telemetry analysis
3. **Production deployment** - Configure HTTP transport for multi-user
4. **Advanced integrations** - LangChain MCP adapters for agent workflows

This MCP integration enables Claude Desktop to use your RAG system natively while preserving
all the telemetry and performance characteristics of the underlying FastAPI application.
"""

import logging
import sys
import os
from pathlib import Path
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mcp_server():
    """Create MCP server from FastAPI app using FastMCP.from_fastapi()"""
    
    try:
        # Add project root to Python path for imports
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent  # Go up 3 levels: mcp_server -> src -> project_root
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            logger.info(f"Added project root to Python path: {project_root}")
        
        # Import the FastAPI app
        from src.main_api import app
        logger.info(f"Successfully imported FastAPI app with {len(app.routes)} routes")
        
        # Convert FastAPI app to MCP server using FastMCP.from_fastapi()
        # This works as a pure wrapper - no backend services needed during conversion
        mcp = FastMCP.from_fastapi(app=app)
        
        logger.info("FastMCP server created successfully from FastAPI app")
        
        return mcp
        
    except Exception as e:
        logger.error(f"Failed to import FastAPI app: {e}")
        logger.error("Environment variables will only be needed when MCP tools execute")
        raise

# Create the MCP server using the recommended approach
mcp = create_mcp_server()

def main():
    """Entry point for MCP server"""
    logger.info("Starting Advanced RAG MCP Server...")
    logger.info("FastMCP acts as a wrapper - backend services only needed when tools execute")
    mcp.run()

if __name__ == "__main__":
    main() 
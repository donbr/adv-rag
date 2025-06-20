# MCP Command-Line Testing Guide

## 🎯 Purpose

This guide focuses on **testing and leveraging MCP tools from the command line** for development and validation work, without requiring Claude Desktop integration.

## 🔧 Quick Command Reference

### Basic MCP Server Operations
```bash
# Start MCP server
python src/mcp/server.py

# Verify MCP tools are working
python tests/integration/verify_mcp.py

# Test specific MCP functionality
PYTHONPATH=$(pwd) python -c "
import asyncio
from fastmcp import Client
from src.mcp.server import mcp

async def test_mcp():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print([tool.name for tool in tools])

asyncio.run(test_mcp())
"
```

### Available MCP Tools (6 Retrieval Strategies)
```bash
# List all available tools
python -c "
import asyncio
from fastmcp import Client
from src.mcp.server import mcp

async def list_tools():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        for tool in tools:
            print(f'• {tool.name}: {tool.description}')

asyncio.run(list_tools())
"
```

**Expected Output:**
- `naive_retriever` - Basic vector similarity search
- `bm25_retriever` - Keyword-based search
- `contextual_compression_retriever` - AI-powered reranking
- `multi_query_retriever` - Query expansion and variation
- `ensemble_retriever` - Weighted combination of methods
- `semantic_retriever` - Advanced semantic chunking

## 🧪 Testing Individual MCP Tools

### Test Single Tool
```bash
# Test semantic retriever
python -c "
import asyncio
from fastmcp import Client
from src.mcp.server import mcp

async def test_semantic():
    async with Client(mcp) as client:
        result = await client.call_tool('semantic_retriever', {
            'question': 'What makes John Wick movies popular?'
        })
        print('Result:', result[0] if result else 'No result')

asyncio.run(test_semantic())
"
```

### Test All Tools with Same Query
```bash
# Compare all retrieval strategies
python -c "
import asyncio
from fastmcp import Client
from src.mcp.server import mcp

async def compare_all():
    question = 'What are the best John Wick action scenes?'
    
    async with Client(mcp) as client:
        tools = await client.list_tools()
        
        for tool in tools:
            if 'retriever' in tool.name:
                try:
                    result = await client.call_tool(tool.name, {'question': question})
                    preview = str(result[0])[:100] + '...' if result and len(str(result[0])) > 100 else str(result[0]) if result else 'No result'
                    print(f'{tool.name}: {preview}')
                except Exception as e:
                    print(f'{tool.name}: ERROR - {e}')

asyncio.run(compare_all())
"
```

## 🔍 MCP Server Inspection

### Server Capabilities
```bash
# Check server capabilities
python -c "
import asyncio
from fastmcp import Client
from src.mcp.server import mcp

async def inspect_server():
    async with Client(mcp) as client:
        # Basic connectivity
        await client.ping()
        print('✅ Server connectivity: OK')
        
        # Available capabilities
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        
        print(f'📊 Server Capabilities:')
        print(f'  • Tools: {len(tools)}')
        print(f'  • Resources: {len(resources)}')
        print(f'  • Prompts: {len(prompts)}')

asyncio.run(inspect_server())
"
```

### Tool Schema Inspection
```bash
# Inspect tool schemas
python -c "
import asyncio
from fastmcp import Client
from src.mcp.server import mcp

async def inspect_schemas():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        
        for tool in tools[:2]:  # First 2 tools
            print(f'🔧 {tool.name}:')
            print(f'  Description: {tool.description}')
            if hasattr(tool, 'inputSchema'):
                print(f'  Input Schema: {tool.inputSchema}')
            print()

asyncio.run(inspect_schemas())
"
```

## 📋 Validation Scripts

### Complete MCP Validation
```bash
# Run comprehensive validation
python tests/integration/verify_mcp.py
```

### Custom Validation Script
```bash
# Create and run custom validation
cat > validate_my_mcp.py << 'EOF'
import asyncio
from fastmcp import Client
from src.mcp.server import mcp

async def custom_validation():
    """Custom MCP validation for specific use case."""
    test_questions = [
        "What makes John Wick movies popular?",
        "Describe the fighting style in John Wick",
        "What are the best action scenes?"
    ]
    
    async with Client(mcp) as client:
        tools = await client.list_tools()
        retriever_tools = [t for t in tools if 'retriever' in t.name]
        
        print(f"🧪 Testing {len(retriever_tools)} retrieval tools with {len(test_questions)} questions")
        
        for question in test_questions:
            print(f"\n❓ Question: {question}")
            
            for tool in retriever_tools[:3]:  # Test first 3 tools
                try:
                    result = await client.call_tool(tool.name, {'question': question})
                    success = "✅" if result and len(str(result[0])) > 50 else "⚠️"
                    print(f"  {success} {tool.name}: {len(str(result[0])) if result else 0} chars")
                except Exception as e:
                    print(f"  ❌ {tool.name}: {str(e)[:50]}...")

if __name__ == "__main__":
    asyncio.run(custom_validation())
EOF

python validate_my_mcp.py
```

## 🔄 Development Workflow Integration

### Pre-Commit MCP Testing
```bash
# Add to your development workflow
#!/bin/bash
# pre-commit-mcp-test.sh

echo "🔍 Testing MCP server before commit..."

# Start services if not running
docker-compose up -d

# Test MCP server
if python tests/integration/verify_mcp.py; then
    echo "✅ MCP server tests passed"
else
    echo "❌ MCP server tests failed"
    exit 1
fi
```

### Performance Testing
```bash
# Time MCP tool execution
time python -c "
import asyncio
from fastmcp import Client
from src.mcp.server import mcp

async def time_test():
    async with Client(mcp) as client:
        result = await client.call_tool('ensemble_retriever', {
            'question': 'Performance test question'
        })
        print(f'Result length: {len(str(result[0])) if result else 0}')

asyncio.run(time_test())
"
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors
```bash
# Fix PYTHONPATH issues
export PYTHONPATH=$(pwd)
python tests/integration/verify_mcp.py

# Or use explicit path
PYTHONPATH=$(pwd) python tests/integration/verify_mcp.py
```

#### 2. Environment Variables
```bash
# Ensure environment is set
source .venv/bin/activate
export OPENAI_API_KEY="your-key"
export COHERE_API_KEY="your-key"
```

#### 3. Server Connection Issues
```bash
# Check if server is actually running
ps aux | grep "python src/mcp/server.py"

# Restart server
pkill -f "python src/mcp/server.py"
python src/mcp/server.py &
```

#### 4. Tool Execution Errors
```bash
# Debug specific tool
python -c "
import asyncio
from fastmcp import Client
from src.mcp.server import mcp

async def debug_tool():
    async with Client(mcp) as client:
        try:
            result = await client.call_tool('naive_retriever', {'question': 'test'})
            print('Success:', result)
        except Exception as e:
            print('Error details:', str(e))
            import traceback
            traceback.print_exc()

asyncio.run(debug_tool())
"
```

## 🎯 Integration with Current Work

### For MCP Baseline Validation
```bash
# Test all 6 retrieval strategies
python -c "
import asyncio
from fastmcp import Client
from src.mcp.server import mcp

async def baseline_validation():
    expected_tools = [
        'naive_retriever', 'bm25_retriever', 'contextual_compression_retriever',
        'multi_query_retriever', 'ensemble_retriever', 'semantic_retriever'
    ]
    
    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        
        print('🔍 MCP Baseline Validation Results:')
        for expected in expected_tools:
            status = '✅' if expected in tool_names else '❌'
            print(f'  {status} {expected}')
        
        # Test functionality
        test_question = 'What makes John Wick movies popular?'
        working_tools = 0
        
        for tool_name in expected_tools:
            if tool_name in tool_names:
                try:
                    result = await client.call_tool(tool_name, {'question': test_question})
                    if result and len(str(result[0])) > 20:
                        working_tools += 1
                        print(f'  ✅ {tool_name}: FUNCTIONAL')
                    else:
                        print(f'  ⚠️  {tool_name}: RETURNS EMPTY')
                except Exception as e:
                    print(f'  ❌ {tool_name}: ERROR - {str(e)[:50]}')
        
        print(f'\n📊 Summary: {working_tools}/{len(expected_tools)} tools working')

asyncio.run(baseline_validation())
"
```

This approach provides command-line testing capabilities for MCP development without requiring Claude Desktop, focusing on validation and development workflows. 
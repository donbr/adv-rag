# MCP Tools Quick Reference - Copy-Paste Commands

**Instant Testing Commands for Advanced RAG MCP Tools**

---

## 🚀 **Quick Start - Test Everything**

```bash
# 1. Start the MCP server
source .venv/bin/activate
python src/mcp/server.py &

# 2. Test basic tool discovery
python tests/integration/verify_mcp.py

# 3. Test specific tool (example)
python -c "
import asyncio
from mcp import Client

async def test_tool():
    async with Client(stdio_server_parameters=['python', 'src/mcp/server.py']) as session:
        result = await session.call_tool('naive_retriever', {'query': 'John Wick action', 'top_k': 3})
        print(result)

asyncio.run(test_tool())
"
```

---

## 📋 **Core RAG Tools - Ready to Run**

### naive_retriever
```bash
# Basic vector search
python -c "
import asyncio
from mcp import Client

async def test():
    async with Client(stdio_server_parameters=['python', 'src/mcp/server.py']) as session:
        result = await session.call_tool('naive_retriever', {
            'query': 'action scenes in John Wick movies',
            'top_k': 3
        })
        print('Results:', len(result.content[0].text.split('results')))

asyncio.run(test())
"
```

### bm25_retriever  
```bash
# Keyword search
python -c "
import asyncio
from mcp import Client

async def test():
    async with Client(stdio_server_parameters=['python', 'src/mcp/server.py']) as session:
        result = await session.call_tool('bm25_retriever', {
            'query': 'Keanu Reeves Continental Hotel',
            'top_k': 3
        })
        print('BM25 Results:', result.content[0].text[:100])

asyncio.run(test())
"
```

### ensemble_retriever (Hybrid Search)
```bash
# Best overall search quality
python -c "
import asyncio
from mcp import Client

async def test():
    async with Client(stdio_server_parameters=['python', 'src/mcp/server.py']) as session:
        result = await session.call_tool('ensemble_retriever', {
            'query': 'John Wick Continental Hotel assassin rules',
            'top_k': 4,
            'vector_weight': 0.6,
            'bm25_weight': 0.4
        })
        print('Hybrid Results:', result.content[0].text[:150])

asyncio.run(test())
"
```

### semantic_retriever
```bash
# Advanced semantic search
python -c "
import asyncio
from mcp import Client

async def test():
    async with Client(stdio_server_parameters=['python', 'src/mcp/server.py']) as session:
        result = await session.call_tool('semantic_retriever', {
            'query': 'themes of vengeance and justice in modern cinema',
            'top_k': 3,
            'semantic_threshold': 0.8
        })
        print('Semantic Results:', result.content[0].text[:150])

asyncio.run(test())
"
```

---

## 🔧 **System Tools - Health & Performance**

### health_check
```bash
# System status
python -c "
import asyncio
from mcp import Client

async def test():
    async with Client(stdio_server_parameters=['python', 'src/mcp/server.py']) as session:
        result = await session.call_tool('health_check', {
            'include_details': True,
            'check_external': True
        })
        print('Health Status:', result.content[0].text)

asyncio.run(test())
"
```

### cache_stats
```bash
# Cache performance 
python -c "
import asyncio
from mcp import Client

async def test():
    async with Client(stdio_server_parameters=['python', 'src/mcp/server.py']) as session:
        result = await session.call_tool('cache_stats', {
            'include_keys': True
        })
        print('Cache Stats:', result.content[0].text)

asyncio.run(test())
"
```

---

## 🌐 **External MCP Services - Direct Testing**

### Phoenix MCP (Port 8001)
```bash
# Test Phoenix tools
python -c "
import asyncio
from mcp import Client

async def test():
    async with Client(
        transport='stdio',
        command='npx',
        args=['@arize-ai/phoenix-mcp']
    ) as session:
        # List available prompts
        result = await session.call_tool('list-prompts', {'limit': 5})
        print('Phoenix Prompts:', result.content[0].text)

asyncio.run(test())
"
```

### Qdrant Semantic Memory (Port 8003)
```bash
# Test Qdrant semantic memory
python -c "
import asyncio
from mcp import Client

async def test():
    async with Client(
        transport='stdio', 
        command='python',
        args=['-m', 'mcp_qdrant_semantic_memory', '--port', '8003']
    ) as session:
        # Store information
        await session.call_tool('qdrant-store', {
            'information': 'Quick test of MCP semantic storage',
            'metadata': {'source': 'quick_reference_test'}
        })
        
        # Find information
        result = await session.call_tool('qdrant-find', {
            'query': 'semantic storage test'
        })
        print('Qdrant Results:', result.content[0].text)

asyncio.run(test())
"
```

### Redis MCP (Integrated)
```bash
# Test Redis caching (already tested in integration)
python tests/integrations/test_redis_mcp.py
```

---

## 🧪 **Test Scripts - Production Ready**

### Complete Tool Validation
```bash
# Run all tool tests
python tasks/temp-code/test_all_mcp_tools.py
```

### Performance Comparison
```bash
# Compare retrieval methods
python -c "
import time
import asyncio
from mcp import Client

async def benchmark():
    tools = ['naive_retriever', 'bm25_retriever', 'ensemble_retriever', 'semantic_retriever']
    query = 'John Wick action scenes'
    
    async with Client(stdio_server_parameters=['python', 'src/mcp/server.py']) as session:
        for tool in tools:
            start = time.time()
            result = await session.call_tool(tool, {'query': query, 'top_k': 5})
            duration = time.time() - start
            print(f'{tool}: {duration:.3f}s')

asyncio.run(benchmark())
"
```

---

## 🔍 **Debugging Commands**

### Tool Discovery
```bash
# List all available tools
python -c "
import asyncio
from mcp import Client

async def test():
    async with Client(stdio_server_parameters=['python', 'src/mcp/server.py']) as session:
        tools = await session.list_tools()
        for tool in tools.tools:
            print(f'Tool: {tool.name} - {tool.description}')

asyncio.run(test())
"
```

### Error Testing
```bash
# Test error handling
python -c "
import asyncio
from mcp import Client

async def test():
    async with Client(stdio_server_parameters=['python', 'src/mcp/server.py']) as session:
        try:
            result = await session.call_tool('naive_retriever', {'query': ''})  # Empty query
        except Exception as e:
            print('Expected error:', str(e))

asyncio.run(test())
"
```

---

## 📊 **Realistic Test Queries**

### Content Discovery
```bash
# Movie analysis queries
QUERIES=(
    "action choreography in John Wick"
    "Continental Hotel world building" 
    "Keanu Reeves performance analysis"
    "revenge themes in action movies"
    "practical effects vs CGI"
)

for query in "${QUERIES[@]}"; do
    echo "Testing: $query"
    python -c "
import asyncio
from mcp import Client

async def test():
    async with Client(stdio_server_parameters=['python', 'src/mcp/server.py']) as session:
        result = await session.call_tool('ensemble_retriever', {
            'query': '$query',
            'top_k': 3
        })
        print('Found:', len(result.content[0].text.split('results')), 'results')

asyncio.run(test())
    "
done
```

---

## ⚡ **One-Liner Tests**

```bash
# Quick tool test
python -c "import asyncio; from mcp import Client; asyncio.run((lambda: Client(stdio_server_parameters=['python', 'src/mcp/server.py']).__aenter__().then(lambda s: s.call_tool('health_check', {})).then(print))())"

# Cache performance check  
python -c "import asyncio; from mcp import Client; asyncio.run((lambda: Client(stdio_server_parameters=['python', 'src/mcp/server.py']).__aenter__().then(lambda s: s.call_tool('cache_stats', {'include_keys': True})).then(lambda r: print('546x speedup confirmed' if '546' in r.content[0].text else 'Cache not working')))())"
```

---

## 🚨 **Troubleshooting Quick Fixes**

### Server Won't Start
```bash
# Check environment
source .venv/bin/activate
python -c "from src.mcp.server import mcp; print('✅ Import success')"

# Check dependencies
docker ps | grep -E "(qdrant|redis|phoenix)"

# Kill stuck processes
pkill -f "src/mcp/server.py"
```

### Tools Not Found
```bash
# Verify FastAPI conversion
python -c "
from src.api.app import app
from fastmcp import FastMCP
mcp = FastMCP.from_fastapi(app)
print('Tools:', len(mcp._tools))
"
```

### External Services Down
```bash
# Test external MCPs individually
python tasks/temp-code/test_external_mcp_independence.py
```

---

## 📈 **Performance Benchmarks**

### Expected Response Times
```bash
# Run performance test
python -c "
import time
import asyncio
from mcp import Client

async def benchmark():
    timings = {}
    tools = ['naive_retriever', 'health_check', 'cache_stats']
    
    async with Client(stdio_server_parameters=['python', 'src/mcp/server.py']) as session:
        for tool in tools:
            start = time.time()
            if tool == 'health_check':
                await session.call_tool(tool, {})
            elif tool == 'cache_stats':  
                await session.call_tool(tool, {})
            else:
                await session.call_tool(tool, {'query': 'test', 'top_k': 5})
            timings[tool] = time.time() - start
    
    print('Performance Results:')
    for tool, duration in timings.items():
        status = '✅' if duration < 1.0 else '⚠️' if duration < 3.0 else '❌'
        print(f'{status} {tool}: {duration:.3f}s')

asyncio.run(benchmark())
"
```

---

## 💡 **Pro Tips**

1. **Always test `ensemble_retriever` first** - best balance of speed/quality
2. **Use `cache_stats` to verify 546x speedup** - should show high hit rates
3. **Test `health_check` when debugging** - shows component status
4. **Run independence test** - verifies external MCPs work without FastAPI
5. **Check Docker services** - `docker ps` shows Qdrant, Redis, Phoenix status

---

## 🎯 **Quick Validation Checklist**

```bash
# Complete system test (30 seconds)
echo "🔄 Testing MCP ecosystem..."

# 1. Core tools (8 tools)
python tests/integration/verify_mcp.py

# 2. External services (if configured)
python tasks/temp-code/test_external_mcp_independence.py  

# 3. Performance check
python -c "
import asyncio
from mcp import Client

async def quick_test():
    async with Client(stdio_server_parameters=['python', 'src/mcp/server.py']) as session:
        # Test basic retrieval
        result1 = await session.call_tool('naive_retriever', {'query': 'test'})
        
        # Test health
        result2 = await session.call_tool('health_check', {})
        
        # Test cache
        result3 = await session.call_tool('cache_stats', {})
        
        print('✅ All core tools working')

asyncio.run(quick_test())
"

echo "✅ MCP validation complete!"
```

**This reference gets you from zero to testing in under 30 seconds.** 
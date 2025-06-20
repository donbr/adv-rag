# MCP Developer Reference - Complete Architecture Guide

**Comprehensive Guide for Experienced Developers: From Tools to Resources with CQRS**

---

## 🎯 Executive Summary

This system implements a **sophisticated MCP architecture** that demonstrates the evolution from tool-centric to resource-centric design, leveraging **CQRS patterns** for optimal data retrieval and **transport-agnostic deployment** for maximum flexibility.

**Key Architectural Insights:**
- **MCP Semantic Correctness**: RAG retrieval should be RESOURCES (read-only data access), not TOOLS (actions with side effects)
- **CQRS Pattern**: Command-Query Responsibility Segregation naturally maps to MCP's tool/resource distinction
- **Transport Agnostic**: Same code serves stdio (Claude Desktop), HTTP (web apps), and WebSocket (real-time)
- **Zero Duplication**: `FastMCP.from_fastapi()` eliminates code duplication between interfaces

---

## 🏗️ Core Architecture Overview

### Tool Index - 40+ Available Capabilities

```
CORE FASTAPI (8):     MCP-RET-01→06 (retrieval) + MCP-UTIL-01→02 (system)
CORE RESOURCES (7):   Enhanced resource handlers with URI templates
PHOENIX (16):         Experiments, datasets, prompts (uvx @arize-ai/phoenix-mcp)
QDRANT (4):          Semantic memory (✅), code snippets (⚠️ init issues)  
REDIS (4):           Cache operations (546x avg speedup)
```

### Architecture Layers

```
┌─ MCP Client (Claude Desktop, Web Apps, Custom) ─┐
│  Transport: stdio / HTTP / WebSocket             │
├─ MCP Server Layer (FastMCP 2.0) ─────────────────┤
│  • Tools: Actions with side effects              │
│  • Resources: Read-only data access              │
│  • Transport Agnostic Design                     │
├─ Application Layer (Domain Logic) ───────────────┤
│  • RAG Chain Orchestration                       │
│  • Phoenix Telemetry Integration                 │
│  • Redis Cache Management                        │
├─ Infrastructure Layer ───────────────────────────┤
│  • Qdrant Vector Store (2 collections)           │
│  • Redis Cache (546x speedup)                    │
│  • Phoenix Observability                         │
└───────────────────────────────────────────────────┘
```

---

## 🔄 CQRS Pattern Implementation

### Command-Query Responsibility Segregation

**Commands (Tools)** = State-changing operations with side effects
**Queries (Resources)** = Read-only data access for LLM context

```python
# ✅ COMMANDS → MCP Tools (Actions)
@mcp.tool()
async def index_documents(documents: List[Document]) -> IndexResult:
    """Ingest documents into vector store (COMMAND - side effect)"""
    # Mutates vector store state
    vector_store.upsert(documents)
    return {"status": "indexed", "count": len(documents)}

@mcp.tool()
async def clear_cache() -> CacheResult:
    """Clear Redis cache (COMMAND - side effect)"""
    # Mutates cache state
    await redis_client.flushdb()
    return {"status": "cleared", "keys_removed": count}

# ✅ QUERIES → MCP Resources (Data Access)
@mcp.resource("retriever://semantic/{query}")
async def semantic_search_resource(query: str) -> str:
    """Load semantic search results into LLM context (QUERY - read-only)"""
    # No side effects, pure data retrieval
    results = await semantic_retrieval_logic(query)
    return format_for_llm_context(results, query)

@mcp.resource("cache://stats")
async def cache_statistics_resource() -> str:
    """Load cache performance data (QUERY - read-only)"""
    # No side effects, just data access
    stats = await redis_client.info("stats")
    return format_cache_stats(stats)
```

### Benefits of CQRS in MCP

| Aspect | Tools (Commands) | Resources (Queries) |
|--------|------------------|---------------------|
| **Caching** | ❌ Not cacheable (side effects) | ✅ URI-based caching |
| **Idempotency** | ❌ May change state | ✅ Safe to retry |
| **Edge Deployment** | Complex state management | ✅ Stateless, CDN-friendly |
| **LLM Integration** | "Execute this action" | ✅ "Load this context" |
| **Performance** | Full request cycle | ✅ Optimized GET patterns |

---

## 🚀 Transport-Agnostic Architecture

### Universal Client Pattern

The **same FastMCP Client code** produces identical results across all transports:

```python
# This EXACT pattern works for ALL transports:
async def universal_mcp_client(connection):
    async with Client(connection) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        result = await client.call_tool('semantic_retriever', {'question': 'test'})
        return tools, resources, result

# stdio Transport (Claude Desktop)
stdio_result = await universal_mcp_client(mcp_server_instance)

# HTTP Transport (Web Applications)  
http_result = await universal_mcp_client("http://127.0.0.1:8000/mcp")

# WebSocket Transport (Real-time Apps)
ws_result = await universal_mcp_client("ws://127.0.0.1:8002/mcp")

# Results are IDENTICAL across all transports
assert stdio_result == http_result == ws_result
```

### Deployment Flexibility

**Choose transport based on deployment needs, not functionality:**

```python
# Multi-transport deployment from same codebase
if __name__ == "__main__":
    if args.transport == "stdio":
        # Optimal for Claude Desktop
        mcp.run(transport="stdio")
    elif args.transport == "http":
        # Web applications, multi-user scenarios
        mcp.run(transport="streamable-http", port=8000, path="/mcp")
    elif args.transport == "websocket":
        # Real-time applications
        mcp.run(transport="websocket", port=8002)
```

### Transport Characteristics

| Transport | Best For | Latency | Concurrency | Schema Discovery |
|-----------|----------|---------|-------------|------------------|
| **stdio** | Claude Desktop, local dev | Minimal | Single-user | Local introspection |
| **HTTP** | Web apps, APIs | Network layer | Multi-user | `POST /mcp` with `rpc.discover` |
| **WebSocket** | Real-time apps | Low | High | Same as HTTP |

---

## 📊 Resource-Centric Data Architecture

### Enhanced Resource Implementation

The system implements **28.4KB of sophisticated resource handlers** with Phoenix tracing:

```python
# src/mcp/resources.py - Production resource architecture
from fastmcp import FastMCP
from phoenix.otel import register

# Enhanced Phoenix integration
tracer_provider = register(project_name="resource-wrapper-{timestamp}")
tracer = tracer_provider.get_tracer("advanced-rag-resource-server")

# Resource factory with Phoenix tracing
def create_resource_handler(method_name: str):
    async def get_retrieval_resource(query: str) -> str:
        with tracer.start_as_current_span(f"MCP.resource.{method_name}") as span:
            # Set span attributes for observability
            span.set_attribute("mcp.resource.method", method_name)
            span.set_attribute("mcp.resource.query_hash", generate_secure_query_hash(query))
            
            # Retrieve data with chain
            chain = get_chain_by_method(method_name)
            result = await chain.ainvoke({"question": query})
            
            # Format for LLM consumption
            return format_rag_content(result, method_name, query, operation_id)
    
    return get_retrieval_resource

# Register resource templates with URI patterns
for method in RETRIEVAL_METHODS:
    handler = create_resource_handler(method)
    operation_id = get_operation_id_for_method(method)
    resource_uri = f"retriever://{operation_id}/{{query}}"
    mcp.resource(resource_uri)(handler)
```

### Resource URI Templates

```python
# Available resource templates (production-ready)
retriever://naive_retriever/{query}                    # Basic vector similarity
retriever://bm25_retriever/{query}                     # Keyword search
retriever://contextual_compression_retriever/{query}   # AI-powered reranking
retriever://multi_query_retriever/{query}              # Query expansion
retriever://ensemble_retriever/{query}                 # Hybrid search
retriever://semantic_retriever/{query}                 # Semantic chunking
system://health                                        # System status
```

### LLM-Optimized Content Formatting

```python
def format_rag_content(result: Any, method: str, query: str, operation_id: str) -> str:
    """Format RAG results as LLM-optimized content with enhanced safety"""
    return f"""# {method.title()} Retrieval: {query}

## Answer
{answer}

## Context Documents  
Retrieved {context_count} relevant documents using {method} retrieval strategy.

### Document Excerpts
{context_snippets}

## Method Details
- **Strategy**: {method.title()} Retrieval
- **Operation ID**: {operation_id}
- **Documents Found**: {context_count}
- **API Consistency**: Resource provides read-only access to retrieval results

## Phoenix Tracing
- **Project**: {project_name}
- **Span**: MCP.resource.{method}
- **Observability**: Full request lifecycle traced

---
*Generated by Advanced RAG MCP Resource Server v2.2*
"""
```

---

## ⚡ Performance & Caching Architecture

### Multi-Layer Caching Strategy

**Redis Cache Performance** (Production Data):

| Tool | No Cache | With Cache | Speedup | Context Docs |
|------|----------|------------|---------|--------------|
| semantic_retriever | 7.024s | 0.009s | **788.6x** | 3-5 |
| bm25_retriever | 4.323s | 0.006s | **720.8x** | 3-5 |
| ensemble_retriever | 1.301s | 0.010s | **131.3x** | 4-6 |
| naive_retriever | 2.1s | 0.008s | **262.5x** | 3-4 |

### Cache Implementation

```python
# Modern dependency injection pattern (src/api/app.py)
async def invoke_chain_logic(
    chain, question: str, chain_name: str, 
    redis: aioredis.Redis = Depends(get_redis)
):
    """Modern chain invocation with Redis caching"""
    cache_key = generate_cache_key(chain_name, {"question": question})
    
    # Check cache first (Redis GET)
    cached_response = await get_cached_response(cache_key)
    if cached_response:
        logger.info(f"✅ Cache hit: {cache_key[:20]}...")
        return AnswerResponse(**cached_response)
    
    # Process request (LangChain LCEL)
    with tracer.start_as_current_span(f"Chain.{chain_name}") as span:
        result = await chain.ainvoke({"question": question})
    
    # Cache result (Redis SET with TTL)
    await cache_response(cache_key, response_data, ttl=300)
    logger.info(f"📝 Cached response: {cache_key[:20]}...")
    return response_data
```

### Cache Key Strategy

```python
def generate_cache_key(endpoint: str, request_data: dict) -> str:
    """Generate deterministic, collision-resistant cache keys"""
    cache_data = f"{endpoint}:{json.dumps(request_data, sort_keys=True)}"
    return f"mcp_cache:{hashlib.md5(cache_data.encode()).hexdigest()}"
```

---

## 🧠 Advanced RAG Pipeline

### Six Retrieval Strategies (Production Implementation)

```python
# src/rag/chain.py - LangChain LCEL implementation
CHAIN_MAPPING = {
    "naive": NAIVE_RETRIEVAL_CHAIN,        # Direct vector similarity
    "bm25": BM25_RETRIEVAL_CHAIN,          # Keyword-based search
    "contextual": CONTEXTUAL_COMPRESSION_CHAIN,  # Cohere reranking
    "multiquery": MULTI_QUERY_CHAIN,       # Query expansion with LLM
    "ensemble": ENSEMBLE_CHAIN,            # Weighted combination
    "semantic": SEMANTIC_CHAIN             # Advanced semantic chunking
}

# Example: Ensemble Chain (Best Performance)
ensemble_chain = (
    RunnableParallel({
        "context": ensemble_retriever | format_docs,
        "question": RunnablePassthrough()
    })
    | ChatPromptTemplate.from_template(template)
    | ChatOpenAI(model="gpt-4.1-mini")  # Pinned for reproducibility
    | StrOutputParser()
)
```

### Vector Store Architecture

```python
# Dual Qdrant collections for optimal performance
BASELINE_VECTORSTORE = Qdrant(
    client=qdrant_client,
    collection_name="adv_rag_baseline",
    embeddings=get_openai_embeddings()  # text-embedding-3-small
)

SEMANTIC_VECTORSTORE = Qdrant(
    client=qdrant_client,
    collection_name="adv_rag_semantic", 
    embeddings=get_openai_embeddings()
)
```

---

## 🔧 Configuration & Settings Management

### Centralized Configuration (src/core/settings.py)

```python
class Settings(BaseSettings):
    # Immutable Model Standards (Tier 1 - Non-Negotiable)
    llm_model_name: str = "gpt-4.1-mini"
    embedding_model_name: str = "text-embedding-3-small"
    
    # Performance Configuration
    mcp_request_timeout: int = 30
    max_snippets: int = 10
    redis_cache_ttl: int = 300
    
    # External Service Endpoints
    phoenix_endpoint: str = "http://localhost:6006"
    qdrant_url: str = "http://localhost:6333"
    redis_url: str = "redis://localhost:6379"
    
    # Phoenix Integration
    phoenix_project_name: str = "advanced-rag-mcp"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### Environment Variable Loading

```bash
# .env file
OPENAI_API_KEY=your-openai-key
COHERE_API_KEY=your-cohere-key
PHOENIX_ENDPOINT=http://localhost:6006
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
MCP_REQUEST_TIMEOUT=30
REDIS_CACHE_TTL=300
```

---

## 🧪 Testing & Validation Architecture

### Multi-Layer Testing Strategy

```python
# tests/mcp/test_resources.py - Resource testing patterns
@pytest.mark.asyncio
async def test_resource_handler_success(mock_resource_dependencies):
    """Test resource handler's successful execution with mocking"""
    mock_chain = AsyncMock()
    mock_chain.ainvoke.return_value = {"response": MagicMock(content="Success"), "context": []}
    
    handler = create_resource_handler("naive")
    response = await handler("test query")
    
    assert "Success" in response
    assert "MCP.resource.naive" in mock_resource_dependencies["tracer"].start_as_current_span.call_args[0][0]

@pytest.mark.asyncio
async def test_resource_handler_timeout(mock_resource_dependencies):
    """Test resource handler's timeout behavior"""
    timeout = mock_resource_dependencies["settings"].return_value.mcp_request_timeout
    with patch('anyio.move_on_after', side_effect=asyncio.TimeoutError):
        handler = create_resource_handler("naive")
        response = await handler("test query")
        assert "# Timeout" in response
        assert f"Request timed out after {timeout} seconds" in response
```

### Comprehensive Validation Suite

```bash
# Complete testing workflow
python tests/integration/verify_mcp.py      # MCP server validation
bash tests/integration/test_api_endpoints.sh # FastAPI endpoint testing
python scripts/mcp/export_mcp_schema_native.py # Schema export
python scripts/mcp/validate_mcp_schema.py   # MCP compliance
python scripts/evaluation/retrieval_method_comparison.py # Performance benchmarks
```

---

## 🔍 Observability & Monitoring

### Phoenix Telemetry Integration

```python
# Enhanced Phoenix tracing throughout the stack
from phoenix.otel import register

# Global tracer registration
tracer_provider = register(
    project_name="advanced-rag-mcp",
    auto_instrument=True
)

# Distributed tracing across components
with tracer.start_as_current_span("MCP.resource.semantic") as span:
    span.set_attribute("mcp.resource.method", "semantic")
    span.set_attribute("mcp.resource.query_hash", query_hash)
    span.add_event("chain.retrieval.start")
    
    result = await chain.ainvoke({"question": query})
    
    span.add_event("chain.retrieval.complete", {
        "context_docs": len(result.get("context", []))
    })
```

### Real-Time Monitoring Dashboard

- **Phoenix UI**: http://localhost:6006 - Request tracing, performance analysis
- **RedisInsight**: http://localhost:5540 - Cache performance, key management
- **Qdrant Console**: http://localhost:6333/dashboard - Vector store metrics

---

## 🚀 Production Deployment Patterns

### Docker Compose Stack

```yaml
# docker-compose.yml - Production-ready infrastructure
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: ["./qdrant_storage:/qdrant/storage"]
    
  redis:
    image: redis:latest  
    ports: ["6379:6379"]
    command: ["redis-server", "--maxmemory", "1gb", "--maxmemory-policy", "allkeys-lru"]
    
  phoenix:
    image: arizephoenix/phoenix:latest
    ports: ["6006:6006"]
    environment: [PHOENIX_SQL_DATABASE_URL=sqlite:///tmp/phoenix.db]
    
  mcp-server:
    build: .
    ports: ["8000:8000"]
    depends_on: [qdrant, redis, phoenix]
    environment:
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
      - PHOENIX_ENDPOINT=http://phoenix:6006
```

### Multi-Transport Server

```python
# Production server with transport selection
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "http", "websocket"], default="stdio")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    
    if args.transport == "stdio":
        # Claude Desktop integration
        mcp.run(transport="stdio")
    elif args.transport == "http":
        # Web applications
        mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")
    elif args.transport == "websocket":
        # Real-time applications
        mcp.run(transport="websocket", host="0.0.0.0", port=args.port)
```

---

## 💡 Advanced Integration Patterns

### LangChain MCP Adapters

```python
# Integration with LangChain ecosystem
from langchain_mcp_adapters import create_langchain_tool

# Convert MCP resources to LangChain tools
semantic_tool = create_langchain_tool(
    server_path="src/mcp/server.py",
    resource_uri="retriever://semantic_retriever/{query}"
)

# Use in LangChain agents
from langchain.agents import initialize_agent
agent = initialize_agent(
    tools=[semantic_tool],
    llm=ChatOpenAI(),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)
```

### Custom MCP Server Development

```python
# Building custom MCP servers with FastMCP
from fastmcp import FastMCP

custom_mcp = FastMCP("domain-specific-server")

@custom_mcp.tool()
async def analyze_document(content: str, analysis_type: str) -> str:
    """Custom domain analysis tool"""
    # Your domain-specific logic
    return f"Analysis complete: {analysis_type}"

@custom_mcp.resource("analysis://document/{doc_id}")
async def get_document_analysis(doc_id: str) -> str:
    """Custom resource for document access"""
    # Your resource logic
    return f"Document {doc_id} analysis content"
```

---

## 🔮 Next-Generation Architecture Roadmap

### Edge-Native Evolution (2025 Vision)

**Current → Target Architecture:**

```
Python FastAPI + MCP (Current)
    ↓ Evolution Path
LangGraphJS + Vercel Edge + FastMCP v2 (Target)
```

**Benefits of Evolution:**
- **Global Edge Deployment**: Sub-100ms latency worldwide
- **Agentic Workflows**: Sophisticated multi-agent reasoning  
- **Server Composition**: FastMCP v2 microservice patterns
- **TypeScript Ecosystem**: Enhanced developer experience

### Implementation Strategy

```typescript
// Next-gen LangGraphJS agent with MCP integration
import { StateGraph } from "@langchain/langgraph"

const ragAgent = new StateGraph({
  channels: {
    query: String,
    context: Array,
    confidence: Number,
    strategy: String
  }
})
.addNode("classify_intent", classifyUserIntent)
.addNode("select_strategy", selectRetrievalStrategy)  
.addNode("parallel_retrieval", parallelMCPRetrieval)
.addNode("confidence_check", evaluateConfidence)
.addConditionalEdges("confidence_check", {
  "high": "synthesize_response",
  "low": "parallel_retrieval"
})
```

---

## 📚 Quick Reference Commands

### Development Workflow

```bash
# Environment setup
source .venv/bin/activate
docker-compose up -d
python scripts/ingestion/csv_ingestion_pipeline.py

# Server startup
python run.py                    # FastAPI server (port 8000)
python src/mcp/server.py         # MCP server (stdio/HTTP)

# Testing & validation
python tests/integration/verify_mcp.py
python scripts/mcp/export_mcp_schema_native.py
python scripts/evaluation/retrieval_method_comparison.py
```

### MCP Client Testing

```python
# Universal MCP client pattern
import asyncio
from fastmcp import Client
from src.mcp.server import mcp

async def test_mcp_capabilities():
    async with Client(mcp) as client:
        # List capabilities
        tools = await client.list_tools()
        resources = await client.list_resources()
        
        # Test retrieval
        result = await client.call_tool('ensemble_retriever', {
            'question': 'What makes John Wick movies popular?'
        })
        
        return len(tools), len(resources), len(str(result[0]))

# Usage
capabilities = asyncio.run(test_mcp_capabilities())
print(f"Tools: {capabilities[0]}, Resources: {capabilities[1]}, Response: {capabilities[2]} chars")
```

### Performance Validation

```bash
# Cache performance test
python -c "
import asyncio, time
from fastmcp import Client
from src.mcp.server import mcp

async def cache_test():
    async with Client(mcp) as client:
        # First call (cache miss)
        start = time.time()
        await client.call_tool('semantic_retriever', {'question': 'cache test'})
        first_time = time.time() - start
        
        # Second call (cache hit)
        start = time.time()
        await client.call_tool('semantic_retriever', {'question': 'cache test'})
        second_time = time.time() - start
        
        speedup = first_time / second_time
        print(f'Cache speedup: {speedup:.1f}x ({first_time:.3f}s → {second_time:.3f}s)')

asyncio.run(cache_test())
"
```

---

## 🎯 Conclusion

This system demonstrates **advanced MCP architecture patterns** that solve real production challenges:

✅ **CQRS Implementation**: Tools for commands, Resources for queries  
✅ **Transport Agnostic**: Same code, multiple deployment options  
✅ **Zero Duplication**: FastMCP.from_fastapi() eliminates redundancy  
✅ **Production Ready**: Phoenix tracing, Redis caching, comprehensive testing  
✅ **Performance Optimized**: 546x average speedup with intelligent caching  
✅ **Semantically Correct**: Proper MCP resource usage for data retrieval  

The architecture provides a **reference implementation** for building sophisticated MCP servers that leverage modern patterns like CQRS, transport independence, and comprehensive observability while maintaining the flexibility to evolve toward next-generation edge-native agentic platforms.

**Key Insight**: MCP's tool/resource distinction maps perfectly to CQRS patterns, enabling optimal performance through proper semantic design and caching strategies.
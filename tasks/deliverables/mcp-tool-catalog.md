# MCP Developer Tool Catalog

**Complete Reference Guide for Advanced RAG MCP Ecosystem**

---

## Quick Reference Summary

| Tool Category | Count | Status | Primary Use Cases |
|---------------|-------|--------|-------------------|
| **RAG Retrieval Tools** | 6 | ✅ Operational | Document search, question answering, content discovery |
| **System Utility Tools** | 2 | ✅ Operational | Health monitoring, cache performance tracking |
| **External AI Services** | 16 | ✅ Phoenix MCP | Experiment tracking, dataset management, observability |
| **Vector Storage** | 4 | ✅ Qdrant MCP | Semantic memory, code snippet storage |
| **Caching Layer** | 4 | ✅ Redis MCP | High-performance data caching (546x speedup) |
| **TOTAL** | **32** | **30 Working** | Comprehensive RAG development toolkit |

---

## Core RAG Retrieval Tools (6 Tools)

### 🔍 MCP-RET-01: naive_retriever
- **Description**: Basic vector similarity search using cosine similarity
- **Use Cases**: 
  - Simple document retrieval
  - Baseline performance comparison
  - Quick content discovery
- **Input**: `{"question": "your search query"}`
- **Output**: `{"answer": "LLM response", "context_document_count": N}`
- **Performance**: ~2-3 seconds, 3-5 context documents
- **Best For**: General purpose searches, development testing

### 🎯 MCP-RET-02: bm25_retriever  
- **Description**: Keyword-based BM25 search for exact term matches
- **Use Cases**:
  - Exact keyword searches
  - Named entity retrieval
  - Technical term lookup
- **Input**: `{"question": "your search query"}`
- **Output**: `{"answer": "LLM response", "context_document_count": N}`
- **Performance**: ~2-3 seconds, optimized for keyword precision
- **Best For**: Specific terminology, proper nouns, exact phrases

### 🔄 MCP-RET-03: contextual_compression_retriever
- **Description**: Compressed context retrieval with relevance filtering
- **Use Cases**:
  - Large document processing
  - Noise reduction in results
  - Focused answer generation
- **Input**: `{"question": "your search query"}`
- **Output**: `{"answer": "LLM response", "context_document_count": N}`  
- **Performance**: ~2-4 seconds, filtered high-relevance context
- **Best For**: Complex documents, reducing information overload

### 🎭 MCP-RET-04: multi_query_retriever
- **Description**: Multiple query expansion search with diverse retrieval strategies
- **Use Cases**:
  - Comprehensive topic coverage
  - Handling ambiguous queries
  - Alternative perspective discovery
- **Input**: `{"question": "your search query"}`
- **Output**: `{"answer": "LLM response", "context_document_count": N}`
- **Performance**: ~3-4 seconds, broader context coverage
- **Best For**: Complex questions, thorough research, topic exploration

### 🎯 MCP-RET-05: ensemble_retriever
- **Description**: Hybrid search combining naive, BM25, contextual compression, and multi-query
- **Use Cases**:
  - Production-grade search
  - Balanced precision and recall
  - Maximum retrieval coverage
- **Input**: `{"question": "your search query"}`
- **Output**: `{"answer": "LLM response", "context_document_count": N}`
- **Performance**: ~3-5 seconds, highest quality results
- **Best For**: Critical searches, production applications, best possible answers

### 🧠 MCP-RET-06: semantic_retriever
- **Description**: Semantic vector search on enhanced 'johnwick_semantic' collection
- **Use Cases**:
  - Conceptual similarity search
  - Thematic content discovery
  - Meaning-based retrieval
- **Input**: `{"question": "your search query"}`
- **Output**: `{"answer": "LLM response", "context_document_count": N}`
- **Performance**: ~2-3 seconds, semantic understanding focus
- **Best For**: Conceptual queries, thematic searches, semantic understanding

---

## System Utility Tools (2 Tools)

### 🏥 MCP-UTIL-01: health_check_health_get
- **Description**: System health verification and status monitoring
- **Use Cases**:
  - System diagnostics
  - Uptime monitoring
  - Integration testing
- **Input**: No parameters (GET endpoint)
- **Output**: `{"status": "healthy", "timestamp": "ISO datetime"}`
- **Performance**: <100ms response time
- **Best For**: Health checks, monitoring dashboards, automated testing

### 📊 MCP-UTIL-02: cache_stats_cache_stats_get
- **Description**: Redis cache statistics and performance metrics
- **Use Cases**:
  - Performance monitoring
  - Cache optimization
  - System analytics
- **Input**: No parameters (GET endpoint)
- **Output**: `{"cache_stats": {"total_keys": N, "hit_rate": 0.XX, "memory_usage": "X.XMB"}}`
- **Performance**: <100ms response time
- **Best For**: Performance tuning, cache management, optimization

---

## External MCP Services (24 Tools)

### 🔬 Phoenix MCP (16 Tools) - AI Observability Platform
**Status**: ✅ Fully Operational | **Command**: `uvx @arize-ai/phoenix-mcp`

#### Dataset Management Tools (3)
- **list-datasets**: Retrieve all available datasets
- **get-dataset-examples**: Get examples from specific dataset  
- **add-dataset-examples**: Add new examples to dataset

#### Experiment Tracking Tools (2)
- **list-experiments-for-dataset**: Get experiments for dataset
- **get-experiment-by-id**: Retrieve specific experiment details

#### Project Management Tools (1)
- **list-projects**: List all Phoenix projects

#### Prompt Management Tools (10+)
- **list-prompts**: Get all available prompts
- **get-latest-prompt**: Retrieve latest prompt version
- **upsert-prompt**: Create/update prompts
- **And 7+ additional prompt versioning tools**

**Use Cases**: ML experiment tracking, prompt engineering, A/B testing, model performance analysis

### 🗄️ Qdrant MCP Semantic Memory (2 Tools) - Vector Storage
**Status**: ✅ Fully Operational | **Port**: 8003 | **Collection**: semantic-memory

- **qdrant-store**: Store contextual information with vector embeddings
  - **Input**: `{"information": "description", "metadata": {...}}`
  - **Use Cases**: Conversation insights, project decisions, learned patterns
- **qdrant-find**: Search semantic memory for relevant context
  - **Input**: `{"query": "natural language search"}`
  - **Use Cases**: Context retrieval, decision history, pattern discovery

### 📝 Qdrant MCP Code Snippets (2 Tools) - Code Storage  
**Status**: ⚠️ Initialization Issues | **Port**: 8002 | **Collection**: code-snippets

- **qdrant-store**: Store reusable code snippets (when working)
- **qdrant-find**: Search for relevant code patterns (when working)

**Known Issue**: Session initialization hangs during embedding setup

### ⚡ Redis MCP (4 Tools) - High-Performance Cache
**Status**: ✅ Fully Operational | **Performance**: 546x average speedup

- **set**: Store key-value pairs with optional TTL
  - **Input**: `{"key": "string", "value": "string", "expireSeconds": N}`
- **get**: Retrieve values by key
  - **Input**: `{"key": "string"}`  
- **list**: Find keys matching patterns
  - **Input**: `{"pattern": "glob_pattern"}`
- **delete**: Remove keys from cache
  - **Input**: `{"key": "string_or_array"}`

**Performance Results**:
- semantic_retriever: 788.6x speedup (7.024s → 0.009s)
- bm25_retriever: 720.8x speedup (4.323s → 0.006s)
- ensemble_retriever: 131.3x speedup (1.301s → 0.010s)

---

## Decision Matrix: When to Use Each Tool

### RAG Retrieval Strategy Selection

| Scenario | Recommended Tool | Rationale |
|----------|------------------|-----------|
| **Production Search** | ensemble_retriever | Best overall quality, combines all strategies |
| **Fast Development** | naive_retriever | Simple, reliable, good baseline |
| **Exact Keywords** | bm25_retriever | Optimal for named entities, technical terms |
| **Large Documents** | contextual_compression_retriever | Reduces noise, focuses on relevance |
| **Complex Questions** | multi_query_retriever | Comprehensive coverage, multiple angles |
| **Conceptual Search** | semantic_retriever | Best for meaning-based, thematic queries |

### External Service Selection

| Use Case | Service | Tools |
|----------|---------|-------|
| **ML Experiment Tracking** | Phoenix MCP | list-datasets, get-experiment-by-id |
| **Prompt Management** | Phoenix MCP | list-prompts, upsert-prompt |
| **Semantic Memory** | Qdrant MCP (Semantic) | qdrant-store, qdrant-find |
| **Performance Optimization** | Redis MCP | set, get, cache_stats |
| **System Monitoring** | Core Utilities | health_check, cache_stats |

---

## Integration Examples

### Quick Copy-Paste Patterns

#### Basic Retrieval
```bash
# Test any retrieval tool
mcp-client call naive_retriever '{"question": "What makes a good action movie?"}'
```

#### Cache Performance Check
```bash
# Check cache status
mcp-client call cache_stats_cache_stats_get '{}'

# Check system health  
mcp-client call health_check_health_get '{}'
```

#### External Service Usage
```bash
# Phoenix: List available datasets
mcp-client call list-datasets '{}'

# Qdrant: Store semantic information
mcp-client call qdrant-store '{"information": "User prefers action movies", "metadata": {"type": "preference"}}'

# Redis: Cache a value
mcp-client call set '{"key": "user:123:pref", "value": "action movies", "expireSeconds": 3600}'
```

### Error Handling Patterns
```python
# Parameter validation
correct = {"question": "search query"}     # ✅ Works
incorrect = {"query": "search query"}      # ❌ HTTP 422 error
missing = {}                               # ❌ Field required error
```

---

## Performance Benchmarks

### Response Time Expectations
- **Cached Responses**: < 100ms (Redis cache hit)
- **Basic Retrieval**: 1-3 seconds (naive, bm25, semantic)
- **Complex Retrieval**: 3-5 seconds (ensemble, multi_query)
- **Utility Tools**: < 100ms (health, cache_stats)
- **External Services**: 200ms-2s (network dependent)

### Quality Metrics
- **Answer Length**: 1000-2500 characters typically
- **Context Usage**: 3-7 documents per response
- **Cache Hit Rate**: 85%+ with Redis integration
- **Tool Success Rate**: 98%+ for operational tools

---

## Security & Authentication

### Core Tools
- **Authentication**: None required (internal FastAPI conversion)
- **Authorization**: Inherits FastAPI server permissions
- **Transport**: STDIO for Claude Desktop, HTTP for production

### External Services
- **Phoenix MCP**: No authentication required (localhost)
- **Qdrant MCP**: No authentication required (localhost)  
- **Redis MCP**: Optional authentication via REDIS_URL

---

## Troubleshooting Quick Reference

### Common Issues
1. **Tool Not Found**: Check MCP server startup and tool discovery
2. **Parameter Errors**: Use `"question"` not `"query"` for retrieval tools
3. **Timeout Errors**: External services may need restart
4. **Cache Miss**: Redis service may be down

### Service Health Checks
```bash
# Check core system
curl http://localhost:8000/health

# Check Docker services
docker ps | grep -E "(qdrant|redis|phoenix)"

# Check MCP tool discovery
mcp-client list-tools
```

---

## Validation Status

✅ **All Core Tools**: 8/8 operational (6 retrieval + 2 utility)  
✅ **Phoenix MCP**: 16/16 tools operational  
✅ **Qdrant Semantic MCP**: 2/2 tools operational  
⚠️ **Qdrant Code MCP**: 0/2 tools (initialization issues)  
✅ **Redis MCP**: 4/4 tools operational  

**Total Operational**: 30/32 tools (93.75% success rate)

---

*Generated: 2025-06-18 | Advanced RAG MCP Ecosystem v1.0*
*Target Audience: Experienced developers needing quick reference* 
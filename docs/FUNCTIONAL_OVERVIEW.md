# Advanced RAG System - Functional Overview

## 🎯 What This Project Does

**Advanced RAG** is a production-ready Retrieval Augmented Generation system that takes questions about John Wick movies and returns intelligent answers by searching through movie review data. The system offers **6 different retrieval strategies** and exposes them both as REST API endpoints and as MCP (Model Context Protocol) tools for Claude Desktop and other AI clients.

## 🔄 Core Workflow

```
User Question → API/MCP → Retrieval Strategy → Vector/Keyword Search → LLM Generation → Cached Answer
```

**Example**: "What makes John Wick movies popular?" 
→ System searches movie reviews → Finds relevant context → GPT-4.1-mini generates answer → Returns structured response

## 🛠️ Six Retrieval Strategies

### 1. **Naive Retriever** (`/invoke/naive_retriever`)
- **Function**: Basic vector similarity search
- **Implementation**: Direct Qdrant vector store lookup
- **Use Case**: Fast, straightforward semantic matching
- **Code Pattern**: `BASELINE_VECTORSTORE.as_retriever(k=10)`

### 2. **BM25 Retriever** (`/invoke/bm25_retriever`) 
- **Function**: Keyword-based search (like traditional search engines)
- **Implementation**: TF-IDF scoring with BM25 algorithm
- **Use Case**: Exact keyword matching, complementary to semantic search
- **Code Pattern**: `BM25Retriever.from_documents(DOCUMENTS)`

### 3. **Contextual Compression** (`/invoke/contextual_compression_retriever`)
- **Function**: Retrieves documents then compresses/reranks with Cohere
- **Implementation**: Naive retriever + Cohere reranking model
- **Use Case**: Higher precision results through AI-powered filtering
- **Code Pattern**: `ContextualCompressionRetriever(base_compressor=CohereRerank, base_retriever=naive)`

### 4. **Multi-Query** (`/invoke/multi_query_retriever`)
- **Function**: Generates multiple search queries from one question
- **Implementation**: LLM creates query variations, searches with each
- **Use Case**: Handles ambiguous or complex questions better
- **Code Pattern**: `MultiQueryRetriever.from_llm(retriever=naive, llm=CHAT_MODEL)`

### 5. **Ensemble** (`/invoke/ensemble_retriever`)
- **Function**: Combines multiple retrieval methods with weighted averaging
- **Implementation**: Merges results from BM25, naive, and other retrievers
- **Use Case**: Best overall performance by leveraging multiple approaches
- **Code Pattern**: `EnsembleRetriever(retrievers=[bm25, naive, ...], weights=[0.33, 0.33, ...])`

### 6. **Semantic** (`/invoke/semantic_retriever`)
- **Function**: Advanced semantic chunking with improved embeddings
- **Implementation**: Specialized vector store with semantic text splitting
- **Use Case**: Better understanding of document meaning and context
- **Code Pattern**: `SEMANTIC_VECTORSTORE.as_retriever(k=10)`

## 🔍 MCP Development & Validation Tools

The system provides comprehensive development tools to validate the dual-interface architecture and test MCP integrations interactively. These tools are essential for ensuring the **zero-duplication architecture** works correctly across FastAPI, MCP Tools, and MCP Resources.

### Why These Tools Matter

The Advanced RAG system implements a **zero-duplication pattern** where:
- FastAPI endpoints are defined once in `src/api/app.py` 
- `FastMCP.from_fastapi()` automatically converts them to MCP tools
- MCP Resources provide the same processing with different output formats

**Validation is critical** because this architecture eliminates traditional testing boundaries between HTTP and MCP interfaces.

### FastMCP Development Inspector

Interactive web UI for testing MCP servers during development:

```bash
# Inspect MCP Tools Server (Command Pattern)
DANGEROUSLY_OMIT_AUTH=true fastmcp dev src/mcp/server.py

# Inspect MCP Resources Server (Query Pattern) 
DANGEROUSLY_OMIT_AUTH=true fastmcp dev src/mcp/resources.py
```

**What This Provides**:
- **Interactive Testing**: Web UI to call tools and read resources
- **Schema Validation**: Verify tool schemas and resource URI patterns
- **Real-time Debugging**: Test changes without full client setup
- **CQRS Validation**: Compare Tools (commands) vs Resources (queries) behavior

**Development Workflow**:
1. Start inspector: `fastmcp dev src/mcp/server.py`
2. Open web UI (usually `http://localhost:8080`)
3. Test all 6 retrieval strategies interactively
4. Validate tools return expected formats
5. Verify error handling and edge cases

### Official MCP Inspector for External Integration

Test integration with external MCP ecosystem tools:

```bash
# Test Phoenix MCP Integration
DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector npx @arizeai/phoenix-mcp@latest --baseUrl http://localhost:6006
```

**What This Validates**:
- **Phoenix Observability**: Test integration with Phoenix telemetry platform
- **External MCP Tools**: Validate compatibility with broader MCP ecosystem
- **Cross-System Tracing**: Ensure telemetry works across MCP boundaries
- **Production Readiness**: Test real-world MCP client integrations

**Phoenix Integration Features**:
- **Telemetry Data Access**: Query Phoenix traces via MCP
- **Experiment Management**: Access datasets and experiment results
- **Performance Analysis**: Retrieve performance metrics through MCP interface
- **AI Agent Observability**: Monitor RAG system behavior from external tools

### Security Note: Development Authentication

The `DANGEROUSLY_OMIT_AUTH=true` flag **bypasses authentication** for development convenience:

- ✅ **Safe for local development**: Testing on localhost only
- ❌ **Never use in production**: Would expose MCP servers publicly
- 🔒 **Production deployment**: Remove flag and configure proper authentication
- 🛡️ **Network isolation**: Development tools should never be exposed externally

### Architecture Validation Workflow

These tools validate the core architectural claims:

```bash
# 1. Validate FastAPI→MCP conversion
fastmcp dev src/mcp/server.py
# Test: All 6 FastAPI endpoints appear as MCP tools
# Verify: Same processing logic, different response format

# 2. Validate CQRS Resource pattern  
fastmcp dev src/mcp/resources.py
# Test: All 6 strategies accessible as resources
# Verify: Same LangChain processing, markdown output format

# 3. Validate external integration
npx @modelcontextprotocol/inspector npx @arizeai/phoenix-mcp@latest --baseUrl http://localhost:6006
# Test: Phoenix telemetry accessible via MCP
# Verify: Cross-system observability works
```

### Integration with System Testing

These inspector tools complement the existing test suite:

**Automated Tests** (`pytest tests/ -v`):
- Unit tests for individual components
- Integration tests for MCP server functionality
- CQRS pattern validation tests

**Interactive Validation** (MCP Inspectors):
- Manual exploration of MCP interfaces
- Edge case testing with custom inputs
- Real-time debugging during development
- Visual verification of tool/resource schemas

**Performance Benchmarking** (`scripts/evaluation/`):
- Quantitative performance analysis
- Cache effectiveness measurement
- Cross-interface latency comparison

### Best Practices for MCP Development

1. **Start with Inspector**: Always test new MCP functionality with inspector first
2. **Validate Conversion**: Ensure FastAPI changes properly convert to MCP tools
3. **Test Edge Cases**: Use inspector to test invalid inputs and error handling
4. **Monitor Integration**: Use Phoenix MCP to verify telemetry integration
5. **Document Changes**: Update MCP schemas when adding new endpoints

### Running Multiple Inspectors Simultaneously

For comprehensive validation of the dual-interface architecture, run all three inspectors simultaneously using different ports:

#### Port Allocation Strategy
```bash
# Avoid conflicts with main application ports:
# FastAPI: 8000, Qdrant: 6333, Redis: 6379, Phoenix: 6006

FastMCP Tools Inspector:     UI=6270, Proxy=6271
FastMCP Resources Inspector: UI=6272, Proxy=6273  
Official MCP Inspector:      UI=6274, Proxy=6277 (defaults)
```

#### Multi-Terminal Setup
```bash
# Terminal 1: FastMCP Tools Server Inspector
DANGEROUSLY_OMIT_AUTH=true fastmcp dev src/mcp/server.py --ui-port 6270 --server-port 6271

# Terminal 2: FastMCP Resources Server Inspector  
DANGEROUSLY_OMIT_AUTH=true fastmcp dev src/mcp/resources.py --ui-port 6272 --server-port 6273

# Terminal 3: Official MCP Inspector (Phoenix Integration)
DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector npx @arizeai/phoenix-mcp@latest --baseUrl http://localhost:6006
```

#### Inspector Access URLs
| Inspector | Purpose | Access URL | Features |
|-----------|---------|------------|----------|
| **Tools Inspector** | Test MCP Tools (Command Pattern) | http://localhost:6270 | 6 retrieval tools, schema validation |
| **Resources Inspector** | Test MCP Resources (Query Pattern) | http://localhost:6272 | 7 resource URIs, markdown output |
| **Phoenix Inspector** | External MCP Integration | http://localhost:6274 | Telemetry data, experiment management |

#### Comprehensive Validation Workflow
1. **Tools Validation** (Port 6270): Test all 6 retrieval strategies as MCP tools
2. **Resources Validation** (Port 6272): Test same strategies as resource URIs  
3. **Integration Validation** (Port 6274): Test Phoenix telemetry and external MCP tools
4. **Cross-Interface Comparison**: Verify identical processing across interfaces
5. **Performance Analysis**: Compare latency and caching behavior

#### Troubleshooting Multi-Inspector Setup
```bash
# Check port availability
netstat -tulpn | grep -E ":(6270|6271|6272|6273|6274|6277)"

# Kill existing inspector processes if needed
pkill -f "fastmcp dev"
pkill -f "@modelcontextprotocol/inspector"

# Verify all services are running before starting inspectors
docker compose ps && curl http://localhost:8000/health
```

## 🔌 Multi-Interface Architecture

The system provides **multiple interfaces** for different use cases, all built on a unified processing foundation:

### 1. FastAPI Layer (Production HTTP API)
```python
@app.post("/invoke/semantic_retriever")
async def semantic_endpoint(request: QuestionRequest):
    # Redis caching + Phoenix tracing + full RAG processing
    result = await invoke_chain_logic(SEMANTIC_CHAIN, request.question, "Semantic")
    return AnswerResponse(answer=result, context_document_count=N)
```

### 2. MCP Tools Server (FastMCP Conversion)
```python
# Unified FastMCP foundation - same processing as FastAPI
mcp = FastMCP.from_fastapi(app=app)
# Automatically converts all FastAPI endpoints to MCP tools
# Claude Desktop can now call: semantic_retriever(question="...")
# Same LLM processing as FastAPI, different response format
```

### 3. MCP Resources Server (Enhanced FastMCP)
```python
# Built on same FastMCP instance with additional resource handlers
mcp = FastMCP.from_fastapi(app=app)  # Same foundation

@mcp.resource("retriever://semantic_retriever/{query}")
async def get_semantic_resource(query: str) -> str:
    # Same LangChain processing as Tools/FastAPI
    chain = get_chain_by_method("semantic")
    result = await chain.ainvoke({"question": query})
    # Return same results formatted as LLM-friendly markdown
    return format_rag_content(result, "semantic", query, "semantic_retriever")
```

### 4. Alternate Vector Access (Qdrant MCP)
```python
# Direct vector database queries (separate from RAG pipeline)
# For advanced vector operations and raw data access
# Bypasses the LangChain/LLM pipeline entirely
```

### Interface Selection Guide

| Interface | Processing | Output Format | Best For | Performance |
|-----------|------------|---------------|----------|-------------|
| **FastAPI HTTP** | Full RAG pipeline | JSON response | Production web apps | Standard |
| **MCP Tools** | Same RAG pipeline | MCP tool response | Claude Desktop integration | Standard |
| **MCP Resources** | Same RAG pipeline | Markdown documents | LLM-friendly data format | Standard |
| **Qdrant MCP** | Direct vector queries | Raw vector data | Advanced vector operations | Fastest |

### Interface Pattern Benefits

**Unified RAG Processing** (FastAPI, MCP Tools, MCP Resources): 
- Same LangChain LCEL chains
- Same LLM synthesis with GPT-4.1-mini
- Same caching and Phoenix tracing
- Different output formats for different consumption patterns

**Direct Vector Access** (Qdrant MCP):
- Bypasses RAG pipeline entirely
- Raw vector similarity searches
- Advanced vector database operations
- Fastest for simple vector queries

### Resource URI Patterns
```bash
# 7 available resources (6 retrievers + 1 health)
retriever://naive_retriever/{query}
retriever://bm25_retriever/{query}
retriever://semantic_retriever/{query}
retriever://contextual_compression_retriever/{query}
retriever://multi_query_retriever/{query}
retriever://ensemble_retriever/{query}
system://health
```

## ⚡ Smart Caching & Performance

### Redis-Powered Caching
- **Cache Key**: MD5 hash of `{endpoint}:{question_data}`
- **TTL**: Configurable expiration (default settings-based)
- **Hit Rate**: Logged with `✅ Cache hit` messages
- **Performance**: Eliminates redundant LLM calls for repeated questions

### Phoenix Telemetry Integration
- **Auto-instrumentation**: All LangChain operations traced
- **Custom Spans**: FastAPI endpoints and MCP tool calls
- **Observability**: Real-time performance monitoring at `localhost:6006`
- **Correlation**: Unified project names link FastAPI and MCP traces

## 🧠 LangChain LCEL Implementation

### Chain Architecture
```python
# Example: Semantic Retrieval Chain
chain = (
    RunnablePassthrough.assign(
        context=semantic_retriever | format_docs
    )
    | prompt_template
    | ChatOpenAI(model="gpt-4.1-mini")  # Pinned version
    | StrOutputParser()
)
```

### Immutable Model Standards
- **LLM**: `gpt-4.1-mini` (pinned for reproducibility)
- **Embeddings**: `text-embedding-3-small` (pinned for consistency)
- **Configuration**: Environment-based with Pydantic validation

## 📊 Data Pipeline

### Document Processing
1. **Source**: CSV file with John Wick movie reviews
2. **Ingestion**: `scripts/ingestion/csv_ingestion_pipeline.py`
3. **Chunking**: Multiple strategies (recursive, semantic)
4. **Storage**: Dual Qdrant collections (baseline + semantic)
5. **Indexing**: Both vector embeddings and BM25 keyword indices

### Vector Store Architecture
- **Baseline Collection**: Standard recursive text splitting
- **Semantic Collection**: Advanced semantic chunking
- **BM25 Index**: In-memory keyword search structure
- **Redis Cache**: Query result caching layer

## 🔄 Request Flow Examples

### Unified RAG Processing Flow (FastAPI, MCP Tools, MCP Resources)
```
1. User asks: "Are John Wick movies worth watching?"

2. Interface receives request (HTTP/MCP Tools/MCP Resources)
   ↓
3. Check Redis cache (FastAPI/Tools) or skip cache (Resources)
   ↓
4. Route to selected retrieval strategy
   ↓
5. Strategy searches relevant data:
   - Naive: Vector similarity in Qdrant
   - BM25: Keyword matching
   - Ensemble: Combines both + weights results
   ↓
6. Retrieved documents fed to LangChain LCEL chain
   ↓
7. GPT-4.1-mini generates contextual answer
   ↓
8. Response cached (FastAPI/Tools) or formatted (Resources)
   ↓
9. Return in appropriate format:
   - FastAPI: JSON {answer: "...", context_document_count: 5}
   - MCP Tools: MCP tool response
   - MCP Resources: Structured Markdown
```

### Alternate Vector Access Flow (Qdrant MCP)
```
1. User/Agent requests: "Find vectors similar to this embedding"

2. Qdrant MCP receives request
   ↓
3. Direct vector database query (bypasses RAG entirely)
   ↓
4. Qdrant similarity search
   ↓
5. Return raw vector results, embeddings, or similarity scores
   Performance: Fastest (no LLM processing)
```

### Processing Comparison
| Interface | RAG Pipeline | Cache | LLM | Output Format |
|-----------|--------------|-------|-----|---------------|
| **FastAPI** | ✅ Full | ✅ Redis | ✅ GPT-4.1-mini | JSON response |
| **MCP Tools** | ✅ Full | ✅ Redis | ✅ GPT-4.1-mini | MCP tool response |
| **MCP Resources** | ✅ Full | ❌ No cache | ✅ GPT-4.1-mini | Markdown documents |
| **Qdrant MCP** | ❌ Bypassed | ❌ No cache | ❌ No LLM | Raw vector data |

## 🐳 Infrastructure Components

### Docker Orchestration
- **Qdrant**: Vector database (`localhost:6333`)
- **Redis**: Caching layer (`localhost:6379`)
- **Phoenix**: Telemetry dashboard (`localhost:6006`)
- **Application**: FastAPI server (`localhost:8000`)

### Development Workflow
```bash
# Start infrastructure
docker-compose up -d

# Ingest data
python scripts/ingestion/csv_ingestion_pipeline.py

# Start FastAPI server
python run.py

# Start MCP server
python src/mcp/server.py
```

## 🎭 Practical Usage Scenarios

### As HTTP API
```bash
curl -X POST "http://localhost:8000/invoke/ensemble_retriever" \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the best John Wick action scenes?"}'
```

### As MCP Tools (Claude Desktop)
```
User: "Use the ensemble retriever to find information about John Wick's fighting style"
Claude: *calls ensemble_retriever tool* → Returns comprehensive analysis
```

### As MCP Resources (Claude Code CLI)
```bash
# Start MCP Resources server
python src/mcp/resources.py

# Use via Claude Code CLI for LLM-friendly data format
# Claude automatically discovers and uses available resources
```

**Claude Code CLI Usage**:
```
User: "Get semantic retrieval data for John Wick fighting techniques"
Claude: *reads retriever://semantic_retriever/John Wick fighting techniques*
       → Returns same RAG results formatted as structured Markdown
```

**Manual Resource Access** (development/testing):
```bash
# Test resource directly
python tests/integration/test_cqrs_resources.py

# Available resource patterns:
# retriever://semantic_retriever/{your_query}
# retriever://ensemble_retriever/{your_query}  
# retriever://naive_retriever/{your_query}
# system://health
```

### As Qdrant MCP (Direct Vector Access)
```bash
# Alternate path: Direct vector database queries
# Bypasses RAG pipeline for raw vector operations
# Use for advanced vector similarity searches, embeddings analysis
```

**Qdrant MCP Usage**:
```
User: "Find similar vectors to this embedding"
Claude: *queries Qdrant directly via qdrant-code-snippets or qdrant-semantic-memory*
       → Returns raw vector similarity results without LLM processing
```

### Performance Comparison
```bash
# Benchmark all strategies
python scripts/evaluation/retrieval_method_comparison.py
# View results in Phoenix dashboard at localhost:6006
```

## 🔧 Key Technical Patterns

### Factory Pattern (Retrievers)
```python
def create_retriever(retrieval_type: str):
    retriever_map = {
        "naive": get_naive_retriever,
        "bm25": get_bm25_retriever,
        "ensemble": get_ensemble_retriever,
        # ...
    }
    return retriever_map[retrieval_type]()
```

### Async Context Management
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize chains, connect Redis
    await redis_client.connect()
    yield
    # Shutdown: Cleanup connections
    await redis_client.disconnect()
```

### Error Resilience
- **Graceful Degradation**: Strategies that fail return None, system continues
- **Chain Validation**: Startup checks ensure all chains are properly initialized
- **Cache Resilience**: Cache failures don't break core functionality

---

**In Summary**: This system takes the complexity of multiple retrieval strategies, LLM integration, and AI client protocols, then presents it as simple question-answering tools that work seamlessly across different interfaces (HTTP API or MCP clients like Claude Desktop). 
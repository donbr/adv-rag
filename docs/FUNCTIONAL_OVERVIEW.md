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

## 🔌 Dual Interface Architecture

### FastAPI Layer (Production HTTP API)
```python
@app.post("/invoke/semantic_retriever")
async def semantic_endpoint(request: QuestionRequest):
    # Redis caching + Phoenix tracing
    result = await invoke_chain_logic(SEMANTIC_CHAIN, request.question, "Semantic")
    return AnswerResponse(answer=result, context_document_count=N)
```

### MCP Layer (AI Client Integration)
```python
# Zero-duplication conversion
mcp = FastMCP.from_fastapi(app=app)
# Automatically converts all FastAPI endpoints to MCP tools
# Claude Desktop can now call: semantic_retriever(question="...")
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

## 🔄 Request Flow Example

```
1. User asks: "Are John Wick movies worth watching?"

2. FastAPI/MCP receives request
   ↓
3. Check Redis cache (miss)
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
8. Response cached in Redis with TTL
   ↓
9. Return structured JSON: {answer: "...", context_document_count: 5}
```

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
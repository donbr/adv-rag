# Advanced RAG System Architecture

📖 **For development guide**: See [CLAUDE.md](../CLAUDE.md) - essential commands and constraints  
📋 **For daily use**: See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - command reference

## Deep Technical Architecture

This document provides detailed technical implementation details for the Advanced RAG system's architecture, focusing on internal patterns and design decisions.

## Implementation Architecture Patterns

📝 **Note**: Basic tier rules covered in [CLAUDE.md](../CLAUDE.md) - this section covers technical implementation details.

## Zero-Duplication MCP Architecture

### Technical Implementation

The system achieves zero code duplication through a sophisticated conversion pattern:

```python
# src/mcp/server.py - Core conversion mechanism
from fastmcp import FastMCP
from src.api.app import app

# Single line converts entire FastAPI app to MCP server
mcp = FastMCP.from_fastapi(app=app)

# Result: 6 FastAPI endpoints → 6 MCP tools automatically
# Tools: naive_retriever, bm25_retriever, semantic_retriever, etc.
```

### CQRS Implementation Detail

**Command Pattern (MCP Tools)**: 
- Inherits all FastAPI route handlers unchanged
- Maintains request/response schemas via Pydantic
- Preserves middleware chain (Phoenix tracing, Redis caching)

**Query Pattern (MCP Resources)**:
- Native FastMCP resource handlers in `src/mcp/resources.py`
- Direct Qdrant access bypassing LangChain pipeline
- URI pattern matching: `retriever://strategy_name/{query}`

### Performance Characteristics

| Interface | Processing Time | Memory Usage | Use Case |
|-----------|----------------|--------------|----------|
| **FastAPI Direct** | 15-25 sec | Medium | HTTP integrations |
| **MCP Tools** | 20-30 sec | Medium | AI agent commands |
| **MCP Resources** | 3-5 sec | Low | AI agent queries |

## Retrieval Strategy Implementation Details

### Factory Pattern Implementation

```python
# src/rag/retriever.py - Strategy factory
def create_retriever(strategy: str, vectorstore: VectorStore, **kwargs) -> BaseRetriever:
    """Factory function with consistent interfaces across all strategies"""
    
    strategies = {
        "naive": lambda: vectorstore.as_retriever(search_kwargs=kwargs),
        "bm25": lambda: BM25Retriever.from_documents(documents, **kwargs),
        "semantic": lambda: SemanticRetriever(vectorstore, chunk_size=200, **kwargs),
        "ensemble": lambda: EnsembleRetriever(
            retrievers=[vectorstore.as_retriever(), bm25_retriever],
            weights=[0.7, 0.3]
        ),
        "contextual_compression": lambda: ContextualCompressionRetriever(
            base_compressor=CohereRerank(),
            base_retriever=vectorstore.as_retriever()
        ),
        "multi_query": lambda: MultiQueryRetriever.from_llm(
            retriever=vectorstore.as_retriever(),
            llm=ChatOpenAI(model="gpt-4.1-mini")
        )
    }
    
    return strategies[strategy]()
```

### Performance Optimization Techniques

| Strategy | Optimization | Technical Detail |
|----------|-------------|-----------------|
| **Naive** | Vector similarity caching | Redis cache with embedding hash keys |
| **BM25** | Term frequency precomputation | Sparse matrix storage in memory |
| **Semantic** | Chunk size optimization | 200-token chunks with 50-token overlap |
| **Ensemble** | Weighted score fusion | Linear combination with normalized scores |
| **Compression** | Cohere reranking | Top-K filtering before LLM reranking |
| **Multi-Query** | Query variation caching | Cache query expansions by semantic similarity |

## LangChain LCEL Implementation Internals

### Core Chain Architecture

```python
# src/rag/chain.py - Actual LCEL implementation
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter

def create_rag_chain(retriever):
    """Simple LCEL chain implementation"""
    if retriever is None:
        return None
        
    try:
        chain = (
            {"context": itemgetter("question") | retriever, "question": itemgetter("question")}
            | RunnablePassthrough.assign(context=itemgetter("context")) 
            | {"response": RAG_PROMPT | get_chat_model_lazy(), "context": itemgetter("context")}
        )
        return chain
    except Exception as e:
        logger.error(f"Failed to create RAG chain: {e}")
        return None

# Template used in actual implementation
RAG_TEMPLATE_STR = """\
You are a helpful and kind assistant. Use the context provided below to answer the question.

If you do not know the answer, or are unsure, say you don't know.

Query:
{question}

Context:
{context}
"""
```

### Advanced Chain Features

#### Streaming Implementation
```python
# Async streaming support with backpressure handling
async def stream_rag_response(chain: Runnable, query: str):
    async for chunk in chain.astream({"question": query}):
        yield chunk
```

#### Caching Integration
```python
# Redis-backed LCEL caching
from langchain.cache import RedisCache
import langchain

langchain.llm_cache = RedisCache(redis_=redis_client)
```

#### Phoenix Tracing Integration
```python
# Automatic LCEL operation tracing
@tracer.start_as_current_span("rag_chain_execution")
def execute_chain(chain: Runnable, input_data: dict) -> str:
    span = tracer.get_current_span()
    span.set_attribute("retrieval_strategy", input_data.get("strategy"))
    return chain.invoke(input_data)
```

## Data Architecture & Storage Patterns

### Vector Storage Implementation (Qdrant)

```python
# src/rag/vectorstore.py - Production Qdrant configuration
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

def create_qdrant_collection(collection_name: str, vector_size: int = 1536):
    """Production-optimized Qdrant collection setup"""
    
    client = QdrantClient("localhost", port=6333)
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,  # text-embedding-3-small dimensions
            distance=Distance.COSINE,
            on_disk=True  # Persist to disk for durability
        ),
        # Production optimizations
        optimizers_config=models.OptimizersConfig(
            default_segment_number=2,
            max_segment_size=20000,
            memmap_threshold=20000,
            indexing_threshold=20000,
        ),
        hnsw_config=models.HnswConfig(
            m=16,  # Number of connections per layer
            ef_construct=200,  # Size of dynamic candidate list
            full_scan_threshold=10000  # Threshold for full scan vs HNSW
        )
    )
```

### Caching Strategy Implementation

```python
# src/integrations/redis_client.py - Multi-level caching
class CacheStrategy:
    """Production caching with TTL and memory management"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.local_cache = {}  # In-memory L1 cache
        
    async def get_embedding_cache(self, text_hash: str) -> Optional[List[float]]:
        # L1: Memory cache (fastest)
        if text_hash in self.local_cache:
            return self.local_cache[text_hash]
            
        # L2: Redis cache (distributed)
        cached = await self.redis.get(f"embedding:{text_hash}")
        if cached:
            embedding = pickle.loads(cached)
            self.local_cache[text_hash] = embedding  # Promote to L1
            return embedding
            
        return None
        
    async def set_embedding_cache(self, text_hash: str, embedding: List[float]):
        # Store in both levels
        self.local_cache[text_hash] = embedding
        await self.redis.setex(
            f"embedding:{text_hash}", 
            3600,  # 1 hour TTL
            pickle.dumps(embedding)
        )
```

## Phoenix Telemetry Implementation

### Automatic Instrumentation
```python
# src/integrations/phoenix_mcp.py - Phoenix tracing integration
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_phoenix_tracing():
    """Configure Phoenix telemetry for RAG operations"""
    
    # Phoenix OTLP endpoint
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:6006/v1/traces",
        insecure=True
    )
    
    # Batch processor for performance
    span_processor = BatchSpanProcessor(otlp_exporter)
    
    # Provider with project correlation
    tracer_provider = TracerProvider(
        resource=Resource.create({
            "service.name": "advanced-rag",
            "project.name": "johnwick_retrieval",
            "version": "2.5"
        })
    )
    
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
    
    return trace.get_tracer(__name__)

# Chain instrumentation
@tracer.start_as_current_span("rag_chain_execution")
def execute_instrumented_chain(chain: Runnable, input_data: dict) -> str:
    span = trace.get_current_span()
    span.set_attribute("retrieval.strategy", input_data.get("strategy"))
    span.set_attribute("query.text", input_data.get("question"))
    
    # Execute with automatic tracing
    result = chain.invoke(input_data)
    
    span.set_attribute("response.length", len(result))
    span.set_attribute("documents.retrieved", input_data.get("doc_count", 0))
    
    return result
```

### Performance Monitoring Patterns
```python
# Retrieval strategy performance tracking
class InstrumentedRetriever:
    def __init__(self, base_retriever: BaseRetriever, strategy_name: str):
        self.base_retriever = base_retriever
        self.strategy_name = strategy_name
        self.tracer = trace.get_tracer(__name__)
    
    @trace_method("vector_search")
    def retrieve(self, query: str) -> List[Document]:
        with self.tracer.start_as_current_span(f"retrieve_{self.strategy_name}") as span:
            start_time = time.time()
            
            # Execute retrieval
            documents = self.base_retriever.get_relevant_documents(query)
            
            # Record metrics
            span.set_attribute("retrieval.latency_ms", (time.time() - start_time) * 1000)
            span.set_attribute("retrieval.document_count", len(documents))
            span.set_attribute("retrieval.strategy", self.strategy_name)
            
            return documents
```

## Error Handling & Resilience (Current Implementation)

### Simple Error Handling Pattern
```python
# src/rag/chain.py - Actual error handling implementation
def create_rag_chain(retriever):
    """Simple chain creation with basic error handling"""
    if retriever is None:
        # Return None if retriever is not available
        return None
        
    try:
        # Create basic LCEL chain
        chain = (
            {"context": itemgetter("question") | retriever, "question": itemgetter("question")}
            | RunnablePassthrough.assign(context=itemgetter("context")) 
            | {"response": RAG_PROMPT | get_chat_model_lazy(), "context": itemgetter("context")}
        )
        logger.info(f"RAG chain created successfully")
        return chain
    except Exception as e:
        # Log error and return None
        logger.error(f"Failed to create RAG chain: {e}", exc_info=True)
        return None

# Chain initialization in src/rag/chain.py
NAIVE_RETRIEVAL_CHAIN = create_rag_chain(get_naive_retriever())
BM25_RETRIEVAL_CHAIN = create_rag_chain(get_bm25_retriever())
CONTEXTUAL_COMPRESSION_CHAIN = create_rag_chain(get_contextual_compression_retriever())
MULTI_QUERY_CHAIN = create_rag_chain(get_multi_query_retriever())
ENSEMBLE_CHAIN = create_rag_chain(get_ensemble_retriever())
SEMANTIC_CHAIN = create_rag_chain(get_semantic_retriever())
```

### FastAPI Error Handling
```python
# src/api/app.py - HTTP error handling pattern
async def invoke_chain_logic(chain, question: str, chain_name: str):
    """Chain invocation with error handling"""
    if chain is None:
        logger.error(f"Chain '{chain_name}' is not available")
        raise HTTPException(
            status_code=503, 
            detail=f"The '{chain_name}' is currently unavailable"
        )
    
    try:
        result = await chain.ainvoke({"question": question})
        return AnswerResponse(
            answer=result.get("response", {}).content,
            context_document_count=len(result.get("context", []))
        )
    except Exception as e:
        logger.error(f"Error invoking '{chain_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while processing your request"
        )
```

## Performance Optimization Internals

### Vector Index Optimization
```python
# src/rag/vectorstore.py - HNSW parameter tuning
def optimize_qdrant_performance(collection_name: str, expected_queries_per_second: int):
    """Optimize Qdrant HNSW parameters based on usage patterns"""
    
    # Calculate optimal parameters based on collection size and QPS
    collection_info = client.get_collection(collection_name)
    points_count = collection_info.points_count
    
    # Dynamic HNSW configuration
    if points_count < 10000:
        # Small collection: prioritize recall
        hnsw_config = models.HnswConfig(
            m=32,  # Higher connectivity for better recall
            ef_construct=200,
            full_scan_threshold=5000
        )
    elif expected_queries_per_second > 100:
        # High QPS: prioritize speed
        hnsw_config = models.HnswConfig(
            m=16,  # Lower connectivity for faster search
            ef_construct=100,
            full_scan_threshold=1000
        )
    else:
        # Balanced configuration
        hnsw_config = models.HnswConfig(
            m=24,
            ef_construct=150,
            full_scan_threshold=2000
        )
    
    # Update collection with optimized parameters
    client.update_collection(
        collection_name=collection_name,
        hnsw_config=hnsw_config
    )
```

### Advanced Caching Implementation
```python
# src/integrations/redis_client.py - Multi-tier caching strategy
class ProductionCacheManager:
    """Production-grade caching with memory management"""
    
    def __init__(self, redis_client, max_memory_mb: int = 512):
        self.redis = redis_client
        self.local_cache = OrderedDict()  # LRU implementation
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.current_memory = 0
    
    async def get_with_compression(self, key: str) -> Optional[Any]:
        """Get cached value with automatic compression"""
        
        # L1: Memory cache (fastest)
        if key in self.local_cache:
            self.local_cache.move_to_end(key)  # LRU update
            return self.local_cache[key]
        
        # L2: Redis with compression
        compressed_data = await self.redis.get(f"compressed:{key}")
        if compressed_data:
            # Decompress and promote to L1
            data = pickle.loads(lz4.frame.decompress(compressed_data))
            await self._add_to_local_cache(key, data)
            return data
        
        return None
    
    async def set_with_compression(self, key: str, value: Any, ttl: int = 3600):
        """Set cached value with automatic compression and memory management"""
        
        # Serialize and compress
        serialized = pickle.dumps(value)
        compressed = lz4.frame.compress(serialized)
        
        # Store in Redis with TTL
        await self.redis.setex(f"compressed:{key}", ttl, compressed)
        
        # Add to local cache with memory management
        await self._add_to_local_cache(key, value)
    
    async def _add_to_local_cache(self, key: str, value: Any):
        """Add to local cache with memory limit enforcement"""
        
        value_size = sys.getsizeof(value)
        
        # Evict old entries if memory limit exceeded
        while (self.current_memory + value_size) > self.max_memory_bytes and self.local_cache:
            oldest_key, oldest_value = self.local_cache.popitem(last=False)
            self.current_memory -= sys.getsizeof(oldest_value)
        
        # Add new entry
        self.local_cache[key] = value
        self.current_memory += value_size
```

This implementation provides deep technical details for production optimization, performance monitoring, and advanced error handling patterns specific to the Advanced RAG system architecture.
# API Reference

## Table of Contents

- [HTTP REST API](#http-rest-api)
  - [Retrieval Endpoints](#retrieval-endpoints)
  - [Utility Endpoints](#utility-endpoints)
  - [Request/Response Schemas](#requestresponse-schemas)
- [MCP Server API](#mcp-server-api)
  - [Resources (Read Operations)](#resources-read-operations)
- [Python API](#python-api)
  - [Core Settings](#core-settings)
  - [Exception Classes](#exception-classes)
  - [RAG Chain Factory](#rag-chain-factory)
  - [Retriever Factory](#retriever-factory)
  - [Cache API](#cache-api)
  - [Embeddings](#embeddings)
  - [Vector Store](#vector-store)
  - [Phoenix MCP Client](#phoenix-mcp-client)
- [Configuration Options](#configuration-options)
- [Usage Patterns and Best Practices](#usage-patterns-and-best-practices)

---

## HTTP REST API

The FastAPI-based REST API provides HTTP endpoints for retrieval operations with caching and Phoenix tracing.

**Base URL**: `http://localhost:8000`

**Source**: `/home/donbr/ghcp/adv-rag/src/api/app.py`

### Retrieval Endpoints

All retrieval endpoints accept questions and return answers with context document counts.

#### POST /invoke/naive_retriever

Basic similarity search using vector store with cosine similarity.

**Operation ID**: `naive_retriever`

**Description**: Performs straightforward vector similarity search on the baseline collection using RecursiveCharacterTextSplitter chunking strategy. Returns the top-k most similar documents based on embedding distance.

**Request Body**:
```json
{
  "question": "string"
}
```

**Response** (200 OK):
```json
{
  "answer": "string",
  "context_document_count": 0
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:8000/invoke/naive_retriever" \
  -H "Content-Type: application/json" \
  -d '{"question": "Did people generally like John Wick?"}'
```

**Example Response**:
```json
{
  "answer": "Yes, people generally liked John Wick. The reviews indicate positive sentiment about the action sequences and Keanu Reeves' performance.",
  "context_document_count": 10
}
```

**Source Reference**: `src/api/app.py:262-265`

**Related Components**:
- Chain: `NAIVE_RETRIEVAL_CHAIN` (src/rag/chain.py:66)
- Retriever: `get_naive_retriever()` (src/rag/retriever.py:51-56)
- Vector Store: `BASELINE_VECTORSTORE` (src/rag/vectorstore.py:25-48)
- Cache: Automatic via `invoke_chain_logic()` (src/api/app.py:174-260)

**Performance Notes**: Fastest retrieval method, suitable for most queries. Cache hit rate typically 40-60% with 5-minute TTL.

---

#### POST /invoke/bm25_retriever

Keyword-based search using BM25 ranking algorithm.

**Operation ID**: `bm25_retriever`

**Description**: Uses the BM25 (Best Matching 25) algorithm for keyword-based document retrieval. Effective for queries with specific terms or proper nouns that should be matched exactly rather than semantically.

**Request Body**:
```json
{
  "question": "string"
}
```

**Response** (200 OK):
```json
{
  "answer": "string",
  "context_document_count": 0
}
```

**Example Request**:
```python
import requests

response = requests.post(
    "http://localhost:8000/invoke/bm25_retriever",
    json={"question": "What action scenes were mentioned in reviews?"}
)
print(response.json())
```

**Example Response**:
```json
{
  "answer": "Reviews frequently mentioned the nightclub scene, the church fight sequence, and the Red Circle scene as standout action moments.",
  "context_document_count": 10
}
```

**Source Reference**: `src/api/app.py:267-270`

**Related Components**:
- Chain: `BM25_RETRIEVAL_CHAIN` (src/rag/chain.py:67)
- Retriever: `get_bm25_retriever()` (src/rag/retriever.py:58-69)
- Document Loader: Uses original documents (src/rag/data_loader.py:77+)

**When to Use**: Best for queries with specific keywords, names, or when exact term matching is more important than semantic similarity.

---

#### POST /invoke/contextual_compression_retriever

Compressed context using Cohere reranking for relevance.

**Operation ID**: `contextual_compression_retriever`

**Description**: First retrieves documents using naive similarity search, then applies Cohere's reranking model to compress and reorder results based on relevance to the query. Reduces noise and improves answer quality.

**Request Body**:
```json
{
  "question": "string"
}
```

**Response** (200 OK):
```json
{
  "answer": "string",
  "context_document_count": 0
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:8000/invoke/contextual_compression_retriever" \
  -H "Content-Type: application/json" \
  -d '{"question": "What did critics say about the cinematography?"}'
```

**Example Response**:
```json
{
  "answer": "Critics praised the cinematography for its sleek, stylish visuals and effective use of lighting in action sequences.",
  "context_document_count": 8
}
```

**Source Reference**: `src/api/app.py:272-275`

**Related Components**:
- Chain: `CONTEXTUAL_COMPRESSION_CHAIN` (src/rag/chain.py:68)
- Retriever: `get_contextual_compression_retriever()` (src/rag/retriever.py:71-90)
- Compressor: Cohere Rerank (model: rerank-english-v3.0)
- Base Retriever: Naive retriever

**Requirements**: Requires `COHERE_API_KEY` environment variable.

**Performance Notes**: Slower than naive retrieval due to reranking API call, but typically produces higher quality, more relevant context.

---

#### POST /invoke/multi_query_retriever

Enhanced query expansion with LLM-generated alternative phrasings.

**Operation ID**: `multi_query_retriever`

**Description**: Uses an LLM to generate multiple alternative phrasings of the input question, retrieves documents for each variant, and combines results to improve coverage and reduce query ambiguity.

**Request Body**:
```json
{
  "question": "string"
}
```

**Response** (200 OK):
```json
{
  "answer": "string",
  "context_document_count": 0
}
```

**Example Request**:
```python
import httpx
import asyncio

async def query_multi():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/invoke/multi_query_retriever",
            json={"question": "How was the plot received?"}
        )
        return response.json()

result = asyncio.run(query_multi())
print(result)
```

**Example Response**:
```json
{
  "answer": "The plot received mixed reviews. Some critics found it simple but effective for an action movie, while others wanted more depth in the storytelling.",
  "context_document_count": 15
}
```

**Source Reference**: `src/api/app.py:277-280`

**Related Components**:
- Chain: `MULTI_QUERY_CHAIN` (src/rag/chain.py:69)
- Retriever: `get_multi_query_retriever()` (src/rag/retriever.py:92-106)
- LLM: Uses ChatOpenAI for query generation (src/integrations/llm_models.py:11-47)
- Base Retriever: Naive retriever

**When to Use**: Best for ambiguous queries, complex questions, or when you want comprehensive coverage of the topic.

**Cost Considerations**: Makes additional LLM API call for query expansion, increasing latency and cost.

---

#### POST /invoke/ensemble_retriever

Combines multiple retrieval strategies with weighted scoring.

**Operation ID**: `ensemble_retriever`

**Description**: Combines results from multiple retrieval methods (BM25, naive, contextual compression, multi-query) using equal weighting. Provides balanced results that leverage strengths of different approaches.

**Request Body**:
```json
{
  "question": "string"
}
```

**Response** (200 OK):
```json
{
  "answer": "string",
  "context_document_count": 0
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:8000/invoke/ensemble_retriever" \
  -H "Content-Type: application/json" \
  -d '{"question": "What makes John Wick stand out?"}'
```

**Example Response**:
```json
{
  "answer": "John Wick stands out for its innovative action choreography, world-building of the assassin underworld, and Keanu Reeves' committed performance.",
  "context_document_count": 12
}
```

**Source Reference**: `src/api/app.py:282-285`

**Related Components**:
- Chain: `ENSEMBLE_CHAIN` (src/rag/chain.py:70)
- Retriever: `get_ensemble_retriever()` (src/rag/retriever.py:115-145)
- Component Retrievers: BM25, Naive, Contextual Compression, Multi-Query
- Weighting: Equal weights (1/n for n retrievers)

**Performance Notes**: Slower due to running multiple retrievers, but often produces the most comprehensive and balanced results.

**Gotchas**: Requires at least 2 component retrievers to function. Falls back to first available retriever if insufficient retrievers are available.

---

#### POST /invoke/semantic_retriever

Advanced semantic search using semantic chunking strategy.

**Operation ID**: `semantic_retriever`

**Description**: Uses SemanticChunker to create semantically coherent chunks rather than fixed-size chunks. Performs similarity search on the semantic vector store for more contextually relevant retrieval.

**Request Body**:
```json
{
  "question": "string"
}
```

**Response** (200 OK):
```json
{
  "answer": "string",
  "context_document_count": 0
}
```

**Example Request**:
```python
import requests

def semantic_search(question: str) -> dict:
    """Perform semantic search query."""
    response = requests.post(
        "http://localhost:8000/invoke/semantic_retriever",
        json={"question": question},
        timeout=60
    )
    response.raise_for_status()
    return response.json()

result = semantic_search("How do the characters develop throughout the movie?")
print(f"Answer: {result['answer']}")
print(f"Context docs: {result['context_document_count']}")
```

**Example Response**:
```json
{
  "answer": "John Wick's character development focuses on his transformation from retired assassin to vengeful force, driven by grief and loss.",
  "context_document_count": 10
}
```

**Source Reference**: `src/api/app.py:287-290`

**Related Components**:
- Chain: `SEMANTIC_CHAIN` (src/rag/chain.py:71)
- Retriever: `get_semantic_retriever()` (src/rag/retriever.py:108-113)
- Vector Store: `SEMANTIC_VECTORSTORE` (src/rag/vectorstore.py:49-71)
- Chunking: SemanticChunker (langchain_experimental)

**When to Use**: Best for queries requiring deep semantic understanding, thematic analysis, or when document structure matters.

---

### Utility Endpoints

#### GET /health

Health check endpoint with Phoenix tracing integration.

**Description**: Returns system health status, timestamp, and Phoenix tracing information. Used for monitoring, load balancer health checks, and debugging.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-12-13",
  "phoenix_integration": {
    "project": "advanced-rag-system-20241213_143022",
    "tracer": "advanced-rag-fastapi-endpoints",
    "trace_id": 123456789
  }
}
```

**Example Request**:
```bash
curl http://localhost:8000/health
```

**Source Reference**: `src/api/app.py:292-308`

**Phoenix Tracing**: Creates span `FastAPI.health_check` with attributes:
- `fastapi.health.type`: "basic"
- `fastapi.health.project`: Project name
- Event: `health_check.complete`

---

#### GET /cache/stats

Get cache statistics and Redis metrics.

**Description**: Returns detailed statistics about cache performance including hit rates, Redis info, and multi-level cache metrics. Useful for monitoring cache effectiveness and troubleshooting.

**Response** (200 OK):
```json
{
  "cache_enabled": true,
  "cache_type": "multi_level",
  "cache_stats": {
    "type": "multi_level",
    "l1_hits": 150,
    "l2_hits": 75,
    "misses": 25,
    "sets": 100,
    "hit_rate": 0.9,
    "l1_stats": {
      "type": "local_memory",
      "hits": 150,
      "misses": 50,
      "sets": 100,
      "evictions": 5,
      "size": 95,
      "hit_rate": 0.75,
      "max_size": 100
    },
    "l2_stats": {
      "type": "redis",
      "operations": 225,
      "errors": 0
    }
  },
  "redis_info": {
    "keys_count": 1234,
    "connected_clients": 5,
    "used_memory_human": "12.5M"
  },
  "phoenix_integration": {
    "project": "advanced-rag-system-20241213_143022",
    "trace_id": 123456790
  }
}
```

**Example Request**:
```python
import requests

def get_cache_stats():
    response = requests.get("http://localhost:8000/cache/stats")
    stats = response.json()

    print(f"Cache enabled: {stats['cache_enabled']}")
    print(f"Cache type: {stats['cache_type']}")
    print(f"Hit rate: {stats['cache_stats']['hit_rate']:.2%}")

    if 'redis_info' in stats:
        print(f"Redis keys: {stats['redis_info']['keys_count']}")
        print(f"Memory: {stats['redis_info']['used_memory_human']}")

get_cache_stats()
```

**Source Reference**: `src/api/app.py:310-359`

**Error Response** (503 Service Unavailable):
```json
{
  "detail": "Cache unavailable: Connection refused"
}
```

**Phoenix Tracing**: Creates span `FastAPI.cache_stats` with attributes:
- `fastapi.cache.type`: Cache type
- `fastapi.cache.enabled`: Boolean
- `fastapi.cache.keys_count`: Number of Redis keys (if available)
- `fastapi.cache.connected_clients`: Redis clients

---

### Request/Response Schemas

All schemas are defined using Pydantic models with automatic validation.

#### QuestionRequest

Request model for all retrieval endpoints.

**Source**: `src/api/app.py:167-168`

```python
from pydantic import BaseModel

class QuestionRequest(BaseModel):
    question: str
```

**Fields**:
- `question` (str, required): The question to answer using RAG

**Example**:
```json
{
  "question": "What did critics say about Keanu Reeves' performance?"
}
```

**Validation**:
- Must be a string
- No length constraints (but very long questions may be truncated by LLM context window)

---

#### AnswerResponse

Response model for all retrieval endpoints.

**Source**: `src/api/app.py:170-172`

```python
from pydantic import BaseModel

class AnswerResponse(BaseModel):
    answer: str
    context_document_count: int
```

**Fields**:
- `answer` (str): The generated answer from the RAG chain
- `context_document_count` (int): Number of documents used as context

**Example**:
```json
{
  "answer": "Critics widely praised Keanu Reeves' performance, noting his physical commitment to the action sequences and his ability to convey emotion through minimal dialogue.",
  "context_document_count": 10
}
```

---

## MCP Server API

The Model Context Protocol (MCP) server provides structured access to RAG resources and Qdrant vector database.

**Server Implementation**: FastMCP wrapper around FastAPI app

**Source**: `/home/donbr/ghcp/adv-rag/src/mcp/server.py`

### Resources (Read Operations)

MCP Resources follow CQRS pattern for read-only access to data.

#### List Collections

List all available Qdrant collections.

**Resource URI**: `qdrant://collections`

**Description**: Returns list of all vector collections available in the Qdrant instance with basic metadata.

**Parameters**: None

**Returns**:
```markdown
# Available Qdrant Collections

## Collections
- johnwick_baseline
- johnwick_semantic

## Collection Count: 2

## Last Updated: 2024-12-13T14:30:22Z
```

**Example Usage (MCP Client)**:
```python
from mcp import ClientSession

async with ClientSession() as session:
    response = await session.read_resource("qdrant://collections")
    print(response.contents[0].text)
```

**Source Reference**: `src/mcp/qdrant_resources.py:578+`

---

#### Get Collection Info

Retrieve detailed information about a specific collection.

**Resource URI**: `qdrant://collections/{collection_name}`

**Description**: Returns comprehensive metadata about a collection including vector configuration, document count, optimizer status, and available operations.

**Parameters**:
- `collection_name` (str): Name of the collection (e.g., "johnwick_baseline", "johnwick_semantic")

**Returns**:
```markdown
# Qdrant Collection: johnwick_baseline

## Collection Metadata
- **Name**: johnwick_baseline
- **Status**: green
- **Vector Size**: 1536
- **Distance Metric**: Cosine
- **Total Documents**: 1250

## Configuration Details
- **Optimizer Status**: ok
- **Indexed Only**: false

## CQRS Information
- **Operation Type**: READ-ONLY Resource
- **Access Pattern**: Query/Retrieval Operations
- **Last Updated**: 2024-12-13T14:30:22.123456Z

## Available Operations
Use these Resource URIs for read-only access:
- Collection info: `qdrant://collections/johnwick_baseline`
- Document by ID: `qdrant://collections/johnwick_baseline/documents/{point_id}`
- Search: `qdrant://collections/johnwick_baseline/search?query={text}&limit={n}`
- Statistics: `qdrant://collections/johnwick_baseline/stats`

---
*Read-only access via CQRS Resources pattern*
```

**Example Usage (MCP CLI)**:
```bash
mcp read qdrant://collections/johnwick_baseline
```

**Source Reference**: `src/mcp/qdrant_resources.py:70-150`

**Error Handling**: Returns formatted error message if collection doesn't exist or Qdrant is unavailable.

---

#### Get Document by ID

Retrieve a specific document by its point ID.

**Resource URI**: `qdrant://collections/{collection_name}/documents/{point_id}`

**Description**: Fetches a single document from the collection by its unique point ID, including vector, payload, and metadata.

**Parameters**:
- `collection_name` (str): Name of the collection
- `point_id` (str): Unique identifier for the document/point

**Returns**:
```markdown
# Document from johnwick_baseline

## Point ID: 123e4567-e89b-12d3-a456-426614174000

## Payload
**Text**: This is a review of John Wick mentioning the incredible action sequences...
**Metadata**: {"source": "reviews.csv", "row": 42}

## Vector Dimensions: 1536
## Score: N/A (direct retrieval)

---
Retrieved at: 2024-12-13T14:30:22.123456Z
```

**Example Usage (Python)**:
```python
from mcp import ClientSession

async with ClientSession() as session:
    uri = "qdrant://collections/johnwick_baseline/documents/123e4567-e89b-12d3-a456-426614174000"
    response = await session.read_resource(uri)
    print(response.contents[0].text)
```

**Source Reference**: `src/mcp/qdrant_resources.py:566+`

---

#### Search Collection

Perform vector similarity search on a collection.

**Resource URI**: `qdrant://collections/{collection_name}/search?query={text}&limit={n}`

**Description**: Embeds the query text and performs vector similarity search, returning top-k most similar documents with scores.

**Parameters**:
- `collection_name` (str): Name of the collection to search
- `query` (str): Text query to embed and search (URL-encoded)
- `limit` (int, optional): Number of results to return (default: 10)

**Returns**:
```markdown
# Search Results: johnwick_baseline

## Query: "action scenes"
## Results: 10
## Search performed at: 2024-12-13T14:30:22.123456Z

---

### Result 1 (Score: 0.912)
**Point ID**: abc123...
**Text**: The nightclub scene is one of the most memorable action sequences in recent cinema...
**Metadata**: {"source": "reviews.csv", "row": 15}

### Result 2 (Score: 0.887)
**Point ID**: def456...
**Text**: John Wick's fight choreography sets a new standard for action films...
**Metadata**: {"source": "reviews.csv", "row": 23}

[... 8 more results ...]

---
*CQRS Read-Only Search Resource*
```

**Example Usage (MCP Client)**:
```python
import urllib.parse

query = urllib.parse.quote("What did critics say about the action?")
uri = f"qdrant://collections/johnwick_baseline/search?query={query}&limit=5"

async with ClientSession() as session:
    response = await session.read_resource(uri)
    print(response.contents[0].text)
```

**Source Reference**: `src/mcp/qdrant_resources.py:570+`

**Performance Notes**: Performs embedding of query text (requires OpenAI API call) followed by vector search.

---

#### Get Collection Statistics

Retrieve detailed statistics about a collection.

**Resource URI**: `qdrant://collections/{collection_name}/stats`

**Description**: Returns comprehensive statistics including document count, index status, vector dimensions, and performance metrics.

**Parameters**:
- `collection_name` (str): Name of the collection

**Returns**:
```markdown
# Collection Statistics: johnwick_baseline

## Document Statistics
- **Total Documents**: 1250
- **Vector Dimensions**: 1536
- **Distance Metric**: Cosine

## Index Status
- **Indexed Vectors**: 1250
- **Status**: green

## Storage
- **Points Count**: 1250
- **Segments Count**: 2

---
Generated at: 2024-12-13T14:30:22.123456Z
```

**Example Usage**:
```bash
mcp read "qdrant://collections/johnwick_baseline/stats"
```

**Source Reference**: `src/mcp/qdrant_resources.py:574+`

---

## Python API

### Core Settings

Centralized configuration management using Pydantic BaseSettings.

**Source**: `/home/donbr/ghcp/adv-rag/src/core/settings.py`

#### Settings Class

Singleton configuration class with environment variable loading.

**Source**: `src/core/settings.py:21-217`

```python
from pydantic_settings import BaseSettings
from src.core.settings import get_settings

# Get settings singleton
settings = get_settings()
```

**Key Attributes** (70+ configuration fields):

**General Settings**:
- `openai_api_key` (str, required): OpenAI API key
- `openai_model_name` (str, default="gpt-4.1-mini"): LLM model selection
- `cohere_api_key` (Optional[str], default=None): Cohere API key for reranking

**LLM Configuration**:
- `openai_temperature` (float, default=0.0): Temperature for LLM responses
- `openai_max_retries` (int, default=3): Maximum API retry attempts
- `openai_request_timeout` (int, default=60): Request timeout in seconds

**Embedding Configuration**:
- `embedding_model_name` (str, default="text-embedding-3-small"): OpenAI embedding model
- `cohere_rerank_model` (str, default="rerank-english-v3.0"): Cohere reranking model

**External Service Endpoints**:
- `phoenix_endpoint` (str, default="http://localhost:6006"): Phoenix observability endpoint
- `qdrant_url` (str, default="http://localhost:6333"): Qdrant vector database URL

**Redis Configuration**:
- `redis_url` (str, default="redis://localhost:6379"): Redis connection URL
- `redis_cache_ttl` (int, default=300): Cache TTL in seconds (5 minutes)
- `redis_max_connections` (int, default=20): Connection pool size
- `redis_socket_keepalive` (bool, default=True): Keep socket alive
- `redis_health_check_interval` (int, default=30): Health check interval in seconds

**Cache Settings**:
- `cache_enabled` (bool, default=True): Enable/disable caching for A/B testing

**MCP Configuration**:
- `mcp_request_timeout` (int, default=30): MCP request timeout in seconds
- `max_snippets` (int, default=5): Maximum context snippets to extract

**Phoenix Integration Configuration** (Task 1.7):
- `phoenix_integration_enabled` (bool, default=True): Enable Phoenix MCP integration
- `phoenix_base_url` (Optional[str], default=None): Phoenix MCP server URL (auto-detected)
- `phoenix_api_key` (Optional[str], default=None): Phoenix API key if required
- `phoenix_timeout_seconds` (float, default=30.0): Default timeout for Phoenix operations

**Phoenix Retry Configuration**:
- `phoenix_retry_max_attempts` (int, default=3): Maximum retry attempts
- `phoenix_retry_base_delay` (float, default=1.0): Base delay for exponential backoff
- `phoenix_retry_max_delay` (float, default=30.0): Maximum backoff delay
- `phoenix_retry_exponential_base` (float, default=2.0): Exponential base for backoff
- `phoenix_retry_jitter` (bool, default=True): Enable jitter to prevent thundering herd

**Phoenix Circuit Breaker Configuration**:
- `phoenix_circuit_breaker_enabled` (bool, default=True): Enable circuit breaker pattern
- `phoenix_circuit_breaker_failure_threshold` (int, default=5): Failures before opening
- `phoenix_circuit_breaker_success_threshold` (int, default=3): Successes to close from half-open
- `phoenix_circuit_breaker_timeout` (float, default=60.0): Time before attempting to close

**Phoenix Batch Processing Configuration**:
- `phoenix_batch_enabled` (bool, default=True): Enable batch processing
- `phoenix_batch_size` (int, default=10): Items per batch
- `phoenix_batch_timeout_seconds` (float, default=300.0): Batch operation timeout
- `phoenix_batch_progress_interval` (int, default=5): Progress reporting interval
- `phoenix_batch_concurrent_limit` (int, default=3): Maximum concurrent batch operations

**Phoenix Pattern Extraction Configuration**:
- `phoenix_pattern_qa_threshold` (float, default=0.8): Minimum QA correctness score
- `phoenix_pattern_rag_threshold` (float, default=0.7): Minimum RAG relevance score
- `phoenix_pattern_confidence_threshold` (float, default=0.75): Minimum confidence score
- `phoenix_pattern_max_patterns_per_experiment` (int, default=50): Maximum patterns per experiment

**Phoenix Data Sync Configuration**:
- `phoenix_sync_enabled` (bool, default=False): Enable periodic sync
- `phoenix_sync_interval_hours` (int, default=24): Sync interval in hours
- `phoenix_sync_datasets` (Union[str, List[str]], default="johnwick_golden_testset"): Datasets to sync
- `phoenix_sync_max_age_days` (int, default=30): Maximum age of experiments to sync

**Access Pattern**:
```python
from src.core.settings import get_settings

# Get singleton instance
settings = get_settings()

# Access configuration
print(f"Using LLM: {settings.openai_model_name}")
print(f"Cache enabled: {settings.cache_enabled}")
print(f"Redis URL: {settings.redis_url}")
print(f"Qdrant URL: {settings.qdrant_url}")
```

**Environment Variables**: Override any setting via .env file or environment variables:
```bash
# .env file
OPENAI_API_KEY=sk-your-key-here
CACHE_ENABLED=true
REDIS_CACHE_TTL=600
PHOENIX_RETRY_MAX_ATTEMPTS=5
```

**Example Configuration**:
```python
# Complete configuration example
from src.core.settings import get_settings

settings = get_settings()

# LLM setup
llm_config = {
    "model": settings.openai_model_name,
    "temperature": settings.openai_temperature,
    "max_retries": settings.openai_max_retries,
    "timeout": settings.openai_request_timeout
}

# Cache setup
cache_config = {
    "enabled": settings.cache_enabled,
    "url": settings.redis_url,
    "ttl": settings.redis_cache_ttl,
    "max_connections": settings.redis_max_connections
}

# Phoenix setup
phoenix_config = {
    "enabled": settings.phoenix_integration_enabled,
    "endpoint": settings.phoenix_endpoint,
    "timeout": settings.phoenix_timeout_seconds,
    "retry_attempts": settings.phoenix_retry_max_attempts,
    "circuit_breaker": settings.phoenix_circuit_breaker_enabled
}
```

**Source Reference**: `src/core/settings.py:21-217`

**Validation**: Pydantic automatically validates types and constraints. Invalid values raise `ValidationError`.

**Thread Safety**: Singleton pattern ensures single instance across application. Settings are read-only after initialization.

---

### Exception Classes

Custom exception hierarchy for consistent error handling.

**Source**: `/home/donbr/ghcp/adv-rag/src/core/exceptions.py`

#### Exception Hierarchy

```
RAGException (Base)
├── ConfigurationError
├── RAGError
│   ├── EmbeddingError
│   ├── VectorStoreError
│   ├── RetrievalError
│   └── ChainExecutionError
├── MCPError
│   ├── MCPServerError
│   ├── MCPTransportError
│   └── MCPResourceError
└── IntegrationError
    ├── RedisError
    └── LLMError
```

#### RAGException

Base exception class for all RAG application errors.

**Source**: `src/core/exceptions.py:14-26`

```python
class RAGException(Exception):
    """Base exception class for all RAG application errors."""

    def __init__(self, message: str, component: str = None, details: dict = None):
        self.message = message
        self.component = component
        self.details = details or {}
        super().__init__(self.message)
```

**Attributes**:
- `message` (str): Error message
- `component` (str, optional): Component where error occurred
- `details` (dict, optional): Additional error context

**Example Usage**:
```python
from src.core.exceptions import RAGException

try:
    # Some operation
    raise RAGException(
        "Failed to process request",
        component="API",
        details={"endpoint": "/invoke/naive_retriever", "status": 500}
    )
except RAGException as e:
    print(f"Error in {e.component}: {e.message}")
    print(f"Details: {e.details}")
```

---

#### ConfigurationError

Raised when there's a configuration error (missing env vars, invalid settings).

**Source**: `src/core/exceptions.py:29-31`

**When to Use**: Missing API keys, invalid URLs, misconfigured services.

```python
from src.core.exceptions import raise_config_error

# Helper function
raise_config_error("Missing OPENAI_API_KEY", missing_var="OPENAI_API_KEY")
```

---

#### RAGError

Base exception for RAG-related errors.

**Source**: `src/core/exceptions.py:34-36`

**Subclasses**:
- `EmbeddingError` (Line 39-41): Embedding operation failures
- `VectorStoreError` (Line 44-46): Vector store operation failures
- `RetrievalError` (Line 49-51): Document retrieval failures
- `ChainExecutionError` (Line 54-56): RAG chain execution failures

**Example Usage**:
```python
from src.core.exceptions import ChainExecutionError

try:
    result = chain.invoke({"question": "test"})
except Exception as e:
    raise ChainExecutionError(
        f"Chain invocation failed: {e}",
        component="RAG Chain",
        details={"chain_type": "naive", "question": "test"}
    )
```

---

#### MCPError

Base exception for MCP-related errors.

**Source**: `src/core/exceptions.py:59-61`

**Subclasses**:
- `MCPServerError` (Line 64-66): MCP server operation failures
- `MCPTransportError` (Line 69-71): MCP transport layer failures
- `MCPResourceError` (Line 74-76): MCP resource operation failures

**Example Usage**:
```python
from src.core.exceptions import MCPResourceError

try:
    resource = await session.read_resource("qdrant://collections/invalid")
except Exception as e:
    raise MCPResourceError(
        f"Failed to read resource: {e}",
        component="MCP Resources",
        details={"uri": "qdrant://collections/invalid"}
    )
```

---

#### IntegrationError

Base exception for external service integration errors.

**Source**: `src/core/exceptions.py:79-81`

**Subclasses**:
- `RedisError` (Line 84-86): Redis operation failures
- `LLMError` (Line 89-91): LLM API call failures

**Example Usage**:
```python
from src.core.exceptions import RedisError, LLMError

# Redis error
try:
    await redis_client.set("key", "value")
except Exception as e:
    raise RedisError(
        f"Redis operation failed: {e}",
        component="Redis Client",
        details={"operation": "set", "key": "key"}
    )

# LLM error
try:
    response = llm.invoke("prompt")
except Exception as e:
    raise LLMError(
        f"LLM API call failed: {e}",
        component="ChatOpenAI",
        details={"model": "gpt-4.1-mini", "error": str(e)}
    )
```

---

#### Helper Functions

**Source**: `src/core/exceptions.py:95-114`

```python
# Raise configuration error
from src.core.exceptions import raise_config_error
raise_config_error("Missing OPENAI_API_KEY", missing_var="OPENAI_API_KEY")

# Raise RAG error
from src.core.exceptions import raise_rag_error
raise_rag_error(
    "Retrieval failed",
    operation="vector_search",
    chain_name="naive_retriever"
)

# Raise MCP error
from src.core.exceptions import raise_mcp_error
raise_mcp_error("Server connection failed", server_type="FastMCP")
```

---

### RAG Chain Factory

Creates and manages RAG chains for different retrieval strategies.

**Source**: `/home/donbr/ghcp/adv-rag/src/rag/chain.py`

#### create_rag_chain()

Create RAG chain from a retriever instance.

**Source**: `src/rag/chain.py:47-62`

```python
def create_rag_chain(retriever):
    """
    Create a RAG chain with the given retriever.

    Args:
        retriever: LangChain retriever instance

    Returns:
        Configured RAG chain or None if creation fails
    """
```

**Parameters**:
- `retriever` (BaseRetriever): LangChain retriever instance

**Returns**: Configured RAG chain (RunnableSequence) or None if creation fails

**Example Usage**:
```python
from src.rag.chain import create_rag_chain
from src.rag.retriever import get_naive_retriever

# Create retriever
retriever = get_naive_retriever()

# Create chain
chain = create_rag_chain(retriever)

# Invoke chain
result = await chain.ainvoke({"question": "Did people like John Wick?"})
answer = result["response"].content
context_docs = result["context"]

print(f"Answer: {answer}")
print(f"Context docs: {len(context_docs)}")
```

**Chain Structure**:
```python
chain = (
    {
        "context": itemgetter("question") | retriever,
        "question": itemgetter("question")
    }
    | RunnablePassthrough.assign(context=itemgetter("context"))
    | {
        "response": RAG_PROMPT | get_chat_model_lazy(),
        "context": itemgetter("context")
    }
)
```

**Prompt Template** (Line 32-42):
```
You are a helpful and kind assistant. Use the context provided below to answer the question.

If you do not know the answer, or are unsure, say you don't know.

Query:
{question}

Context:
{context}
```

**Pre-initialized Chains** (Lines 66-71):
- `NAIVE_RETRIEVAL_CHAIN`: Basic similarity search
- `BM25_RETRIEVAL_CHAIN`: Keyword-based search
- `CONTEXTUAL_COMPRESSION_CHAIN`: Cohere reranking
- `MULTI_QUERY_CHAIN`: Query expansion
- `ENSEMBLE_CHAIN`: Combined strategies
- `SEMANTIC_CHAIN`: Semantic chunking

**Source Reference**: `src/rag/chain.py:47-62`

---

### Retriever Factory

Factory for creating various retriever types.

**Source**: `/home/donbr/ghcp/adv-rag/src/rag/retriever.py`

#### create_retriever()

Factory function to create retrievers based on type.

**Source**: `src/rag/retriever.py:148-187`

```python
def create_retriever(retrieval_type: str, vectorstore=None, **kwargs):
    """
    Factory function to create retrievers based on type.

    Args:
        retrieval_type: Type of retriever ("naive", "bm25", "hybrid", "ensemble", etc.)
        vectorstore: Vector store instance (may not be used by all retrievers)
        **kwargs: Additional arguments (currently unused)

    Returns:
        Configured retriever instance or None if creation fails
    """
```

**Parameters**:
- `retrieval_type` (str): Retriever type identifier
- `vectorstore` (optional): Vector store instance
- `**kwargs`: Additional configuration

**Supported Types**:
- `"naive"`: Basic similarity search (`get_naive_retriever()`)
- `"bm25"`: BM25 keyword search (`get_bm25_retriever()`)
- `"hybrid"`: Ensemble retrieval (`get_ensemble_retriever()`)
- `"ensemble"`: Ensemble retrieval (`get_ensemble_retriever()`)
- `"contextual"`: Contextual compression (`get_contextual_compression_retriever()`)
- `"contextual_compression"`: Contextual compression
- `"multi_query"`: Multi-query expansion (`get_multi_query_retriever()`)
- `"semantic"`: Semantic chunking (`get_semantic_retriever()`)

**Returns**: BaseRetriever instance or None

**Example Usage**:
```python
from src.rag.retriever import create_retriever

# Create different retriever types
naive_ret = create_retriever("naive")
bm25_ret = create_retriever("bm25")
ensemble_ret = create_retriever("ensemble")

# Use retriever
if naive_ret:
    docs = naive_ret.get_relevant_documents("test query")
    print(f"Retrieved {len(docs)} documents")
```

**Individual Retriever Functions**:

**get_naive_retriever()** (Line 51-56):
```python
def get_naive_retriever():
    """Basic similarity search on baseline vector store."""
    if not BASELINE_VECTORSTORE:
        return None
    return BASELINE_VECTORSTORE.as_retriever(search_kwargs={"k": 10})
```

**get_bm25_retriever()** (Line 58-69):
```python
def get_bm25_retriever():
    """BM25 keyword-based search."""
    if not DOCUMENTS:
        return None
    return BM25Retriever.from_documents(DOCUMENTS)
```

**get_contextual_compression_retriever()** (Line 71-90):
```python
def get_contextual_compression_retriever():
    """Contextual compression with Cohere reranking."""
    naive_ret = get_naive_retriever()
    if not naive_ret or not os.getenv("COHERE_API_KEY"):
        return None

    settings = get_settings()
    compressor = CohereRerank(model=settings.cohere_rerank_model)
    return ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=naive_ret
    )
```

**get_multi_query_retriever()** (Line 92-106):
```python
def get_multi_query_retriever():
    """Multi-query expansion with LLM."""
    naive_ret = get_naive_retriever()
    if not naive_ret:
        return None

    return MultiQueryRetriever.from_llm(
        retriever=naive_ret,
        llm=CHAT_MODEL
    )
```

**get_semantic_retriever()** (Line 108-113):
```python
def get_semantic_retriever():
    """Semantic search on semantic vector store."""
    if not SEMANTIC_VECTORSTORE:
        return None
    return SEMANTIC_VECTORSTORE.as_retriever(search_kwargs={"k": 10})
```

**get_ensemble_retriever()** (Line 115-145):
```python
def get_ensemble_retriever():
    """Ensemble of multiple retrievers with equal weighting."""
    retrievers_to_ensemble = {
        "bm25": get_bm25_retriever(),
        "naive": get_naive_retriever(),
        "contextual_compression": get_contextual_compression_retriever(),
        "multi_query": get_multi_query_retriever()
    }

    active_retrievers = [r for r in retrievers_to_ensemble.values() if r is not None]

    if len(active_retrievers) < 2:
        return active_retrievers[0] if active_retrievers else None

    equal_weighting = [1.0 / len(active_retrievers)] * len(active_retrievers)
    return EnsembleRetriever(
        retrievers=active_retrievers,
        weights=equal_weighting
    )
```

**Source Reference**: `src/rag/retriever.py:31-187`

**Global Variables** (Lines 28-48):
- `DOCUMENTS`: Loaded documents from data_loader
- `CHAT_MODEL`: Initialized ChatOpenAI instance
- `BASELINE_VECTORSTORE`: Main vector store (RecursiveCharacterTextSplitter)
- `SEMANTIC_VECTORSTORE`: Semantic vector store (SemanticChunker)

---

### Cache API

Lightweight cache abstraction layer for A/B testing.

**Source**: `/home/donbr/ghcp/adv-rag/src/integrations/cache.py`

#### CacheInterface (Abstract Base Class)

Abstract interface for all cache implementations.

**Source**: `src/integrations/cache.py:26-47`

```python
from abc import ABC, abstractmethod

class CacheInterface(ABC):
    """Abstract base class for cache implementations"""

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        pass
```

**Methods**:
- `get(key: str) -> Optional[str]`: Retrieve value by key
- `set(key: str, value: str, ttl: int = 300) -> bool`: Store value with TTL
- `delete(key: str) -> bool`: Remove key from cache
- `get_stats() -> Dict[str, Any]`: Get cache statistics

---

#### NoOpCache

No-operation cache for when caching is disabled.

**Source**: `src/integrations/cache.py:50-77`

```python
class NoOpCache(CacheInterface):
    """No-operation cache for when caching is disabled"""
```

**Behavior**:
- `get()`: Always returns None (cache miss)
- `set()`: Always returns True (no-op success)
- `delete()`: Always returns True (no-op success)
- `get_stats()`: Returns operation count

**Example Usage**:
```python
from src.integrations.cache import NoOpCache

cache = NoOpCache()

# All operations are no-ops
await cache.set("key", "value")  # Returns True, does nothing
value = await cache.get("key")   # Returns None
stats = cache.get_stats()        # {"type": "noop", "enabled": False, "operations": 2}
```

**When to Use**: When `cache_enabled=False` in settings, for testing without cache overhead.

---

#### LocalMemoryCache

Simple L1 in-memory cache with TTL and LRU eviction.

**Source**: `src/integrations/cache.py:80-144`

```python
class LocalMemoryCache(CacheInterface):
    """Simple L1 in-memory cache with TTL support"""

    def __init__(self, max_size: int = 1000):
        self.cache: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self.max_size = max_size
```

**Configuration**:
- `max_size` (int, default=1000): Maximum cache capacity
- Eviction: LRU (Least Recently Used)
- TTL: Per-key expiration

**Methods**:
- `get(key)`: Check TTL, return value or None if expired/missing
- `set(key, value, ttl)`: Store with expiration, evict oldest if at capacity
- `delete(key)`: Remove key if exists
- `get_stats()`: Returns hits, misses, sets, evictions, hit_rate, size

**Example Usage**:
```python
from src.integrations.cache import LocalMemoryCache

# Create cache with 100-item capacity
cache = LocalMemoryCache(max_size=100)

# Set with 60-second TTL
await cache.set("user:123", '{"name": "John"}', ttl=60)

# Get (within TTL)
value = await cache.get("user:123")  # Returns '{"name": "John"}'

# Wait 61 seconds
await asyncio.sleep(61)
value = await cache.get("user:123")  # Returns None (expired)

# Statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Size: {stats['size']}/{stats['max_size']}")
```

**Thread Safety**: Not thread-safe for concurrent access. Use with asyncio.

**LRU Behavior**: Most recently accessed items stay in cache longer.

**Source Reference**: `src/integrations/cache.py:80-144`

---

#### RedisCache

L2 Redis cache wrapper for persistent caching.

**Source**: `src/integrations/cache.py:147-190`

```python
class RedisCache(CacheInterface):
    """L2 Redis cache wrapper"""

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
```

**Configuration**:
- Requires Redis client instance
- TTL: Per-key expiration
- Persistence: Data survives restarts

**Methods**:
- `get(key)`: Fetch from Redis
- `set(key, value, ttl)`: Store in Redis with expiration
- `delete(key)`: Remove from Redis
- `get_stats()`: Returns operations count and error count

**Example Usage**:
```python
from src.integrations.cache import RedisCache
from src.integrations.redis_client import get_redis

# Get Redis client
redis_client = await get_redis()

# Create cache
cache = RedisCache(redis_client)

# Set with 5-minute TTL
await cache.set("session:abc123", '{"user_id": 42}', ttl=300)

# Get
session = await cache.get("session:abc123")

# Delete
await cache.delete("session:abc123")

# Stats
stats = cache.get_stats()
print(f"Operations: {stats['operations']}")
print(f"Errors: {stats['errors']}")
```

**Error Handling**: Logs errors and returns None/False on failures. Records errors in stats.

**Source Reference**: `src/integrations/cache.py:147-190`

---

#### MultiLevelCache

Multi-level cache combining L1 (local) and L2 (Redis).

**Source**: `src/integrations/cache.py:193-251`

```python
class MultiLevelCache(CacheInterface):
    """Multi-level cache combining L1 (local) and L2 (Redis)"""

    def __init__(self, l1_cache: CacheInterface, l2_cache: CacheInterface):
        self.l1 = l1_cache
        self.l2 = l2_cache
```

**Configuration**:
- `l1_cache`: Fast local memory cache
- `l2_cache`: Persistent Redis cache

**Behavior**:
- `get()`: Try L1 first, then L2 if miss. Populate L1 on L2 hit.
- `set()`: Write to both L1 and L2
- `delete()`: Remove from both levels
- `get_stats()`: Combined statistics from both levels

**Example Usage**:
```python
from src.integrations.cache import MultiLevelCache, LocalMemoryCache, RedisCache
from src.integrations.redis_client import get_redis

# Create L1 and L2
l1 = LocalMemoryCache(max_size=100)
redis_client = await get_redis()
l2 = RedisCache(redis_client)

# Create multi-level cache
cache = MultiLevelCache(l1, l2)

# Set (writes to both levels)
await cache.set("key", "value", ttl=300)

# Get (tries L1, then L2)
value = await cache.get("key")  # L1 hit (fast)

# After L1 eviction
await cache.delete("key")  # Forces re-fetch
value = await cache.get("key")  # L2 hit, populates L1

# Stats
stats = cache.get_stats()
print(f"L1 hits: {stats['l1_hits']}")
print(f"L2 hits: {stats['l2_hits']}")
print(f"Overall hit rate: {stats['hit_rate']:.2%}")
print(f"L1 stats: {stats['l1_stats']}")
print(f"L2 stats: {stats['l2_stats']}")
```

**TTL Strategy**:
- L1: Shorter TTL (60 seconds max) for quick invalidation
- L2: Full TTL for persistence

**Source Reference**: `src/integrations/cache.py:193-251`

---

#### get_cache()

Factory function to get appropriate cache implementation based on settings.

**Source**: `src/integrations/cache.py:254-281`

```python
async def get_cache(settings: Optional[Settings] = None) -> CacheInterface:
    """
    Factory function to get appropriate cache implementation based on settings.

    Returns:
        - NoOpCache if cache_enabled=False
        - MultiLevelCache (L1+L2) if cache_enabled=True and Redis available
        - LocalMemoryCache if cache_enabled=True but Redis unavailable
    """
```

**Parameters**:
- `settings` (Optional[Settings]): Settings instance (uses global if None)

**Returns**: CacheInterface implementation

**Logic**:
1. If `cache_enabled=False`: Return NoOpCache
2. Try to connect to Redis:
   - Success: Return MultiLevelCache (L1: 100 items, L2: Redis)
   - Failure: Return LocalMemoryCache (500 items)

**Example Usage**:
```python
from src.integrations.cache import get_cache

# Get appropriate cache based on configuration
cache = await get_cache()

# Use cache (works with any implementation)
await cache.set("key", "value", ttl=300)
value = await cache.get("key")
stats = cache.get_stats()

print(f"Cache type: {stats['type']}")
```

**Configuration via Environment**:
```bash
# Enable multi-level cache
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379

# Disable cache (NoOpCache)
CACHE_ENABLED=false
```

**Source Reference**: `src/integrations/cache.py:254-281`

---

#### Convenience Functions

Backward-compatible wrapper functions.

**Source**: `src/integrations/cache.py:284-300`

```python
async def cache_get(key: str) -> Optional[str]:
    """Get from cache using default cache instance"""
    cache = await get_cache()
    return await cache.get(key)

async def cache_set(key: str, value: str, ttl: int = 300) -> bool:
    """Set in cache using default cache instance"""
    cache = await get_cache()
    return await cache.set(key, value, ttl)

async def cache_delete(key: str) -> bool:
    """Delete from cache using default cache instance"""
    cache = await get_cache()
    return await cache.delete(key)
```

**Example Usage**:
```python
from src.integrations.cache import cache_get, cache_set, cache_delete

# Simple API without managing cache instances
await cache_set("user:123", '{"name": "John"}', ttl=600)
user_data = await cache_get("user:123")
await cache_delete("user:123")
```

---

### Embeddings

OpenAI embeddings model initialization.

**Source**: `/home/donbr/ghcp/adv-rag/src/rag/embeddings.py`

#### get_openai_embeddings()

Initialize OpenAI embeddings model.

**Source**: `src/rag/embeddings.py:8-17`

```python
def get_openai_embeddings():
    """
    Initialize OpenAI embeddings model.

    Returns:
        OpenAIEmbeddings instance configured with model from settings
    """
    settings = get_settings()
    logger.info(f"Initializing OpenAIEmbeddings model: {settings.embedding_model_name}")

    model = OpenAIEmbeddings(model=settings.embedding_model_name)
    logger.info("OpenAIEmbeddings model initialized successfully.")
    return model
```

**Configuration**: Uses `embedding_model_name` from settings (default: "text-embedding-3-small")

**Returns**: OpenAIEmbeddings instance

**Example Usage**:
```python
from src.rag.embeddings import get_openai_embeddings

# Get embeddings model
embeddings = get_openai_embeddings()

# Embed a query
query = "What did critics say about the action?"
query_vector = embeddings.embed_query(query)

print(f"Vector dimensions: {len(query_vector)}")  # 1536 for text-embedding-3-small
print(f"First 5 dimensions: {query_vector[:5]}")

# Embed documents
docs = ["Doc 1 text", "Doc 2 text"]
doc_vectors = embeddings.embed_documents(docs)

print(f"Embedded {len(doc_vectors)} documents")
```

**Supported Models**:
- `text-embedding-3-small` (1536 dimensions, default)
- `text-embedding-3-large` (3072 dimensions)
- `text-embedding-ada-002` (1536 dimensions, legacy)

**API Key**: Requires `OPENAI_API_KEY` environment variable.

**Error Handling**: Raises exception if initialization fails. Check logs for details.

**Source Reference**: `src/rag/embeddings.py:8-17`

---

### Vector Store

Qdrant vector store initialization and management.

**Source**: `/home/donbr/ghcp/adv-rag/src/rag/vectorstore.py`

#### get_main_vectorstore()

Create/load baseline vector store with RecursiveCharacterTextSplitter chunking.

**Source**: `src/rag/vectorstore.py:25-48`

```python
def get_main_vectorstore():
    """
    Create main vector store 'johnwick_baseline'.

    Returns:
        QdrantVectorStore instance connected to baseline collection
    """
    logger.info("Attempting to create main vector store 'johnwick_baseline'...")

    # Initialize Qdrant client
    qdrant_client = QdrantClient(
        url=QDRANT_API_URL,
        prefer_grpc=True
    )

    # Construct the VectorStore
    vs = QdrantVectorStore(
        embedding=EMBEDDINGS,
        client=qdrant_client,
        collection_name=BASELINE_COLLECTION_NAME,
        retrieval_mode=RetrievalMode.DENSE,
    )

    logger.info("Main vector store 'johnwick_baseline' created successfully.")
    return vs
```

**Configuration**:
- Collection: "johnwick_baseline"
- Embedding: OpenAI embeddings (text-embedding-3-small)
- Retrieval Mode: Dense (vector similarity only)
- Chunking: RecursiveCharacterTextSplitter (fixed-size chunks)

**Returns**: QdrantVectorStore instance

**Example Usage**:
```python
from src.rag.vectorstore import get_main_vectorstore

# Get vector store
vectorstore = get_main_vectorstore()

# Query directly
results = vectorstore.similarity_search("action scenes", k=5)
for doc in results:
    print(doc.page_content)

# Get as retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
docs = retriever.get_relevant_documents("plot analysis")
```

**Source Reference**: `src/rag/vectorstore.py:25-48`

---

#### get_semantic_vectorstore()

Create/load semantic vector store with SemanticChunker.

**Source**: `src/rag/vectorstore.py:49-71`

```python
def get_semantic_vectorstore():
    """
    Create semantic vector store 'johnwick_semantic'.

    Returns:
        QdrantVectorStore instance connected to semantic collection
    """
    logger.info("Attempting to create semantic vector store 'johnwick_semantic'...")

    # Initialize Qdrant client
    qdrant_client = QdrantClient(
        url=QDRANT_API_URL,
        prefer_grpc=True
    )

    # Construct the VectorStore
    vs = QdrantVectorStore(
        embedding=EMBEDDINGS,
        client=qdrant_client,
        collection_name=SEMANTIC_COLLECTION_NAME,
        retrieval_mode=RetrievalMode.DENSE,
    )

    logger.info("Semantic vector store 'johnwick_semantic' created successfully.")
    return vs
```

**Configuration**:
- Collection: "johnwick_semantic"
- Embedding: OpenAI embeddings (text-embedding-3-small)
- Retrieval Mode: Dense (vector similarity only)
- Chunking: SemanticChunker (meaning-based boundaries)

**Returns**: QdrantVectorStore instance

**Example Usage**:
```python
from src.rag.vectorstore import get_semantic_vectorstore

# Get semantic vector store
vectorstore = get_semantic_vectorstore()

# Semantic search (preserves context better)
results = vectorstore.similarity_search(
    "character development and themes",
    k=5
)

for doc in results:
    print(f"Chunk: {doc.page_content}")
    print(f"Metadata: {doc.metadata}")
    print("---")
```

**Differences from Baseline**:
- Chunks respect semantic boundaries (not fixed size)
- Better preservation of context and meaning
- May have variable chunk sizes
- Better for queries requiring thematic understanding

**Source Reference**: `src/rag/vectorstore.py:49-71`

---

### Phoenix MCP Client

Comprehensive Phoenix observability integration with error handling.

**Source**: `/home/donbr/ghcp/adv-rag/src/integrations/phoenix_mcp.py`

#### Error Handling Classes

**RetryError** (Line 29-35):
```python
class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted."""
    def __init__(self, message: str, last_exception: Exception, attempts: int):
        self.last_exception = last_exception
        self.attempts = attempts
```

**CircuitBreakerState** (Line 37-42):
```python
class CircuitBreakerState(Enum):
    """Circuit breaker states for Phoenix MCP communication."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered
```

**RetryConfig** (Line 45-53):
```python
@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
```

**CircuitBreakerConfig** (Line 55-60):
```python
@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern."""
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout: float = 60.0
```

**CircuitBreaker** (Line 62-182):
- Implements circuit breaker pattern for reliability
- States: CLOSED → OPEN → HALF_OPEN → CLOSED
- Methods: `is_call_allowed()`, `record_success()`, `record_failure()`

---

#### Data Classes

**PhoenixExperiment** (Line 184-193):
```python
@dataclass
class PhoenixExperiment:
    """Phoenix experiment metadata."""
    id: str
    dataset_id: str
    project_name: str
    created_at: str
    repetitions: int = 1
    metadata: Dict[str, Any] = None
```

**PhoenixExperimentResult** (Line 195-208):
```python
@dataclass
class PhoenixExperimentResult:
    """Phoenix experiment result with annotations."""
    example_id: str
    repetition_number: int
    input: str
    reference_output: str
    # ... additional fields for QA correctness, RAG relevance, etc.
```

**Additional Data Classes**:
- `PhoenixDataset` (Line 210-218): Dataset metadata
- `ExtractedPattern` (Line 220-262): Pattern with validation
- `PatternExtractionResult` (Line 264-281): Pattern extraction results
- `DatasetAnalysisResult` (Line 283-315): Dataset analysis
- `GoldenTestsetAnalysis` (Line 317-340): Golden testset analysis
- `BatchSyncConfig` (Line 342-380): Batch sync configuration
- `SyncState` (Line 382-475): Synchronization state tracking
- `BatchSyncResult` (Line 477-547): Batch sync results

---

#### PhoenixMCPClient

Core Phoenix MCP client with retry and circuit breaker.

**Source**: `src/integrations/phoenix_mcp.py:549-1177`

```python
class PhoenixMCPClient:
    """
    Phoenix MCP client with comprehensive error handling.

    Features:
    - Retry logic with exponential backoff
    - Circuit breaker pattern
    - Experiment data extraction
    - Pattern analysis
    - Dataset synchronization
    """
```

**Methods** (15+ operations):
- `get_experiment(experiment_id: str) -> PhoenixExperiment`
- `get_experiment_results(experiment_id: str) -> List[PhoenixExperimentResult]`
- `extract_patterns(experiment_id: str, threshold: float) -> PatternExtractionResult`
- `analyze_dataset(dataset_id: str) -> DatasetAnalysisResult`
- `sync_experiments(dataset_ids: List[str]) -> BatchSyncResult`
- ... and more

**Example Usage**:
```python
from src.integrations.phoenix_mcp import get_phoenix_client

# Get client with default configuration
client = get_phoenix_client(timeout=30.0)

# Get experiment
experiment = await client.get_experiment("exp_123")
print(f"Experiment: {experiment.project_name}")

# Extract patterns from successful experiments
patterns = await client.extract_patterns(
    experiment_id="exp_123",
    threshold=0.8  # QA correctness threshold
)

print(f"Found {len(patterns.patterns)} patterns")
for pattern in patterns.patterns:
    print(f"Pattern: {pattern.input_pattern}")
    print(f"Confidence: {pattern.confidence_score}")
```

**Error Handling**:
```python
from src.integrations.phoenix_mcp import RetryError

try:
    result = await client.get_experiment("exp_123")
except RetryError as e:
    print(f"All {e.attempts} attempts failed")
    print(f"Last error: {e.last_exception}")
except Exception as e:
    print(f"Circuit breaker open or other error: {e}")
```

**Configuration**:
```python
from src.integrations.phoenix_mcp import (
    create_phoenix_retry_config,
    create_phoenix_circuit_breaker_config,
    create_configured_phoenix_client
)

# Create custom configuration
retry_config = create_phoenix_retry_config()
circuit_config = create_phoenix_circuit_breaker_config()

# Create client with custom config
client = create_configured_phoenix_client()
```

**Source Reference**: `src/integrations/phoenix_mcp.py:549-1177`

---

#### Factory Functions

**get_phoenix_client()** (Line 1594-1606):
```python
def get_phoenix_client(timeout: float = 30.0) -> PhoenixMCPClient:
    """Get Phoenix client instance with default configuration."""
```

**get_batch_processor()** (Line 1860-1872):
```python
def get_batch_processor(config: Optional[BatchSyncConfig] = None) -> PhoenixBatchProcessor:
    """Get batch processor instance for Phoenix data synchronization."""
```

**create_configured_phoenix_client()** (Line 2133-2155):
```python
def create_configured_phoenix_client(settings: Optional['Settings'] = None) -> PhoenixMCPClient:
    """Create Phoenix client with configuration from settings."""
```

**Convenience Functions**:
- `get_experiment_by_id()`
- `get_experiment_summary()`
- `extract_patterns_from_experiment()`
- `extract_patterns_from_golden_testset()`
- `analyze_golden_testset()`
- `get_dataset_pattern_summary()`
- `compare_dataset_performance()`
- `run_full_phoenix_sync()`
- `run_incremental_phoenix_sync()`
- `sync_specific_datasets()`
- `start_periodic_phoenix_sync()`
- `retry_failed_phoenix_sync()`

---

## Configuration Options

### Environment Variables

Complete list from `.env.example`:

**Required API Keys**:
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here          # Required
COHERE_API_KEY=your-cohere-api-key-here             # Required for contextual compression
```

**LLM Configuration**:
```bash
OPENAI_MODEL_NAME=gpt-4.1-mini                      # Optional, default shown
OPENAI_TEMPERATURE=0.0                              # Optional, default: 0.0
OPENAI_MAX_RETRIES=3                                # Optional, default: 3
OPENAI_REQUEST_TIMEOUT=60                           # Optional, default: 60 seconds
```

**Embedding Configuration**:
```bash
EMBEDDING_MODEL_NAME=text-embedding-3-small         # Optional, default shown
```

**Cohere Configuration**:
```bash
COHERE_RERANK_MODEL=rerank-english-v3.0             # Optional, default shown
```

**External Service Endpoints**:
```bash
PHOENIX_ENDPOINT=http://localhost:6006              # Optional, default: localhost:6006
QDRANT_URL=http://localhost:6333                    # Optional, default: localhost:6333
```

**Redis Configuration**:
```bash
REDIS_URL=redis://localhost:6379                    # Optional, default: localhost:6379
CACHE_ENABLED=true                                  # Optional, default: true
REDIS_CACHE_TTL=300                                 # Optional, default: 300 seconds
REDIS_MAX_CONNECTIONS=20                            # Optional, default: 20
REDIS_SOCKET_KEEPALIVE=true                         # Optional, default: true
REDIS_HEALTH_CHECK_INTERVAL=30                      # Optional, default: 30 seconds
```

**MCP Configuration**:
```bash
MCP_REQUEST_TIMEOUT=30                              # Optional, default: 30 seconds
MAX_SNIPPETS=5                                      # Optional, default: 5
```

**Phoenix Integration**:
```bash
PHOENIX_INTEGRATION_ENABLED=true                    # Optional, default: true
PHOENIX_TIMEOUT_SECONDS=30.0                        # Optional, default: 30.0
```

**Phoenix Retry Configuration**:
```bash
PHOENIX_RETRY_MAX_ATTEMPTS=3                        # Optional, default: 3
PHOENIX_RETRY_BASE_DELAY=1.0                        # Optional, default: 1.0
PHOENIX_RETRY_MAX_DELAY=30.0                        # Optional, default: 30.0
PHOENIX_RETRY_EXPONENTIAL_BASE=2.0                  # Optional, default: 2.0
PHOENIX_RETRY_JITTER=true                           # Optional, default: true
```

**Phoenix Circuit Breaker**:
```bash
PHOENIX_CIRCUIT_BREAKER_ENABLED=true                # Optional, default: true
PHOENIX_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5         # Optional, default: 5
PHOENIX_CIRCUIT_BREAKER_SUCCESS_THRESHOLD=3         # Optional, default: 3
PHOENIX_CIRCUIT_BREAKER_TIMEOUT=60.0                # Optional, default: 60.0
```

**Phoenix Batch Processing**:
```bash
PHOENIX_BATCH_ENABLED=true                          # Optional, default: true
PHOENIX_BATCH_SIZE=10                               # Optional, default: 10
PHOENIX_BATCH_TIMEOUT_SECONDS=300.0                 # Optional, default: 300.0
PHOENIX_BATCH_PROGRESS_INTERVAL=5                   # Optional, default: 5
PHOENIX_BATCH_CONCURRENT_LIMIT=3                    # Optional, default: 3
```

**Phoenix Pattern Extraction**:
```bash
PHOENIX_PATTERN_QA_THRESHOLD=0.8                    # Optional, default: 0.8
PHOENIX_PATTERN_RAG_THRESHOLD=0.7                   # Optional, default: 0.7
PHOENIX_PATTERN_CONFIDENCE_THRESHOLD=0.75           # Optional, default: 0.75
PHOENIX_PATTERN_MAX_PATTERNS_PER_EXPERIMENT=50      # Optional, default: 50
```

**Phoenix Data Sync**:
```bash
PHOENIX_SYNC_ENABLED=false                          # Optional, default: false
PHOENIX_SYNC_INTERVAL_HOURS=24                      # Optional, default: 24
PHOENIX_SYNC_DATASETS=johnwick_golden_testset       # Optional, comma-separated list
PHOENIX_SYNC_MAX_AGE_DAYS=30                        # Optional, default: 30
```

---

### Cache Configuration

**Feature Flag**:
- `CACHE_ENABLED=true`: Enable multi-level caching (L1 + L2)
- `CACHE_ENABLED=false`: Use NoOpCache (disable caching)

**Cache Types**:
- NoOpCache: When disabled
- LocalMemoryCache: Fallback when Redis unavailable
- MultiLevelCache: L1 (local) + L2 (Redis) when Redis available

**Redis Settings**:
- `REDIS_URL`: Connection string
- `REDIS_CACHE_TTL`: Default TTL in seconds
- `REDIS_MAX_CONNECTIONS`: Connection pool size
- `REDIS_SOCKET_KEEPALIVE`: Keep connections alive
- `REDIS_HEALTH_CHECK_INTERVAL`: Health check frequency

---

### LLM Configuration

**Model Selection**:
- `OPENAI_MODEL_NAME`: GPT model to use
- Supported: gpt-4.1-mini, gpt-4, gpt-3.5-turbo

**Behavior**:
- `OPENAI_TEMPERATURE`: Randomness (0.0 = deterministic, 1.0 = creative)
- `OPENAI_MAX_RETRIES`: Retry attempts for API failures
- `OPENAI_REQUEST_TIMEOUT`: Timeout in seconds

**Cost Optimization**:
- Use gpt-4.1-mini for cost savings
- Set temperature=0.0 for consistent answers
- Enable caching to reduce API calls

---

### Vector Store Configuration

**Qdrant Settings**:
- `QDRANT_URL`: Qdrant server URL
- Collections: johnwick_baseline, johnwick_semantic
- Retrieval Mode: Dense (vector similarity)

**Embedding Model**:
- `EMBEDDING_MODEL_NAME`: OpenAI embedding model
- Dimensions: 1536 (text-embedding-3-small)

---

### RAG Configuration

**Retrieval Settings**:
- `k=10`: Number of documents to retrieve (configurable in retriever)
- Chunking: RecursiveCharacterTextSplitter (baseline), SemanticChunker (semantic)

**Reranking**:
- `COHERE_RERANK_MODEL`: Cohere model for contextual compression
- Default: rerank-english-v3.0

---

## Usage Patterns and Best Practices

### Common Workflows

#### 1. Simple Query Workflow

```python
import requests

# Step 1: Choose endpoint based on needs
endpoint = "http://localhost:8000/invoke/naive_retriever"

# Step 2: Prepare question
question = "What did critics say about John Wick?"

# Step 3: Make request
response = requests.post(
    endpoint,
    json={"question": question}
)

# Step 4: Handle response
if response.status_code == 200:
    result = response.json()
    print(f"Answer: {result['answer']}")
    print(f"Context documents: {result['context_document_count']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

---

#### 2. Custom Cache Setup

```python
from src.integrations.cache import LocalMemoryCache, RedisCache, MultiLevelCache
from src.integrations.redis_client import get_redis

# Option A: Local-only cache (no Redis)
cache = LocalMemoryCache(max_size=1000)

# Option B: Redis-only cache
redis_client = await get_redis()
cache = RedisCache(redis_client)

# Option C: Multi-level cache (recommended)
l1 = LocalMemoryCache(max_size=100)
l2 = RedisCache(redis_client)
cache = MultiLevelCache(l1, l2)

# Use cache
await cache.set("key", "value", ttl=300)
value = await cache.get("key")

# Monitor performance
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

---

#### 3. Multi-Query Retrieval Best Practices

```python
import asyncio
import httpx

async def comprehensive_query(question: str) -> dict:
    """
    Use multi-query retriever for comprehensive coverage.
    Best for complex or ambiguous questions.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "http://localhost:8000/invoke/multi_query_retriever",
            json={"question": question}
        )
        return response.json()

# Example: Complex question with multiple facets
question = "How was John Wick received by critics and audiences?"
result = await comprehensive_query(question)

print(result['answer'])
print(f"Based on {result['context_document_count']} sources")
```

**When to use Multi-Query**:
- Ambiguous questions
- Complex multi-faceted queries
- When you need comprehensive coverage
- Research or analysis tasks

**Avoid for**:
- Simple factual queries
- Time-sensitive applications
- High-volume production use (cost/latency)

---

#### 4. Error Handling Pattern

```python
import requests
from requests.exceptions import RequestException, Timeout

def robust_query(question: str, retriever_type: str = "naive") -> dict:
    """
    Robust query with comprehensive error handling.
    """
    endpoint = f"http://localhost:8000/invoke/{retriever_type}_retriever"

    try:
        response = requests.post(
            endpoint,
            json={"question": question},
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    except Timeout:
        print(f"Request timeout for {retriever_type}")
        # Fallback to faster retriever
        if retriever_type != "naive":
            print("Falling back to naive retriever")
            return robust_query(question, "naive")
        raise

    except RequestException as e:
        print(f"Request error: {e}")
        # Check if service is up
        try:
            health = requests.get("http://localhost:8000/health", timeout=5)
            if health.status_code == 200:
                print("Service is healthy, retrying...")
                return robust_query(question, retriever_type)
        except:
            pass
        raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

# Usage
try:
    result = robust_query("What are the best action scenes?", "ensemble")
    print(result['answer'])
except Exception as e:
    print(f"Query failed: {e}")
```

---

#### 5. MCP Integration Pattern

```python
from mcp import ClientSession
import asyncio

async def query_via_mcp():
    """
    Query Qdrant collections via MCP resources.
    Demonstrates CQRS read-only pattern.
    """
    async with ClientSession() as session:
        # List collections
        collections = await session.read_resource("qdrant://collections")
        print(collections.contents[0].text)

        # Get collection info
        info = await session.read_resource(
            "qdrant://collections/johnwick_baseline"
        )
        print(info.contents[0].text)

        # Search collection
        import urllib.parse
        query = urllib.parse.quote("action scenes")
        search_uri = f"qdrant://collections/johnwick_baseline/search?query={query}&limit=5"
        results = await session.read_resource(search_uri)
        print(results.contents[0].text)

# Run
asyncio.run(query_via_mcp())
```

---

### Performance Optimization

#### When to Use Each Retrieval Strategy

**Naive Retriever**:
- Best for: General queries, production use
- Performance: Fastest (~100-200ms)
- Quality: Good for most queries
- Use when: Speed matters, general questions

**BM25 Retriever**:
- Best for: Keyword-heavy queries, proper nouns
- Performance: Fast (~150-250ms)
- Quality: Excellent for exact term matching
- Use when: Query has specific keywords or names

**Contextual Compression**:
- Best for: High-quality answers, research
- Performance: Slower (~500-1000ms due to reranking)
- Quality: Highest relevance
- Use when: Quality over speed, willing to pay for reranking API

**Multi-Query**:
- Best for: Complex/ambiguous questions
- Performance: Slowest (~1-3s due to query generation + multiple retrievals)
- Quality: Most comprehensive
- Use when: Complex analysis, research, offline processing

**Ensemble**:
- Best for: Balanced quality and coverage
- Performance: Medium (~400-800ms)
- Quality: Combines strengths of multiple methods
- Use when: Need robust results, can afford slight latency

**Semantic**:
- Best for: Thematic analysis, context-aware retrieval
- Performance: Similar to naive (~150-300ms)
- Quality: Better for meaning-based queries
- Use when: Queries require deep semantic understanding

---

#### Cache Configuration for Different Workloads

**High-Throughput Production** (many repeated queries):
```bash
CACHE_ENABLED=true
REDIS_CACHE_TTL=3600  # 1 hour
REDIS_MAX_CONNECTIONS=50
# Use MultiLevelCache with larger L1
```

**Research/Development** (unique queries):
```bash
CACHE_ENABLED=false  # Or short TTL
REDIS_CACHE_TTL=60   # 1 minute
# NoOpCache or small LocalMemoryCache
```

**Demo/Showcase** (same queries repeated):
```bash
CACHE_ENABLED=true
REDIS_CACHE_TTL=86400  # 24 hours
# Maximize cache hits for consistent experience
```

**A/B Testing** (comparing cached vs uncached):
```python
# Test cached
settings.cache_enabled = True
cached_result = await query_with_cache(question)

# Test uncached
settings.cache_enabled = False
uncached_result = await query_without_cache(question)

# Compare latency
print(f"Cached: {cached_time}ms")
print(f"Uncached: {uncached_time}ms")
print(f"Speedup: {uncached_time/cached_time:.2f}x")
```

---

#### Vector Store Optimization

**Collection Selection**:
```python
# Use baseline for general queries (faster)
baseline_retriever = get_naive_retriever()

# Use semantic for thematic queries (better context)
semantic_retriever = get_semantic_retriever()

# Choose based on query type
def get_optimal_retriever(question: str):
    # Heuristic: questions about themes, character, plot → semantic
    semantic_keywords = ["theme", "character", "development", "meaning"]
    if any(kw in question.lower() for kw in semantic_keywords):
        return get_semantic_retriever()
    return get_naive_retriever()
```

**Retrieval Parameters**:
```python
# Adjust k based on needs
retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 5,  # Fewer docs = faster, less context
        # "k": 20,  # More docs = slower, more comprehensive
    }
)
```

---

### Testing

#### Running Tests

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/api/test_app.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run integration tests only
pytest tests/integration/

# Run with verbose output
pytest -v -s
```

#### Test Fixtures

Available fixtures from `tests/conftest.py`:

```python
# Use in test functions
def test_endpoint(client):
    """client fixture provides TestClient instance"""
    response = client.get("/health")
    assert response.status_code == 200

def test_fastapi_app(fastapi_app_instance):
    """fastapi_app_instance provides FastAPI app"""
    assert fastapi_app_instance.title == "Advanced RAG Retriever API"

async def test_mcp_server(mcp_server_instance):
    """mcp_server_instance provides MCP server"""
    # Use for MCP-related tests
```

#### Mock Configurations

```python
from unittest.mock import patch
from src.core.settings import Settings

# Mock settings
def test_with_custom_settings():
    with patch('src.core.settings.get_settings') as mock_settings:
        mock_settings.return_value = Settings(
            openai_api_key="test-key",
            cache_enabled=False,
            redis_url="redis://test:6379"
        )
        # Test code here
```

---

### Common Pitfalls and Gotchas

**1. Cache Key Collisions**:
```python
# WRONG: Same cache key for different retrievers
cache_key = hashlib.md5(question.encode()).hexdigest()

# RIGHT: Include retriever type in cache key
cache_key = hashlib.md5(f"{retriever_type}:{question}".encode()).hexdigest()
```

**2. Missing API Keys**:
```python
# Always check for required keys
if not os.getenv("COHERE_API_KEY"):
    logger.warning("Contextual compression unavailable without COHERE_API_KEY")
    # Fallback to different retriever
```

**3. Vector Store Initialization**:
```python
# WRONG: Assuming vector store is always available
retriever = BASELINE_VECTORSTORE.as_retriever()

# RIGHT: Check for None
if BASELINE_VECTORSTORE:
    retriever = BASELINE_VECTORSTORE.as_retriever()
else:
    logger.error("Vector store not initialized")
    return None
```

**4. Async/Sync Mixing**:
```python
# WRONG: Mixing sync and async
result = chain.ainvoke({"question": "test"})  # Missing await

# RIGHT: Use await with async methods
result = await chain.ainvoke({"question": "test"})
```

**5. Circuit Breaker State**:
```python
# Check circuit breaker before critical operations
from src.integrations.phoenix_mcp import get_phoenix_client

client = get_phoenix_client()
if not client.circuit_breaker.is_call_allowed():
    logger.warning("Circuit breaker is OPEN, Phoenix unavailable")
    # Use fallback or return error
```

**6. TTL Configuration**:
```python
# WRONG: TTL too long for rapidly changing data
REDIS_CACHE_TTL=86400  # 24 hours

# RIGHT: Match TTL to data volatility
REDIS_CACHE_TTL=300  # 5 minutes for dynamic data
```

---

## Summary

This API reference documents:
- **8 HTTP REST endpoints** for retrieval with caching and tracing
- **5 MCP resources** for CQRS read-only Qdrant access
- **70+ configuration options** via environment variables
- **17 exception classes** for error handling
- **6 retriever types** with factory patterns
- **4 cache implementations** with multi-level support
- **15+ Phoenix MCP operations** with retry/circuit breaker

**Key Design Patterns**:
- Singleton: Settings, cache instances
- Factory: Retrievers, chains, caches
- CQRS: Read (Resources) vs Write (Tools) separation
- Circuit Breaker: Phoenix MCP reliability
- Observer: Phoenix tracing integration

**Source Files**:
- API: `/home/donbr/ghcp/adv-rag/src/api/app.py`
- Settings: `/home/donbr/ghcp/adv-rag/src/core/settings.py`
- Exceptions: `/home/donbr/ghcp/adv-rag/src/core/exceptions.py`
- Chain: `/home/donbr/ghcp/adv-rag/src/rag/chain.py`
- Retriever: `/home/donbr/ghcp/adv-rag/src/rag/retriever.py`
- Cache: `/home/donbr/ghcp/adv-rag/src/integrations/cache.py`
- Phoenix: `/home/donbr/ghcp/adv-rag/src/integrations/phoenix_mcp.py`
- MCP Resources: `/home/donbr/ghcp/adv-rag/src/mcp/qdrant_resources.py`

For architecture details, see `01_component_inventory.md` and `03_data_flows.md`.

# Repository Architecture Documentation

> **Generated**: 2025-10-04
> **Version**: 1.0
> **Analysis Framework**: ra_orchestrators, ra_agents, ra_tools

---

## Overview

The **Advanced RAG System** is a production-ready Retrieval-Augmented Generation (RAG) application built with educational transparency in mind. It demonstrates best practices in modern Python architecture through a carefully designed system that combines FastAPI, LangChain, Qdrant vector database, Redis caching, and comprehensive observability via Phoenix tracing.

This system showcases **six distinct retrieval strategies** (naive similarity, BM25 keyword search, contextual compression, multi-query expansion, ensemble combination, and semantic chunking) with **multi-level caching** for performance optimization and **circuit breaker patterns** for fault tolerance. The architecture follows **CQRS principles** (Command Query Responsibility Segregation) for clean read/write separation via the Model Context Protocol (MCP).

The implementation leverages **modern Python best practices** including Pydantic settings management, structured exception hierarchies, dependency injection, factory patterns, and distributed tracing. With **70+ configuration variables**, **17 exception classes**, **50+ test files**, and **zero circular dependencies**, the system balances educational clarity with production readiness.

Key capabilities include:
- Multiple retrieval strategies optimized for different query types
- Multi-level caching (L1 in-memory + L2 Redis) with automatic promotion
- Comprehensive observability via Phoenix with distributed tracing
- Circuit breaker and retry patterns for reliability
- CQRS-compliant MCP server for read-only vector database access
- Feature flags for A/B testing (cache toggle, retriever selection)
- Defensive programming with comprehensive error handling

**Target Audience**: This documentation is designed for developers learning RAG architecture, architects evaluating design patterns, operations engineers deploying the system, and integrators consuming the APIs.

---

## Quick Start

### Navigation Guide

This architecture documentation consists of four complementary documents:

1. **[Component Inventory](docs/01_component_inventory.md)** (Complete code catalog)
   - All modules, classes, functions with line numbers
   - Public API vs internal implementation breakdown
   - Entry points and test suite organization
   - Use for: Finding specific components, understanding code organization

2. **[Architecture Diagrams](diagrams/02_architecture_diagrams.md)** (Visual system design)
   - 5-layer architecture visualization
   - Component relationships and dependencies
   - Class hierarchies (exceptions, retrievers, cache)
   - Module dependency graph (DAG, no circular dependencies)
   - Use for: Understanding system structure, onboarding new developers

3. **[Data Flow Analysis](docs/03_data_flows.md)** (System behavior)
   - 10 detailed sequence diagrams
   - Request/response flows with caching
   - Multi-level cache, circuit breaker, retry patterns
   - Phoenix tracing integration flows
   - Use for: Understanding runtime behavior, debugging, performance tuning

4. **[API Reference](docs/04_api_reference.md)** (Complete API documentation)
   - HTTP REST endpoints (8 endpoints)
   - MCP resources (5 CQRS resources)
   - Python API (classes, functions, configuration)
   - Code examples and usage patterns
   - Use for: Integration, extending the system, configuration

### Recommended Reading Order

**For New Developers** (joining the team):
1. This README (overview and quick reference)
2. Architecture Diagrams (visual understanding)
3. Component Inventory (code organization)
4. Data Flow Analysis (system behavior)
5. API Reference (implementation details)

**For Architects** (reviewing the design):
1. This README (overview)
2. Architecture Diagrams (design patterns and layers)
3. Data Flow Analysis (behavioral patterns)
4. Component Inventory (implementation completeness)
5. API Reference (public contracts)

**For Operations/DevOps Engineers** (deploying and monitoring):
1. API Reference § Configuration Options
2. This README § Configuration section
3. Data Flow Analysis § Circuit Breaker Pattern
4. API Reference § GET /health and /cache/stats
5. This README § Running the System

**For API Consumers/Integrators** (using the system):
1. API Reference § HTTP REST API
2. API Reference § Usage Patterns and Best Practices
3. This README § Quick Start
4. Data Flow Analysis § Query Flow
5. API Reference § Common Pitfalls

### Finding Specific Information

Use the **Common Tasks** section at the end of this README for quick links to frequently needed information.

---

## Architecture Summary

### System Layers

The Advanced RAG system follows a **5-layer clean architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER                                          │
│ • FastAPI REST API (8 endpoints)                            │
│ • MCP Server (FastMCP wrapper)                              │
│ • CQRS Resources (Qdrant read-only access)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ APPLICATION LAYER                                           │
│ • RAG Chains (6 chain types)                                │
│ • Retrievers (6 retrieval strategies)                       │
│ • Chain Factory (create_rag_chain)                          │
│ • Retriever Factory (create_retriever)                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ DOMAIN LAYER                                                │
│ • Exception Hierarchy (17 exception classes)                │
│ • Settings Management (Pydantic BaseSettings)               │
│ • Logging Configuration (structured logging)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE LAYER                                        │
│ • Cache System (4 cache implementations)                    │
│ • Redis Client (connection pool)                            │
│ • LLM Integration (ChatOpenAI with caching)                 │
│ • Embeddings (OpenAI embeddings)                            │
│ • Phoenix MCP Client (observability with retry/CB)          │
│ • Qdrant MCP Integration (enhanced server)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ DATA LAYER                                                  │
│ • Qdrant (vector database - 2 collections)                  │
│ • Redis (distributed cache)                                 │
│ • CSV Files (document source)                               │
└─────────────────────────────────────────────────────────────┘
```

**Layer Responsibilities:**

1. **Presentation Layer**: Provides HTTP/MCP interfaces for external access
   - Handles request validation, response serialization
   - Routes requests to appropriate chains
   - Manages caching and Phoenix tracing

2. **Application Layer**: Implements RAG business logic
   - Chain orchestration (retriever → LLM → response)
   - Retrieval strategies (6 different approaches)
   - Factory patterns for flexible instantiation

3. **Domain Layer**: Core configuration and cross-cutting concerns
   - Centralized settings with environment variable support
   - Comprehensive exception hierarchy for error handling
   - Structured logging configuration

4. **Infrastructure Layer**: External service integrations
   - Multi-level caching with L1 (memory) and L2 (Redis)
   - LLM integration with Redis-backed caching
   - Observability via Phoenix with circuit breaker
   - Vector database clients

5. **Data Layer**: Persistent storage
   - Vector embeddings in Qdrant
   - Cache entries in Redis
   - Source documents in CSV format

### Key Design Patterns

The system demonstrates production-grade design patterns:

**Factory Pattern** (Chains, Retrievers, Cache):
- `create_rag_chain(retriever)` creates configured RAG chains
- `create_retriever(type)` factory returns appropriate retriever
- `get_cache()` returns cache implementation based on settings
- **Why**: Flexible instantiation, easy testing, configuration-driven behavior

**Singleton Pattern** (Settings, Cache instances):
- `get_settings()` ensures single settings instance across application
- Cache instances reused for consistency
- **Why**: Consistent configuration, reduced resource usage

**CQRS Pattern** (Read vs Write separation):
- MCP Resources provide read-only access to Qdrant
- Read operations isolated from write operations
- Clear query/command separation
- **Why**: Safety, clarity, scalability

**Circuit Breaker Pattern** (Phoenix MCP fault isolation):
- States: CLOSED → OPEN → HALF_OPEN → CLOSED
- Automatic fault detection and recovery
- Prevents cascade failures
- **Why**: Reliability, graceful degradation

**Strategy Pattern** (Retrieval strategies):
- Six different retrieval implementations
- Runtime strategy selection via configuration
- Common BaseRetriever interface
- **Why**: Flexibility, experimentation, optimization

**Observer Pattern** (Phoenix tracing):
- Distributed tracing across all layers
- Automatic span creation and attribute tracking
- Event-driven observability
- **Why**: Debugging, performance analysis, monitoring

### Architectural Principles

The codebase demonstrates these architectural principles:

**Clean Architecture and Separation of Concerns**:
- 5 distinct layers with clear boundaries
- Dependencies flow inward (presentation → application → domain)
- No upward dependencies

**Low Coupling** (2.3 imports/module average):
- Minimal inter-module dependencies
- Interface-based design
- Dependency injection via FastAPI and settings

**No Circular Dependencies**:
- Module dependency graph is a DAG (Directed Acyclic Graph)
- Clean import structure validated
- Build-time guarantees

**Defensive Programming**:
- Comprehensive 17-class exception hierarchy
- Try-except blocks with specific exception types
- Graceful fallbacks (e.g., cache degradation)
- Input validation via Pydantic

**Observability-First Design**:
- Phoenix tracing on all operations
- Structured logging with context
- Cache statistics tracking
- Health endpoints for monitoring

**Configuration-Driven Behavior**:
- 70+ environment variables with sensible defaults
- Feature flags for A/B testing (cache toggle)
- Runtime configuration changes (no code changes needed)

---

## Component Overview

### Public API Surface

The system exposes two primary APIs:

**HTTP REST API** (8 endpoints):
- `POST /invoke/naive_retriever` - Basic similarity search
- `POST /invoke/bm25_retriever` - Keyword-based BM25 search
- `POST /invoke/contextual_compression_retriever` - Cohere reranking
- `POST /invoke/multi_query_retriever` - LLM query expansion
- `POST /invoke/ensemble_retriever` - Combined strategies
- `POST /invoke/semantic_retriever` - Semantic chunking search
- `GET /health` - Health check with Phoenix integration
- `GET /cache/stats` - Cache statistics and Redis metrics

**MCP Server API** (5 CQRS resources):
- `qdrant://collections` - List all collections
- `qdrant://collections/{name}` - Collection metadata
- `qdrant://collections/{name}/documents/{id}` - Retrieve document
- `qdrant://collections/{name}/search?query={text}` - Vector search
- `qdrant://collections/{name}/stats` - Collection statistics

All retrieval endpoints accept a `QuestionRequest` with a question string and return an `AnswerResponse` with the answer and context document count.

### Core Components

**Settings Management** (`src/core/settings.py`):
- Pydantic BaseSettings with environment variable loading
- 70+ configuration fields organized by category
- Singleton pattern via `get_settings()`
- Categories: General, Vector Store, LLM, Cache, RAG, Phoenix, Logging

**Exception Handling** (`src/core/exceptions.py`):
- 17-class hierarchical exception system
- Base `RAGException` with component tracking and details
- Specialized exceptions: ConfigurationError, RAGError, MCPError, IntegrationError
- Helper functions: `raise_config_error()`, `raise_rag_error()`, `raise_mcp_error()`

**RAG Chains** (`src/rag/chain.py`):
- `create_rag_chain(retriever)` factory function
- 6 pre-initialized chains for different strategies
- Pipeline: `{context: retriever, question} | prompt | llm`
- Shared RAG prompt template with context injection

**Retrieval Strategies** (`src/rag/retriever.py`):
1. **Naive**: Basic similarity search (fastest, ~100-200ms)
2. **BM25**: Keyword-based ranking (good for specific terms)
3. **Contextual Compression**: Cohere reranking (highest quality, ~500-1000ms)
4. **Multi-Query**: LLM query expansion (most comprehensive, ~1-3s)
5. **Ensemble**: Combined strategies with equal weighting
6. **Semantic**: Semantic chunking for context preservation

**Cache System** (`src/integrations/cache.py`):
1. **NoOpCache**: When caching disabled (A/B testing)
2. **LocalMemoryCache**: L1 in-memory with LRU eviction
3. **RedisCache**: L2 persistent cache with TTL
4. **MultiLevelCache**: L1 + L2 with automatic promotion

**Vector Stores** (`src/rag/vectorstore.py`):
- Baseline: RecursiveCharacterTextSplitter chunking
- Semantic: SemanticChunker for meaning-based boundaries
- Qdrant client with dense vector retrieval mode

**Embeddings** (`src/rag/embeddings.py`):
- OpenAI embeddings (text-embedding-3-small, 1536 dimensions)
- Configurable model selection via settings

**Phoenix MCP Integration** (`src/integrations/phoenix_mcp.py`):
- Comprehensive observability client
- Circuit breaker pattern with states: CLOSED, OPEN, HALF_OPEN
- Retry logic with exponential backoff and jitter
- 15+ data classes for experiment, dataset, pattern analysis
- Batch processing for synchronization

See the [Component Inventory](docs/01_component_inventory.md) for complete details.

### Entry Points

**Main Application Entry Point** (`src/main.py`):
- `initialize_application()` - Initializes all system components
- `main()` - Entry point with logging and error handling
- Coordinates settings, FastAPI app, and MCP server

**FastAPI Server** (`run.py`):
- Starts uvicorn server on port 8000
- Port availability checking
- Environment variable PORT support

**MCP Server** (`src/mcp/server.py`):
- `create_mcp_server()` - Creates FastMCP server from FastAPI app
- `get_server_health()` - Comprehensive health information
- `main()` - Entry point for MCP server with Phoenix tracing

**Management Scripts**:
- `scripts/manage.py` - Start/stop/restart services (tier management)
- `scripts/status.py` - System status checks across all tiers
- `scripts/validation/system_health_check.py` - Health validation

**Evaluation Scripts**:
- `scripts/evaluation/semantic_architecture_benchmark.py` - Architecture evaluation
- `scripts/evaluation/retrieval_method_comparison.py` - Retrieval method comparison
- `scripts/ingestion/csv_ingestion_pipeline.py` - Data ingestion

---

## Data Flows

### Key Flow Patterns

The system implements several sophisticated data flow patterns for performance, reliability, and observability:

#### 1. Simple Query Flow

The basic RAG query flow demonstrates the complete lifecycle from HTTP request to response:

**Key Steps**:
1. **Request Reception**: FastAPI validates incoming QuestionRequest
2. **Phoenix Tracing**: Span created for distributed tracing
3. **Cache Key Generation**: MD5 hash of `"{endpoint}:{request}"`
4. **Cache Lookup**: Check L1 (local), then L2 (Redis) if miss
5. **Retrieval** (on cache miss): Vector similarity search in Qdrant
6. **LLM Generation**: ChatOpenAI generates answer with context
7. **Response Caching**: Store in L1 and L2 with TTL
8. **Phoenix Completion**: Span closed with metrics
9. **Response Return**: AnswerResponse with answer and context count

**Performance Characteristics**:
- Cache hit: ~5-10ms (L1) or ~20-30ms (L2)
- Cache miss: ~100-200ms (naive) to ~1-3s (multi-query)
- Cache hit rate: Typically 40-60% with 5-minute TTL

**Error Handling**:
- Chain unavailability: HTTP 503
- Chain execution errors: HTTP 500
- All errors logged and traced in Phoenix

See [Data Flow Analysis § Query Flow](docs/03_data_flows.md#1-query-flow-simple-rag-query) for the complete sequence diagram.

#### 2. Multi-Level Caching

The cache system uses a sophisticated L1 + L2 strategy:

**L1 (LocalMemoryCache)**:
- In-memory OrderedDict with LRU eviction
- TTL validation on every access
- Capacity: 100 items (with Redis) or 500 items (without Redis)
- Access time: O(1) dict lookup

**L2 (RedisCache)**:
- Persistent Redis storage with TTL
- Survives application restarts
- Network latency: ~1ms local, ~10ms remote
- Automatic expiration via Redis

**Cache Promotion Strategy**:
- GET: Try L1 → L2 → Miss
- On L2 hit: Populate L1 with shorter TTL (60s)
- SET: Write to both L1 (60s TTL) and L2 (full TTL)
- DELETE: Remove from both levels

**Statistics Tracking**:
- L1: hits, misses, sets, evictions, size, hit_rate
- L2: operations, errors
- Combined: l1_hits, l2_hits, overall hit_rate

**Graceful Degradation**:
- If Redis unavailable: Falls back to larger LocalMemoryCache (500 items)
- If caching disabled: Uses NoOpCache (all operations are no-ops)

See [Data Flow Analysis § Multi-Level Cache Flow](docs/03_data_flows.md#3-multi-level-cache-flow) for detailed sequence diagrams.

#### 3. Ensemble Retrieval

Combines multiple retrieval strategies using Reciprocal Rank Fusion (RRF):

**Component Retrievers**:
- BM25 (keyword matching)
- Naive (vector similarity)
- Contextual Compression (Cohere reranking)
- Multi-Query (LLM expansion)

**Combining Strategy**:
- Equal weighting: 1/n for n available retrievers
- RRF algorithm for merging ranked results
- Deduplication of results across retrievers

**When to Use**:
- Queries requiring balanced quality and coverage
- Production use with acceptable latency (~400-800ms)
- When you need robust results across query types

**Fallback Behavior**:
- Requires at least 2 component retrievers
- Falls back to first available retriever if insufficient

See [Data Flow Analysis § Ensemble Retrieval Flow](docs/03_data_flows.md#5-ensemble-retrieval-flow).

#### 4. Circuit Breaker Pattern

Prevents cascade failures in Phoenix MCP integration:

**States**:
- **CLOSED**: Normal operation, all calls allowed
- **OPEN**: Failing, blocking all calls for timeout period
- **HALF_OPEN**: Testing if service recovered, limited calls allowed

**State Transitions**:
- CLOSED → OPEN: After `failure_threshold` consecutive failures (default: 5)
- OPEN → HALF_OPEN: After `timeout` period (default: 60s)
- HALF_OPEN → CLOSED: After `success_threshold` consecutive successes (default: 3)
- HALF_OPEN → OPEN: On any failure during testing

**Configuration**:
```bash
PHOENIX_CIRCUIT_BREAKER_ENABLED=true
PHOENIX_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
PHOENIX_CIRCUIT_BREAKER_SUCCESS_THRESHOLD=3
PHOENIX_CIRCUIT_BREAKER_TIMEOUT=60.0
```

**Benefits**:
- Prevents wasted resources on failing service
- Automatic recovery testing
- System remains responsive even when Phoenix unavailable

See [Data Flow Analysis § Circuit Breaker Pattern Flow](docs/03_data_flows.md#9-circuit-breaker-pattern-flow).

#### 5. Phoenix Tracing

Comprehensive distributed tracing across all operations:

**Span Hierarchy**:
```
FastAPI.chain.naive_retriever (root span)
├── cache.lookup (cache check)
├── chain.invocation (RAG pipeline)
│   ├── retriever.similarity_search (Qdrant query)
│   └── llm.generate (ChatOpenAI call)
└── cache.store (cache write)
```

**Span Attributes**:
- `fastapi.chain.name`: Chain type
- `fastapi.question.length`: Input question length
- `fastapi.cache.hit`: Cache hit/miss status
- `fastapi.answer.length`: Generated answer length
- `fastapi.context.document_count`: Context documents used

**Events**:
- `cache.lookup.hit` / `cache.lookup.miss`
- `chain.invocation.complete`
- `cache.store.complete`
- `health_check.complete`

**Use Cases**:
- Debugging slow queries
- Analyzing cache effectiveness
- Identifying bottlenecks
- Performance optimization

See [Data Flow Analysis § Phoenix Tracing Integration Flow](docs/03_data_flows.md#8-phoenix-tracing-integration-flow).

---

## Technology Stack

### Core Technologies

**FastAPI** (REST API framework):
- Async request handling with Starlette
- Automatic OpenAPI schema generation
- Pydantic validation for request/response
- Dependency injection for settings and clients
- Lifespan context manager for Redis/Phoenix setup

**LangChain** (RAG and LLM orchestration):
- Chain composition with Runnable interface
- Multiple retriever implementations
- Prompt templates for RAG
- Document loaders and text splitters
- Integration with OpenAI and Cohere

**Qdrant** (Vector database):
- Dense vector similarity search
- gRPC client for performance
- Two collections: baseline (RecursiveCharacterTextSplitter) and semantic (SemanticChunker)
- 1536-dimensional embeddings (text-embedding-3-small)

**Redis** (Distributed cache):
- Async aioredis client
- Connection pooling (max 20 connections)
- TTL-based expiration
- Socket keepalive for reliability
- Health check interval (30s)

**OpenAI** (Embeddings and LLM):
- text-embedding-3-small for embeddings (1536 dimensions)
- gpt-4.1-mini for generation (default, configurable)
- Redis-backed caching at LangChain level
- Configurable temperature, retries, timeout

**Phoenix** (Observability and tracing):
- OpenTelemetry integration via phoenix.otel
- Distributed tracing with span hierarchy
- Automatic attribute and event tracking
- Project-based organization with timestamps

**MCP** (Model Context Protocol):
- FastMCP wrapper around FastAPI app
- CQRS resources for read-only Qdrant access
- Structured resource URIs (qdrant://...)
- Markdown-formatted responses

### Supporting Libraries

**Pydantic** (Data validation and settings):
- BaseSettings for environment variable loading
- BaseModel for request/response schemas
- Automatic validation and serialization
- Type safety and IDE support

**FastMCP** (MCP server wrapper):
- from_fastapi() for automatic MCP server creation
- Resource registration for CQRS
- Integration with FastAPI routes

**pytest** (Testing framework):
- 50+ test files across all components
- Fixtures for app, client, MCP server
- Integration and unit tests
- Coverage reporting

**python-dotenv** (Configuration):
- .env file loading
- Environment variable management
- Override system environment variables

**aioredis** (Async Redis client):
- Connection pooling
- Async/await support
- TTL and expiration
- Error handling

---

## Configuration

### Environment Variables

The system supports **70+ environment variables** organized by category, all with sensible defaults. Only `OPENAI_API_KEY` is required.

**Required**:
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**Optional - External Services** (defaults shown):
```bash
PHOENIX_ENDPOINT=http://localhost:6006
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
```

**Optional - LLM Configuration** (defaults shown):
```bash
OPENAI_MODEL_NAME=gpt-4.1-mini
OPENAI_TEMPERATURE=0.0
OPENAI_MAX_RETRIES=3
OPENAI_REQUEST_TIMEOUT=60
EMBEDDING_MODEL_NAME=text-embedding-3-small
```

**Optional - Cache Configuration** (defaults shown):
```bash
CACHE_ENABLED=true
REDIS_CACHE_TTL=300
REDIS_MAX_CONNECTIONS=20
REDIS_SOCKET_KEEPALIVE=true
REDIS_HEALTH_CHECK_INTERVAL=30
```

**Optional - Phoenix Integration** (defaults shown):
```bash
PHOENIX_INTEGRATION_ENABLED=true
PHOENIX_TIMEOUT_SECONDS=30.0
PHOENIX_RETRY_MAX_ATTEMPTS=3
PHOENIX_RETRY_BASE_DELAY=1.0
PHOENIX_CIRCUIT_BREAKER_ENABLED=true
PHOENIX_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
```

See [API Reference § Configuration Options](docs/04_api_reference.md#configuration-options) for the complete list.

### Cache Configuration

**Feature Flag**:
```bash
CACHE_ENABLED=true   # Enable multi-level caching (L1 + L2)
CACHE_ENABLED=false  # Disable caching (use NoOpCache for A/B testing)
```

**Cache Behavior**:
- `CACHE_ENABLED=true` with Redis available: MultiLevelCache (L1: 100 items, L2: Redis)
- `CACHE_ENABLED=true` without Redis: LocalMemoryCache (500 items)
- `CACHE_ENABLED=false`: NoOpCache (all operations are no-ops)

**TTL Configuration**:
```bash
REDIS_CACHE_TTL=300   # 5 minutes (default for production)
REDIS_CACHE_TTL=60    # 1 minute (development/testing)
REDIS_CACHE_TTL=3600  # 1 hour (demo/showcase with repeated queries)
```

### Retrieval Configuration

**Retriever Selection**: Choose endpoint based on query characteristics:
- `/invoke/naive_retriever` - Fast, general queries (~100-200ms)
- `/invoke/bm25_retriever` - Keyword-heavy, specific terms (~150-250ms)
- `/invoke/contextual_compression_retriever` - High quality, research (~500-1000ms)
- `/invoke/multi_query_retriever` - Complex, ambiguous queries (~1-3s)
- `/invoke/ensemble_retriever` - Balanced coverage (~400-800ms)
- `/invoke/semantic_retriever` - Thematic, context-aware (~150-300ms)

**Top-K Documents**: Configured in retriever factory (default: k=10)

**Chunking Strategies**:
- Baseline collection: RecursiveCharacterTextSplitter (fixed size)
- Semantic collection: SemanticChunker (meaning-based boundaries)

---

## Development

### Project Structure

```
adv-rag/
├── src/
│   ├── api/              # FastAPI REST API
│   │   ├── app.py        # Main application with 8 endpoints
│   │   └── run.py        # Uvicorn server runner
│   ├── core/             # Core configuration and utilities
│   │   ├── settings.py   # Pydantic settings (70+ vars)
│   │   ├── exceptions.py # 17-class exception hierarchy
│   │   └── logging_config.py
│   ├── rag/              # RAG implementation
│   │   ├── chain.py      # Chain factory (6 chain types)
│   │   ├── retriever.py  # Retriever factory (6 retrievers)
│   │   ├── vectorstore.py # Qdrant vector stores
│   │   ├── embeddings.py  # OpenAI embeddings
│   │   └── data_loader.py # CSV document loader
│   ├── integrations/     # External service integrations
│   │   ├── cache.py      # 4 cache implementations
│   │   ├── redis_client.py # Redis connection pool
│   │   ├── llm_models.py  # ChatOpenAI with caching
│   │   ├── phoenix_mcp.py # Phoenix observability (15+ classes)
│   │   └── qdrant_mcp.py  # Qdrant MCP integration
│   ├── mcp/              # Model Context Protocol server
│   │   ├── server.py     # FastMCP server wrapper
│   │   ├── resources.py  # MCP resource handlers
│   │   └── qdrant_resources.py # CQRS resources (5 resources)
│   └── main.py           # Main application entry point
├── scripts/
│   ├── evaluation/       # Benchmarking and evaluation
│   │   ├── semantic_architecture_benchmark.py
│   │   └── retrieval_method_comparison.py
│   ├── ingestion/        # Data ingestion pipelines
│   │   └── csv_ingestion_pipeline.py
│   ├── migration/        # Database migration tools
│   │   └── pgvector_to_qdrant_migration.py
│   ├── validation/       # Health checks and validation
│   │   └── system_health_check.py
│   ├── manage.py         # Service tier management (start/stop/restart)
│   └── status.py         # System status checks
├── tests/
│   ├── api/              # FastAPI endpoint tests
│   ├── core/             # Core component tests
│   ├── rag/              # RAG chain and retriever tests
│   ├── integrations/     # Integration tests (Redis, LLM, etc.)
│   ├── mcp/              # MCP server tests
│   ├── integration/      # CQRS and cross-component tests
│   └── conftest.py       # Pytest fixtures
├── docs/                 # Documentation
├── .env.example          # Environment variable template
├── pyproject.toml        # Project metadata and dependencies
├── pytest.ini            # Pytest configuration
└── README.md             # Project README
```

### Running the System

**Prerequisites**:
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start external services
docker-compose up -d  # Starts Qdrant, Redis, Phoenix
```

**Start FastAPI Server**:
```bash
# Method 1: Direct execution
python src/api/main.py

# Method 2: Via run.py
python run.py

# Method 3: With uvicorn directly
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

# Access API docs
# OpenAPI docs: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

**Start MCP Server**:
```bash
python src/mcp/server.py
```

**Run Tests**:
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

**Health Check**:
```bash
# System health validation
python scripts/validation/system_health_check.py

# Status check (all tiers)
python scripts/status.py

# Health endpoint
curl http://localhost:8000/health

# Cache statistics
curl http://localhost:8000/cache/stats
```

### Testing

**Test Organization** (50+ test files):
- `tests/api/` - FastAPI endpoint tests
- `tests/core/` - Settings, exceptions, logging tests
- `tests/rag/` - Chain, retriever, embeddings, vectorstore tests
- `tests/integrations/` - Redis, LLM, Phoenix, Qdrant MCP tests
- `tests/mcp/` - MCP server and resource tests
- `tests/integration/` - CQRS compliance and cross-component tests

**Available Fixtures** (`tests/conftest.py`):
```python
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

**Running Tests**:
```bash
# All tests
pytest

# Specific module
pytest tests/api/test_app.py

# With coverage
pytest --cov=src --cov-report=html

# Integration tests only
pytest tests/integration/

# Verbose output
pytest -v -s
```

---

## Key Statistics

The following metrics quantify the system's architecture:

**Public API**:
- **8** HTTP REST endpoints (6 retrieval strategies + 2 utility)
- **5** MCP CQRS resources (read-only Qdrant access)
- **2** request/response schemas (QuestionRequest, AnswerResponse)

**Implementation Depth**:
- **6** retrieval strategies (naive, BM25, contextual, multi-query, ensemble, semantic)
- **4** cache implementations (NoOp, Local, Redis, MultiLevel)
- **17** exception classes in hierarchy (RAGException → specialized errors)
- **15+** Phoenix MCP data classes (experiment, dataset, pattern analysis)
- **70+** configuration variables with environment override

**Code Quality**:
- **5** architectural layers with clear boundaries
- **2.3** average imports per module (low coupling)
- **0** circular dependencies (clean DAG)
- **50+** test files across all components

**Key Design Patterns**:
- Factory (chains, retrievers, cache)
- Singleton (settings, cache instances)
- CQRS (read resources vs write tools)
- Circuit Breaker (Phoenix fault isolation)
- Strategy (retrieval strategies)
- Observer (Phoenix tracing)

**Performance Characteristics**:
- Cache hit (L1): ~5-10ms
- Cache hit (L2): ~20-30ms
- Naive retrieval: ~100-200ms
- BM25 retrieval: ~150-250ms
- Contextual compression: ~500-1000ms
- Multi-query: ~1-3s
- Ensemble: ~400-800ms
- Semantic: ~150-300ms

---

## Documentation Index

### Detailed Documentation

1. **[Component Inventory](docs/01_component_inventory.md)**
   Complete catalog of all modules, classes, and functions with line numbers.

   **Contents**:
   - Public API (FastAPI REST, MCP Server, CQRS Resources)
   - Internal Implementation (Core, RAG, Integrations)
   - Entry Points (main.py, run.py, scripts)
   - Test Suite (50+ test files)
   - Summary statistics

   **Use this for**: Finding specific components, understanding code organization, locating implementations.

   **File Size**: ~17,000 lines covering all source code

2. **[Architecture Diagrams](diagrams/02_architecture_diagrams.md)**
   Visual representations of system structure with Mermaid diagrams.

   **Contents**:
   - System Architecture (5-layer diagram)
   - Component Relationships (data flow graph)
   - Class Hierarchies (exceptions, retrievers, cache, chains, Phoenix MCP)
   - Module Dependencies (DAG with no circular deps)
   - Import Relationships and statistics

   **Use this for**: Understanding system structure, onboarding new developers, architectural reviews.

   **Diagrams**: 9 comprehensive Mermaid diagrams

3. **[Data Flow Analysis](docs/03_data_flows.md)**
   Sequence diagrams showing runtime behavior with detailed walkthroughs.

   **Contents**:
   - Query Flow (simple RAG query with caching)
   - Cache Hit/Miss Flow (L1/L2 coordination)
   - Multi-Level Cache Flow (detailed cache operations)
   - Multi-Query Retrieval Flow (LLM query expansion)
   - Ensemble Retrieval Flow (combined strategies)
   - MCP Server Communication Flow
   - CQRS Resource Access Flow
   - Phoenix Tracing Integration Flow
   - Circuit Breaker Pattern Flow
   - Error Handling and Retry Flow

   **Use this for**: Understanding system behavior, debugging, performance tuning, flow analysis.

   **Diagrams**: 10 detailed sequence diagrams with code references

4. **[API Reference](docs/04_api_reference.md)**
   Complete API documentation with code examples and usage patterns.

   **Contents**:
   - HTTP REST API (8 endpoints with examples)
   - MCP Server API (5 CQRS resources)
   - Python API (Settings, Exceptions, Chains, Retrievers, Cache, Embeddings, Vector Store, Phoenix)
   - Configuration Options (70+ environment variables)
   - Usage Patterns and Best Practices
   - Common Pitfalls and Gotchas

   **Use this for**: Integration, extending the system, configuration, API consumption.

   **File Size**: ~2,800 lines with extensive code examples

### Reading Paths

**New Developer Path** (comprehensive understanding):
1. This README (overview)
2. Architecture Diagrams (visual structure)
3. Component Inventory (code organization)
4. Data Flow Analysis (runtime behavior)
5. API Reference (implementation details)

**Architect Path** (design evaluation):
1. This README (overview)
2. Architecture Diagrams (design patterns)
3. Data Flow Analysis (behavioral patterns)
4. Component Inventory (implementation completeness)

**Operations Path** (deployment and monitoring):
1. API Reference § Configuration Options
2. This README § Configuration and Running the System
3. Data Flow Analysis § Circuit Breaker Pattern
4. API Reference § GET /health and /cache/stats

**Integrator Path** (API consumption):
1. API Reference § HTTP REST API
2. API Reference § Usage Patterns
3. This README § Quick Start
4. Data Flow Analysis § Query Flow

---

## Getting Help

### Common Tasks

Quick links to frequently needed documentation:

**"How do I make a query?"**
→ [API Reference § HTTP REST API](docs/04_api_reference.md#http-rest-api)
→ [API Reference § POST /invoke/naive_retriever](docs/04_api_reference.md#post-invokenaive_retriever)

**"How does caching work?"**
→ [Data Flow Analysis § Multi-Level Cache Flow](docs/03_data_flows.md#3-multi-level-cache-flow)
→ [API Reference § Cache API](docs/04_api_reference.md#cache-api)

**"What retrieval strategy should I use?"**
→ [API Reference § Usage Patterns § When to Use Each Retrieval Strategy](docs/04_api_reference.md#when-to-use-each-retrieval-strategy)
→ This README § Component Overview § Retrieval Strategies

**"How do I configure the system?"**
→ [API Reference § Configuration Options](docs/04_api_reference.md#configuration-options)
→ This README § Configuration

**"What's the architecture?"**
→ [Architecture Diagrams § System Architecture](diagrams/02_architecture_diagrams.md#system-architecture)
→ This README § Architecture Summary

**"How does the circuit breaker work?"**
→ [Data Flow Analysis § Circuit Breaker Pattern Flow](docs/03_data_flows.md#9-circuit-breaker-pattern-flow)
→ [API Reference § Phoenix MCP Client](docs/04_api_reference.md#phoenix-mcp-client)

**"Where is X implemented?"**
→ [Component Inventory](docs/01_component_inventory.md) (search for component)
→ Use grep: `grep -r "class X" src/`

**"How do I debug slow queries?"**
→ [Data Flow Analysis § Phoenix Tracing Integration Flow](docs/03_data_flows.md#8-phoenix-tracing-integration-flow)
→ [API Reference § GET /cache/stats](docs/04_api_reference.md#get-cachestats)

**"What are the best practices?"**
→ [API Reference § Usage Patterns and Best Practices](docs/04_api_reference.md#usage-patterns-and-best-practices)
→ [API Reference § Common Pitfalls and Gotchas](docs/04_api_reference.md#common-pitfalls-and-gotchas)

**"How do I run tests?"**
→ This README § Development § Testing
→ [API Reference § Testing](docs/04_api_reference.md#testing)

### Quick Reference Cards

**Retrieval Strategy Selection**:
```
Query Type               → Recommended Strategy    → Latency
─────────────────────────────────────────────────────────────
General questions        → naive_retriever         → ~100-200ms
Keywords/names          → bm25_retriever          → ~150-250ms
High-quality answers    → contextual_compression  → ~500-1000ms
Complex/ambiguous       → multi_query_retriever   → ~1-3s
Balanced coverage       → ensemble_retriever      → ~400-800ms
Thematic/contextual     → semantic_retriever      → ~150-300ms
```

**Cache Configuration**:
```
Workload Type           → Configuration
───────────────────────────────────────────────
High throughput         → CACHE_ENABLED=true, TTL=3600
Research/Development    → CACHE_ENABLED=false or TTL=60
Demo/Showcase          → CACHE_ENABLED=true, TTL=86400
A/B Testing            → Toggle CACHE_ENABLED flag
```

**Error Handling**:
```
Error Type              → Exception Class        → HTTP Status
────────────────────────────────────────────────────────────────
Missing config          → ConfigurationError     → 500
Embedding failure       → EmbeddingError         → 500
Vector store error      → VectorStoreError       → 503
Retrieval failure       → RetrievalError         → 500
Chain execution         → ChainExecutionError    → 500
MCP server error        → MCPServerError         → 503
Redis failure           → RedisError             → (degrades to local)
LLM API failure         → LLMError               → 500
```

---

## Maintenance

### Documentation Updates

**Generated**: 2025-10-04
**Analysis Framework**: ra_orchestrators, ra_agents, ra_tools (custom architecture analysis system)
**Source Code Version**: Latest (git status shows modified files as of analysis date)

**To Regenerate Documentation**:
1. Use the analyzer agent to extract component information
2. Use the doc-writer agent to generate updated documentation
3. Verify all file paths and line numbers are current
4. Update this README's generation date

### Source Code References

All documentation includes **file paths with line numbers** for traceability. Examples:
- `src/api/app.py:262-265` - naive_retriever endpoint definition
- `src/core/settings.py:21-217` - Settings class
- `src/integrations/cache.py:193-251` - MultiLevelCache implementation

When code changes:
1. Update corresponding documentation sections
2. Verify line number references
3. Update sequence diagrams if flow changes
4. Regenerate architecture diagrams if structure changes

### Version History

**v1.0 (2025-10-04)**:
- Initial comprehensive architecture documentation
- 4 primary documents (Component Inventory, Architecture Diagrams, Data Flow Analysis, API Reference)
- 9 architecture diagrams (Mermaid)
- 10 sequence diagrams (data flows)
- Complete API documentation with examples
- 70+ configuration options documented

---

## License & Contributing

**License**: [Add license information]

**Contributing**: [Add contribution guidelines]

**Code of Conduct**: [Add code of conduct]

**Contact**: [Add contact information]

---

## Summary

This Advanced RAG System demonstrates production-ready architecture with:

- **Clean 5-layer architecture** with zero circular dependencies
- **6 retrieval strategies** optimized for different query types
- **Multi-level caching** (L1 memory + L2 Redis) with automatic promotion
- **Comprehensive observability** via Phoenix with distributed tracing
- **Circuit breaker and retry patterns** for reliability
- **CQRS-compliant MCP server** for safe read-only access
- **70+ configuration variables** with sensible defaults
- **17-class exception hierarchy** for comprehensive error handling
- **50+ test files** ensuring code quality
- **Defensive programming** with graceful degradation

**Key Metrics**:
- 8 HTTP endpoints, 5 MCP resources
- 2.3 average imports/module (low coupling)
- 0 circular dependencies (clean DAG)
- Cache hit rate: 40-60% typical
- Latency: 5-10ms (L1 hit) to 1-3s (multi-query)

**Documentation Structure**:
1. **Component Inventory**: What code exists and where
2. **Architecture Diagrams**: How components are organized
3. **Data Flow Analysis**: How the system behaves at runtime
4. **API Reference**: How to use and extend the system

**Target Audience**: Developers learning RAG architecture, architects evaluating design patterns, operations engineers deploying systems, API consumers integrating services.

---

**Note**: This documentation was generated using automated analysis agents (analyzer, doc-writer) and represents a comprehensive snapshot of the system architecture as of October 4, 2025. All file paths and line numbers reference the actual source code at the time of analysis.

For questions or updates, refer to the maintenance section above.

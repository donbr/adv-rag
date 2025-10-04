# Component Inventory

## Public API

### FastAPI REST Interface
**File:** `/home/donbr/ghcp/adv-rag/src/api/app.py`

The main public-facing API providing HTTP endpoints for retrieval operations.

#### API Endpoints

1. **POST /invoke/naive_retriever** (Line 262-265)
   - Operation ID: `naive_retriever`
   - Purpose: Basic similarity search using vector store
   - Request: `QuestionRequest` (question: str)
   - Response: `AnswerResponse` (answer: str, context_document_count: int)

2. **POST /invoke/bm25_retriever** (Line 267-270)
   - Operation ID: `bm25_retriever`
   - Purpose: Keyword-based search using BM25 algorithm
   - Request: `QuestionRequest`
   - Response: `AnswerResponse`

3. **POST /invoke/contextual_compression_retriever** (Line 272-275)
   - Operation ID: `contextual_compression_retriever`
   - Purpose: Compressed context using Cohere reranking
   - Request: `QuestionRequest`
   - Response: `AnswerResponse`

4. **POST /invoke/multi_query_retriever** (Line 277-280)
   - Operation ID: `multi_query_retriever`
   - Purpose: Enhanced query expansion with LLM
   - Request: `QuestionRequest`
   - Response: `AnswerResponse`

5. **POST /invoke/ensemble_retriever** (Line 282-285)
   - Operation ID: `ensemble_retriever`
   - Purpose: Combines multiple retrieval strategies
   - Request: `QuestionRequest`
   - Response: `AnswerResponse`

6. **POST /invoke/semantic_retriever** (Line 287-290)
   - Operation ID: `semantic_retriever`
   - Purpose: Advanced semantic search using semantic chunking
   - Request: `QuestionRequest`
   - Response: `AnswerResponse`

7. **GET /health** (Line 292-308)
   - Purpose: Health check endpoint with Phoenix tracing integration
   - Response: Status, timestamp, Phoenix integration details

8. **GET /cache/stats** (Line 310-359)
   - Purpose: Cache statistics and Redis metrics
   - Response: Cache type, stats, Redis info if available

#### Key Classes

- **QuestionRequest** (Line 167-168): Request model for question queries
- **AnswerResponse** (Line 170-172): Response model with answer and context count

#### Key Functions

- **generate_cache_key()** (Line 48-51): Creates MD5 hash cache keys
- **get_cached_response()** (Line 53-59): Retrieves cached responses
- **cache_response()** (Line 61-75): Stores responses in cache with TTL
- **invoke_chain_logic()** (Line 174-260): Core chain invocation with caching and tracing
- **lifespan()** (Line 77-158): FastAPI lifecycle management with Redis and Phoenix setup

#### Dependencies
- `src.core.settings.get_settings`
- `src.integrations.redis_client` (redis_client, get_redis)
- `src.integrations.cache` (get_cache, CacheInterface)
- `src.rag.chain` (all chain instances)
- `phoenix.otel.register` (observability)

---

### MCP Server Interface
**File:** `/home/donbr/ghcp/adv-rag/src/mcp/server.py`

FastMCP-based Model Context Protocol server wrapping the FastAPI application.

#### Key Functions

1. **create_mcp_server()** (Line 36-153)
   - Purpose: Creates MCP server from FastAPI app using FastMCP.from_fastapi()
   - Returns: FastMCP server instance
   - Features: Enhanced Phoenix tracing, path setup, error handling

2. **get_server_health()** (Line 203-288)
   - Purpose: Comprehensive server health information
   - Returns: Health status dict with Phoenix integration details
   - Includes: CQRS resources, system info, version

3. **main()** (Line 290-365)
   - Purpose: Entry point for MCP server with enhanced tracing
   - Starts: MCP server with health monitoring

#### CQRS Resources Registered

- `qdrant://collections` - List all collections
- `qdrant://collections/{collection_name}` - Get collection info
- `qdrant://collections/{collection_name}/documents/{point_id}` - Retrieve document
- `qdrant://collections/{collection_name}/search?query={text}&limit={n}` - Search collection
- `qdrant://collections/{collection_name}/stats` - Collection statistics

#### Dependencies
- `src.core.settings.get_settings`
- `src.api.app.app` (FastAPI application)
- `src.mcp.qdrant_resources` (CQRS resource functions)
- `fastmcp.FastMCP`
- `phoenix.otel.register`

---

### MCP Resources
**File:** `/home/donbr/ghcp/adv-rag/src/mcp/resources.py`

Enhanced MCP resource implementation for RAG chain access.

#### Key Functions

1. **setup_project_path()** (Line 34-49)
   - Purpose: Add project root to Python path with environment variable support
   - Supports: PROJECT_ROOT env var, fallback to relative path

2. **extract_operation_ids_from_fastapi()** (Line 66-79)
   - Purpose: Extract operation_ids from FastAPI for consistent naming
   - Returns: Dict mapping method names to operation IDs

3. **get_chain_by_method()** (Line 117-123)
   - Purpose: Get appropriate chain instance by method name
   - Raises: ValueError for unknown methods

4. **get_operation_id_for_method()** (Line 125-127)
   - Purpose: Get FastAPI operation_id for a given method

5. **safe_escape_markdown()** (Line 129-139)
   - Purpose: Safely escape text for Markdown using HTML escaping

6. **generate_secure_query_hash()** (Line 141-143)
   - Purpose: Generate secure, privacy-safe query hash for logging

7. **extract_context_snippets()** (Line 145-150+)
   - Purpose: Extract and format context document snippets

8. **format_rag_content()** (Line 191+)
   - Purpose: Format RAG results as structured Markdown

9. **create_resource_handler()** (Line 264+)
   - Purpose: Create dynamic resource handler for each retrieval method

10. **health_check()** (Line 499+)
    - Purpose: Async health check resource

#### Global Variables
- `CHAIN_MAPPING` (Line 85-92): Maps method names to chain instances
- `METHOD_TO_OPERATION_ID` (Line 95-102): Maps methods to FastAPI operation IDs
- `RETRIEVAL_METHODS` (Line 105): List of available retrieval methods
- `REQUEST_TIMEOUT`, `MAX_SNIPPETS`, `QUERY_HASH_LENGTH` (Line 109-111): Configuration

---

### Qdrant CQRS Resources
**File:** `/home/donbr/ghcp/adv-rag/src/mcp/qdrant_resources.py`

CQRS-compliant read-only access to Qdrant vector database.

#### Key Classes

**QdrantResourceProvider** (Line 39-68)
- Purpose: CQRS-compliant resource provider for read-only Qdrant access
- Methods:
  - `get_collection_info()` (Line 70+): Get collection metadata and statistics
  - `get_document()`: Retrieve document by ID
  - `search_collection()`: Raw vector similarity search
  - `get_collection_stats()`: Collection statistics
  - `list_collections()`: List all collections

#### Async Resource Functions (Line 562+)
- **get_collection_info_resource()** (Line 562): Collection metadata
- **get_document_resource()** (Line 566): Document retrieval by point ID
- **search_collection_resource()** (Line 570): Search with query
- **get_collection_stats_resource()** (Line 574): Collection statistics
- **list_collections_resource()** (Line 578): List all collections

#### Dependencies
- `src.core.settings.get_settings`
- `src.rag.embeddings.get_openai_embeddings`
- `qdrant_client.QdrantClient`

---

## Internal Implementation

### Core Module

#### Settings Management
**File:** `/home/donbr/ghcp/adv-rag/src/core/settings.py`

Centralized configuration using Pydantic BaseSettings.

**Settings Class** (Line 21-217)
- Purpose: Application settings with environment variable loading
- Key Attributes:
  - `openai_api_key`: OpenAI API key (required)
  - `openai_model_name`: Default "gpt-4.1-mini" (Line 26)
  - `embedding_model_name`: Default "text-embedding-3-small" (Line 35)
  - `phoenix_endpoint`: Default "http://localhost:6006" (Line 41)
  - `qdrant_url`: Default "http://localhost:6333" (Line 42)
  - `redis_url`: Default "redis://localhost:6379" (Line 45)
  - `cache_enabled`: Feature flag for caching (Line 52-55)
  - Phoenix integration settings (Line 62-196)
  - Redis configuration (Line 44-49)

**Key Functions:**
- **get_settings()** (Line 222-227): Singleton settings instance
- **get_env_variable()** (Line 229-237): Get environment variable with logging
- **setup_env_vars()** (Line 239-258): Setup OpenAI and Cohere API keys

#### Exception Hierarchy
**File:** `/home/donbr/ghcp/adv-rag/src/core/exceptions.py`

Custom exception classes for error handling.

**Exception Classes:**
- **RAGException** (Line 14-26): Base exception for all RAG errors
- **ConfigurationError** (Line 29-31): Configuration/settings errors
- **RAGError** (Line 34-36): Base for RAG-related errors
  - **EmbeddingError** (Line 39-41): Embedding operations
  - **VectorStoreError** (Line 44-46): Vector store operations
  - **RetrievalError** (Line 49-51): Document retrieval
  - **ChainExecutionError** (Line 54-56): RAG chain execution
- **MCPError** (Line 59-61): Base for MCP-related errors
  - **MCPServerError** (Line 64-66): MCP server operations
  - **MCPTransportError** (Line 69-71): MCP transport layer
  - **MCPResourceError** (Line 74-76): MCP resource operations
- **IntegrationError** (Line 79-81): Base for external service errors
  - **RedisError** (Line 84-86): Redis operations
  - **LLMError** (Line 89-91): LLM API calls

**Helper Functions:**
- **raise_config_error()** (Line 95-98): Raise configuration error
- **raise_rag_error()** (Line 101-108): Raise RAG error with context
- **raise_mcp_error()** (Line 111-114): Raise MCP error with server type

#### Logging Configuration
**File:** `/home/donbr/ghcp/adv-rag/src/core/logging_config.py`

**ConsoleFilter Class** (Line 10): Filter for console-specific logging
**setup_logging()** (Line 32+): Configure logging with file and console handlers

---

### RAG Module

#### Chain Factory
**File:** `/home/donbr/ghcp/adv-rag/src/rag/chain.py`

Creates and manages RAG chains for different retrieval strategies.

**Key Functions:**
- **get_chat_model_lazy()** (Line 24-30): Lazy initialization of chat model
- **create_rag_chain()** (Line 47-62): Create RAG chain from retriever

**Global Chain Instances:**
- `RAG_PROMPT` (Line 45): Chat prompt template
- `NAIVE_RETRIEVAL_CHAIN` (Line 66): Basic similarity search chain
- `BM25_RETRIEVAL_CHAIN` (Line 67): BM25 keyword search chain
- `CONTEXTUAL_COMPRESSION_CHAIN` (Line 68): Contextual compression chain
- `MULTI_QUERY_CHAIN` (Line 69): Multi-query expansion chain
- `ENSEMBLE_CHAIN` (Line 70): Ensemble retrieval chain
- `SEMANTIC_CHAIN` (Line 71): Semantic chunking chain

**Dependencies:**
- `src.integrations.llm_models.get_chat_model`
- `src.rag.retriever` (all retriever functions)

#### Retriever Factory
**File:** `/home/donbr/ghcp/adv-rag/src/rag/retriever.py`

Factory for creating various retriever types.

**Global Variables:**
- `DOCUMENTS` (Line 29): Loaded documents
- `CHAT_MODEL` (Line 31): Chat model instance
- `BASELINE_VECTORSTORE` (Line 35): Main vector store
- `SEMANTIC_VECTORSTORE` (Line 36): Semantic vector store

**Retriever Functions:**
- **get_naive_retriever()** (Line 51-56): Basic similarity search
- **get_bm25_retriever()** (Line 58-69): BM25 keyword search
- **get_contextual_compression_retriever()** (Line 71-90): Contextual compression with Cohere
- **get_multi_query_retriever()** (Line 92-106): Multi-query expansion
- **get_semantic_retriever()** (Line 108-113): Semantic search
- **get_ensemble_retriever()** (Line 115-145): Ensemble of multiple retrievers
- **create_retriever()** (Line 148-187): Factory function for retriever creation

**Dependencies:**
- `src.core.settings.get_settings`
- `src.rag.data_loader.load_documents`
- `src.integrations.llm_models.get_chat_model`
- `src.rag.embeddings.get_openai_embeddings`
- `src.rag.vectorstore` (get_main_vectorstore, get_semantic_vectorstore)

#### Embeddings
**File:** `/home/donbr/ghcp/adv-rag/src/rag/embeddings.py`

**get_openai_embeddings()** (Line 8-17)
- Purpose: Initialize OpenAI embeddings model
- Model: Configured via settings.embedding_model_name
- Returns: OpenAIEmbeddings instance

#### Vector Store
**File:** `/home/donbr/ghcp/adv-rag/src/rag/vectorstore.py`

**Key Functions:**
- **get_main_vectorstore()** (Line 25-48): Create/load baseline vector store (RecursiveCharacterTextSplitter)
- **get_semantic_vectorstore()** (Line 49+): Create/load semantic vector store (SemanticChunker)

**Dependencies:**
- `src.core.settings.get_settings`
- `src.rag.data_loader.load_documents`
- `src.rag.embeddings.get_openai_embeddings`

#### Data Loader
**File:** `/home/donbr/ghcp/adv-rag/src/rag/data_loader.py`

**Key Functions:**
- **download_file()** (Line 23-35): Download CSV files from URLs
- **ensure_data_files_exist()** (Line 37-75): Ensure data files are available
- **load_documents()** (Line 77+): Load CSV documents with CSVLoader

---

### Integrations Module

#### Cache Abstraction
**File:** `/home/donbr/ghcp/adv-rag/src/integrations/cache.py`

Lightweight cache abstraction layer for A/B testing.

**Cache Interface Classes:**
- **CacheInterface** (Line 26-47): Abstract base class
  - `get()`: Get value from cache
  - `set()`: Set value with TTL
  - `delete()`: Delete key
  - `get_stats()`: Get cache statistics

**Implementations:**
- **NoOpCache** (Line 50-77): No-operation cache when disabled
- **LocalMemoryCache** (Line 80-144): L1 in-memory cache with TTL and LRU
- **RedisCache** (Line 147-190): L2 Redis cache wrapper
- **MultiLevelCache** (Line 193-251): Multi-level L1+L2 cache

**Factory Function:**
- **get_cache()** (Line 254-281): Get appropriate cache implementation based on settings

**Utility Functions:**
- **cache_get()** (Line 285-288): Get from default cache instance
- **cache_set()** (Line 291-294): Set in default cache instance
- **cache_delete()** (Line 297-300): Delete from default cache instance

#### Redis Client
**File:** `/home/donbr/ghcp/adv-rag/src/integrations/redis_client.py`

**RedisClient Class** (Line 15+)
- Purpose: Manage Redis connection pool
- Methods: connect(), disconnect(), get_client()

**Async Functions:**
- **get_redis()** (Line 66-79): Get Redis client dependency
- **redis_lifespan()** (Line 81-88): Redis connection lifecycle
- **cache_set()** (Line 90-97): Set key with TTL
- **cache_get()** (Line 99-106): Get key value
- **cache_delete()** (Line 108-115): Delete key

#### LLM Models
**File:** `/home/donbr/ghcp/adv-rag/src/integrations/llm_models.py`

**Key Functions:**
- **get_chat_openai()** (Line 11-47): Initialize ChatOpenAI with Redis caching
- **get_chat_model()** (Line 49+): Alias for get_chat_openai()

**Dependencies:**
- `src.core.settings.get_settings`

#### Phoenix MCP Client
**File:** `/home/donbr/ghcp/adv-rag/src/integrations/phoenix_mcp.py`

Comprehensive Phoenix observability integration with error handling.

**Error Handling Classes:**
- **RetryError** (Line 29-35): Retry operation errors
- **CircuitBreakerState** (Line 37-42): Circuit breaker states enum
- **RetryConfig** (Line 45-53): Retry configuration dataclass
- **CircuitBreakerConfig** (Line 55-60): Circuit breaker configuration
- **CircuitBreaker** (Line 62-182): Circuit breaker implementation

**Data Classes:**
- **PhoenixExperiment** (Line 184-193): Experiment metadata
- **PhoenixExperimentResult** (Line 195-208): Experiment results
- **PhoenixDataset** (Line 210-218): Dataset metadata
- **ExtractedPattern** (Line 220-262): Extracted pattern with validation
- **PatternExtractionResult** (Line 264-281): Pattern extraction result
- **DatasetAnalysisResult** (Line 283-315): Dataset analysis result
- **GoldenTestsetAnalysis** (Line 317-340): Golden testset analysis
- **BatchSyncConfig** (Line 342-380): Batch sync configuration
- **SyncState** (Line 382-475): Synchronization state tracking
- **BatchSyncResult** (Line 477-547): Batch synchronization result

**Main Client Class:**
- **PhoenixMCPClient** (Line 549-1177): Core Phoenix MCP client with retry/circuit breaker
- **PhoenixBatchProcessor** (Line 1179-1592): Batch processing for Phoenix data

**Factory Functions:**
- **get_phoenix_client()** (Line 1594-1606): Get Phoenix client instance
- **get_batch_processor()** (Line 1860-1872): Get batch processor instance

**Convenience Functions:**
- **get_experiment_by_id()** (Line 1608-1620): Get experiment by ID
- **get_experiment_summary()** (Line 1622-1635): Get experiment summary
- **extract_patterns_from_experiment()** (Line 1637-1657): Extract patterns from experiment
- **extract_patterns_from_golden_testset()** (Line 1659-1699): Extract from golden testset
- **analyze_golden_testset()** (Line 1701-1728): Analyze golden testset
- **get_dataset_pattern_summary()** (Line 1730-1797): Dataset pattern summary
- **compare_dataset_performance()** (Line 1799-1858): Compare datasets
- **run_full_phoenix_sync()** (Line 1875-1897): Full synchronization
- **run_incremental_phoenix_sync()** (Line 1899-1921): Incremental sync
- **sync_specific_datasets()** (Line 1923-1947): Sync specific datasets
- **start_periodic_phoenix_sync()** (Line 1949-1990): Periodic sync
- **retry_failed_phoenix_sync()** (Line 1992-2016): Retry failed sync

**Configuration Functions:**
- **create_batch_sync_config()** (Line 2018-2056): Create batch sync config
- **create_phoenix_retry_config()** (Line 2058-2078): Create retry config
- **create_phoenix_circuit_breaker_config()** (Line 2080-2098): Create circuit breaker config
- **create_phoenix_batch_config()** (Line 2100-2131): Create batch config
- **create_configured_phoenix_client()** (Line 2133-2155): Create configured client
- **create_configured_batch_processor()** (Line 2157-2190): Create configured processor
- **validate_phoenix_configuration()** (Line 2192+): Validate configuration

#### Qdrant MCP Integration
**File:** `/home/donbr/ghcp/adv-rag/src/integrations/qdrant_mcp.py`

**Data Classes:**
- **ValidationMetadata** (Line 44-55): Validation metadata for patterns
- **EnhancedQdrantPattern** (Line 57-65): Enhanced pattern with Phoenix compatibility
- **EnhancedQdrantMCPServer** (Line 67+): Enhanced Qdrant MCP server

**Factory Function:**
- **create_enhanced_qdrant_mcp_server()** (Line 477+): Create enhanced Qdrant MCP server

---

## Entry Points

### Main Application Entry Point
**File:** `/home/donbr/ghcp/adv-rag/src/main.py`

**Purpose:** Central entry point coordinating all system components

**Key Functions:**
- **initialize_application()** (Line 34-55)
  - Purpose: Initialize complete Advanced RAG application
  - Returns: Dict with initialized components (settings, version, fastapi_app, mcp_server)

- **main()** (Line 58-73)
  - Purpose: Main entry point with logging and error handling
  - Sets up: Logging, initializes all components

**Dependencies:**
- `src.core.logging_config.setup_logging`
- `src.core.settings.get_settings`
- `src.api.app.app`
- `src.mcp.server.create_mcp_server`

---

### FastAPI Server Startup
**File:** `/home/donbr/ghcp/adv-rag/run.py`

**Purpose:** Start FastAPI server with uvicorn

**Key Functions:**
- **check_port_available()** (Line 35-46)
  - Purpose: Check if port is available for binding
  - Args: port (int), host (str)
  - Returns: bool

**Main Execution** (Line 49-83)
- Checks port availability
- Handles PORT environment variable
- Starts uvicorn server on port 8000 (default)

**Dependencies:**
- `src.api.app.app`
- `src.core.logging_config.setup_logging`

---

### MCP Server Startup
**File:** `/home/donbr/ghcp/adv-rag/src/mcp/server.py`

**Main Function:** `main()` (Line 290-365)
- Entry point for MCP server with enhanced Phoenix tracing
- Starts MCP server with health monitoring

**Usage:** `python -m src.mcp.server`

---

### Management Scripts

#### System Manager
**File:** `/home/donbr/ghcp/adv-rag/scripts/manage.py`

**TierManager Class** (Line 26-372)
- Purpose: Manage application tiers (start, stop, restart, clean)

**Key Methods:**
- `status()` (Line 33-46): Check tier status
- `start()` (Line 48-64): Start services
- `stop()` (Line 65-78): Stop services
- `restart()` (Line 80-85): Restart services
- `clean()` (Line 87-103): Clean up orphaned processes

**main()** (Line 373+): CLI entry point for tier management

**Usage:** `python scripts/manage.py [start|stop|restart|clean] [--tier N]`

#### System Status
**File:** `/home/donbr/ghcp/adv-rag/scripts/status.py`

**TierStatus Class** (Line 39+)
- Purpose: Check status of all system tiers

**Colors Class** (Line 29-37): Terminal color constants

**main()** (Line 623+): Display comprehensive system status

**Usage:** `python scripts/status.py`

#### Health Check
**File:** `/home/donbr/ghcp/adv-rag/scripts/validation/system_health_check.py`

**HealthChecker Class** (Line 34-209)
- Purpose: Comprehensive system health validation

**Key Methods:**
- `run_command()` (Line 42-62): Execute validation command
- `check_http_endpoint()` (Line 64-76): Check HTTP endpoint health
- `log_result()` (Line 78-80+): Log test result

**main()** (Line 211+): Run all health checks

**Usage:** `python scripts/validation/system_health_check.py`

---

### Evaluation and Benchmarking Scripts

#### Semantic Architecture Benchmark
**File:** `/home/donbr/ghcp/adv-rag/scripts/evaluation/semantic_architecture_benchmark.py`

**SemanticArchitectureBenchmark Class** (Line 30-547)
- Purpose: Comprehensive RAG architecture evaluation and benchmarking

**main()** (Line 549+): Run benchmark suite

**Usage:** `python scripts/evaluation/semantic_architecture_benchmark.py`

#### Retrieval Method Comparison
**File:** `/home/donbr/ghcp/adv-rag/scripts/evaluation/retrieval_method_comparison.py`

**Config Class** (Line 55-88): Evaluation configuration

**Key Functions:**
- **setup_environment()** (Line 90-105): Setup evaluation environment
- **setup_phoenix_tracing()** (Line 107-114): Configure Phoenix tracing
- **setup_vectorstore_client()** (Line 116-134): Setup Qdrant client
- **create_retrievers()** (Line 136-211): Create all retriever types
- **create_rag_chain()** (Line 213-225): Create RAG chain
- **load_and_process_data()** (Line 169-196): Load and process CSV data
- **run_evaluation()** (Line 227-256): Run evaluation for question
- **run_cache_comparison()** (Line 258-292): Compare cache performance
- **main()** (Line 294+): Main evaluation orchestration

**Usage:** `python scripts/evaluation/retrieval_method_comparison.py`

---

### Data Ingestion Scripts

#### CSV Ingestion Pipeline
**File:** `/home/donbr/ghcp/adv-rag/scripts/ingestion/csv_ingestion_pipeline.py`

**Config Class** (Line 54-83): Ingestion configuration

**Key Functions:**
- **setup_environment()** (Line 85-100): Setup ingestion environment
- **setup_phoenix_tracing()** (Line 102-109): Configure Phoenix tracing
- **setup_vectorstore()** (Line 111-121): Setup Qdrant vector store
- **load_and_process_data()** (Line 123-165): Load and chunk CSV data
- **main()** (Line 167+): Main ingestion orchestration

**Usage:** `python scripts/ingestion/csv_ingestion_pipeline.py`

---

### Migration Scripts

#### PostgreSQL to Qdrant Migration
**File:** `/home/donbr/ghcp/adv-rag/scripts/migration/pgvector_to_qdrant_migration.py`

**Key Classes:**
- **MigrationConfig** (Line 38-71): Migration configuration
- **PostgreSQLExtractor** (Line 73-137): Extract data from PostgreSQL
- **QdrantLoader** (Line 139-221): Load data into Qdrant
- **MigrationRunner** (Line 223-363): Orchestrate migration

**main()** (Line 365+): Run migration

**Usage:** `python scripts/migration/pgvector_to_qdrant_migration.py`

---

### Utility Scripts

#### Project Extractor
**File:** `/home/donbr/ghcp/adv-rag/scripts/project_extractor.py`

**Key Classes:**
- **FileInfo** (Line 28-36): File information dataclass
- **Config** (Line 38-50): Extraction configuration
- **ProjectExtractor** (Line 52-174): Extract project structure and files

**main()** (Line 176+): Run extraction

**Usage:** `python scripts/project_extractor.py`

---

## Test Suite

### API Tests
**Location:** `/home/donbr/ghcp/adv-rag/tests/api/`

- `test_app.py`: FastAPI endpoint tests
- `test_schema.py`: OpenAPI schema validation (TestOpenAPISchema class, Line 5)

### Core Tests
**Location:** `/home/donbr/ghcp/adv-rag/tests/core/`

- `test_settings.py`: Settings configuration tests (TestSettings class, Line 17)
- `test_exceptions.py`: Exception hierarchy tests (Multiple test classes, Line 33-248)
- `test_logging_config.py`: Logging configuration tests (TestLoggingConfig class, Line 19)

### RAG Tests
**Location:** `/home/donbr/ghcp/adv-rag/tests/rag/`

- `test_chain.py`: Chain creation and execution tests
- `test_retriever.py`: Retriever factory tests
- `test_embeddings.py`: Embedding model tests
- `test_vectorstore.py`: Vector store tests
- `test_data_loader.py`: Data loading tests

### Integration Tests
**Location:** `/home/donbr/ghcp/adv-rag/tests/integrations/`

- `test_redis_client.py`: Redis client integration tests
- `test_llm_models.py`: LLM model integration tests
- `test_redis_mcp.py`: Redis MCP integration (RedisMCPTester class, Line 24)
- `test_qdrant_mcp.py`: Qdrant MCP integration (Multiple test classes, Line 31-360)
- `test_phoenix_mcp.py`: Phoenix MCP integration (Multiple test classes, Line 58-1533)
- `mcp_tool_validation.py`: MCP tool validation (MCPToolValidator class, Line 85)

### MCP Tests
**Location:** `/home/donbr/ghcp/adv-rag/tests/mcp/`

- `test_server.py`: MCP server tests
- `test_resources.py`: MCP resource tests
- `test_conversion.py`: FastAPI to MCP conversion tests (TestFastAPItoMCPConversion, Line 8)

### CQRS Integration Tests
**Location:** `/home/donbr/ghcp/adv-rag/tests/integration/`

- `test_cqrs_resources.py`: CQRS resource compliance tests
- `test_cqrs_resources_with_assertions.py`: CQRS with assertions (TestResults class, Line 27)
- `test_cqrs_structure_validation.py`: CQRS structure validation
- `test_cqrs_expected_responses.py`: CQRS response format validation
- `verify_mcp.py`: MCP server verification

### Test Configuration
**File:** `/home/donbr/ghcp/adv-rag/tests/conftest.py`

**Fixtures:**
- **fastapi_app_instance()** (Line 7-12): FastAPI app instance fixture
- **client()** (Line 14-21): Test client fixture
- **mcp_server_instance()** (Line 23+): MCP server instance fixture

---

## Configuration Files

### Environment Configuration
**File:** `/home/donbr/ghcp/adv-rag/.env.example`
- Template for environment variables
- API keys, service endpoints, feature flags

### Python Project Configuration
**File:** `/home/donbr/ghcp/adv-rag/pyproject.toml`
- Project metadata, dependencies, tool configurations

### Test Configuration
**File:** `/home/donbr/ghcp/adv-rag/pytest.ini`
- Pytest configuration and test discovery settings

---

## Summary Statistics

### Public API Components
- **8 HTTP Endpoints** (6 retrieval strategies + 2 utility endpoints)
- **2 Request/Response Models** (QuestionRequest, AnswerResponse)
- **1 MCP Server Interface** (FastMCP wrapper)
- **5 CQRS Resources** (Qdrant read-only access)

### Internal Components
- **17 Core Exception Classes** (hierarchical error handling)
- **6 RAG Chain Types** (retrieval strategies)
- **6 Retriever Implementations** (search algorithms)
- **4 Cache Implementations** (NoOp, Local, Redis, Multi-level)
- **15+ Phoenix MCP Data Classes** (observability integration)
- **10+ Configuration Classes** (settings, batch processing, error handling)

### Entry Points
- **3 Main Entry Points** (main.py, run.py, mcp/server.py)
- **5 Management Scripts** (manage.py, status.py, health_check.py, etc.)
- **3 Evaluation Scripts** (benchmarking and comparison)
- **2 Data Pipeline Scripts** (ingestion, migration)

### Test Coverage
- **50+ Test Files** across API, core, RAG, integrations, and MCP
- **Multiple Test Classes** for comprehensive coverage
- **Integration and Unit Tests** for all major components

### Key Design Patterns
- **Singleton Pattern**: Settings, cache instances
- **Factory Pattern**: Retrievers, chains, cache implementations
- **Dependency Injection**: FastAPI dependencies, settings injection
- **CQRS Pattern**: Read (Resources) vs Write (Tools) separation
- **Circuit Breaker Pattern**: Phoenix MCP error handling
- **Retry Pattern**: Exponential backoff with jitter
- **Observer Pattern**: Phoenix tracing and observability

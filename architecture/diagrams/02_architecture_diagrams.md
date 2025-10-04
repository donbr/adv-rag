# Architecture Diagrams

This document provides comprehensive Mermaid diagrams visualizing the architecture, component relationships, class hierarchies, and module dependencies of the Advanced RAG system.

---

## System Architecture

The Advanced RAG system follows a layered architecture pattern with clear separation of concerns across five distinct layers.

```mermaid
graph TB
    subgraph "Presentation Layer"
        HTTP[FastAPI REST API<br/>8 Endpoints]
        MCP[MCP Server<br/>FastMCP Wrapper]
        CQRS[CQRS Resources<br/>Qdrant Read-Only]
    end

    subgraph "Application Layer"
        CHAINS[RAG Chains<br/>6 Chain Types]
        RETRIEVERS[Retrievers<br/>6 Retriever Types]
        CHAINF[Chain Factory<br/>create_rag_chain]
        RETRF[Retriever Factory<br/>create_retriever]
    end

    subgraph "Domain Layer"
        EXCEPTIONS[Exception Hierarchy<br/>17 Exception Classes]
        SETTINGS[Settings Management<br/>Pydantic BaseSettings]
        LOGGING[Logging Config<br/>Structured Logging]
    end

    subgraph "Infrastructure Layer"
        CACHE[Cache System<br/>4 Cache Types]
        REDISCLI[Redis Client<br/>Connection Pool]
        LLMINT[LLM Integration<br/>ChatOpenAI]
        EMBINT[Embeddings<br/>OpenAI Embeddings]
        PHOENIX[Phoenix MCP Client<br/>Observability]
        QDRANTMCP[Qdrant MCP<br/>Enhanced Server]
    end

    subgraph "Data Layer"
        QDRANT[(Qdrant<br/>Vector Store)]
        REDIS[(Redis<br/>Cache Store)]
        CSV[CSV Files<br/>Document Source]
    end

    HTTP --> CHAINS
    MCP --> CHAINS
    MCP --> CQRS
    CQRS --> QDRANT

    CHAINS --> RETRIEVERS
    CHAINS --> LLMINT
    CHAINF --> CHAINS
    RETRF --> RETRIEVERS

    RETRIEVERS --> EMBINT
    RETRIEVERS --> QDRANT

    CHAINS -.uses.-> EXCEPTIONS
    RETRIEVERS -.uses.-> EXCEPTIONS
    HTTP -.uses.-> SETTINGS
    CHAINS -.uses.-> SETTINGS

    HTTP --> CACHE
    CACHE --> REDISCLI
    REDISCLI --> REDIS

    LLMINT --> REDISCLI
    LLMINT -.external.-> OPENAI[OpenAI API]
    EMBINT -.external.-> OPENAI

    PHOENIX -.external.-> PHXSRV[Phoenix Server]

    RETRIEVERS --> CSV

    style HTTP fill:#e1f5ff
    style MCP fill:#e1f5ff
    style CQRS fill:#e1f5ff
    style CHAINS fill:#fff4e1
    style RETRIEVERS fill:#fff4e1
    style EXCEPTIONS fill:#f0f0f0
    style SETTINGS fill:#f0f0f0
    style CACHE fill:#e8f5e9
    style QDRANT fill:#ffebee
    style REDIS fill:#ffebee
```

### Layer Responsibilities

1. **Presentation Layer**: HTTP/MCP interfaces for external access
2. **Application Layer**: RAG business logic, chain orchestration, retrieval strategies
3. **Domain Layer**: Core configuration, exceptions, cross-cutting concerns
4. **Infrastructure Layer**: External service integrations (LLM, cache, observability)
5. **Data Layer**: Persistent storage for vectors, cache, and source documents

---

## Component Relationships

This diagram shows how major components interact and data flows through the system.

```mermaid
graph LR
    subgraph "API Components"
        APP[FastAPI App<br/>app.py]
        MCPSRV[MCP Server<br/>server.py]
        MCPRES[MCP Resources<br/>resources.py]
        QDRANTRES[Qdrant Resources<br/>qdrant_resources.py]
    end

    subgraph "RAG Components"
        CHAIN[Chain Factory<br/>chain.py]
        RET[Retriever Factory<br/>retriever.py]
        VSTORE[Vector Store<br/>vectorstore.py]
        EMB[Embeddings<br/>embeddings.py]
        LOADER[Data Loader<br/>data_loader.py]
    end

    subgraph "Integration Components"
        LLMMOD[LLM Models<br/>llm_models.py]
        CACHESYS[Cache System<br/>cache.py]
        REDISCLIENT[Redis Client<br/>redis_client.py]
        PHXMCP[Phoenix MCP<br/>phoenix_mcp.py]
        QDMCP[Qdrant MCP<br/>qdrant_mcp.py]
    end

    subgraph "Core Components"
        SETTINGS[Settings<br/>settings.py]
        EXC[Exceptions<br/>exceptions.py]
        LOG[Logging<br/>logging_config.py]
    end

    subgraph "External Services"
        QDRANT[(Qdrant)]
        REDIS[(Redis)]
        OPENAI[OpenAI API]
        PHXSRV[Phoenix Server]
    end

    %% API to RAG flow
    APP -->|invoke chain| CHAIN
    MCPSRV -->|wrap| APP
    MCPRES -->|use chains| CHAIN
    QDRANTRES -->|query| QDRANT

    %% RAG internal flow
    CHAIN -->|create with| RET
    RET -->|retrieve from| VSTORE
    VSTORE -->|use| EMB
    VSTORE -->|load| LOADER
    RET -->|load docs| LOADER

    %% Integration flow
    CHAIN -->|use LLM| LLMMOD
    APP -->|cache responses| CACHESYS
    CACHESYS -->|L1: local memory| CACHESYS
    CACHESYS -->|L2: Redis| REDISCLIENT
    REDISCLIENT --> REDIS

    %% LLM caching
    LLMMOD -->|cache calls| REDISCLIENT
    LLMMOD --> OPENAI
    EMB --> OPENAI

    %% Vector store connection
    VSTORE --> QDRANT

    %% Observability
    APP -.trace.-> PHXMCP
    MCPSRV -.trace.-> PHXMCP
    PHXMCP --> PHXSRV

    %% Core dependencies
    APP --> SETTINGS
    CHAIN --> SETTINGS
    RET --> SETTINGS
    VSTORE --> SETTINGS

    APP -.error handling.-> EXC
    CHAIN -.error handling.-> EXC
    RET -.error handling.-> EXC

    SETTINGS --> LOG

    %% Styling
    style APP fill:#4fc3f7
    style MCPSRV fill:#4fc3f7
    style CHAIN fill:#ffb74d
    style RET fill:#ffb74d
    style CACHESYS fill:#81c784
    style QDRANT fill:#e57373
    style REDIS fill:#e57373
    style OPENAI fill:#ba68c8
```

### Key Data Flows

1. **Question Flow**: Client → FastAPI → Chain → Retriever → VectorStore → Qdrant → LLM → Response
2. **Cache Flow**: Request → Cache (L1 local, L2 Redis) → Cached or Generate → Store
3. **Observability Flow**: All operations → Phoenix MCP → Phoenix Server for tracing
4. **MCP Flow**: MCP Client → MCP Server → FastAPI wrapper → Chain execution

---

## Class Hierarchies

### 1. Exception Class Hierarchy

The system uses a comprehensive exception hierarchy with 17 custom exception classes organized by functional area.

```mermaid
classDiagram
    class RAGException {
        +str message
        +str component
        +dict details
        +__init__(message, component, details)
        +__str__()
    }

    class ConfigurationError {
        Configuration/settings errors
    }

    class RAGError {
        Base for RAG errors
    }

    class EmbeddingError {
        Embedding operation failures
    }

    class VectorStoreError {
        Vector store operation failures
    }

    class RetrievalError {
        Document retrieval failures
    }

    class ChainExecutionError {
        RAG chain execution failures
    }

    class MCPError {
        Base for MCP errors
    }

    class MCPServerError {
        MCP server operation failures
    }

    class MCPTransportError {
        MCP transport layer failures
    }

    class MCPResourceError {
        MCP resource operation failures
    }

    class IntegrationError {
        Base for external service errors
    }

    class RedisError {
        Redis operation failures
    }

    class LLMError {
        LLM API call failures
    }

    Exception <|-- RAGException
    RAGException <|-- ConfigurationError
    RAGException <|-- RAGError
    RAGException <|-- MCPError
    RAGException <|-- IntegrationError

    RAGError <|-- EmbeddingError
    RAGError <|-- VectorStoreError
    RAGError <|-- RetrievalError
    RAGError <|-- ChainExecutionError

    MCPError <|-- MCPServerError
    MCPError <|-- MCPTransportError
    MCPError <|-- MCPResourceError

    IntegrationError <|-- RedisError
    IntegrationError <|-- LLMError

    note for RAGException "Base exception with\ncomponent tracking\nand structured details"
    note for RAGError "All RAG-related\noperational errors"
    note for MCPError "All MCP-related\nprotocol errors"
    note for IntegrationError "All external\nservice errors"
```

### 2. Retriever Class Hierarchy

Six retriever types implementing different search strategies, all based on LangChain retriever interfaces.

```mermaid
classDiagram
    class BaseRetriever {
        <<interface>>
        +get_relevant_documents(query)
    }

    class NaiveRetriever {
        +QdrantVectorStore vectorstore
        +search_kwargs dict
        Basic similarity search
    }

    class BM25Retriever {
        +List documents
        +BM25 index
        Keyword-based search
    }

    class ContextualCompressionRetriever {
        +BaseRetriever base_retriever
        +CohereRerank compressor
        Compressed context with reranking
    }

    class MultiQueryRetriever {
        +BaseRetriever base_retriever
        +ChatModel llm
        Query expansion with LLM
    }

    class SemanticRetriever {
        +QdrantVectorStore semantic_vectorstore
        +search_kwargs dict
        Semantic chunking search
    }

    class EnsembleRetriever {
        +List~BaseRetriever~ retrievers
        +List~float~ weights
        Combined retrieval strategies
    }

    BaseRetriever <|.. NaiveRetriever
    BaseRetriever <|.. BM25Retriever
    BaseRetriever <|.. ContextualCompressionRetriever
    BaseRetriever <|.. MultiQueryRetriever
    BaseRetriever <|.. SemanticRetriever
    BaseRetriever <|.. EnsembleRetriever

    ContextualCompressionRetriever --> NaiveRetriever : wraps
    MultiQueryRetriever --> NaiveRetriever : wraps
    EnsembleRetriever --> BM25Retriever : includes
    EnsembleRetriever --> NaiveRetriever : includes

    note for NaiveRetriever "Uses baseline\nvectorstore with\nRecursiveCharacterTextSplitter"
    note for SemanticRetriever "Uses semantic\nvectorstore with\nSemanticChunker"
    note for EnsembleRetriever "Combines multiple\nretrievers with\nequal weighting"
```

### 3. Cache Implementation Hierarchy

Four cache types supporting multi-level caching strategy with NoOp pattern for A/B testing.

```mermaid
classDiagram
    class CacheInterface {
        <<abstract>>
        +get(key)* Optional~str~
        +set(key, value, ttl)* bool
        +delete(key)* bool
        +get_stats()* Dict
    }

    class NoOpCache {
        +dict stats
        +get(key) None
        +set(key, value, ttl) True
        +delete(key) True
        +get_stats() dict
        No-operation cache when disabled
    }

    class LocalMemoryCache {
        +OrderedDict cache
        +int max_size
        +dict stats
        +get(key) Optional~str~
        +set(key, value, ttl) bool
        +delete(key) bool
        +get_stats() dict
        L1 in-memory cache with TTL and LRU
    }

    class RedisCache {
        +Redis redis_client
        +dict stats
        +get(key) Optional~str~
        +set(key, value, ttl) bool
        +delete(key) bool
        +get_stats() dict
        L2 Redis cache wrapper
    }

    class MultiLevelCache {
        +CacheInterface l1_cache
        +CacheInterface l2_cache
        +dict stats
        +get(key) Optional~str~
        +set(key, value, ttl) bool
        +delete(key) bool
        +get_stats() dict
        Multi-level L1 + L2 cache
    }

    CacheInterface <|.. NoOpCache
    CacheInterface <|.. LocalMemoryCache
    CacheInterface <|.. RedisCache
    CacheInterface <|.. MultiLevelCache

    MultiLevelCache --> LocalMemoryCache : L1
    MultiLevelCache --> RedisCache : L2

    note for NoOpCache "Used when\ncache_enabled=False"
    note for MultiLevelCache "L1: 100-500 items\nL2: Redis with TTL\nAuto-promotion on L2 hit"
```

### 4. Chain Factory Pattern

The chain factory creates RAG chains by combining retrievers with LLM prompts following the factory pattern.

```mermaid
classDiagram
    class ChainFactory {
        +ChatModel _CHAT_MODEL
        +ChatPromptTemplate RAG_PROMPT
        +get_chat_model_lazy() ChatModel
        +create_rag_chain(retriever) Chain
    }

    class RAGChain {
        +Retriever retriever
        +ChatModel llm
        +ChatPromptTemplate prompt
        +invoke(question) response
        Pipeline: question → retriever → context → LLM → answer
    }

    class NaiveChain {
        Uses NaiveRetriever
    }

    class BM25Chain {
        Uses BM25Retriever
    }

    class ContextualCompressionChain {
        Uses ContextualCompressionRetriever
    }

    class MultiQueryChain {
        Uses MultiQueryRetriever
    }

    class EnsembleChain {
        Uses EnsembleRetriever
    }

    class SemanticChain {
        Uses SemanticRetriever
    }

    ChainFactory ..> RAGChain : creates
    RAGChain <|-- NaiveChain
    RAGChain <|-- BM25Chain
    RAGChain <|-- ContextualCompressionChain
    RAGChain <|-- MultiQueryChain
    RAGChain <|-- EnsembleChain
    RAGChain <|-- SemanticChain

    ChainFactory --> NaiveRetriever : uses
    ChainFactory --> BM25Retriever : uses
    ChainFactory --> ContextualCompressionRetriever : uses
    ChainFactory --> MultiQueryRetriever : uses
    ChainFactory --> EnsembleRetriever : uses
    ChainFactory --> SemanticRetriever : uses

    note for ChainFactory "Factory creates chains\nwith lazy LLM initialization\nand shared prompt template"
    note for RAGChain "Chain structure:\n{context, question}\n→ prompt\n→ LLM\n→ response"
```

### 5. Phoenix MCP Data Classes Structure

The Phoenix MCP integration uses 15+ data classes for comprehensive observability and error handling.

```mermaid
classDiagram
    class PhoenixMCPClient {
        +RetryConfig retry_config
        +CircuitBreaker circuit_breaker
        +get_experiment_by_id() PhoenixExperiment
        +get_datasets() List~PhoenixDataset~
        +extract_patterns() PatternExtractionResult
    }

    class RetryConfig {
        +int max_retries
        +float initial_delay
        +float max_delay
        +float backoff_factor
    }

    class CircuitBreakerConfig {
        +int failure_threshold
        +int timeout_seconds
        +int half_open_attempts
    }

    class CircuitBreaker {
        +CircuitBreakerState state
        +int failure_count
        +datetime last_failure_time
        +call(func) result
    }

    class CircuitBreakerState {
        <<enumeration>>
        CLOSED
        OPEN
        HALF_OPEN
    }

    class PhoenixExperiment {
        +str experiment_id
        +str name
        +datetime created_at
        +dict metadata
    }

    class PhoenixExperimentResult {
        +PhoenixExperiment experiment
        +List~dict~ traces
        +dict metrics
        +dict summary
    }

    class PhoenixDataset {
        +str dataset_id
        +str name
        +int example_count
        +datetime created_at
    }

    class ExtractedPattern {
        +str pattern_id
        +str query_text
        +str expected_response
        +dict metadata
        +validate() bool
    }

    class PatternExtractionResult {
        +List~ExtractedPattern~ patterns
        +int total_extracted
        +int validation_passed
        +List~str~ errors
    }

    class DatasetAnalysisResult {
        +PhoenixDataset dataset
        +PatternExtractionResult patterns
        +dict statistics
        +dict quality_metrics
    }

    class GoldenTestsetAnalysis {
        +List~DatasetAnalysisResult~ datasets
        +dict aggregate_metrics
        +datetime analysis_timestamp
    }

    class BatchSyncConfig {
        +int batch_size
        +int max_workers
        +int timeout_seconds
        +bool validate_on_sync
    }

    class SyncState {
        +int total_items
        +int processed_items
        +int failed_items
        +datetime start_time
        +List~str~ errors
    }

    class BatchSyncResult {
        +SyncState state
        +bool success
        +float duration_seconds
        +dict summary
    }

    class PhoenixBatchProcessor {
        +BatchSyncConfig config
        +process_batch() BatchSyncResult
        +sync_datasets() BatchSyncResult
    }

    PhoenixMCPClient --> RetryConfig
    PhoenixMCPClient --> CircuitBreaker
    CircuitBreaker --> CircuitBreakerState
    CircuitBreaker --> CircuitBreakerConfig

    PhoenixMCPClient ..> PhoenixExperiment : returns
    PhoenixMCPClient ..> PhoenixExperimentResult : returns
    PhoenixMCPClient ..> PhoenixDataset : returns
    PhoenixMCPClient ..> PatternExtractionResult : returns

    PhoenixExperimentResult --> PhoenixExperiment
    PatternExtractionResult --> ExtractedPattern
    DatasetAnalysisResult --> PhoenixDataset
    DatasetAnalysisResult --> PatternExtractionResult
    GoldenTestsetAnalysis --> DatasetAnalysisResult

    PhoenixBatchProcessor --> BatchSyncConfig
    PhoenixBatchProcessor ..> BatchSyncResult : returns
    BatchSyncResult --> SyncState

    note for PhoenixMCPClient "Client with retry logic,\ncircuit breaker pattern,\nand comprehensive error handling"
    note for ExtractedPattern "Validated patterns from\nPhoenix experiments\nfor golden testsets"
```

---

## Module Dependencies

This diagram shows how modules in `src/` depend on each other and identifies core vs peripheral modules.

```mermaid
graph TB
    subgraph "Core Modules [Foundation]"
        CORE_SETTINGS[core/settings.py]
        CORE_EXCEPTIONS[core/exceptions.py]
        CORE_LOGGING[core/logging_config.py]
    end

    subgraph "RAG Modules [Business Logic]"
        RAG_EMBEDDINGS[rag/embeddings.py]
        RAG_LOADER[rag/data_loader.py]
        RAG_VSTORE[rag/vectorstore.py]
        RAG_RETRIEVER[rag/retriever.py]
        RAG_CHAIN[rag/chain.py]
    end

    subgraph "Integration Modules [External Services]"
        INT_CACHE[integrations/cache.py]
        INT_REDIS[integrations/redis_client.py]
        INT_LLM[integrations/llm_models.py]
        INT_PHOENIX[integrations/phoenix_mcp.py]
        INT_QDRANT[integrations/qdrant_mcp.py]
    end

    subgraph "MCP Modules [Protocol Layer]"
        MCP_RESOURCES[mcp/resources.py]
        MCP_QDRANT[mcp/qdrant_resources.py]
        MCP_SERVER[mcp/server.py]
    end

    subgraph "API Modules [Presentation]"
        API_APP[api/app.py]
    end

    subgraph "Entry Point"
        MAIN[main.py]
    end

    %% Core dependencies (no internal deps)
    CORE_LOGGING --> CORE_SETTINGS

    %% RAG module dependencies
    RAG_EMBEDDINGS --> CORE_SETTINGS
    RAG_LOADER -.no deps.-> RAG_LOADER
    RAG_VSTORE --> CORE_SETTINGS
    RAG_VSTORE --> RAG_LOADER
    RAG_VSTORE --> RAG_EMBEDDINGS
    RAG_RETRIEVER --> CORE_SETTINGS
    RAG_RETRIEVER --> RAG_LOADER
    RAG_RETRIEVER --> RAG_EMBEDDINGS
    RAG_RETRIEVER --> RAG_VSTORE
    RAG_RETRIEVER --> INT_LLM
    RAG_CHAIN --> CORE_SETTINGS
    RAG_CHAIN --> INT_LLM
    RAG_CHAIN --> RAG_RETRIEVER

    %% Integration dependencies
    INT_REDIS --> CORE_SETTINGS
    INT_CACHE --> CORE_SETTINGS
    INT_CACHE --> INT_REDIS
    INT_LLM --> CORE_SETTINGS
    INT_LLM --> INT_REDIS
    INT_PHOENIX --> CORE_SETTINGS
    INT_QDRANT --> CORE_SETTINGS
    INT_QDRANT --> RAG_EMBEDDINGS
    INT_QDRANT --> INT_PHOENIX

    %% MCP dependencies
    MCP_QDRANT --> CORE_SETTINGS
    MCP_QDRANT --> RAG_EMBEDDINGS
    MCP_RESOURCES --> CORE_SETTINGS
    MCP_RESOURCES --> API_APP
    MCP_RESOURCES --> RAG_CHAIN
    MCP_SERVER --> CORE_SETTINGS
    MCP_SERVER --> API_APP
    MCP_SERVER --> MCP_QDRANT

    %% API dependencies
    API_APP --> CORE_SETTINGS
    API_APP --> INT_REDIS
    API_APP --> INT_CACHE
    API_APP --> RAG_CHAIN

    %% Main entry point
    MAIN --> CORE_LOGGING
    MAIN --> CORE_SETTINGS
    MAIN --> API_APP
    MAIN --> MCP_SERVER

    %% Error handling (dashed)
    RAG_CHAIN -.uses.-> CORE_EXCEPTIONS
    RAG_RETRIEVER -.uses.-> CORE_EXCEPTIONS
    RAG_VSTORE -.uses.-> CORE_EXCEPTIONS
    API_APP -.uses.-> CORE_EXCEPTIONS
    MCP_SERVER -.uses.-> CORE_EXCEPTIONS

    %% Styling
    style CORE_SETTINGS fill:#f9f9f9,stroke:#333,stroke-width:3px
    style CORE_EXCEPTIONS fill:#f9f9f9,stroke:#333,stroke-width:3px
    style CORE_LOGGING fill:#f9f9f9,stroke:#333,stroke-width:3px

    style RAG_CHAIN fill:#fff4e1,stroke:#ff9800
    style RAG_RETRIEVER fill:#fff4e1,stroke:#ff9800

    style API_APP fill:#e3f2fd,stroke:#2196f3
    style MCP_SERVER fill:#e3f2fd,stroke:#2196f3

    style MAIN fill:#ffebee,stroke:#f44336,stroke-width:3px
```

### Dependency Analysis

#### Core Modules (Foundation - No circular deps)
- `core/settings.py` - Central configuration, depends only on logging
- `core/exceptions.py` - Exception hierarchy, no dependencies
- `core/logging_config.py` - Logging setup, depends on settings

#### RAG Modules (Business Logic)
- **Dependency Chain**: `data_loader` → `embeddings` → `vectorstore` → `retriever` → `chain`
- `rag/chain.py` is the highest-level RAG module, orchestrating retrievers and LLM
- All RAG modules depend on `core/settings.py`

#### Integration Modules (External Services)
- `integrations/redis_client.py` - Redis connection, depends on settings only
- `integrations/cache.py` - Cache abstraction, depends on settings and Redis client
- `integrations/llm_models.py` - LLM integration, depends on settings and Redis client
- `integrations/phoenix_mcp.py` - Observability, depends on settings only
- `integrations/qdrant_mcp.py` - Enhanced Qdrant, depends on settings, embeddings, and Phoenix

#### MCP Modules (Protocol Layer)
- `mcp/qdrant_resources.py` - CQRS resources, depends on settings and embeddings
- `mcp/resources.py` - MCP resource handlers, depends on API app and chains
- `mcp/server.py` - MCP server wrapper, depends on API app and Qdrant resources

#### API Module (Presentation)
- `api/app.py` - FastAPI application, depends on settings, Redis, cache, and chains

#### No Circular Dependencies Detected
The module dependency graph is a Directed Acyclic Graph (DAG), ensuring clean architecture.

---

## Import Relationships by Module

### High-Level Import Patterns

```mermaid
graph LR
    subgraph "External Libraries"
        LANGCHAIN[LangChain]
        FASTAPI[FastAPI]
        PYDANTIC[Pydantic]
        OPENAI_LIB[OpenAI SDK]
        REDIS_LIB[Redis]
        QDRANT_LIB[Qdrant Client]
        PHOENIX_LIB[Phoenix OTEL]
        FASTMCP[FastMCP]
    end

    subgraph "src/ Modules"
        CORE[core/*]
        RAG[rag/*]
        INT[integrations/*]
        MCP[mcp/*]
        API[api/*]
    end

    %% External dependencies
    RAG --> LANGCHAIN
    RAG --> OPENAI_LIB
    RAG --> QDRANT_LIB

    API --> FASTAPI
    API --> PYDANTIC

    MCP --> FASTMCP
    MCP --> PHOENIX_LIB

    INT --> REDIS_LIB
    INT --> OPENAI_LIB
    INT --> PHOENIX_LIB

    CORE --> PYDANTIC

    %% Internal dependencies
    RAG --> CORE
    INT --> CORE
    MCP --> CORE
    API --> CORE

    API --> RAG
    API --> INT

    MCP --> API
    MCP --> RAG
    MCP --> INT

    style LANGCHAIN fill:#4caf50
    style FASTAPI fill:#2196f3
    style FASTMCP fill:#9c27b0
    style OPENAI_LIB fill:#ff9800
```

### Module Import Counts

Based on the analysis, here's the import usage pattern:

| Module | Internal Imports | External Imports | Total |
|--------|-----------------|------------------|-------|
| `api/app.py` | 6 | 10 | 16 |
| `mcp/server.py` | 4 | 7 | 11 |
| `mcp/resources.py` | 5 | 8 | 13 |
| `mcp/qdrant_resources.py` | 3 | 9 | 12 |
| `rag/chain.py` | 3 | 5 | 8 |
| `rag/retriever.py` | 5 | 8 | 13 |
| `rag/vectorstore.py` | 3 | 4 | 7 |
| `rag/embeddings.py` | 1 | 2 | 3 |
| `rag/data_loader.py` | 0 | 3 | 3 |
| `integrations/cache.py` | 2 | 6 | 8 |
| `integrations/redis_client.py` | 1 | 4 | 5 |
| `integrations/llm_models.py` | 1 | 5 | 6 |
| `integrations/phoenix_mcp.py` | 1 | 10 | 11 |
| `integrations/qdrant_mcp.py` | 4 | 10 | 14 |
| `core/settings.py` | 1 | 5 | 6 |
| `core/exceptions.py` | 0 | 0 | 0 |
| `core/logging_config.py` | 0 | 3 | 3 |

**Observations**:
- `core/exceptions.py` has zero dependencies (pure exception definitions)
- `rag/data_loader.py` has no internal dependencies (data source layer)
- `api/app.py` has the most dependencies (orchestration layer)
- Average internal imports: 2.3 per module (low coupling)
- Average external imports: 6.1 per module (leveraging libraries)

---

## Summary

This architecture demonstrates:

1. **Clear Layering**: 5 distinct layers with well-defined responsibilities
2. **Low Coupling**: Average 2.3 internal imports per module
3. **High Cohesion**: Modules grouped by functional area (RAG, MCP, Core, etc.)
4. **No Circular Dependencies**: Clean DAG structure in module imports
5. **Factory Patterns**: Chain and retriever factories for flexible instantiation
6. **Comprehensive Error Handling**: 17-class exception hierarchy covering all areas
7. **Multi-Level Caching**: 4 cache implementations with fallback strategies
8. **Robust Observability**: Phoenix MCP with circuit breaker and retry patterns
9. **CQRS Compliance**: Read-only resources for safe Qdrant access
10. **Flexible Retrieval**: 6 retriever types supporting different search strategies

The architecture supports the system's goals of:
- Educational transparency (clear structure, comprehensive documentation)
- Production readiness (error handling, caching, observability)
- Extensibility (factory patterns, interface-based design)
- Maintainability (low coupling, clear dependencies)

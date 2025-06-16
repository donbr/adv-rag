## 🏗️ **Advanced RAG Project Structure - Domain-Organized Architecture**

### **Project Overview**
This advanced RAG project implements a sophisticated domain-organized architecture that separates concerns into logical packages while maintaining zero-duplication patterns for MCP integration.

✅ **Domain-organized structure** with `/src/core/`, `/src/api/`, `/src/rag/`, `/src/mcp/`, `/src/integrations/`  
✅ **Zero-duplication MCP architecture** using `FastMCP.from_fastapi()`  
✅ **Transport-agnostic design** with streamable HTTP and stdio support  
✅ **Comprehensive configuration management** with centralized settings  
✅ **Production-ready features** (logging, error handling, telemetry)  

### **📁 Current Project Structure**

```
adv-rag/
├── src/
│   ├── __init__.py                   # Root package initialization
│   ├── main.py                       # Application entry point
│   ├── core/                         # 🔧 Core shared components
│   │   ├── __init__.py
│   │   ├── settings.py               # Centralized configuration management
│   │   ├── logging_config.py         # Structured logging setup
│   │   └── exceptions.py             # Global exception hierarchy
│   ├── api/                          # 🌐 FastAPI web layer
│   │   ├── __init__.py
│   │   └── app.py                    # FastAPI routes and endpoints (6 retrieval strategies)
│   ├── rag/                          # 🧠 RAG pipeline components
│   │   ├── __init__.py
│   │   ├── embeddings.py             # OpenAI embedding models
│   │   ├── vectorstore.py            # Qdrant vector store setup
│   │   ├── retriever.py              # Retrieval strategies (naive, BM25, ensemble, etc.)
│   │   ├── chain.py                  # LangChain RAG chain construction
│   │   └── data_loader.py            # Document processing and loading
│   ├── mcp/                          # 🔗 MCP server implementation
│   │   ├── __init__.py
│   │   ├── server.py                 # Primary MCP server (FastMCP.from_fastapi)
│   │   └── resources.py              # Enhanced MCP resource handlers
│   └── integrations/                 # 🔌 External service integrations
│       ├── __init__.py
│       ├── llm_models.py             # LLM client configurations
│       └── redis_client.py           # Redis caching integration
├── tests/
│   ├── __init__.py
│   ├── core/                         # Unit tests for core components
│   │   ├── __init__.py
│   │   ├── test_settings.py          # Configuration testing
│   │   ├── test_logging_config.py    # Logging validation
│   │   └── test_exceptions.py        # Exception hierarchy testing
│   ├── integration/                  # Integration and E2E tests
│   │   ├── __init__.py
│   │   ├── verify_mcp.py             # MCP server validation
│   │   └── test_api_endpoints.sh     # FastAPI endpoint testing
│   ├── test_jsonrpc_transport.py     # JSON-RPC transport testing
│   ├── test_schema_accuracy.py       # MCP schema validation
│   └── test_redis_mcp_integration.py # Redis integration testing
├── scripts/
│   ├── mcp/                          # MCP tooling and validation
│   │   ├── export_mcp_schema_native.py
│   │   ├── export_mcp_schema_stdio.py
│   │   ├── validate_mcp_schema.py
│   │   ├── compare_schema_outputs.py
│   │   ├── compare_transports.py
│   │   └── mcp_config.toml
│   ├── evaluation/                   # Performance and quality evaluation
│   │   ├── retrieval_method_comparison.py
│   │   └── semantic_architecture_benchmark.py
│   ├── ingestion/                    # Data pipeline scripts
│   │   └── csv_ingestion_pipeline.py
│   └── testing/                      # Testing utilities
│       └── test_redis_integration.py
├── docs/                             # Documentation
│   ├── project-structure.md          # This file
│   ├── MCP_LEARNING_JOURNEY.md       # MCP implementation guide
│   ├── REDIS_MCP_INTEGRATION.md      # Redis caching patterns
│   ├── RESOURCE_TEMPLATE_ENHANCEMENT.md
│   ├── ROADMAP.md                    # Project roadmap
│   └── TRANSPORT_AGNOSTIC_VALIDATION.md
├── data/                             # Data storage
│   ├── raw/                          # Raw CSV files (John Wick reviews)
│   └── processed/                    # Processed documents
├── run.py                            # FastAPI server launcher
├── pyproject.toml                    # Dependencies and project config
├── docker-compose.yml                # Development services (Qdrant, Phoenix, Redis)
└── README.md                         # Project overview and setup
```

### **🎯 Domain Architecture Principles**

#### **1. Core Domain (`src/core/`)**
**Purpose**: Shared infrastructure and cross-cutting concerns
- **Settings Management**: Centralized configuration with environment variable support
- **Logging Configuration**: Structured logging with console filtering and file output
- **Exception Hierarchy**: Domain-specific exception classes with detailed error context

```python
# Example: Centralized settings with comprehensive configuration
from src.core.settings import get_settings

settings = get_settings()
# Access LLM config: settings.llm_temperature, settings.llm_max_retries
# Access embedding config: settings.embedding_model_name
# Access external endpoints: settings.phoenix_endpoint, settings.qdrant_url
```

#### **2. API Domain (`src/api/`)**
**Purpose**: Web interface and HTTP endpoint management
- **FastAPI Application**: 6 sophisticated retrieval strategies exposed as HTTP endpoints
- **Request/Response Models**: Pydantic schemas for API validation
- **Health Monitoring**: System health checks and cache statistics

```python
# Available endpoints:
# POST /invoke/naive_retriever
# POST /invoke/bm25_retriever  
# POST /invoke/contextual_compression_retriever
# POST /invoke/multi_query_retriever
# POST /invoke/ensemble_retriever
# POST /invoke/semantic_retriever
# GET /health
# GET /cache/stats
```

#### **3. RAG Domain (`src/rag/`)**
**Purpose**: Retrieval-Augmented Generation pipeline components
- **Embeddings**: OpenAI text-embedding-3-small integration
- **Vector Stores**: Qdrant baseline and semantic collections
- **Retrievers**: 6 different retrieval strategies (naive, BM25, contextual compression, multi-query, ensemble, semantic)
- **Chains**: LangChain RAG chain construction with configurable prompts
- **Data Loading**: CSV document processing with metadata enrichment

#### **4. MCP Domain (`src/mcp/`)**
**Purpose**: Model Context Protocol server implementation
- **Server**: FastMCP.from_fastapi() conversion with Phoenix tracing
- **Resources**: Enhanced resource handlers with semantic operation mapping
- **Transport Support**: stdio (Claude Desktop) and HTTP (programmatic access)

#### **5. Integrations Domain (`src/integrations/`)**
**Purpose**: External service clients and adapters
- **LLM Models**: GPT-4.1-mini with configurable parameters and Redis caching
- **Redis Client**: Distributed caching for LLM responses and embeddings
- **External APIs**: Cohere reranking, Phoenix telemetry

### **🔧 Configuration Management**

#### **Centralized Settings Architecture**
All configuration is managed through `src/core/settings.py` with environment variable support:

```python
class Settings(BaseSettings):
    # LLM Configuration
    llm_model_name: str = "gpt-4.1-mini"
    llm_temperature: float = 0.0
    llm_max_retries: int = 3
    llm_request_timeout: int = 60
    
    # Embedding Configuration  
    embedding_model_name: str = "text-embedding-3-small"
    
    # External Service Endpoints
    phoenix_endpoint: str = "http://localhost:6006"
    qdrant_url: str = "http://localhost:6333"
    
    # Cohere Configuration
    cohere_rerank_model: str = "rerank-english-v3.0"
    
    # MCP Configuration
    max_snippets: int = 10
    mcp_request_timeout: int = 30
```

### **🚀 MCP Server Architecture**

#### **Zero-Duplication Pattern**
The MCP server uses `FastMCP.from_fastapi()` to convert the existing FastAPI application into MCP tools without code duplication:

```python
# src/mcp/server.py
from fastmcp import FastMCP
from src.api.app import app

# Convert FastAPI app to MCP server
mcp = FastMCP.from_fastapi(app=app)

# Result: 8 HTTP routes → 8 MCP tools
# - 6 retrieval tools (naive, BM25, contextual, multi-query, ensemble, semantic)
# - 2 utility tools (health, cache stats)
```

#### **Transport Flexibility**
- **stdio Transport**: For Claude Desktop integration
- **HTTP Transport**: For programmatic access and debugging
- **Enhanced Tracing**: Phoenix observability integration

### **🧪 Testing Architecture**

#### **Multi-Layer Testing Strategy**
1. **Unit Tests** (`tests/core/`): Core component validation
2. **Integration Tests** (`tests/integration/`): End-to-end pipeline testing
3. **Transport Tests**: MCP protocol compliance validation
4. **Schema Tests**: OpenAPI and MCP schema accuracy

#### **Test Coverage**
- **57 Core Tests**: Settings, logging, exceptions (100% pass rate)
- **MCP Validation**: Schema export, transport testing, tool execution
- **API Testing**: All 6 retrieval endpoints with sample queries
- **Redis Integration**: Caching layer validation

### **📊 Production Features**

#### **Observability and Monitoring**
- **Phoenix Tracing**: Request/response tracking across all components
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Health Checks**: System dependency validation
- **Performance Metrics**: Retrieval latency, LLM token usage, cache hit rates

#### **Security and Reliability**
- **Input Validation**: Pydantic schemas for all API inputs
- **Error Handling**: Graceful degradation with detailed error context
- **Rate Limiting**: Configurable request timeouts and retry logic
- **Caching**: Redis-based response caching for performance

### **🔄 Development Workflow**

#### **Local Development**
```bash
# Start infrastructure services
docker-compose up -d

# Run data ingestion
python scripts/ingestion/csv_ingestion_pipeline.py

# Start FastAPI server
python run.py

# Start MCP server (separate terminal)
python src/mcp/server.py

# Run tests
uv run pytest tests/core/ -v
```

#### **MCP Development and Testing**
```bash
# Export MCP schema for validation
python scripts/mcp/export_mcp_schema_native.py

# Test MCP server with Claude Desktop
DANGEROUSLY_OMIT_AUTH=true fastmcp dev src/mcp/server.py

# Validate schema compliance
python scripts/mcp/validate_mcp_schema.py
```

### **📈 Scalability Considerations**

#### **Horizontal Scaling**
- **Stateless Design**: All components support horizontal scaling
- **External State**: Redis for caching, Qdrant for vector storage
- **Load Balancing**: FastAPI supports multiple workers

#### **Performance Optimization**
- **Vector Store Optimization**: Separate baseline and semantic collections
- **Caching Strategy**: Multi-level caching (Redis, in-memory)
- **Retrieval Efficiency**: Configurable retrieval parameters per strategy

### **🎯 Benefits of This Architecture**

✅ **Domain Separation**: Clear boundaries between concerns  
✅ **Zero Duplication**: Single source of truth for business logic  
✅ **Configuration Management**: Centralized, environment-aware settings  
✅ **Testing Robustness**: Comprehensive test coverage across all layers  
✅ **Production Readiness**: Observability, security, and reliability features  
✅ **MCP Compliance**: Full protocol support with transport flexibility  
✅ **Developer Experience**: Clear structure, comprehensive documentation  

This architecture maintains sophisticated RAG capabilities while providing a clean, scalable foundation for both direct API access and MCP integration patterns.

---

## **📚 Implementation References**

### **Architecture Patterns**
- **Domain-Driven Design**: Organized by business capability rather than technical layer
- **Hexagonal Architecture**: Core business logic isolated from external concerns
- **Zero-Duplication Pattern**: Single source of truth with multiple interfaces

### **Technology Integration**
- **FastMCP 2.8.0**: Latest MCP server framework with FastAPI integration
- **LangChain**: RAG pipeline construction and chain management
- **Phoenix**: Distributed tracing and observability
- **Qdrant**: High-performance vector database
- **Redis**: Distributed caching and session management

### **Best Practices Applied**
- **Configuration as Code**: Environment-aware settings management
- **Observability First**: Comprehensive logging and tracing
- **Test-Driven Development**: Multi-layer testing strategy
- **Security by Design**: Input validation and error handling
- **Documentation as Code**: Comprehensive inline and external documentation
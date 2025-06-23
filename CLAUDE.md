# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**System Version**: Advanced RAG with CQRS MCP Resources v2.4  
**Last Updated**: 2025-06-23  
**Key Feature**: Dual MCP interface (Tools + Resources) with zero duplication + external MCP ecosystem + feedback analysis capabilities  
**Python Requirement**: Python >=3.13 (runtime), py311 target (tooling compatibility)

## Architectural Constraints (IMMUTABLE)

This system follows a **tier-based architecture** with strict modification rules. Understanding these tiers is critical for maintaining system integrity.

### Tier Hierarchy (Non-Negotiable)
1. **Tier 1: Project Core** - Model pinning, import conventions, configuration (IMMUTABLE)
2. **Tier 2: Development Workflow** - Environment setup, testing, quality (REQUIRED)  
3. **Tier 3: RAG Foundation** - LangChain patterns, retrieval strategies (IMMUTABLE)
4. **Tier 4: MCP Interface** - FastAPI→MCP conversion, interface layer only (INTERFACE ONLY)
5. **Tier 5: Schema Management** - Export, validation, compliance (TOOLING)

### Critical Constraints (Never Modify)
- **Model Pinning**: Always use `ChatOpenAI(model="gpt-4.1-mini")` and `OpenAIEmbeddings(model="text-embedding-3-small")` - these are part of the public contract for deterministic responses and stable embedding dimensions
- **MCP Interface Rule**: MCP serves as interface only - never modify core RAG business logic in `src/rag/`
- **Virtual Environment Activation**: REQUIRED for all development work - system will fail without proper environment
- **Import Convention**: Use absolute imports from `src` package structure consistently

### What You Can vs. Cannot Modify

#### ✅ **Safe to Modify (Interface & Tooling Layers)**
- `src/api/app.py` - Add new FastAPI endpoints (auto-converts to MCP tools)
- `src/mcp/server.py` - MCP server configuration and wrapper logic
- `src/mcp/resources.py` - MCP resources for CQRS data access
- `scripts/` - Evaluation, ingestion, and migration scripts
- `tests/` - All test files and test data
- Docker configuration and infrastructure setup

#### ❌ **Never Modify (Core & Foundation)**
- `src/rag/` - Core RAG pipeline components (modify breaks contracts)
- `src/core/settings.py` - Model pinning configurations
- `src/integrations/llm_models.py` - Model instantiation logic
- LangChain LCEL chain patterns in `src/rag/chain.py`
- Retrieval factory patterns in `src/rag/retriever.py`

## Essential Commands

⚠️  **CRITICAL**: Always activate virtual environment first: `source .venv/bin/activate`

### Development Server
```bash
# Verify environment activation (REQUIRED)
which python  # Should show .venv path
source .venv/bin/activate  # If not already activated

# Start FastAPI server (port 8000)
python run.py

# Start MCP Tools server (stdio mode)
python src/mcp/server.py

# Start MCP Resources server (separate terminal)
python src/mcp/resources.py
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run single test file
pytest tests/rag/test_chain.py -v

# Run single test function
pytest tests/api/test_app.py::test_semantic_retriever -v

# Test API endpoints
bash tests/integration/test_api_endpoints.sh

# Test MCP conversion
python tests/integration/verify_mcp.py

# Run specific test categories (defined in pytest.ini)
pytest tests/ -m unit -v          # Unit tests - isolated component testing
pytest tests/ -m integration -v   # Integration tests - cross-system validation
pytest tests/ -m requires_llm -v  # Tests needing API keys - LLM-dependent tests
```

### Data Pipeline
```bash
# Ingest sample data (John Wick movie reviews)
python scripts/ingestion/csv_ingestion_pipeline.py

# Compare retrieval strategies
python scripts/evaluation/retrieval_method_comparison.py

# Run semantic architecture benchmark
python scripts/evaluation/semantic_architecture_benchmark.py

# Migrate from PostgreSQL pgvector (if using legacy data)
python scripts/migration/pgvector_to_qdrant_migration.py --dry-run
python scripts/migration/pgvector_to_qdrant_migration.py
```

### Infrastructure
```bash
# Start Docker services (Qdrant, Redis, Phoenix, RedisInsight)
docker-compose up -d

# Check service health
curl http://localhost:6333/health    # Qdrant
curl http://localhost:6006           # Phoenix
curl http://localhost:8000/health    # FastAPI
curl http://localhost:6379           # Redis (PING response)
# RedisInsight available at http://localhost:5540

# View services
docker-compose ps
```

### Code Quality
```bash
# Format code
black src/ tests/ --line-length 88

# Lint code
ruff check src/ tests/

# Fix linting issues automatically
ruff check src/ tests/ --fix

# Install development dependencies
uv sync --dev
```

## Implementation Patterns (Foundation)

These patterns are established in the RAG foundation layer and should be followed when extending the system.

### LangChain LCEL Chain Construction
```python
# Standard RAG chain pattern (src/rag/chain.py)
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

def create_rag_chain(
    retriever: BaseRetriever,
    llm: BaseChatModel,
    prompt_template: str = None
) -> Runnable:
    """Create LCEL RAG chain with proper composition"""
    
    # Default RAG prompt
    if not prompt_template:
        prompt_template = """Answer the question based on the context below.
        
Context: {context}
Question: {question}
Answer:"""
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    
    # LCEL chain with parallel retrieval and context formatting
    rag_chain = (
        RunnableParallel({
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        })
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain
```

### Retrieval Factory Pattern
```python
# Standard retrieval interface (src/rag/retriever.py)
def create_retriever(
    retrieval_type: str,
    vectorstore: VectorStore,
    search_kwargs: dict = None
) -> BaseRetriever:
    """Factory function for consistent retriever creation"""
    
    # Supported types: similarity, mmr, hybrid, contextual
    match retrieval_type:
        case "similarity":
            return vectorstore.as_retriever(search_kwargs=search_kwargs)
        case "mmr":
            return vectorstore.as_retriever(
                search_type="mmr", search_kwargs=search_kwargs
            )
        case "hybrid":
            return create_hybrid_retriever(vectorstore, search_kwargs)
        case _:
            raise ValueError(f"Unsupported retrieval type: {retrieval_type}")
```

### Error Handling with Fallbacks
```python
# Resilient chain pattern
from langchain_core.runnables import RunnableWithFallbacks

def create_resilient_rag_chain(
    primary_retriever: BaseRetriever,
    fallback_retriever: BaseRetriever,
    llm: BaseChatModel
) -> Runnable:
    """RAG chain with fallback mechanisms"""
    
    # Primary chain
    primary_chain = create_rag_chain(primary_retriever, llm)
    
    # Fallback chain with simpler retrieval
    fallback_chain = create_rag_chain(fallback_retriever, llm)
    
    # Chain with fallbacks
    resilient_chain = RunnableWithFallbacks(
        runnable=primary_chain,
        fallbacks=[fallback_chain],
        exception_key="error"
    )
    
    return resilient_chain
```

### Adding New Retrieval Strategies
When adding new retrieval strategies, follow this pattern:

1. **Add FastAPI endpoint** in `src/api/app.py` (auto-converts to MCP tool)
2. **Implement retriever** in `src/rag/retriever.py` using factory pattern
3. **Create LCEL chain** in `src/rag/chain.py` following established patterns
4. **Never modify** existing retrieval logic - only add new strategies

## Architecture Overview

This is a production-ready RAG system with dual MCP interfaces and comprehensive telemetry:
- **FastAPI REST API** (6 retrieval endpoints)
- **MCP Tools** (automatic conversion via FastMCP) + **CQRS Resources** (direct data access)
- **Phoenix Telemetry Integration** for AI agent observability and experiment tracking

### Key Architectural Patterns
- **Clean Architecture**: Clear separation between API layer (`src/api/`), business logic (`src/rag/`), and infrastructure (`src/core/`, `src/integrations/`)
- **Zero Duplication**: FastMCP converts FastAPI endpoints to MCP tools automatically
- **Strategy Pattern**: 6 different retrieval strategies implemented as interchangeable components
- **Dependency Injection**: Centralized configuration via `src/core/settings.py`

### Critical Constraints (Non-Negotiable)
- **Model Pinning**: Always use `ChatOpenAI` with `model="gpt-4.1-mini"` and `OpenAIEmbeddings` with `model="text-embedding-3-small"`
- **MCP Interface Layer**: MCP serves as interface only - never modify core RAG business logic
- **Import Convention**: Use absolute imports from `src` package structure
- **Code Quality**: Always run `ruff check src/ tests/ --fix` before committing
- **Environment Setup**: Virtual environment activation is REQUIRED for all development work
- **Dependency Management**: Use `uv` for package management and virtual environments

### Core Components

**src/api/app.py** - FastAPI server with 6 retrieval endpoints:
- `/invoke/naive_retriever` - Basic vector similarity
- `/invoke/bm25_retriever` - Keyword search
- `/invoke/contextual_compression_retriever` - AI reranking
- `/invoke/multi_query_retriever` - Query expansion
- `/invoke/ensemble_retriever` - Hybrid approach
- `/invoke/semantic_retriever` - Advanced semantic search

**src/mcp/server.py** - MCP server using `FastMCP.from_fastapi()` for zero-duplication conversion

**src/rag/** - Core RAG components:
- `chain.py` - LangChain LCEL chains for all 6 retrieval strategies
- `vectorstore.py` - Qdrant vector database integration
- `retriever.py` - Custom retriever implementations
- `embeddings.py` - OpenAI text-embedding-3-small

**src/core/settings.py** - Centralized configuration using Pydantic settings

**src/mcp/resources.py** - Native FastMCP resources for read-only data access

**src/integrations/** - External service integrations:
- `redis_client.py` - Redis caching client
- `llm_models.py` - OpenAI LLM wrapper
- `phoenix_mcp.py` - Phoenix telemetry integration

### Key Dependencies
- **FastAPI + FastMCP** - API server and MCP conversion (fastapi>=0.115.12, fastmcp>=2.8.0)
- **LangChain** - RAG pipeline (langchain>=0.3.25, langchain-core>=0.3.65)
- **Qdrant** - Vector database (qdrant-client>=1.11.0) 
- **Redis** - Caching (redis[hiredis]>=6.2.0)
- **Phoenix** - Telemetry and monitoring (arize-phoenix>=10.12.0)
- **uv** - Package and environment management (recommended over pip)

### Request/Response Schema
All endpoints use:
```json
// Request
{"question": "What makes John Wick movies popular?"}

// Response  
{
  "answer": "Generated response based on retrieved context",
  "context_document_count": 5
}
```

## Development Workflow

**📖 Note**: For detailed setup instructions, see `docs/SETUP.md` which provides a complete bootstrap walkthrough.

### Initial Setup
1. **Environment Setup (REQUIRED)**: 
   ```bash
   # Create and activate virtual environment using uv
   uv venv
   source .venv/bin/activate  # Linux/Mac
   # OR
   .venv\Scripts\activate  # Windows
   ```
2. `uv sync --dev` - Install all dependencies including dev tools
3. `docker-compose up -d` - Start infrastructure (Qdrant, Redis, Phoenix)
4. Create `.env` file with required API keys (`OPENAI_API_KEY`, `COHERE_API_KEY`)
5. `python scripts/ingestion/csv_ingestion_pipeline.py` - Load sample data
6. `python run.py` - Start FastAPI server
7. `python src/mcp/server.py` - Start MCP Tools server (separate terminal)
8. `python src/mcp/resources.py` - Start MCP Resources server (separate terminal)

**Note**: Steps 7-8 are for MCP development. For API-only development, step 6 is sufficient.

### Testing Strategy
- **Unit tests** - Individual components (`src/core/`, `src/rag/`)
- **Integration tests** - API endpoints and MCP conversion
- **Performance tests** - Retrieval strategy comparisons

### Configuration
- Environment variables in `.env` file (see `src/core/settings.py` for all options)
- Required: `OPENAI_API_KEY`, `COHERE_API_KEY`
- Services: Qdrant (6333), Redis (6379), Phoenix (6006)
- Optional: `OPENAI_MODEL_NAME` (default: "gpt-4.1-mini"), `EMBEDDING_MODEL_NAME` (default: "text-embedding-3-small")

### Monitoring & AI Agent Observability
- **Phoenix telemetry** at http://localhost:6006 - **Critical for understanding agent behavior**
- **Automatic tracing** for all retrieval operations and agent decision points
- **Experiment tracking** with `johnwick_golden_testset` for performance analysis
- **Redis caching** with TTL configuration and performance monitoring

### Key Telemetry Use Cases (Following Samuel Colvin's MCP Pattern)
- **Agent Performance Analysis**: Query Phoenix via MCP to understand retrieval strategy effectiveness
- **Debugging Agent Decisions**: Trace through agent reasoning with full context
- **Performance Optimization**: Identify bottlenecks in agent workflows using live telemetry data
- **Experiment Comparison**: Compare different RAG strategies with quantified metrics from `johnwick_golden_testset`

## MCP Integration

This system implements **dual MCP interfaces** plus external MCP ecosystem integration:

### 1. MCP Tools Server (`src/mcp/server.py`)
**Purpose**: Converts FastAPI endpoints to MCP tools using zero-duplication pattern
- **Pattern**: `FastMCP.from_fastapi()` automatic conversion
- **Interface**: MCP Tools that execute RAG pipelines
- **Use Case**: Command operations that process and format data

### 2. MCP Resources Server (`src/mcp/resources.py`)
**Purpose**: Native FastMCP resources with CQRS read-only access
- **Pattern**: Direct FastMCP resource registration
- **Interface**: MCP Resources for optimized data access
- **Use Case**: Query operations with LLM-formatted responses

### 3. External MCP Ecosystem
**Purpose**: Access external MCP services via Claude Code CLI
- **Pattern**: Use configured external MCP servers directly
- **Interface**: qdrant-code-snippets, qdrant-semantic-memory, ai-docs-server, etc.
- **Use Case**: Code patterns, semantic memory, documentation access

### MCP Tools vs Resources Architecture

#### Tools Server (`server.py`)
```bash
# Start tools server (FastAPI → MCP conversion)
python src/mcp/server.py

# Test tools via CLI
python tests/integration/verify_mcp.py

# Inspector for tools validation
DANGEROUSLY_OMIT_AUTH=true fastmcp dev src/mcp/server.py
```

**Available Tools** (Command Pattern):
- `naive_retriever` - Basic vector search with full RAG pipeline
- `bm25_retriever` - Keyword search with response formatting
- `ensemble_retriever` - Hybrid approach with AI processing
- `semantic_retriever` - Advanced semantic search with context
- `contextual_compression_retriever` - AI reranking with filtering
- `multi_query_retriever` - Query expansion with synthesis

#### Resources Server (`resources.py`)  
```bash
# Start resources server (Native FastMCP resources)
python src/mcp/resources.py

# Test resources implementation
python tests/integration/test_cqrs_resources.py

# Inspector for resources validation
DANGEROUSLY_OMIT_AUTH=true fastmcp dev src/mcp/resources.py
```

**Note**: The resources server provides native FastMCP resources for optimized read-only access to the RAG system's data

**Available Resources** (Query Pattern):
- `retriever://naive_retriever/{query}` - Direct access to naive results
- `retriever://semantic_retriever/{query}` - Direct semantic processing
- `retriever://ensemble_retriever/{query}` - Direct hybrid results
- `system://health` - System status and configuration

### Invalid Tests (Clean Up Required)
**CRITICAL**: The following test files reference removed components and need attention:
- `tests/integration/test_cqrs_resources.py` - Imports missing `src.mcp.qdrant_resources` module
- `tests/integration/test_cqrs_resources_with_assertions.py` - Same import issue
- `tests/integration/test_cqrs_structure_validation.py` - Validates non-existent file structure

**Action Required**: Retrieve and reintroduce these files from Github history. The `test_cqrs_structure_validation.py` code highlight an essential usecase for agent centric data retrieval from `johnwick_baseline` and `johnwick_semantic` collections.

### Schema Management (Tier 5)

#### Native Schema Discovery (RECOMMENDED)
Use native MCP discovery instead of legacy export methods:

```bash
# Start server with streamable HTTP
python src/mcp/server.py

# Native schema discovery via HTTP
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"rpc.discover","params":{}}'

# Or via FastMCP client
python -c "
import asyncio
from fastmcp import Client

async def get_schema():
    async with Client('http://127.0.0.1:8000/mcp', transport='streamable-http') as client:
        return await client.discover()

print(asyncio.run(get_schema()))
"
```

#### Legacy Schema Export (Development Only)
```bash
# Generate both legacy and official MCP schemas
python scripts/mcp/export_mcp_schema.py

# Outputs:
# - mcp_server_schema.json (legacy/community format)
# - mcp_server_official.json (official MCP format - RECOMMENDED)

# Validate schemas against MCP 2025-03-26 specification
python scripts/mcp/validate_mcp_schema.py
```

#### Configuration-Driven Schema Management
Edit `scripts/mcp/mcp_config.toml` to configure:
- MCP specification version and schema URLs
- Tool annotations and governance policies
- Validation settings and compliance requirements

### FastMCP Inspector Commands

#### Tools Server Inspection
```bash
# Start inspector for tools server
DANGEROUSLY_OMIT_AUTH=true fastmcp dev src/mcp/server.py

# Available in inspector:
# - List available tools (from FastAPI conversion)
# - Test tool execution with sample queries
# - Validate tool schemas and parameters
# - Monitor tool performance and responses
```

#### Resources Server Inspection
```bash
# Start inspector for resources server  
DANGEROUSLY_OMIT_AUTH=true fastmcp dev src/mcp/resources.py

# Available in inspector:
# - List available resources (native + CQRS)
# - Test resource access with URI patterns
# - Validate resource responses and formatting
# - Monitor resource performance and caching
```

#### Inspector Workflow
1. **Start Inspector**: Use appropriate `fastmcp dev` command
2. **Discover Schema**: Inspector auto-discovers available tools/resources
3. **Test Functionality**: Execute tools/resources with sample inputs
4. **Validate Responses**: Verify output format and content quality
5. **Performance Testing**: Monitor execution times and resource usage

### CQRS Benefits and Use Cases

#### Tools (Command Pattern)
- **Full RAG Pipeline**: Complete LangChain LCEL execution
- **Response Formatting**: AI-optimized answer generation
- **Context Processing**: Document retrieval and synthesis
- **Heavy Processing**: Embedding generation, reranking, synthesis

#### Resources (Query Pattern)  
- **Direct Data Access**: 3-5x faster than full pipeline
- **Raw Results**: Unprocessed vector search results
- **Metadata Rich**: Full document payloads and statistics
- **LLM Optimized**: Pre-formatted for consumption

### Development and Testing

#### Comprehensive Testing
```bash
# Test both servers independently
python tests/integration/verify_mcp.py                    # Tools server
# NOTE: CQRS resources tests are currently broken and need to be reintroduced - see Invalid Tests section

# Schema validation
python scripts/mcp/export_mcp_schema_stdio.py            # Tools schema
python scripts/mcp/export_mcp_schema_native.py           # Resources schema
python scripts/mcp/compare_schema_outputs.py             # Compare schemas

# Quality comparison
pytest tests/integration/functional_quality_comparison.py -v
```

#### Inspector-Based Development
```bash
# Tools development workflow
DANGEROUSLY_OMIT_AUTH=true fastmcp dev src/mcp/server.py
# → Test FastAPI conversion fidelity
# → Validate tool parameter schemas  
# → Verify response formatting

# Resources development workflow
DANGEROUSLY_OMIT_AUTH=true fastmcp dev src/mcp/resources.py
# → Test native resource registration
# → Validate URI pattern matching
# → Verify CQRS compliance
```

#### Client Integration Testing
```bash
# Test external MCP client integrations
python tests/integrations/test_phoenix_mcp.py            # Phoenix client wrapper
python tests/integrations/test_qdrant_mcp.py             # Qdrant client wrapper
python tests/integrations/mcp_tool_validation.py         # Cross-system validation

# Test Redis MCP integration
python tests/integrations/test_redis_mcp.py              # Redis MCP wrapper
```

## Available MCP Ecosystem

Claude Code has access to the following MCP servers defined in `mcp_client_config.json`. These should be leveraged during development:

### Core Development Tools
- **`ai-docs-server`**: Access to comprehensive documentation
  - Cursor, PydanticAI, MCP Protocol, FastMCP, ArizePhoenix
  - LangGraph, LangChain, Vercel AI SDK, Anthropic docs
  - Use for reference and implementation guidance

- **`sequential-thinking`**: Enhanced reasoning capabilities
  - Use for complex problem-solving and analysis
  - Helpful for architectural decisions and debugging

### Data Storage & Retrieval
- **`qdrant-code-snippets`** (Port 8002): Code snippet management
  - Store reusable code patterns and solutions
  - Find existing implementations for reference
  - Collection: `code-snippets`

- **`qdrant-semantic-memory`** (Port 8003): Contextual memory
  - Store conversation insights and project decisions
  - Remember learned patterns and user preferences
  - Collection: `semantic-memory`

- **`memory`**: Official MCP knowledge graph memory
  - Persistent entity-relationship storage across sessions
  - Structured user modeling and project knowledge
  - Complements semantic memory with graph-based relationships
  - Setup: `claude mcp add memory -- npx -y @modelcontextprotocol/server-memory`
  - **Storage**: Default `memory.json` in npm package directory (see configuration below)

- **`redis-mcp`**: Redis database operations
  - Cache management and session storage
  - Integration with existing Redis infrastructure

### Observability & Analysis  
- **`phoenix`** (localhost:6006): **Critical for AI agent observability**
  - Access Phoenix UI data and experiments via MCP
  - Analyze RAG performance and agent behavior patterns
  - Query `johnwick_golden_testset` experiment results
  - Essential for understanding agent decision-making and performance optimization

### Utility Services
- **`mcp-server-time`**: Time and timezone operations
- **`brave-search`**: Web search capabilities (requires `BRAVE_API_KEY`)
- **`fetch`**: HTTP requests and web content retrieval

### MCP Tools Usage for Claude Code CLI

**CRITICAL**: Claude Code CLI requires explicit permissions for MCP tool access. See `claude_code_mcp_guide.md` for complete usage patterns and tested commands.

#### Verified Working Commands
```bash
# Store code patterns (requires permission)
claude -p --allowedTools "qdrant-store" "Store this FastMCP pattern in qdrant-code-snippets: [PATTERN]"

# Find existing patterns (requires permission)
claude -p --allowedTools "qdrant-find" "Search qdrant-code-snippets for FastMCP conversion patterns"

# Access documentation (NO permissions needed)
"Check ai-docs-server FastMCP documentation for resource registration patterns"

# Store project decisions (requires permission)
claude -p --allowedTools "qdrant-store" "Store in qdrant-semantic-memory: Decision - [ARCHITECTURAL_DECISION]"

# Create structured knowledge entities (no permissions needed)
"Create entity in memory: John_Smith, person, [works on RAG optimization, prefers semantic retrieval]"
```

#### Interactive Session (Recommended)
```bash
# Start with verbose mode for permission prompts
claude --verbose

# Claude Code will prompt for permission on each MCP tool use
> Search qdrant-code-snippets for FastMCP patterns
# Response: "Allow qdrant-find?" → Answer: Yes
```

#### Development Workflow Pattern (Research → Develop → Store → Validate)
```bash
# 1. Research existing knowledge first
claude -p --allowedTools "qdrant-find" "Search qdrant-semantic-memory for previous work on [TOPIC]"

# 2. Access documentation (no permissions needed)
"Check ai-docs-server FastMCP documentation for [SPECIFIC_NEED]"

# 3. Store learnings during development
claude -p --allowedTools "qdrant-store" "Store in qdrant-semantic-memory: [LEARNING_OR_DECISION]"

# 3b. Create structured knowledge entities
"Create entity in memory: [PROJECT_NAME], project, [key insights and decisions]"

# 4. Validate storage worked
claude -p --allowedTools "qdrant-find" "Find the [TOPIC] pattern I just stored"
```

#### Integration with Local Development
- **Phoenix Integration**: Use `phoenix` MCP alongside local Phoenix instance (port 6006)
- **Qdrant Integration**: Leverage external Qdrant collections alongside project collections
- **Redis Integration**: Coordinate with local Redis for comprehensive caching
- **Documentation**: Access latest docs for all dependencies via `ai-docs-server`

### MCP Server Configuration Notes
- **Environment Variables**: Servers use environment variables for API keys and URLs
- **Port Management**: External Qdrant servers use ports 8002-8003 
- **Local Services**: Phoenix and Redis connect to local infrastructure
- **Documentation**: AI docs server provides comprehensive reference material
- **Permissions**: Use `--allowedTools` flag or interactive mode with permission prompts

### Memory Server Storage Configuration

The Memory MCP server stores data in a JSON file. Configure custom storage location:

```bash
# Option 1: Set environment variable globally
export MEMORY_FILE_PATH="/home/donbr/ghcp/adv-rag/data/memory.json"

# Option 2: Configure via Claude Code settings (recommended for project)
# Add to ~/.claude/config.json under the memory server entry:
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "/home/donbr/ghcp/adv-rag/data/memory.json"
      }
    }
  }
}
```

**Recommended for Advanced RAG**: Store memory file in project `data/` directory for:
- ✅ Project-specific knowledge persistence
- ✅ Easier backup and version control
- ✅ Team collaboration on shared knowledge
- ✅ Clear data organization alongside other project data

### MCP Success Metrics
**Effective MCP usage when:**
- ✅ Store and retrieve patterns without permission errors
- ✅ Find stored patterns from previous sessions
- ✅ Access ai-docs-server documentation without issues
- ✅ Use `/mcp` command to check server status when needed
- ✅ Build context across development sessions

### Comprehensive Memory Architecture

This project now provides **three-tier memory and observability**:

1. **Knowledge Graph Memory** (`memory`): Structured entities, relationships, and observations
   - User preferences and project team modeling
   - Experiment relationships and configuration tracking
   - Cross-session persistence of structured knowledge

2. **Semantic Memory** (`qdrant-semantic-memory`): Contextual insights and patterns
   - Unstructured learning insights and decisions
   - Pattern recognition across development sessions
   - Contextual project knowledge

3. **Telemetry Data** (`phoenix`): Performance metrics and experiment tracking
   - Real-time agent behavior analysis
   - `johnwick_golden_testset` performance benchmarking
   - Quantified retrieval strategy effectiveness

This creates a comprehensive agentic AI observability platform following Samuel Colvin's MCP telemetry patterns.

These MCP servers provide a rich ecosystem for development, testing, and analysis that should be actively used alongside the project's own MCP implementations.

**📖 Documentation References**:
- `docs/SETUP.md` - Complete bootstrap walkthrough
- `docs/FUNCTIONAL_OVERVIEW.md` - System architecture details  
- `docs/MCP_COMMAND_LINE_GUIDE.md` - MCP CLI usage patterns
- `docs/CQRS_IMPLEMENTATION_SUMMARY.md` - MCP Resources implementation details
- `docs/project-structure.md` - Detailed architecture reference
- `claude_code_mcp_guide.md` - Claude Code MCP integration guide

## Development Decision Matrix

| Development Task | Tier Level | Recommended Approach | Implementation Location | Modification Rule |
|------------------|------------|---------------------|------------------------|-------------------|
| **Add new retrieval strategy** | Tier 4 (Interface) | FastAPI endpoint → auto-converts to MCP tool | `src/api/app.py` + `src/rag/` | ✅ Safe - adds new functionality |
| **Direct data access for LLMs** | Tier 4 (Interface) | CQRS Resource | `src/mcp/resources.py` | ✅ Safe - interface layer only |
| **Phoenix telemetry integration** | Tier 2 (Workflow) | Integration Module | `src/integrations/phoenix_mcp.py` | ✅ Safe - monitoring enhancement |
| **Modify existing retrieval logic** | Tier 3 (Foundation) | **FORBIDDEN** | `src/rag/` | ❌ Never - breaks contracts |
| **Change model configurations** | Tier 1 (Core) | **FORBIDDEN** | `src/core/settings.py` | ❌ Never - public contract |
| **Read-only query operations** | Tier 4 (Interface) | MCP Resources | `src/mcp/resources.py` | ✅ Safe - data access layer |
| **Command operations with processing** | Tier 4 (Interface) | MCP Tools (FastAPI) | Automatic via `src/mcp/server.py` | ✅ Safe - wrapper functionality |
| **Cache integration** | Tier 2 (Workflow) | Redis client | `src/integrations/redis_client.py` | ✅ Safe - performance optimization |
| **Schema export and validation** | Tier 5 (Tooling) | Configuration-driven | `scripts/mcp/` | ✅ Safe - tooling layer |

### Decision Framework
1. **Identify the tier** of your intended change
2. **Check modification rules** for that tier  
3. **Use interface layers** (Tier 4) to expose new functionality
4. **Never modify** foundation layers (Tier 1-3) without architectural review

## Environment Validation Checklist

**CRITICAL**: Run these checks in order - each tier depends on the previous ones.

```bash
# Tier 1: Core Environment (REQUIRED)
which python  # Should show .venv path - MUST be virtual environment
python --version  # Should show Python >= 3.13 (runtime requirement)
uv --version  # Should show uv version >= 0.5.0

# Validate model pinning contracts
python -c "from src.core.settings import get_settings; s=get_settings(); print(f'OpenAI: {bool(s.openai_api_key)}, Cohere: {bool(s.cohere_api_key)}')"

# Tier 2: Development Workflow  
python src/core/settings.py         # Check environment variables and configuration

# Tier 3: RAG Foundation (Infrastructure)
docker-compose ps  # All services should be Up
curl http://localhost:6333/health    # Qdrant: {"status":"ok"}
curl http://localhost:6379           # Redis: +PONG  
curl http://localhost:6006           # Phoenix: HTML response
curl http://localhost:6333/collections  # Should show johnwick collections

# Tier 4: MCP Interface Layer
curl http://localhost:8000/health    # FastAPI: {"status":"healthy"}
python tests/integration/verify_mcp.py  # MCP tools validation

# Tier 5: Schema Management & Tooling
python scripts/mcp/validate_mcp_schema.py  # Schema compliance check
# Optional: Check memory server storage (if configured)
ls -la data/memory.json  # Should exist if custom path configured

# Additional Infrastructure (Optional)
curl -s http://localhost:5540 > /dev/null && echo "RedisInsight available" || echo "RedisInsight not running"
```

### Validation Failure Recovery
- **Tier 1 failure**: Fix virtual environment activation before proceeding
- **Tier 2 failure**: Check `.env` file and API keys
- **Tier 3 failure**: Restart Docker services: `docker-compose down && docker-compose up -d`
- **Tier 4 failure**: Check FastAPI server status and MCP conversion
- **Tier 5 failure**: Regenerate schemas: `python scripts/mcp/export_mcp_schema.py`

## MCP Interface Selection Guide

### Use MCP Tools (FastAPI Conversion) When:
- **Processing required**: Full RAG pipeline with LLM synthesis
- **Response formatting needed**: AI-optimized answer generation
- **Command pattern**: Execute operations that modify or process data
- **LangChain integration**: Leveraging LCEL chains and retrievers

### Use MCP Resources (Native FastMCP) When:
- **Direct data access**: Raw vector search results
- **Query pattern**: Read-only operations without processing
- **Performance critical**: 3-5x faster than full pipeline
- **LLM consumption**: Pre-formatted data for AI processing

### Use External MCP Services When:
- **Code pattern management**: Use `qdrant-code-snippets` MCP via Claude Code CLI
- **Semantic memory**: Use `qdrant-semantic-memory` MCP via Claude Code CLI  
- **External data access**: Use dedicated MCP servers rather than Python wrappers

## Data Sources & Telemetry

### Core Datasets
- **Sample dataset**: John Wick movie reviews (CSV format in `data/raw/`)
- **Vector collections**: `johnwick_baseline` and `johnwick_semantic`
- **Semantic chunking**: Advanced retrieval strategies with different chunk sizes
- **Ingestion pipeline**: `scripts/ingestion/csv_ingestion_pipeline.py` for data loading

### Golden Test Sets & Experiment Tracking
- **`johnwick_golden_testset`**: Curated evaluation dataset for RAG performance
- **Phoenix integration**: Automatic experiment tracking and agent behavior analysis
- **Performance benchmarking**: Compare retrieval strategies with quantified metrics
- **AI Agent Observability**: Following Samuel Colvin's MCP telemetry patterns for understanding agent decision-making

## Error Handling & Debugging

### Service Health Checks
- **Qdrant**: `curl http://localhost:6333`
- **Phoenix**: `curl http://localhost:6006`
- **FastAPI**: `curl http://localhost:8000/health`

### Debugging Tools
- **API endpoints**: Use curl commands in `tests/integration/test_api_endpoints.sh`
- **MCP Tools**: Run `python tests/integration/verify_mcp.py` for validation
- **CQRS Resources**: Run `python tests/integration/test_cqrs_structure_validation.py`
- **Environment**: Run `python src/core/settings.py` to check API keys

### Monitoring
- **Logs**: API server logs to console
- **Telemetry**: Phoenix dashboard at http://localhost:6006
- **Caching**: Redis monitoring via RedisInsight at http://localhost:5540

## MCP Troubleshooting

### Common Claude Code CLI Permission Issues

#### Problem: "Permission denied for tool 'qdrant-store'"
```bash
# Solution 1: Use explicit permissions
claude -p --allowedTools "qdrant-store" "Store this pattern..."

# Solution 2: Interactive mode with prompts
claude --verbose
> Store pattern in qdrant-code-snippets
# Answer "Yes" when prompted for qdrant-store permission
```

#### Problem: "MCP server not found" or connection errors
```bash
# Check MCP server status
claude
> /mcp  # Lists all available MCP servers and their status

# Verify external MCP servers are running
curl http://localhost:8002/health  # qdrant-code-snippets
curl http://localhost:8003/health  # qdrant-semantic-memory
```

#### Problem: "Tool execution failed" with MCP Tools
```bash
# Verify FastAPI server is running
curl http://localhost:8000/health

# Test MCP tools server directly
python tests/integration/verify_mcp.py

# Check for service dependencies
python src/core/settings.py  # Verify API keys
```

### MCP Resources Access Issues

#### Problem: "Resource not found" errors
```bash
# Test CQRS resources server (BROKEN - needs update)
# python tests/integration/test_cqrs_resources.py

# Verify Qdrant collections exist
curl http://localhost:6333/collections

# Check resource server is running
python src/mcp/resources.py
```

#### Problem: Empty or malformed responses
```bash
# Validate data pipeline completed
python scripts/ingestion/csv_ingestion_pipeline.py

# Check collection contents
curl "http://localhost:6333/collections/johnwick_baseline/points?limit=1"
```

### Service Startup Troubleshooting

#### Docker Services Won't Start
```bash
# Check port conflicts
netstat -tulpn | grep -E ":(6333|6379|6006|8000)"

# Clean Docker state
docker-compose down && docker system prune -f && docker-compose up -d

# Check logs
docker-compose logs qdrant
docker-compose logs redis  
docker-compose logs phoenix
```

#### API Keys Not Loading
```bash
# Verify .env file exists and is readable
ls -la .env && cat .env | grep -E "(OPENAI|COHERE)_API_KEY"

# Test environment loading
python -c "from src.core.settings import get_settings; print(bool(get_settings().openai_api_key))"
```

NOTE:  remember to always mask sensitive information from `.env` files when output in logs and never commit them to version control.
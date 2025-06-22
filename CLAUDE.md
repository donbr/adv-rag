# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**System Version**: Advanced RAG with CQRS MCP Resources v2.4  
**Last Updated**: 2025-06-22  
**Key Feature**: Dual MCP interface (Tools + Resources) with zero duplication + external MCP ecosystem + feedback analysis capabilities  
**Python Requirement**: Python >=3.13 (as specified in pyproject.toml)

## Essential Commands

### Development Server
```bash
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

# Run specific test categories
pytest tests/ -m unit -v          # Unit tests
pytest tests/ -m integration -v   # Integration tests  
pytest tests/ -m requires_llm -v  # Tests needing API keys
```

### Data Pipeline
```bash
# Ingest sample data (John Wick movie reviews)
python scripts/ingestion/csv_ingestion_pipeline.py

# Compare retrieval strategies
python scripts/evaluation/retrieval_method_comparison.py

# Run semantic architecture benchmark
python scripts/evaluation/semantic_architecture_benchmark.py
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
python tests/integration/test_cqrs_resources.py          # Resources server
python tests/integration/test_cqrs_structure_validation.py # CQRS compliance

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
- `claude_code_mcp_guide.md` - Claude Code MCP integration guide

## Development Decision Matrix

| Development Task | Recommended Approach | Implementation Location | Notes |
|------------------|---------------------|------------------------|-------|
| **Add new retrieval strategy** | FastAPI endpoint → auto-converts to MCP tool | `src/api/app.py` + `src/rag/` | Zero duplication via FastMCP |
| **Direct data access for LLMs** | CQRS Resource | `src/mcp/resources.py` | 3-5x faster than full pipeline |
| **Phoenix telemetry integration** | Integration Module | `src/integrations/phoenix_mcp.py` | Phoenix experiment tracking |
| **Read-only query operations** | MCP Resources | `src/mcp/resources.py` | Direct RAG data access |
| **Command operations with processing** | MCP Tools (FastAPI) | Automatic via `src/mcp/server.py` | Full RAG pipeline execution |
| **Cache integration** | Redis client | `src/integrations/redis_client.py` | Built-in TTL management |

## Environment Validation Checklist

```bash
# 1. Verify virtual environment and uv
which python  # Should show .venv path
uv --version  # Should show uv version >= 0.5.0

# 2. Check Docker services
docker-compose ps  # All services should be Up
curl http://localhost:6333/health    # Qdrant: {"status":"ok"}
curl http://localhost:6379           # Redis: +PONG
curl http://localhost:6006           # Phoenix: HTML response
curl http://localhost:8000/health    # FastAPI: {"status":"healthy"}
# RedisInsight: http://localhost:5540 (web interface)

# 3. Validate API keys
python src/core/settings.py         # Check environment variables

# 4. Test data pipeline
curl http://localhost:6333/collections  # Should show johnwick collections

# 5. Verify MCP servers
python tests/integration/verify_mcp.py  # MCP tools validation
python tests/integration/test_cqrs_resources.py  # CQRS resources check

# 6. Check memory server storage (if configured)
ls -la data/memory.json  # Should exist if custom path configured

# 7. Verify Python version compatibility
python --version  # Should show Python >= 3.13 (required by pyproject.toml)

# 8. Check RedisInsight (optional)
curl -s http://localhost:5540 > /dev/null && echo "RedisInsight available" || echo "RedisInsight not running"
```

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
# Test CQRS resources server
python tests/integration/test_cqrs_resources.py

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
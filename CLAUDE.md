# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Development Server
```bash
# Start FastAPI server (port 8000)
python run.py

# Start MCP server (stdio mode)
python src/mcp/server.py
```

### Testing
```bash
# Run all tests
pytest tests/ -v

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
# Start Docker services (Qdrant, Redis, Phoenix)
docker-compose up -d

# Check service health
curl http://localhost:6333/health    # Qdrant
curl http://localhost:6006           # Phoenix
curl http://localhost:8000/health    # FastAPI

# View services
docker-compose ps
```

### Code Quality
```bash
# Format code
black src/ tests/ --line-length 88

# Lint code
ruff check src/ tests/
```

## Architecture Overview

This is a production-ready RAG system with dual interfaces:
- **FastAPI REST API** (6 retrieval endpoints)
- **MCP Tools** (automatic conversion via FastMCP)

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

### Key Dependencies
- **FastAPI + FastMCP** - API server and MCP conversion
- **LangChain** - RAG pipeline (langchain>=0.3.25)
- **Qdrant** - Vector database (qdrant-client>=1.11.0) 
- **Redis** - Caching (redis[hiredis]>=6.2.0)
- **Phoenix** - Telemetry and monitoring (arize-phoenix>=10.12.0)

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

### Initial Setup
1. `docker-compose up -d` - Start infrastructure
2. `uv sync && source .venv/bin/activate` - Install dependencies
3. `python scripts/ingestion/csv_ingestion_pipeline.py` - Load sample data
4. `python run.py` - Start FastAPI server
5. `python src/mcp/server.py` - Start MCP server

### Testing Strategy
- **Unit tests** - Individual components (`src/core/`, `src/rag/`)
- **Integration tests** - API endpoints and MCP conversion
- **Performance tests** - Retrieval strategy comparisons

### Configuration
- Environment variables in `.env` file
- Required: `OPENAI_API_KEY`, `COHERE_API_KEY`
- Services: Qdrant (6333), Redis (6379), Phoenix (6006)

### Monitoring
- Phoenix telemetry at http://localhost:6006
- Automatic tracing for all retrieval operations
- Redis caching with TTL configuration

## MCP Integration

This system demonstrates FastAPI → MCP conversion patterns:
- Zero code duplication between REST API and MCP tools
- Automatic schema generation and validation
- Production-ready MCP server implementation

### MCP Development
```bash
# Test MCP tools
python tests/integration/verify_mcp.py

# Export MCP schemas
python scripts/mcp/export_mcp_schema_native.py
python scripts/mcp/export_mcp_schema_stdio.py

# Validate MCP compliance
python scripts/mcp/validate_mcp_schema.py
```

## Data Sources
- Sample dataset: John Wick movie reviews (CSV format)
- Two vector collections: `johnwick_baseline` and `johnwick_semantic`
- Semantic chunking for advanced retrieval strategies
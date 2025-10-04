# Advanced RAG Quick Reference

📖 **First time?** See **[SETUP.md](SETUP.md)** for complete setup  
📘 **Development guide**: See **[CLAUDE.md](../CLAUDE.md)** for architecture constraints and patterns  
🚨 **Problems?** See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for solutions

## ⚡ Most Common Commands

### Quick Status Check
```bash
# Single command to check everything
python scripts/status.py

# Expected: All ✅ (Environment, Infrastructure, Application, MCP, Data)
```

### System Validation ✅
```bash
# Complete validation (recommended after setup)
bash scripts/validation/run_system_health_check.sh

# Quick health checks
curl http://localhost:6333           # Qdrant: {"title":"qdrant - vector search engine"}
curl http://localhost:8000/health    # FastAPI: {"status":"healthy"}
curl http://localhost:6006           # Phoenix: HTML response
```

### Daily Development
```bash
# Start system (in this order)
source .venv/bin/activate        # REQUIRED first step
docker-compose up -d             # Start infrastructure 
python run.py                    # Start API server (separate terminal)

# Quick test
curl -X POST "http://localhost:8000/invoke/semantic_retriever" \
     -H "Content-Type: application/json" \
     -d '{"question": "test query"}'
```

### Emergency Reset
```bash
# If everything breaks
docker-compose down -v && docker-compose up -d
python scripts/ingestion/csv_ingestion_pipeline.py && python run.py
```

## 🛠️ Command Categories

### Service Management
```bash
# Infrastructure
docker-compose up -d                 # Start all Docker services
docker-compose ps                    # Check service status
curl http://localhost:6333           # Qdrant health
curl http://localhost:8000/health    # FastAPI health

# Application servers  
python run.py                        # Main API server (port 8000)
python src/mcp/server.py             # MCP Tools server 
python src/mcp/resources.py          # MCP Resources server
```

### Data & Testing
```bash
# Load data (required once)
python scripts/ingestion/csv_ingestion_pipeline.py

# Run tests
pytest tests/ -v                     # All tests
python tests/integration/verify_mcp.py  # MCP validation

# Benchmarks
python scripts/evaluation/retrieval_method_comparison.py
```

## 🏗️ What You Can/Cannot Modify

📘 **Full details**: See [CLAUDE.md](../CLAUDE.md) for complete architectural constraints

### ✅ Safe to Modify
- **Interface Layer**: `src/api/app.py`, `src/mcp/` - Add new endpoints/features  
- **Configuration**: `.env` file, environment variables
- **Scripts**: `scripts/`, `tests/` - All tooling and testing
- **Documentation**: All `.md` files

### ❌ Never Modify (Breaks System)
- **Core RAG**: `src/rag/` - Retrieval pipeline components
- **Settings**: `src/core/settings.py` - Model pinning (gpt-4.1-mini, text-embedding-3-small)
- **Chain Patterns**: `src/rag/chain.py` - LangChain LCEL foundations

**Rule**: Add new features via interface layers, never modify existing core components

## 🔄 6 Retrieval Strategies

| Strategy | Use Case | Endpoint |
|----------|----------|----------|
| **Naive** | Fast baseline | `/invoke/naive_retriever` |
| **BM25** | Keyword search | `/invoke/bm25_retriever` |
| **Semantic** | Best overall | `/invoke/semantic_retriever` |
| **Ensemble** | Hybrid approach | `/invoke/ensemble_retriever` |
| **Compression** | Quality focus | `/invoke/contextual_compression_retriever` |
| **Multi-Query** | Comprehensive | `/invoke/multi_query_retriever` |

### Quick Test Template
```bash
curl -X POST "http://localhost:8000/invoke/STRATEGY_NAME" \
     -H "Content-Type: application/json" \
     -d '{"question": "YOUR_QUESTION"}'

# Returns: {"answer": "...", "context_document_count": N}
```

## 🔌 MCP Integration

📘 **Full MCP details**: See [CLAUDE.md](../CLAUDE.md) MCP section

### Quick MCP Usage
```bash
# Start MCP Tools server (Command pattern - full processing)
python src/mcp/server.py

# Start MCP Resources server (Query pattern - direct data)  
python src/mcp/resources.py

# Test MCP functionality
python tests/integration/verify_mcp.py
```

**Interface Selection**:
- **MCP Tools**: Need complete answers with AI processing (~20-30 sec)
- **MCP Resources**: Need raw data for further processing (~3-5 sec)

## 🧪 Testing & Validation

```bash
# Quick tests
pytest tests/ -v                           # All tests
pytest tests/ -m unit -v                   # Unit tests only
pytest tests/ -m integration -v            # Integration tests

# System validation  
python tests/integration/verify_mcp.py     # MCP functionality
bash tests/integration/test_api_endpoints.sh  # API endpoints
python scripts/status.py                   # Complete system check
```

## 📊 Performance & Monitoring

```bash
# Compare retrieval strategies
python scripts/evaluation/retrieval_method_comparison.py

# Phoenix telemetry dashboard
open http://localhost:6006

# Redis cache monitoring  
open http://localhost:5540  # RedisInsight
```

## 🔧 Code Quality
```bash
# Format and lint (before commits)
black src/ tests/ --line-length 88
ruff check src/ tests/ --fix
```

## 📋 Required Environment Variables
```bash
# In .env file
OPENAI_API_KEY=your_openai_key_here
COHERE_API_KEY=your_cohere_key_here
```

## 🎯 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 in use | `lsof -ti :8000 | xargs kill -9` or use `PORT=8001 python run.py` |
| Virtual env not active | `source .venv/bin/activate` |
| Services not running | `docker-compose restart` |
| MCP tools fail | `python tests/integration/verify_mcp.py` |
| Tests fail | Check API keys: `python src/core/settings.py` |

**For detailed solutions**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 🔄 Adding New Features

**Safe Pattern**: Add new endpoints to `src/api/app.py` → auto-converts to MCP tools  
**Never modify**: `src/rag/` (core components) or `src/core/settings.py` (model pinning)

📘 **Full constraints**: See [CLAUDE.md](../CLAUDE.md) Development Decision Matrix

---

## 📚 Documentation Navigation

- **[CLAUDE.md](../CLAUDE.md)** - Main developer guide with all commands and architecture
- **[SETUP.md](SETUP.md)** - Initial setup walkthrough  
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Problem-solving by component
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Deep technical architecture details
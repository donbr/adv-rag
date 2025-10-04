# Advanced RAG System - Complete Setup Guide

## 🚀 Quick Start Reference

📖 **For development guidance after setup**: See **[CLAUDE.md](../CLAUDE.md)** - comprehensive developer guide  
🚀 **For daily commands**: See **[docs/QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - essential commands by function  
🚨 **If something breaks**: See **[docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - problem-solving guide

This guide walks you through the **4-step bootstrap process** to get the Advanced RAG system running.

### Prerequisites
- **Docker & Docker Compose** - Infrastructure services
- **Python 3.13+** - Runtime requirement
- **uv package manager** - Recommended for dependency management
- **OpenAI API key** - Required for LLM and embeddings
- **Cohere API key** - Required for reranking (optional for basic functionality)

⚠️ **CRITICAL**: Virtual environment activation is REQUIRED - see [CLAUDE.md](../CLAUDE.md) for details

## 🔄 4-Step Bootstrap Process

### 1. **Environment Setup** (2 minutes)
```bash
# Clone and setup environment
git clone <repository>
cd adv-rag

# Create and activate virtual environment (REQUIRED)
uv venv && source .venv/bin/activate && uv sync --dev

# Configure environment
cp .env.example .env
# Edit .env with your API keys:
# OPENAI_API_KEY=your_key_here
# COHERE_API_KEY=your_key_here
```

**✅ Success Check**: `which python` should show `.venv` path  
**❌ If this fails**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#tier-1-environment--dependencies-issues)

### 2. **Infrastructure & Data** (3 minutes)
```bash
# Start Docker services (Qdrant, Redis, Phoenix, RedisInsight)
docker compose up -d

# Load John Wick movie data
python scripts/ingestion/csv_ingestion_pipeline.py
```

**✅ Success Check**: `curl http://localhost:6333/collections` shows `johnwick_baseline`, `johnwick_semantic`  
**❌ If this fails**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#tier-2-infrastructure-services-issues)

### 3. **Start API Server** (30 seconds)  
```bash
# Start FastAPI server with 6 retrieval endpoints
python run.py

# Test in another terminal
curl -X POST "http://localhost:8000/invoke/semantic_retriever" \
     -H "Content-Type: application/json" \
     -d '{"question": "What makes John Wick movies popular?"}'
```

**✅ Success Check**: Should return JSON with `answer` and `context_document_count`  
**❌ If this fails**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#tier-4-mcp-interface-layer-issues)

### 4. **MCP Integration** (60 seconds)
```bash
# Start MCP server (converts FastAPI → MCP tools)
python src/mcp/server.py

# Verify MCP tools
python tests/integration/verify_mcp.py
```

**✅ Success Check**: Should show "All expected FastAPI endpoints converted to MCP tools"  
**❌ If this fails**: See [MCP troubleshooting guide](MCP_COMMAND_LINE_GUIDE.md#troubleshooting)

### MCP Resources Server (CQRS Query Pattern)
```bash
# Start additional MCP resources server for direct data access
python src/mcp/resources.py

# Test resources
python tests/integration/test_cqrs_resources.py
```

## ✅ Success Validation

After completing the 4 steps, verify everything is working:

```bash
# Quick system check (recommended)
python scripts/status.py

# Expected output - all tiers operational:
# ✅ Tier 1 (Environment): Ready  
# ✅ Tier 2 (Infrastructure): All Services Running
# ✅ Tier 3 (Application): FastAPI Running
# ✅ Tier 4 (MCP Interface): MCP Servers Available
# ✅ Tier 5 (Data): Collections Loaded
```

## 🎯 What You Now Have

- ✅ **6 Retrieval Strategies** ready for testing
- ✅ **Dual MCP Interfaces** (Tools + Resources) 
- ✅ **Phoenix Telemetry** at http://localhost:6006
- ✅ **John Wick Dataset** loaded for immediate testing

## 🚀 Next Steps

1. **Read [CLAUDE.md](../CLAUDE.md)** - comprehensive developer guide with commands and constraints
2. **Try different retrieval strategies** - see [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for all endpoints
3. **Explore Phoenix dashboard** - http://localhost:6006 for telemetry and performance analysis
4. **Run benchmarks** - `python scripts/evaluation/retrieval_method_comparison.py`

## 🔧 Optional Advanced Setup

### Claude Desktop Integration
```json
// Add to Claude Desktop MCP settings:
{
  "mcpServers": {
    "advanced-rag": {
      "command": "python",
      "args": ["/full/path/to/src/mcp/server.py"],
      "env": {
        "OPENAI_API_KEY": "your-key-here",
        "COHERE_API_KEY": "your-key-here"
      }
    }
  }
}
```

## 🚨 If Something Goes Wrong

**Quick Reset** (nuclear option):
```bash
docker compose down -v && docker compose up -d
python scripts/ingestion/csv_ingestion_pipeline.py
python run.py
```

**Specific Issues**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed problem-solving by component

---

**📚 Documentation Navigation**:
- **[CLAUDE.md](../CLAUDE.md)** - Main developer guide with all commands and constraints
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Daily command reference
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Problem solving guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Deep technical details 
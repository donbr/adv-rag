# Advanced RAG Troubleshooting Guide

📖 **See also**: [CLAUDE.md](../CLAUDE.md) for architectural constraints | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for commands

## 🚨 Most Common Issues (Start Here)

### 1. Port 8000 Already in Use ⭐ **#1 Most Common**
**Symptoms**: `[Errno 98] address already in use` when starting FastAPI

**Solution A - Use different port (easiest)**:
```bash
PORT=8001 python run.py
```

**Solution B - Kill existing process**:
```bash
# Find what's using port 8000
lsof -i :8000

# You'll see output like:
# COMMAND   PID   USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
# python  12345   user   4u  IPv4 0x1234567890abcdef      0t0  TCP *:8000 (LISTEN)

# Kill it using the PID from above (in this example: 12345)
kill -9 12345
```

**Solution C - One-liner to kill whatever is on port 8000**:
```bash
lsof -ti :8000 | xargs kill -9
```

### 2. Virtual Environment Not Active ⭐ **#2 Most Common**  
**Symptoms**: `ModuleNotFoundError`, wrong Python path
```bash
# Fix
source .venv/bin/activate
which python  # Should show .venv path

# If broken, recreate
rm -rf .venv && uv venv && source .venv/bin/activate && uv sync --dev
```

### 3. Missing API Keys ⭐ **#3 Most Common**
**Symptoms**: Authentication errors, empty responses
```bash
# Check keys
python src/core/settings.py

# Fix
cp .env.example .env
# Edit .env with your keys:
# OPENAI_API_KEY=your_key_here
# COHERE_API_KEY=your_key_here
```

### 4. Docker Services Down ⭐ **#4 Most Common**
**Symptoms**: Connection refused errors
```bash
# Quick fix
docker-compose restart

# Or full reset
docker-compose down -v && docker-compose up -d

# Check status
docker-compose ps  # All should be "Up"
```

## 🔍 Quick Diagnostic

### One-Command System Check
```bash
# Single command to check everything
python scripts/status.py

# Expected: All ✅ (Environment, Infrastructure, Application, MCP, Data)
```

### Manual Health Validation
```bash
# Core services
curl http://localhost:6333           # Qdrant: {"title":"qdrant - vector search engine"}
curl http://localhost:8000/health    # FastAPI: {"status":"healthy"}
curl http://localhost:6006           # Phoenix: HTML response
```

## 🛠️ Issues by Component

### Python & Environment Issues

| Problem | Quick Fix |
|---------|-----------|
| Python version wrong | `pyenv install 3.13.0 && pyenv local 3.13.0` |
| Model pinning wrong | Check `.env` - must use `gpt-4.1-mini`, `text-embedding-3-small` |
| Dependencies broken | `rm -rf .venv && uv venv && source .venv/bin/activate && uv sync --dev` |

### Docker Services Issues  

| Problem | Quick Fix |
|---------|-----------|
| Qdrant down | `docker-compose restart qdrant` |
| Redis down | `docker-compose restart redis` |
| Phoenix down | `docker-compose restart phoenix` |
| Port conflicts | `netstat -tulpn \| grep -E ":(6333\|6379\|6006\|8000)"` |

### Application Issues

| Problem | Quick Fix |
|---------|-----------|
| No collections found | `python scripts/ingestion/csv_ingestion_pipeline.py` |
| Test discovery fails | `export PYTHONPATH=$PWD:$PYTHONPATH && pytest tests/ -v` |
| Package conflicts | `rm -rf .venv && uv venv && source .venv/bin/activate && uv sync --dev` |

### MCP Server Issues

| Problem | Quick Fix |
|---------|-----------|
| MCP tools fail | `python tests/integration/verify_mcp.py` then restart servers |
| Resources not found | `curl http://localhost:6333/collections` to verify data exists |
| Server won't start | `pkill -f "src/mcp" && python src/mcp/server.py` |

### Data & Validation Issues

| Problem | Quick Fix |
|---------|-----------|
| Schema validation fails | `python scripts/mcp/export_mcp_schema.py && python scripts/mcp/validate_mcp_schema.py` |
| Empty search results | `curl "http://localhost:6333/collections/johnwick_baseline/points?limit=1"` |
| Ingestion fails | `ls -la data/raw/` then re-run `python scripts/ingestion/csv_ingestion_pipeline.py` |

## 🔧 Performance Issues

### Slow Performance
```bash
# Check Redis cache
redis-cli info memory

# Restart cache
docker-compose restart redis

# Performance benchmark
python scripts/evaluation/retrieval_method_comparison.py
```

### High Memory Usage
```bash
# Check container memory
docker stats

# Restart services
docker-compose restart && python run.py
```

## 🧪 Testing Issues

| Problem | Solution |
|---------|----------|
| Tests not found | `export PYTHONPATH=$PWD:$PYTHONPATH && pytest tests/ -v` |
| Import errors | Check virtual env: `which python` should show `.venv` |
| API key errors | `python src/core/settings.py` to verify keys loaded |
| MCP tests fail | `python tests/integration/verify_mcp.py` for details |

## 🌐 External MCP Issues  

| Problem | Solution |
|---------|----------|
| Claude permission denied | `claude -p --allowedTools "qdrant-store" "your command"` |
| MCP server not found | `claude` then `/mcp` to list available servers |
| Memory not persisting | `export MEMORY_FILE_PATH="/path/to/memory.json"` |

## 🆘 Nuclear Recovery Options

### Complete System Reset
```bash
# When everything is broken - this will delete ALL data and start fresh
# WARNING: This deletes your vector database data!

# 1. Stop and remove all Docker containers and volumes
docker-compose down -v

# 2. Clean up Docker completely (optional, but thorough)
docker system prune -a -f --volumes

# 3. Recreate Python environment
rm -rf .venv
uv venv
source .venv/bin/activate
uv sync --dev

# 4. Start fresh
docker-compose up -d
sleep 30  # Wait for services to start
python scripts/ingestion/csv_ingestion_pipeline.py  # Reload sample data
python run.py  # Start API server
```

### Quick Service Restart
```bash
# Restart just what you need
docker-compose restart && python run.py
```

### Diagnostic Data Collection
```bash
# For support/debugging
python scripts/status.py --json > system_status.json
docker-compose ps > services_status.txt
python src/core/settings.py > env_check.txt 2>&1
```

## 📚 Additional Resources

- **[CLAUDE.md](../CLAUDE.md)** - Architectural constraints and development patterns
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Daily commands and quick fixes
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Deep technical details
- **Phoenix Dashboard** - http://localhost:6006 (telemetry and monitoring)
- **RedisInsight** - http://localhost:5540 (cache monitoring)

---

⚠️ **Remember**: Always check you're in the virtual environment (`which python` shows `.venv`) before troubleshooting!
# Advanced RAG System Troubleshooting Guide

## Quick Diagnostic Commands

### Comprehensive System Status Check
```bash
# Check all tiers at once (NEW - Recommended)
python scripts/status.py

# Get detailed JSON output
python scripts/status.py --json

# Manage system state
python scripts/manage.py status              # Check status
python scripts/manage.py start               # Start all services
python scripts/manage.py stop --tier 4       # Stop application servers
python scripts/manage.py restart             # Restart everything
python scripts/manage.py clean               # Clean up orphaned processes
```

### Manual Health Checks
```bash
# Tier-based validation (run in order)
which python  # Should show .venv path
python --version  # Should show Python >= 3.13
docker-compose ps  # All services should be "Up"

# Service health validation
curl http://localhost:6333/health    # Qdrant: {"status":"ok"}
curl http://localhost:6379           # Redis: +PONG
curl http://localhost:6006           # Phoenix: HTML response
curl http://localhost:8000/health    # FastAPI: {"status":"healthy"}

# API key validation
python -c "from src.core.settings import get_settings; s=get_settings(); print(f'OpenAI: {bool(s.openai_api_key)}, Cohere: {bool(s.cohere_api_key)}')"
```

## Common Issues by Tier

Use `python scripts/status.py` to diagnose issues across all tiers.

### Tier 1: Environment & Dependencies Issues

#### ❌ Virtual Environment Not Activated
**Symptoms**: `ModuleNotFoundError`, wrong Python path
```bash
# Problem
which python  # Shows system Python, not .venv

# Solution
source .venv/bin/activate
which python  # Should now show .venv/bin/python
```

#### ❌ Python Version Incompatibility  
**Symptoms**: Package installation failures, syntax errors
```bash
# Problem
python --version  # Shows Python < 3.13

# Solution
# Install Python 3.13+ using pyenv, conda, or system package manager
pyenv install 3.13.0
pyenv local 3.13.0
uv venv --python 3.13
source .venv/bin/activate
```

#### ❌ Missing API Keys
**Symptoms**: Authentication errors, empty responses
```bash
# Problem
python src/core/settings.py  # Shows missing API keys

# Solution
cp .env.example .env
# Edit .env with your keys:
# OPENAI_API_KEY=your_openai_key_here
# COHERE_API_KEY=your_cohere_key_here
```

#### ❌ Model Pinning Violations
**Symptoms**: Status script shows "WRONG" for model pinning
```bash
# Problem
python scripts/status.py  # Shows incorrect models

# Solution
# Check your .env file for overrides:
grep -E "(OPENAI_MODEL|EMBEDDING_MODEL)" .env

# Required values (IMMUTABLE):
# OPENAI_MODEL_NAME=gpt-4.1-mini
# EMBEDDING_MODEL_NAME=text-embedding-3-small
```

### Tier 2: Infrastructure Services Issues

#### ❌ Docker Services Won't Start
**Symptoms**: Connection refused, port conflicts
```bash
# Problem diagnosis
docker-compose ps  # Shows unhealthy services
netstat -tulpn | grep -E ":(6333|6379|6006|8000)"  # Port conflicts

# Solution
docker-compose down
docker system prune -f  # Clean up
docker-compose up -d

# Check logs
docker-compose logs qdrant
docker-compose logs redis
docker-compose logs phoenix
```

### Tier 3: Core RAG Application Issues

#### ❌ Package Installation Failures
**Symptoms**: `uv sync` fails, dependency conflicts
```bash
# Problem diagnosis
uv pip check  # Shows dependency conflicts

# Solution
rm -rf .venv
uv venv
source .venv/bin/activate
uv sync --dev
```

#### ❌ Test Discovery Issues
**Symptoms**: `pytest` finds no tests, import errors
```bash
# Problem
pytest tests/ -v  # No tests found

# Solution - check PYTHONPATH and imports
export PYTHONPATH=$PWD:$PYTHONPATH
pytest tests/ -v

# Or use absolute imports
python -m pytest tests/ -v
```


#### ❌ Qdrant Collection Missing
**Symptoms**: Empty search results, collection errors
```bash
# Problem diagnosis
curl http://localhost:6333/collections  # No johnwick collections

# Solution - re-run data ingestion
python scripts/ingestion/csv_ingestion_pipeline.py

# Verify collections created
curl http://localhost:6333/collections | jq '.result.collections[].name'
```

#### ❌ Vector Database Connection Issues
**Symptoms**: Timeout errors, connection refused
```bash
# Problem diagnosis
curl http://localhost:6333  # Connection refused

# Solution
docker-compose restart qdrant
sleep 10  # Wait for startup
curl http://localhost:6333/health
```

### Tier 4: MCP Interface Layer Issues

#### ❌ FastAPI Server Not Starting (Port Already in Use)
**Symptoms**: Error: `[Errno 98] error while attempting to bind on address ('0.0.0.0', 8000): address already in use`

This is a common issue when FastAPI is already running from a previous session.

**Quick Solutions**:
```bash
# Option 1: Use the management script (RECOMMENDED)
python scripts/manage.py restart --tier 4

# Option 2: Check what's running and stop it
python scripts/status.py                    # See what's running
python scripts/manage.py stop --tier 4      # Stop application servers
python run.py                               # Start fresh

# Option 3: Use a different port
PORT=8001 python run.py

# Option 4: Manual cleanup
lsof -i :8000                              # Find process using port 8000
kill -9 <PID>                              # Kill the process
python run.py                              # Start fresh
```

**Prevention**: The updated `run.py` now checks for port conflicts before starting and provides helpful options.

#### ❌ MCP Tool Execution Failures
**Symptoms**: MCP tools fail, conversion errors
```bash
# Problem diagnosis
python tests/integration/verify_mcp.py  # Shows MCP errors

# Solution
# Ensure FastAPI server is running
curl http://localhost:8000/health

# Restart MCP server
pkill -f "src/mcp/server.py"
python src/mcp/server.py
```

#### ❌ MCP Resource Access Issues
**Symptoms**: Resource not found, empty responses
```bash
# Problem diagnosis
python src/mcp/resources.py  # Check for errors

# Solution
# Verify Qdrant collections exist
curl http://localhost:6333/collections

# Restart resources server
python src/mcp/resources.py
```

### Tier 5: Data & Validation Issues

#### ❌ Schema Validation Failures
**Symptoms**: Invalid MCP schemas, compliance errors
```bash
# Problem diagnosis
python scripts/mcp/validate_mcp_schema.py  # Shows validation errors

# Solution
# Regenerate schemas
python scripts/mcp/export_mcp_schema.py

# Update configuration if needed
vim scripts/mcp/mcp_config.toml

# Re-validate
python scripts/mcp/validate_mcp_schema.py
```

## External MCP Ecosystem Issues

### ❌ Claude Code CLI Permission Errors
**Symptoms**: "Permission denied for tool 'qdrant-store'"
```bash
# Problem
claude "Store pattern in qdrant-code-snippets"  # Permission denied

# Solution 1: Use explicit permissions
claude -p --allowedTools "qdrant-store" "Store this pattern..."

# Solution 2: Interactive mode with prompts
claude --verbose
> Store pattern in qdrant-code-snippets
# Answer "Yes" when prompted for qdrant-store permission
```

### ❌ External MCP Server Connection Issues
**Symptoms**: "MCP server not found" or connection errors
```bash
# Problem diagnosis
claude
> /mcp  # Lists available MCP servers and status

# Solution
# Verify external MCP servers are running
curl http://localhost:8002/health  # qdrant-code-snippets
curl http://localhost:8003/health  # qdrant-semantic-memory

# Check Claude Code MCP configuration
cat ~/.claude/config.json | jq '.mcpServers'
```

### ❌ Memory Server Storage Issues
**Symptoms**: Memory not persisting, file permission errors
```bash
# Problem diagnosis
ls -la data/memory.json  # File doesn't exist or wrong permissions

# Solution
# Create data directory and set permissions
mkdir -p data
chmod 755 data

# Configure memory server path in Claude Code
export MEMORY_FILE_PATH="/home/donbr/ghcp/adv-rag/data/memory.json"
```

## Performance Issues

### ❌ Slow Retrieval Performance
**Symptoms**: Long response times, timeouts
```bash
# Problem diagnosis
# Check Redis cache
redis-cli info memory

# Check Qdrant performance
curl "http://localhost:6333/collections/johnwick_baseline/points/count"

# Solution
# Restart Redis cache
docker-compose restart redis

# Optimize Qdrant collections
python scripts/evaluation/retrieval_method_comparison.py
```

### ❌ Memory Usage Issues
**Symptoms**: High memory consumption, OOM errors
```bash
# Problem diagnosis
docker stats  # Check container memory usage
ps aux | grep python  # Check Python process memory

# Solution
# Restart services
docker-compose restart
source .venv/bin/activate
python run.py
```

## Testing and Development Issues

### ❌ Test Failures
**Symptoms**: Tests fail with import/connection errors
```bash
# Problem diagnosis
pytest tests/ -v --tb=short  # Show detailed error traces

# Solution for specific test categories
pytest tests/ -m unit -v          # Test isolated components
pytest tests/ -m integration -v   # Test cross-system validation
pytest tests/ -m requires_llm -v  # Test LLM-dependent features (needs API keys)
```

### ❌ Code Quality Issues
**Symptoms**: Linting failures, formatting errors
```bash
# Problem diagnosis
ruff check src/ tests/  # Show linting issues

# Solution
# Fix automatically
ruff check src/ tests/ --fix
black src/ tests/ --line-length 88

# Manual fixes for remaining issues
ruff check src/ tests/  # Review remaining issues
```

## Data Pipeline Issues

### ❌ Ingestion Pipeline Failures
**Symptoms**: No data in vector collections, ingestion errors
```bash
# Problem diagnosis
python scripts/ingestion/csv_ingestion_pipeline.py  # Check for errors

# Solution
# Verify data files exist
ls -la data/raw/  # Should contain CSV files

# Check Qdrant is accessible
curl http://localhost:6333/health

# Re-run ingestion with verbose logging
python scripts/ingestion/csv_ingestion_pipeline.py --verbose
```

### ❌ Empty Search Results
**Symptoms**: No results returned from retrieval
```bash
# Problem diagnosis
curl "http://localhost:6333/collections/johnwick_baseline/points?limit=1"

# Solution
# Verify data was ingested
curl http://localhost:6333/collections | jq '.result.collections[] | select(.name | contains("johnwick"))'

# Re-run ingestion if collections are empty
python scripts/ingestion/csv_ingestion_pipeline.py
```

## Environment-Specific Issues

### ❌ Windows-Specific Issues
**Symptoms**: Path errors, script execution failures
```bash
# Solution
# Use Windows-compatible commands
.venv\Scripts\activate  # Instead of source .venv/bin/activate

# Use proper path separators
python -c "import sys; print(sys.executable)"  # Verify Python path
```

### ❌ macOS-Specific Issues
**Symptoms**: Permission errors, homebrew conflicts
```bash
# Solution
# Use homebrew Python if needed
brew install python@3.13
which python3.13

# Fix permissions
sudo chown -R $(whoami) .venv
```

### ❌ Linux-Specific Issues
**Symptoms**: Package installation failures, library conflicts
```bash
# Solution
# Install system dependencies
sudo apt-get update
sudo apt-get install python3.13-dev python3.13-venv

# Fix library paths
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
```

## Recovery Commands

### Complete System Reset
```bash
# Nuclear option - full reset
docker-compose down
docker system prune -a -f --volumes
rm -rf .venv
uv venv
source .venv/bin/activate
uv sync --dev
docker-compose up -d
sleep 30  # Wait for services
python scripts/ingestion/csv_ingestion_pipeline.py
python run.py
```

### Selective Service Restart
```bash
# Restart just the services you need
docker-compose restart qdrant redis phoenix
python run.py
python src/mcp/server.py &
python src/mcp/resources.py &
```

## Getting Help

### Diagnostic Information Collection
```bash
# Collect system information for support
echo "=== System Info ===" > debug.log
uname -a >> debug.log
python --version >> debug.log
docker --version >> debug.log
echo "=== Service Status ===" >> debug.log
docker-compose ps >> debug.log
echo "=== Environment ===" >> debug.log
python src/core/settings.py >> debug.log 2>&1
echo "=== MCP Status ===" >> debug.log
python tests/integration/verify_mcp.py >> debug.log 2>&1
```

### Useful Resources
- **CLAUDE.md**: Comprehensive development guide
- **docs/ARCHITECTURE.md**: System architecture and constraints
- **Phoenix Dashboard**: http://localhost:6006 for telemetry
- **RedisInsight**: http://localhost:5540 for cache monitoring
- **MCP Protocol Documentation**: https://spec.modelcontextprotocol.io/

Remember: Always check that you're in the correct virtual environment and that all services are running before troubleshooting specific issues.
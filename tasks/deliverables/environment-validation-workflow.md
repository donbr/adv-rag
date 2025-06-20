# Environment Validation Workflow

**Purpose**: Comprehensive validation protocol for Advanced RAG system environment setup and FastAPI endpoint verification.

## Overview

This workflow ensures all system components are properly configured and operational before MCP tool testing or production deployment. It validates the complete stack from Python environment through Docker services to API endpoints.

## Prerequisites

- **Python Environment**: Virtual environment activated (`.venv`)
- **Docker**: Docker and docker-compose installed and running
- **API Keys**: OPENAI_API_KEY and COHERE_API_KEY configured
- **Repository**: Working directory at project root (`/home/donbr/aim/adv-rag`)

## Validation Steps

### Step 1: Python Environment & Startup Verification

**Objective**: Verify core application startup and environment configuration

```bash
# Activate virtual environment
source .venv/bin/activate

# Test application startup (10-second timeout)
timeout 10s python run.py
```

**Expected Results**:
- ✅ 6 retrieval chains initialize successfully
- ✅ Phoenix tracing auto-configuration
- ✅ Server starts on http://0.0.0.0:8000
- ✅ Graceful shutdown capability

**Verification Commands**:
```bash
python -c "import sys; print(f'Python: {sys.version}')"
python -c "from src.core.settings import get_settings; print('✅ Settings module loaded')"
```

### Step 2: Docker Services Verification

**Objective**: Ensure all backend services are running and accessible

```bash
# Check Docker status
docker --version
docker-compose --version
docker-compose ps
```

**Required Services**:
1. **Qdrant** (Vector Database) - Port 6333
2. **Phoenix** (Observability) - Ports 6006, 4317  
3. **Redis** (Caching) - Port 6379
4. **RedisInsight** (Management UI) - Port 5540

**Service Health Checks**:
```bash
# Qdrant collections
curl -s http://localhost:6333/collections

# Phoenix health
curl -s http://localhost:6006/health

# Redis ping
redis-cli -h localhost -p 6379 ping

# RedisInsight availability  
curl -s -o /dev/null -w "%{http_code}" http://localhost:5540
```

**Expected Collections**: `code-snippets`, `johnwick_semantic`, `johnwick_baseline`

### Step 3: API Keys Validation

**Objective**: Verify API keys are present and functional

```bash
# Check key presence (with masking)
python -c "
from src.core.settings import get_settings
settings = get_settings()
openai_key = settings.openai_api_key
cohere_key = settings.cohere_api_key
print('✅ OPENAI_API_KEY: Present' if openai_key else '❌ OPENAI_API_KEY: Missing')
print('✅ COHERE_API_KEY: Present' if cohere_key else '❌ COHERE_API_KEY: Missing')
"
```

**API Validation Tests**:
```bash
# OpenAI API test
python -c "from src.integrations.llm_models import get_chat_openai; llm = get_chat_openai(); response = llm.invoke('Hello'); print('✅ OpenAI API Valid')"

# Cohere API test  
python -c "import cohere; from src.core.settings import get_settings; settings = get_settings(); client = cohere.Client(settings.cohere_api_key); response = client.chat(message='Hello', model='command-r'); print('✅ Cohere API Valid')"
```

### Step 4: FastAPI Endpoints Verification

**Objective**: Test all 6 retrieval endpoints with real queries

```bash
# Start FastAPI server
python run.py &

# Wait for startup
sleep 5

# Health check
curl -s http://127.0.0.1:8000/health

# Run comprehensive endpoint tests
chmod +x tests/integration/test_api_endpoints.sh
./tests/integration/test_api_endpoints.sh
```

**Tested Endpoints**:
1. `/invoke/naive_retriever` - Basic vector similarity
2. `/invoke/bm25_retriever` - Keyword search (BM25)
3. `/invoke/contextual_compression_retriever` - Compressed retrieval
4. `/invoke/multi_query_retriever` - Multi-query expansion
5. `/invoke/ensemble_retriever` - Hybrid search
6. `/invoke/semantic_retriever` - Semantic vector search

**Test Queries**:
- "Did people generally like John Wick?"
- "Do any reviews have a rating of 10? If so - can I have the URLs to those reviews?"
- "What happened in John Wick?"

**Expected Response Format**:
```json
{
  "answer": "Contextual response based on retrieved documents...",
  "context_document_count": 10
}
```

## Validation Results Tracking

### Log Files
- **API Tests**: `logs/api_test_results_YYYYMMDD_HHMMSS.log`
- **Server Logs**: `app.log` and `/logs` directory
- **Detailed Notes**: `tasks/temp-notes/0.X-[component]-verification.md`

### Success Criteria
- ✅ **Environment**: Python 3.13.2, virtual environment active
- ✅ **Docker**: All 4 services up and responding (7+ hours uptime)
- ✅ **API Keys**: Both OpenAI and Cohere keys valid and functional
- ✅ **Endpoints**: 18/18 tests passing (100% success rate)
- ✅ **Integration**: Phoenix tracing active, Redis caching working

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Verify environment activation
which python
python -c "import sys; print(sys.path)"
```

**Docker Service Issues**:
```bash
# Restart services
docker-compose down
docker-compose up -d
```

**API Key Problems**:
```bash
# Check environment variables
env | grep -E "(OPENAI|COHERE)_API_KEY"
```

**Endpoint Failures**:
```bash
# Check server status
curl -s http://127.0.0.1:8000/health
# Review server logs
tail -f app.log
```

### Performance Notes
- **Response Times**: All endpoints respond within reasonable timeframes
- **Context Retrieval**: Consistent 10 documents per query
- **Caching**: Redis cache active with `mcp_cache:` prefix
- **Tracing**: Phoenix integration with project `advanced-rag-system-YYYYMMDD_HHMMSS`

## Security Considerations

- ✅ **API Key Masking**: All keys properly masked in logs and output
- ✅ **Environment Isolation**: Virtual environment prevents conflicts
- ✅ **Service Isolation**: Docker containers provide service boundaries
- ✅ **Validation Only**: No modification of production data during tests

## Integration Points

This validation workflow serves as:
- **Pre-MCP Testing**: Ensures backend stability before MCP tool conversion
- **CI/CD Health Check**: Automated environment verification
- **Developer Onboarding**: Step-by-step setup verification
- **Production Readiness**: Comprehensive system validation

## Next Steps

After successful validation:
1. **MCP Tool Testing**: Proceed with FastAPI → MCP conversion testing
2. **External MCP Integration**: Test Phoenix, Qdrant, Redis MCP servers
3. **Performance Benchmarking**: Load testing and optimization
4. **Documentation Updates**: Keep validation procedures current

---

**Last Updated**: June 17, 2025  
**Validation Version**: 1.0  
**Environment**: WSL2 Ubuntu, Python 3.13.2, Docker 28.2.2 
#!/usr/bin/env python
"""
🚀 FastAPI RAG Server - Production Bootstrap Walkthrough

This script starts the Advanced RAG Retriever API server, exposing 6 sophisticated retrieval
strategies as HTTP endpoints. This is the core API that gets wrapped by the MCP server.

## 📋 STEP 1: Prerequisites (Complete Before Running)

### Data Foundation Required:
```bash
# MUST complete data ingestion first
python scripts/ingestion/csv_ingestion_pipeline.py

# Verify vector stores exist in Qdrant
curl http://localhost:6333/collections
# Should show: johnwick_baseline, johnwick_semantic
```

### Environment Validation:
```bash
# Ensure services are running
docker-compose ps
# Should show: qdrant, phoenix, redis (all Up)

# Verify environment variables
echo $OPENAI_API_KEY    # Required for LLM and embeddings
echo $COHERE_API_KEY    # Required for reranking
```

## 🎯 STEP 2: FastAPI Server Architecture

### 6 Retrieval Endpoints Exposed:
1. **`/invoke/naive_retriever`** - Basic vector similarity search
2. **`/invoke/bm25_retriever`** - Keyword-based BM25 search  
3. **`/invoke/contextual_compression_retriever`** - Cohere reranking compression
4. **`/invoke/multi_query_retriever`** - Multi-query expansion strategy
5. **`/invoke/ensemble_retriever`** - Hybrid ensemble combining multiple methods
6. **`/invoke/semantic_retriever`** - Semantic chunking + vector search

### Request Schema (All Endpoints):
```json
{
  "question": "What makes John Wick movies so popular?"
}
```

### Response Schema:
```json
{
  "answer": "Generated response based on retrieved context",
  "metadata": {
    "retrieval_method": "semantic_retriever",
    "documents_retrieved": 5,
    "processing_time_ms": 234
  }
}
```

## 🔗 STEP 3: Server Startup Process

### What Happens During Startup:
1. **Logging Configuration** - Structured logging with proper levels
2. **Environment Loading** - API keys and database connections
3. **Model Initialization** - GPT-4.1-mini + text-embedding-3-small (pinned versions)
4. **Vector Store Connections** - Qdrant baseline + semantic collections
5. **Retriever Factory Setup** - All 6 retrieval strategies initialized
6. **FastAPI App Launch** - HTTP server on port 8000

### Health Check Validation:
```bash
# Test server startup
python run.py

# In another terminal - verify endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs    # Swagger UI

# Test a retrieval endpoint
curl -X POST "http://localhost:8000/invoke/semantic_retriever" \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the best John Wick action scenes?"}'
```

## 📊 STEP 4: Telemetry & Monitoring Integration

### Phoenix Tracing (Auto-Enabled):
- **Request/Response tracking** for all 6 endpoints
- **LLM call instrumentation** (token usage, latency)
- **Vector search telemetry** (retrieval time, relevance scores)
- **Real-time dashboards** at http://localhost:6006

### Key Metrics Monitored:
- **Endpoint latency** (P50, P95, P99)
- **Retrieval quality** (document relevance)
- **LLM token consumption** (cost tracking)
- **Error rates** by retrieval method
- **Concurrent request handling**

## 🎯 STEP 5: API Usage Patterns

### Development Testing:
```bash
# Test all retrieval methods
bash tests/integration/test_api_endpoints.sh

# Individual endpoint testing
curl -X POST "http://localhost:8000/invoke/naive_retriever" \
     -H "Content-Type: application/json" \
     -d '{"question": "Compare John Wick fight choreography"}'
```

### Integration with MCP:
```bash
# This FastAPI server becomes the backend for MCP tools
python src/mcp/server.py

# FastMCP.from_fastapi() converts these endpoints to MCP tools automatically
```

## 🔄 STEP 6: Performance & Production Considerations

### Development vs Production:
- **Development**: Single-worker, debug logging, auto-reload
- **Production**: Multi-worker, structured logging, health checks

### Scaling Options:
```bash
# Multi-worker production deployment
uvicorn src.api.app:app --workers 4 --host 0.0.0.0 --port 8000

# Docker deployment
docker-compose -f docker-compose.prod.yml up
```

### Monitoring Production Health:
- **Endpoint**: `GET /health` (dependency checks)
- **Metrics**: `GET /metrics` (Prometheus format)
- **Documentation**: `GET /docs` (Swagger UI)

## 🚨 Troubleshooting

### Common Startup Issues:
- **Qdrant Connection Failed**: Check `docker-compose ps`, restart if needed
- **OpenAI API Error**: Verify OPENAI_API_KEY is valid and has credits
- **Vector Store Not Found**: Run data ingestion pipeline first
- **Port 8000 Occupied**: Kill existing process or change port

### Recovery Steps:
```bash
# Reset everything
docker-compose restart
python scripts/ingestion/csv_ingestion_pipeline.py
python run.py
```

## 🎯 Expected Outcomes

After successful startup:
- ✅ FastAPI server running on http://localhost:8000
- ✅ All 6 retrieval endpoints responding correctly
- ✅ Swagger documentation accessible at /docs
- ✅ Phoenix telemetry tracking all operations
- ✅ Ready for MCP server integration

## 🔗 Next Steps

1. **Test API endpoints** using curl or test scripts
2. **Start MCP server** with `python src/mcp/server.py`
3. **Run evaluations** to compare retrieval strategies
4. **Monitor telemetry** in Phoenix UI for performance insights

This FastAPI server is the foundation that enables both direct HTTP access and MCP tool integration
for Claude Desktop and other MCP clients.
"""

import uvicorn
import logging
from src.api.app import app
from src.core.logging_config import setup_logging

# Ensure logging is set up
if not logging.getLogger().hasHandlers():
    setup_logging()

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Advanced RAG Retriever API server...")
    logger.info("API documentation will be available at http://127.0.0.1:8000/docs")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested via keyboard interrupt")
    except Exception as e:
        logger.error(f"Error starting server: {e}", exc_info=True)
    finally:
        logger.info("Server has been shut down") 
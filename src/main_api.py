# main_api.py
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import uvicorn
import logging
import json
import hashlib
from typing import Optional
from contextlib import asynccontextmanager

from src import settings
from src.redis_client import redis_client, get_redis
from redis import asyncio as aioredis

from src.chain_factory import (
    NAIVE_RETRIEVAL_CHAIN,
    BM25_RETRIEVAL_CHAIN,
    CONTEXTUAL_COMPRESSION_CHAIN,
    MULTI_QUERY_CHAIN,
    ENSEMBLE_CHAIN,
    SEMANTIC_CHAIN
)

from phoenix.otel import register

# Unified Phoenix configuration - coordinate with fastapi_wrapper.py
phoenix_endpoint: str = "http://localhost:6006"
# Use coordinated project name for trace correlation across FastAPI and MCP components
project_name: str = f"advanced-rag-system-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = phoenix_endpoint

# Enhanced Phoenix integration with tracer provider for FastAPI endpoints
tracer_provider = register(
    project_name=project_name,
    auto_instrument=True
)

# Get tracer for FastAPI endpoint instrumentation
tracer = tracer_provider.get_tracer("advanced-rag-fastapi-endpoints")

# Get a logger for this module
logger = logging.getLogger(__name__)

def generate_cache_key(endpoint: str, request_data: dict) -> str:
    """Generate cache key from endpoint and request data"""
    cache_data = f"{endpoint}:{json.dumps(request_data, sort_keys=True)}"
    return f"mcp_cache:{hashlib.md5(cache_data.encode()).hexdigest()}"

async def get_cached_response(cache_key: str, redis: aioredis.Redis) -> Optional[dict]:
    """Get cached response if available"""
    try:
        cached = await redis.get(cache_key)
        if cached:
            logger.info(f"✅ Cache hit for key: {cache_key[:20]}...")
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"⚠️ Cache read error: {e}")
    return None

async def cache_response(cache_key: str, response_data: dict, redis: aioredis.Redis, ttl: int = 300):
    """Cache response with TTL (default 5 minutes)"""
    try:
        await redis.setex(
            cache_key, 
            ttl, 
            json.dumps(response_data, default=str)
        )
        logger.info(f"💾 Cached response for key: {cache_key[:20]}...")
    except Exception as e:
        logger.warning(f"⚠️ Cache write error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan management with Redis and Phoenix tracing"""
    # Startup with Phoenix tracing
    with tracer.start_as_current_span("FastAPI.application.startup") as span:
        logger.info("🚀 Starting FastAPI application with Phoenix tracing...")
        
        # Set span attributes for application startup
        span.set_attribute("fastapi.app.title", "Advanced RAG Retriever API")
        span.set_attribute("fastapi.app.version", "1.0.0")
        span.set_attribute("fastapi.app.phoenix_project", project_name)
        span.add_event("application.startup.start")
        
        await redis_client.connect()
        span.add_event("redis.connection.established")
        
        # Initialize chains with tracing
        available_chains = {
            "Naive Retriever Chain": NAIVE_RETRIEVAL_CHAIN,
            "BM25 Retriever Chain": BM25_RETRIEVAL_CHAIN,
            "Contextual Compression Chain": CONTEXTUAL_COMPRESSION_CHAIN,
            "Multi-Query Chain": MULTI_QUERY_CHAIN,
            "Ensemble Chain": ENSEMBLE_CHAIN,
            "Semantic Chain": SEMANTIC_CHAIN
        }

        logger.info("\n--- Chain Initialization Status ---")
        all_chains_ready = True
        ready_chains = 0
        
        for name, chain_instance in available_chains.items():
            if chain_instance is not None:
                logger.info(f"[+] {name}: Ready")
                ready_chains += 1
            else:
                logger.warning(f"[-] {name}: Not available. Check logs for retriever/vectorstore initialization issues.")
                all_chains_ready = False
        
        # Set span attributes for chain initialization
        span.set_attribute("fastapi.chains.total", len(available_chains))
        span.set_attribute("fastapi.chains.ready", ready_chains)
        span.set_attribute("fastapi.chains.all_ready", all_chains_ready)
        
        if all_chains_ready:
            logger.info("✅ All chains initialized successfully.")
            span.add_event("chains.initialization.complete", {"status": "all_ready"})
        else:
            logger.warning("⚠️ One or more chains failed to initialize. API functionality may be limited.")
            span.add_event("chains.initialization.partial", {"ready_count": ready_chains})
            
        logger.info("------------------------------------------------------")
        span.add_event("application.startup.complete")
    
    yield
    
    # Shutdown with Phoenix tracing
    with tracer.start_as_current_span("FastAPI.application.shutdown") as span:
        logger.info("🛑 Shutting down FastAPI application...")
        span.add_event("application.shutdown.start")
        await redis_client.disconnect()
        span.add_event("redis.connection.closed")
        span.add_event("application.shutdown.complete")

app = FastAPI(
    title="Advanced RAG Retriever API",
    description="API for invoking various LangChain retrieval chains for John Wick movie reviews with Redis caching and Phoenix tracing.",
    version="1.0.0",
    lifespan=lifespan
)

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    context_document_count: int

async def invoke_chain_logic(chain, question: str, chain_name: str, redis: aioredis.Redis = Depends(get_redis)):
    """Enhanced chain invocation with Redis caching and Phoenix tracing"""
    # Enhanced chain invocation with explicit Phoenix tracing
    with tracer.start_as_current_span(f"FastAPI.chain.{chain_name.lower().replace(' ', '_')}") as span:
        if chain is None:
            span.set_attribute("fastapi.chain.status", "unavailable")
            span.add_event("chain.error", {
                "error_type": "ChainUnavailable",
                "chain_name": chain_name
            })
            
            logger.error(f"Chain '{chain_name}' is not available (None). Cannot process request for question: '{question}'")
            raise HTTPException(status_code=503, detail=f"The '{chain_name}' is currently unavailable. Please check server logs.")
        
        # Set span attributes for chain invocation
        span.set_attribute("fastapi.chain.name", chain_name)
        span.set_attribute("fastapi.chain.question_length", len(question))
        span.set_attribute("fastapi.chain.project", project_name)
        
        # Generate cache key
        cache_key = generate_cache_key(chain_name, {"question": question})
        span.set_attribute("fastapi.cache.key_hash", cache_key[-8:])  # Last 8 chars for identification
        
        # Check cache first
        span.add_event("cache.lookup.start")
        cached_response = await get_cached_response(cache_key, redis)
        if cached_response:
            span.set_attribute("fastapi.cache.hit", True)
            span.add_event("cache.lookup.hit", {
                "response_length": len(str(cached_response.get("answer", ""))),
                "context_docs": cached_response.get("context_document_count", 0)
            })
            
            logger.info(f"🎯 Returning cached response for '{chain_name}' question: '{question[:50]}...'")
            return AnswerResponse(**cached_response)
        
        span.set_attribute("fastapi.cache.hit", False)
        span.add_event("cache.lookup.miss")
        
        try:
            logger.info(f"🔄 Invoking '{chain_name}' with question: '{question[:50]}...'")
            
            # Add span event for chain invocation start
            span.add_event("chain.invocation.start", {
                "question_preview": question[:50] + "..." if len(question) > 50 else question
            })
            
            result = await chain.ainvoke({"question": question})
            answer = result.get("response", {}).content if hasattr(result.get("response"), "content") else "No answer content found."
            context_docs_count = len(result.get("context", []))
            
            # Set span attributes for successful invocation
            span.set_attribute("fastapi.chain.status", "success")
            span.set_attribute("fastapi.chain.answer_length", len(answer))
            span.set_attribute("fastapi.chain.context_docs", context_docs_count)
            
            span.add_event("chain.invocation.complete", {
                "answer_length": len(answer),
                "context_docs": context_docs_count
            })
            
            logger.info(f"✅ '{chain_name}' invocation successful. Answer: '{answer[:50]}...', Context docs: {context_docs_count}")
            
            # Create response
            response_data = {"answer": answer, "context_document_count": context_docs_count}
            
            # Cache the response (5 minutes TTL for RAG results)
            span.add_event("cache.store.start")
            await cache_response(cache_key, response_data, redis, ttl=300)
            span.add_event("cache.store.complete", {"ttl": 300})
            
            return AnswerResponse(**response_data)
            
        except Exception as e:
            span.set_attribute("fastapi.chain.status", "error")
            span.set_attribute("fastapi.chain.error", str(e))
            span.add_event("chain.invocation.error", {
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            
            logger.error(f"❌ Error invoking '{chain_name}' for question '{question[:50]}...': {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"An error occurred while processing your request with {chain_name}.")

@app.post("/invoke/naive_retriever", response_model=AnswerResponse, operation_id="naive_retriever")
async def invoke_naive_endpoint(request: QuestionRequest, redis: aioredis.Redis = Depends(get_redis)):
    """Invokes the Naive Retriever chain for basic similarity search."""
    return await invoke_chain_logic(NAIVE_RETRIEVAL_CHAIN, request.question, "Naive Retriever Chain", redis)

@app.post("/invoke/bm25_retriever", response_model=AnswerResponse, operation_id="bm25_retriever")
async def invoke_bm25_endpoint(request: QuestionRequest, redis: aioredis.Redis = Depends(get_redis)):
    """Invokes the BM25 Retriever chain for keyword-based search."""
    return await invoke_chain_logic(BM25_RETRIEVAL_CHAIN, request.question, "BM25 Retriever Chain", redis)

@app.post("/invoke/contextual_compression_retriever", response_model=AnswerResponse, operation_id="contextual_compression_retriever")
async def invoke_contextual_compression_endpoint(request: QuestionRequest, redis: aioredis.Redis = Depends(get_redis)):
    """Invokes the Contextual Compression Retriever chain for compressed context."""
    return await invoke_chain_logic(CONTEXTUAL_COMPRESSION_CHAIN, request.question, "Contextual Compression Chain", redis)

@app.post("/invoke/multi_query_retriever", response_model=AnswerResponse, operation_id="multi_query_retriever")
async def invoke_multi_query_endpoint(request: QuestionRequest, redis: aioredis.Redis = Depends(get_redis)):
    """Invokes the Multi-Query Retriever chain for enhanced query expansion."""
    return await invoke_chain_logic(MULTI_QUERY_CHAIN, request.question, "Multi-Query Chain", redis)

@app.post("/invoke/ensemble_retriever", response_model=AnswerResponse, operation_id="ensemble_retriever")
async def invoke_ensemble_endpoint(request: QuestionRequest, redis: aioredis.Redis = Depends(get_redis)):
    """Invokes the Ensemble Retriever chain combining multiple retrieval strategies."""
    return await invoke_chain_logic(ENSEMBLE_CHAIN, request.question, "Ensemble Chain", redis)

@app.post("/invoke/semantic_retriever", response_model=AnswerResponse, operation_id="semantic_retriever")
async def invoke_semantic_endpoint(request: QuestionRequest, redis: aioredis.Redis = Depends(get_redis)):
    """Invokes the Semantic Retriever chain for advanced semantic search."""
    return await invoke_chain_logic(SEMANTIC_CHAIN, request.question, "Semantic Chain", redis)

@app.get("/health")
async def health_check():
    """Health check endpoint with Phoenix tracing integration"""
    with tracer.start_as_current_span("FastAPI.health_check") as span:
        span.set_attribute("fastapi.health.type", "basic")
        span.set_attribute("fastapi.health.project", project_name)
        span.add_event("health_check.complete", {"status": "healthy"})
        
        return {
            "status": "healthy", 
            "timestamp": "2024-12-13",
            "phoenix_integration": {
                "project": project_name,
                "tracer": "advanced-rag-fastapi-endpoints",
                "trace_id": span.get_span_context().trace_id
            }
        }

@app.get("/cache/stats")
async def cache_stats(redis: aioredis.Redis = Depends(get_redis)):
    """Get cache statistics with Phoenix tracing"""
    with tracer.start_as_current_span("FastAPI.cache_stats") as span:
        try:
            span.add_event("redis.info.start")
            info = await redis.info()
            keys_count = await redis.dbsize()
            
            span.set_attribute("fastapi.cache.keys_count", keys_count)
            span.set_attribute("fastapi.cache.connected_clients", info.get("connected_clients", 0))
            span.add_event("redis.info.complete", {
                "keys_count": keys_count,
                "redis_version": info.get("redis_version", "unknown")
            })
            
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_keys": keys_count,
                "cache_prefix": "mcp_cache:",
                "phoenix_integration": {
                    "project": project_name,
                    "trace_id": span.get_span_context().trace_id
                }
            }
        except Exception as e:
            span.set_attribute("fastapi.cache.error", str(e))
            span.add_event("redis.error", {
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            raise HTTPException(status_code=503, detail=f"Cache unavailable: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting FastAPI server using uvicorn.run() from __main__...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
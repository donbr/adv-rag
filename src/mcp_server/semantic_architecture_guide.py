#!/usr/bin/env python3
"""
Semantic Architecture Guide for MCP RAG Systems

This module demonstrates the correct semantic patterns for implementing
RAG systems in MCP, distinguishing between Tools (actions) and Resources (data access).

Based on the breakthrough insight that:
- Tools = "Doers" (side effects, mutations, complex logic)  
- Resources = "Getter-uppers" (read-only, parameterized, LLM context loading)
"""

from typing import List, Dict, Any
from fastmcp import FastMCP
from mcp import tool, resource
from pydantic import BaseModel

# ============================================================================
# SEMANTIC PATTERN 1: TOOLS FOR ACTIONS (Side Effects)
# ============================================================================

class IndexRequest(BaseModel):
    documents: List[Dict[str, Any]]
    collection_name: str = "default"
    
class IndexResult(BaseModel):
    ingested: int
    status: str
    collection: str
    
@tool(name="index_documents", description="Ingest documents into vector store")
def index_documents(request: IndexRequest) -> IndexResult:
    """
    ✅ CORRECT: This is a TOOL because it has side effects
    - Modifies vector store state
    - Creates/updates indexes
    - Has persistent effects
    """
    # Simulate document ingestion
    vector_store.upsert(request.documents, request.collection_name)
    
    return IndexResult(
        ingested=len(request.documents),
        status="success", 
        collection=request.collection_name
    )

@tool(name="update_retrieval_config", description="Update retrieval configuration")
def update_retrieval_config(config: Dict[str, Any]) -> Dict[str, str]:
    """
    ✅ CORRECT: This is a TOOL because it modifies system state
    - Changes configuration
    - Affects future behavior
    - Has side effects
    """
    # Update system configuration
    system_config.update(config)
    
    return {"status": "updated", "config_version": "1.2.3"}

# ============================================================================
# SEMANTIC PATTERN 2: RESOURCES FOR DATA ACCESS (Read-Only)
# ============================================================================

@resource(
    name="bm25_retriever",
    uri_template="retriever://bm25_retriever/{query}",
    description="BM25 keyword-based document retrieval"
)
def bm25_retriever(query: str) -> List[Dict[str, Any]]:
    """
    ✅ CORRECT: This is a RESOURCE because it's read-only data access
    - No side effects
    - Parameterized by URI
    - Optimizable for caching
    - Perfect for LLM context loading
    """
    results = bm25_index.search(query, top_k=5)
    
    return [
        {
            "content": doc.content,
            "metadata": doc.metadata,
            "score": doc.score,
            "source": "bm25"
        }
        for doc in results
    ]

@resource(
    name="semantic_retriever", 
    uri_template="retriever://semantic_retriever/{query}",
    description="Vector similarity-based document retrieval"
)
def semantic_retriever(query: str) -> List[Dict[str, Any]]:
    """
    ✅ CORRECT: This is a RESOURCE because it's pure data access
    - Read-only operation
    - Cacheable by URI
    - No state changes
    - Optimized for edge deployment
    """
    results = vector_store.similarity_search(query, k=5)
    
    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": doc.score,
            "source": "semantic"
        }
        for doc in results
    ]

@resource(
    name="hybrid_retriever",
    uri_template="retriever://hybrid_retriever/{query}?weight_vector={weight_vector}&weight_bm25={weight_bm25}",
    description="Hybrid BM25 + vector retrieval with configurable weights"
)
def hybrid_retriever(
    query: str, 
    weight_vector: float = 0.7, 
    weight_bm25: float = 0.3
) -> List[Dict[str, Any]]:
    """
    ✅ CORRECT: This is a RESOURCE with parameterized URI
    - Read-only with configurable parameters
    - URI-based parameter passing
    - Cacheable with parameter-specific keys
    - No side effects
    """
    # Combine results from both retrievers
    vector_results = vector_store.similarity_search(query, k=10)
    bm25_results = bm25_index.search(query, top_k=10)
    
    # Weighted fusion (simplified)
    combined_results = fuse_results(
        vector_results, bm25_results, 
        weight_vector, weight_bm25
    )
    
    return [
        {
            "content": doc.content,
            "metadata": doc.metadata,
            "score": doc.final_score,
            "source": "hybrid",
            "fusion_weights": {
                "vector": weight_vector,
                "bm25": weight_bm25
            }
        }
        for doc in combined_results[:5]
    ]

# ============================================================================
# PERFORMANCE OPTIMIZATION PATTERNS
# ============================================================================

class CacheableResource:
    """
    Pattern for implementing cacheable resources with TTL and invalidation
    """
    
    @staticmethod
    @resource(
        name="cached_semantic_retriever",
        uri_template="retriever://cached_semantic_retriever/{query}",
        description="Cached semantic retrieval with TTL"
    )
    def cached_semantic_retriever(query: str) -> List[Dict[str, Any]]:
        """
        ✅ ADVANCED: Resource with built-in caching strategy
        - URI-based cache keys
        - TTL-based invalidation
        - Edge-deployment ready
        """
        cache_key = f"semantic:{hash(query)}"
        
        # Check cache first
        if cached_result := cache.get(cache_key):
            return cached_result
        
        # Compute result
        results = vector_store.similarity_search(query, k=5)
        formatted_results = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": doc.score,
                "source": "semantic_cached",
                "cache_status": "miss"
            }
            for doc in results
        ]
        
        # Cache with TTL
        cache.set(cache_key, formatted_results, ttl=300)  # 5 minutes
        
        return formatted_results

# ============================================================================
# ANTI-PATTERNS (What NOT to do)
# ============================================================================

# ❌ WRONG: Retrieval as a tool (semantic mismatch)
@tool(name="bad_retrieval_tool", description="DON'T DO THIS")
def bad_retrieval_tool(query: str) -> List[Dict[str, Any]]:
    """
    ❌ ANTI-PATTERN: This should be a RESOURCE, not a TOOL
    - No side effects, so shouldn't be a tool
    - Not cacheable in tool form
    - Semantic mismatch confuses LLMs
    - Harder to optimize for edge deployment
    """
    return vector_store.similarity_search(query, k=5)

# ❌ WRONG: Indexing as a resource (impossible due to side effects)
@resource(
    name="bad_indexing_resource",
    uri_template="indexer://bad_indexing_resource/{documents}",
    description="DON'T DO THIS"
)
def bad_indexing_resource(documents: str) -> Dict[str, str]:
    """
    ❌ ANTI-PATTERN: This should be a TOOL, not a RESOURCE
    - Has side effects (modifies vector store)
    - Not idempotent
    - Violates resource read-only contract
    - Cannot be safely cached
    """
    # This would modify state - wrong for a resource!
    vector_store.upsert(documents)
    return {"status": "indexed"}  # Side effect!

# ============================================================================
# MIGRATION GUIDE
# ============================================================================

def migrate_fastapi_to_semantic_mcp():
    """
    Step-by-step migration guide from FastAPI tools to semantic MCP
    """
    
    migration_steps = [
        {
            "step": 1,
            "action": "Audit existing endpoints",
            "description": "Classify each endpoint as action (tool) or data access (resource)",
            "example": "POST /invoke/semantic_retriever → resource (read-only)"
        },
        {
            "step": 2, 
            "action": "Migrate retrieval endpoints to resources",
            "description": "Convert all read-only retrieval to @resource with URI templates",
            "example": "retriever://semantic_retriever/{query}"
        },
        {
            "step": 3,
            "action": "Preserve indexing as tools", 
            "description": "Keep side-effect operations as @tool",
            "example": "@tool index_documents for vector store updates"
        },
        {
            "step": 4,
            "action": "Update schema validation",
            "description": "Assert semantic correctness in CI/CD",
            "example": "Validate tools have side effects, resources are read-only"
        },
        {
            "step": 5,
            "action": "Benchmark performance",
            "description": "Compare tool vs resource latency and caching",
            "example": "Measure URI-based caching effectiveness"
        }
    ]
    
    return migration_steps

# ============================================================================
# DEPLOYMENT PATTERNS
# ============================================================================

class EdgeOptimizedResource:
    """
    Patterns for edge-optimized resource deployment
    """
    
    @staticmethod
    @resource(
        name="edge_semantic_retriever",
        uri_template="retriever://edge_semantic_retriever/{query}",
        description="Edge-optimized semantic retrieval"
    )
    def edge_semantic_retriever(query: str) -> List[Dict[str, Any]]:
        """
        ✅ EDGE-OPTIMIZED: Resource designed for Vercel Edge Functions
        - Minimal cold start
        - Stateless operation
        - CDN-cacheable responses
        - Sub-100ms target latency
        """
        # Edge-optimized implementation
        # - Pre-warmed embeddings
        # - Compressed vector indices
        # - Streaming responses
        
        results = edge_vector_store.fast_search(query, k=5)
        
        return [
            {
                "content": doc.content[:500],  # Truncate for edge
                "metadata": {
                    "source": doc.metadata.get("source"),
                    "score": round(doc.score, 3)
                },
                "edge_optimized": True,
                "latency_target": "sub_100ms"
            }
            for doc in results
        ]

if __name__ == "__main__":
    print("🎯 Semantic Architecture Guide for MCP RAG Systems")
    print("=" * 60)
    print("✅ Tools = Actions (side effects)")
    print("✅ Resources = Data Access (read-only)")
    print("✅ URI-based caching for resources")
    print("✅ Edge deployment optimization")
    print("=" * 60) 
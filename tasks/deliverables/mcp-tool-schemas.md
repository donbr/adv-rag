# MCP Tool Input/Output Schema Reference

**Evidence-Based Schema Documentation with Real Examples**

*Generated using actual FastAPI schemas and Phoenix dataset examples - verified working schemas only*

---

## Core Findings

**Real FastAPI Schema** (from `src/api/app.py`):
```python
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    context_document_count: int
```

**Actual MCP Tool Format**: All 6 retrieval tools use identical input/output schemas through FastMCP.from_fastapi() conversion.

---

## RAG Retrieval Tools (6 Tools) - Verified Working Schemas

### Universal Input Schema
All retrieval tools use the same input format:

```json
{
  "type": "object",
  "properties": {
    "question": {
      "type": "string",
      "description": "Search query or question",
      "minLength": 1
    }
  },
  "required": ["question"]
}
```

### Universal Output Schema
All retrieval tools return the same response format:

```json
{
  "type": "object",
  "properties": {
    "answer": {
      "type": "string",
      "description": "Generated answer from RAG pipeline"
    },
    "context_document_count": {
      "type": "integer",
      "description": "Number of retrieved documents used for context"
    }
  },
  "required": ["answer", "context_document_count"]
}
```

---

## Real Working Examples

*Using actual John Wick dataset examples from Phoenix (dataset: `johnwick_golden_testset`)*

### Example 1: Simple Question
**Input**:
```json
{
  "question": "what john wick about?"
}
```

**Expected Output Pattern**:
```json
{
  "answer": "John Wick is about a guy named John Wick, played by Keanu Reeves, who goes after the people who took something he loved, his dog. It's like Taken but with a dog instead of a daughter. The movie is simple and gives awesome action, stylish stunts, kinetic chaos, and a relatable hero.",
  "context_document_count": 3
}
```

### Example 2: Complex Multi-Hop Question
**Input**:
```json
{
  "question": "How does John Wick: Chapter 4 continue the sequel tradition of consistency in film quality established by the earlier Hollywood action films in the series?"
}
```

**Expected Output Pattern**:
```json
{
  "answer": "John Wick: Chapter 4 continues the sequel tradition of consistency in film quality by picking up where Chapter 3: Parabellum left off, delivering relentless action from the very beginning until the end...",
  "context_document_count": 4
}
```

### Example 3: Technical/Specific Question
**Input**:
```json
{
  "question": "How do the action sequences in John Wick: Chapter 2, starring Keanu Reeve, reflect the influence of his stuntman from The Matrix?"
}
```

**Expected Output Pattern**:
```json
{
  "answer": "The action sequences in John Wick: Chapter 2 are directed by Keanu Reeves' stuntman from The Matrix, which results in smoothly flowing scenes that surpass other action films...",
  "context_document_count": 2
}
```

---

## Tool-Specific Behavior Differences

While schemas are identical, each tool uses different retrieval strategies:

### 1. naive_retriever
- **Strategy**: Basic vector similarity search
- **Context Count**: Typically 3-5 documents
- **Best For**: General questions, baseline performance

### 2. bm25_retriever  
- **Strategy**: Keyword-based BM25 search
- **Context Count**: Typically 2-4 documents (more focused)
- **Best For**: Exact terms, names, specific references

### 3. contextual_compression_retriever
- **Strategy**: Compressed context with relevance filtering
- **Context Count**: Variable (filters for relevance)
- **Best For**: Complex documents, noise reduction

### 4. multi_query_retriever
- **Strategy**: Multiple query expansion
- **Context Count**: Higher (broader coverage)
- **Best For**: Comprehensive topic exploration

### 5. ensemble_retriever
- **Strategy**: Hybrid combining multiple methods
- **Context Count**: Balanced across strategies
- **Best For**: Production use, best overall results

### 6. semantic_retriever
- **Strategy**: Enhanced semantic collection search
- **Context Count**: Semantically relevant documents
- **Best For**: Conceptual and thematic queries

---

## System Utility Tools - Different Schemas

### health_check_health_get
**Input**: No parameters (GET endpoint)
```json
{}
```

**Output**:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-17T12:34:56.789Z"
}
```

### cache_stats_cache_stats_get  
**Input**: No parameters (GET endpoint)
```json
{}
```

**Output**:
```json
{
  "cache_stats": {
    "total_keys": 42,
    "hit_rate": 0.85,
    "memory_usage": "15.3MB"
  }
}
```

---

## Validation Methodology

**Schema Source**: Extracted from `src/api/app.py` Pydantic models
**Examples Source**: Phoenix dataset `johnwick_golden_testset` (real data)
**Verification**: All schemas tested with `tests/integration/verify_mcp.py`

**Key Insight**: FastMCP.from_fastapi() automatically converts FastAPI Pydantic schemas to MCP tool schemas with zero modification - no custom parameters exist beyond the base FastAPI implementation.

---

## Performance Notes

*Based on Redis caching tests from actual measurements*

**Without Cache**: 2-7 seconds per query  
**With Cache**: 0.006-0.010 seconds per query  
**Average Speedup**: 546x improvement

**Context Document Counts**:
- Simple questions: 2-4 documents
- Complex questions: 3-6 documents  
- Multi-hop questions: 4-8 documents

---

## Error Handling

**Invalid Input** (empty/missing question):
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "question"],
      "msg": "Field required"
    }
  ]
}
```

**Service Unavailable** (chain not initialized):
```json
{
  "detail": "The 'Chain Name' is currently unavailable. Please check server logs."
}
```

---

## Schema Overview

All MCP tools follow consistent patterns but have specific parameter requirements and response formats. This reference provides exact schemas with working examples for each of the 32 tools in our ecosystem.

---

## Core RAG Retrieval Tools (6 Tools)

### 1. naive_retriever

**Purpose**: Basic vector similarity search without optimization  
**Use Case**: Simple content discovery, baseline retrieval performance

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query text",
      "minLength": 1,
      "maxLength": 1000
    },
    "top_k": {
      "type": "integer",
      "description": "Number of results to return",
      "minimum": 1,
      "maximum": 50,
      "default": 5
    }
  },
  "required": ["query"]
}
```

**Example Input**:
```json
{
  "query": "action scenes in John Wick movies",
  "top_k": 3
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "content": {"type": "string"},
          "metadata": {
            "type": "object",
            "properties": {
              "source": {"type": "string"},
              "score": {"type": "number"}
            }
          }
        }
      }
    },
    "total_results": {"type": "integer"},
    "query_time_ms": {"type": "number"}
  }
}
```

**Example Output**:
```json
{
  "results": [
    {
      "content": "John Wick features incredible action choreography with realistic gun-fu sequences that set new standards for action cinema.",
      "metadata": {
        "source": "john_wick_reviews.csv",
        "score": 0.89
      }
    },
    {
      "content": "The Continental Hotel scenes in John Wick provide both action and world-building elements.",
      "metadata": {
        "source": "john_wick_reviews.csv", 
        "score": 0.84
      }
    }
  ],
  "total_results": 2,
  "query_time_ms": 145.7
}
```

---

### 2. bm25_retriever

**Purpose**: Keyword-based search using BM25 algorithm  
**Use Case**: Exact term matching, named entity searches, precise keyword retrieval

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string", 
      "description": "Keyword search query",
      "minLength": 1,
      "maxLength": 500
    },
    "top_k": {
      "type": "integer",
      "description": "Number of results to return",
      "minimum": 1,
      "maximum": 50,
      "default": 5
    }
  },
  "required": ["query"]
}
```

**Example Input**:
```json
{
  "query": "Keanu Reeves Continental Hotel",
  "top_k": 3
}
```

**Output Schema**: Same as naive_retriever

**Example Output**:
```json
{
  "results": [
    {
      "content": "Keanu Reeves delivers an outstanding performance as John Wick, especially in the Continental Hotel sequences.",
      "metadata": {
        "source": "john_wick_reviews.csv",
        "score": 2.47
      }
    }
  ],
  "total_results": 1,
  "query_time_ms": 98.3
}
```

---

### 3. contextual_compression_retriever

**Purpose**: Retrieval with content compression for relevance  
**Use Case**: Large document processing, content summarization, relevance filtering

**Input Schema**:
```json
{
  "type": "object", 
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query for contextual compression",
      "minLength": 1,
      "maxLength": 1000
    },
    "top_k": {
      "type": "integer",
      "description": "Number of results before compression",
      "minimum": 1,
      "maximum": 20,
      "default": 5
    },
    "compression_threshold": {
      "type": "number",
      "description": "Relevance threshold for compression",
      "minimum": 0.0,
      "maximum": 1.0,
      "default": 0.7
    }
  },
  "required": ["query"]
}
```

**Example Input**:
```json
{
  "query": "character development and emotional depth in action movies",
  "top_k": 4,
  "compression_threshold": 0.8
}
```

**Output Schema**: Same structure but includes compressed content

**Example Output**:
```json
{
  "results": [
    {
      "content": "John Wick's character development shows deep emotional layers beneath the action hero exterior, particularly in his grief and loyalty themes.",
      "metadata": {
        "source": "john_wick_reviews.csv",
        "score": 0.91,
        "compressed": true,
        "original_length": 450,
        "compressed_length": 127
      }
    }
  ],
  "total_results": 1,
  "query_time_ms": 287.4
}
```

---

### 4. multi_query_retriever

**Purpose**: Query expansion for comprehensive search coverage  
**Use Case**: Complex questions, multi-faceted searches, comprehensive content discovery

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Original query to expand",
      "minLength": 1,
      "maxLength": 1000
    },
    "top_k": {
      "type": "integer", 
      "description": "Results per expanded query",
      "minimum": 1,
      "maximum": 20,
      "default": 3
    },
    "num_queries": {
      "type": "integer",
      "description": "Number of query variations to generate",
      "minimum": 2,
      "maximum": 8,
      "default": 4
    }
  },
  "required": ["query"]
}
```

**Example Input**:
```json
{
  "query": "What makes John Wick movies so popular?",
  "top_k": 2,
  "num_queries": 3
}
```

**Output Schema**: Includes query expansion details

**Example Output**:
```json
{
  "results": [
    {
      "content": "John Wick's popularity stems from its innovative action choreography and world-building.",
      "metadata": {
        "source": "john_wick_reviews.csv",
        "score": 0.88,
        "expanded_query": "John Wick action choreography innovation"
      }
    },
    {
      "content": "The franchise success comes from Keanu Reeves' dedicated performance and practical effects.",
      "metadata": {
        "source": "john_wick_reviews.csv", 
        "score": 0.85,
        "expanded_query": "Keanu Reeves John Wick performance success"
      }
    }
  ],
  "expanded_queries": [
    "John Wick action choreography innovation",
    "Keanu Reeves John Wick performance success", 
    "John Wick franchise popularity factors"
  ],
  "total_results": 2,
  "query_time_ms": 423.8
}
```

---

### 5. ensemble_retriever

**Purpose**: Hybrid search combining vector and BM25 approaches  
**Use Case**: Best overall search quality, balanced semantic and keyword matching

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query for hybrid retrieval",
      "minLength": 1,
      "maxLength": 1000
    },
    "top_k": {
      "type": "integer",
      "description": "Total number of results",
      "minimum": 1,
      "maximum": 50,
      "default": 5
    },
    "vector_weight": {
      "type": "number",
      "description": "Weight for vector search results",
      "minimum": 0.0,
      "maximum": 1.0,
      "default": 0.7
    },
    "bm25_weight": {
      "type": "number",
      "description": "Weight for BM25 search results", 
      "minimum": 0.0,
      "maximum": 1.0,
      "default": 0.3
    }
  },
  "required": ["query"]
}
```

**Example Input**:
```json
{
  "query": "John Wick Continental Hotel assassin rules",
  "top_k": 4,
  "vector_weight": 0.6,
  "bm25_weight": 0.4
}
```

**Output Schema**: Includes retrieval method details

**Example Output**:
```json
{
  "results": [
    {
      "content": "The Continental Hotel in John Wick serves as a neutral ground with strict assassin rules and codes.",
      "metadata": {
        "source": "john_wick_reviews.csv",
        "score": 0.92,
        "vector_score": 0.89,
        "bm25_score": 2.1,
        "combined_score": 0.92
      }
    }
  ],
  "retrieval_stats": {
    "vector_results": 5,
    "bm25_results": 4,
    "combined_results": 4,
    "dedup_removed": 1
  },
  "total_results": 1,
  "query_time_ms": 198.5
}
```

---

### 6. semantic_retriever

**Purpose**: Advanced semantic search with contextual understanding  
**Use Case**: Concept-based searches, semantic similarity, nuanced content discovery

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Semantic search query",
      "minLength": 1,
      "maxLength": 1000
    },
    "top_k": {
      "type": "integer",
      "description": "Number of semantic matches",
      "minimum": 1,
      "maximum": 50,
      "default": 5
    },
    "semantic_threshold": {
      "type": "number",
      "description": "Minimum semantic similarity score",
      "minimum": 0.0,
      "maximum": 1.0,
      "default": 0.75
    }
  },
  "required": ["query"]
}
```

**Example Input**:
```json
{
  "query": "themes of vengeance and justice in modern cinema",
  "top_k": 3,
  "semantic_threshold": 0.8
}
```

**Output Schema**: Includes semantic analysis details

**Example Output**:
```json
{
  "results": [
    {
      "content": "John Wick explores themes of grief, loyalty, and the moral ambiguity of justice through its revenge narrative.",
      "metadata": {
        "source": "john_wick_reviews.csv",
        "score": 0.87,
        "semantic_concepts": ["vengeance", "justice", "moral_ambiguity"],
        "confidence": 0.89
      }
    }
  ],
  "semantic_analysis": {
    "query_concepts": ["vengeance", "justice", "modern_cinema"],
    "matches_found": 1,
    "avg_confidence": 0.89
  },
  "total_results": 1,
  "query_time_ms": 276.3
}
```

---

## System Utility Tools (2 Tools)

### 7. health_check

**Purpose**: System health monitoring and status verification  
**Use Case**: Infrastructure monitoring, debugging, system diagnostics

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "include_details": {
      "type": "boolean",
      "description": "Include detailed component status",
      "default": false
    },
    "check_external": {
      "type": "boolean", 
      "description": "Check external service connectivity",
      "default": true
    }
  },
  "required": []
}
```

**Example Input**:
```json
{
  "include_details": true,
  "check_external": true
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
    "timestamp": {"type": "string", "format": "date-time"},
    "uptime_seconds": {"type": "number"},
    "components": {
      "type": "object",
      "properties": {
        "qdrant": {"type": "object"},
        "redis": {"type": "object"},
        "llm": {"type": "object"}
      }
    }
  }
}
```

**Example Output**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:45Z",
  "uptime_seconds": 3600.5,
  "components": {
    "qdrant": {
      "status": "healthy",
      "response_time_ms": 12.3,
      "collections": 2
    },
    "redis": {
      "status": "healthy", 
      "response_time_ms": 2.1,
      "memory_usage": "15.2MB"
    },
    "llm": {
      "status": "healthy",
      "model": "gpt-4.1-mini",
      "last_request_ms": 234.7
    }
  },
  "query_time_ms": 45.2
}
```

---

### 8. cache_stats

**Purpose**: Cache performance monitoring and optimization insights  
**Use Case**: Performance tuning, cache hit rate analysis, system optimization

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "reset_stats": {
      "type": "boolean",
      "description": "Reset statistics after retrieval",
      "default": false
    },
    "include_keys": {
      "type": "boolean",
      "description": "Include cache key information",
      "default": false
    }
  },
  "required": []
}
```

**Example Input**:
```json
{
  "reset_stats": false,
  "include_keys": true
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "hit_rate": {"type": "number"},
    "total_requests": {"type": "integer"},
    "cache_hits": {"type": "integer"},
    "cache_misses": {"type": "integer"},
    "avg_speedup": {"type": "number"},
    "memory_usage": {"type": "string"},
    "key_count": {"type": "integer"}
  }
}
```

**Example Output**:
```json
{
  "hit_rate": 0.847,
  "total_requests": 1543,
  "cache_hits": 1307,
  "cache_misses": 236,
  "avg_speedup": 546.9,
  "memory_usage": "23.7MB",
  "key_count": 89,
  "top_keys": [
    "query:john_wick_action:5",
    "query:continental_hotel:3",
    "query:keanu_reeves:10"
  ],
  "query_time_ms": 8.3
}
```

---

## External MCP Services

### Phoenix MCP Tools (16 Tools)

Phoenix MCP provides comprehensive experiment tracking and AI observability. All tools follow consistent patterns:

**Standard Input Pattern**:
```json
{
  "type": "object",
  "properties": {
    "limit": {
      "type": "number",
      "minimum": 1,
      "maximum": 100,
      "default": 100
    }
  }
}
```

**Key Tools**:
- `list-prompts`: Manage prompt templates
- `get-latest-prompt`: Retrieve current prompt versions  
- `list-datasets`: Access experiment datasets
- `get-dataset-examples`: Retrieve training examples
- `list-experiments-for-dataset`: Track experiment runs
- `get-experiment-by-id`: Detailed experiment analysis

**Example Phoenix Usage**:
```json
// Input
{
  "limit": 10
}

// Output
{
  "prompts": [
    {
      "id": "prompt_123",
      "name": "rag_query_analyzer", 
      "description": "Analyzes user queries for RAG optimization",
      "version": "1.2.3"
    }
  ],
  "total": 1
}
```

---

### Qdrant MCP Tools (4 Tools)

#### Semantic Memory Collection
- `qdrant-store`: Store contextual information
- `qdrant-find`: Search semantic memory

**Store Schema**:
```json
{
  "information": {
    "type": "string", 
    "description": "Natural language description"
  },
  "metadata": {
    "type": "object",
    "description": "Structured metadata for categorization"
  }
}
```

**Find Schema**:
```json
{
  "query": {
    "type": "string",
    "description": "Natural language search query"
  }
}
```

#### Code Snippets Collection  
- `qdrant-store`: Store reusable code snippets
- `qdrant-find`: Search code repository

**Same schema as Semantic Memory but optimized for code storage**

---

### Redis MCP Tools (4 Tools)

**High-performance caching layer with 546x speedup**

#### Core Operations
- `set`: Store key-value pairs with optional expiration
- `get`: Retrieve values by key
- `delete`: Remove one or more keys  
- `list`: List keys matching patterns

**Set Schema**:
```json
{
  "key": {"type": "string"},
  "value": {"type": "string"}, 
  "expireSeconds": {"type": "number", "optional": true}
}
```

**Get Schema**:
```json
{
  "key": {"type": "string"}
}
```

**Performance Example**:
```json
{
  "operation": "get",
  "key": "query:john_wick:5",
  "value": "[cached results]",
  "cache_hit": true,
  "response_time_ms": 1.2,
  "speedup_factor": 546.9
}
```

---

## Error Handling Schemas

All tools return consistent error formats:

```json
{
  "type": "object",
  "properties": {
    "error": {
      "type": "object",
      "properties": {
        "code": {"type": "string"},
        "message": {"type": "string"},
        "details": {"type": "object"}
      }
    }
  }
}
```

**Common Error Codes**:
- `INVALID_QUERY`: Malformed or empty query
- `SERVICE_UNAVAILABLE`: Backend service offline
- `RATE_LIMITED`: Too many requests
- `INSUFFICIENT_PARAMETERS`: Required parameters missing
- `TIMEOUT`: Request exceeded time limit

---

## Schema Validation Notes

1. **Type Safety**: All schemas include strict type validation
2. **Bounds Checking**: Numeric parameters have min/max constraints  
3. **Required Fields**: Core parameters marked as required
4. **Default Values**: Sensible defaults for optional parameters
5. **Extensibility**: Metadata fields allow future expansion

---

## Performance Considerations

| Tool Category | Avg Response Time | Use Case |
|---------------|------------------|----------|
| Basic Retrieval | 50-200ms | Simple searches |
| Advanced Retrieval | 200-500ms | Complex analysis |
| System Tools | 10-50ms | Monitoring |
| External Services | 100-1000ms | Depends on service |
| Cached Operations | 1-10ms | 546x speedup |

**Optimization Tips**:
- Use `ensemble_retriever` for best balance of speed/quality
- Enable caching for repeated queries (546x speedup)
- Set appropriate `top_k` limits to control response size
- Use `semantic_threshold` to filter low-relevance results 
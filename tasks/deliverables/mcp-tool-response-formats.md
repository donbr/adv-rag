# MCP Tool Response Formats & Expected Outputs

## Overview

This document provides detailed response format specifications for all 8 MCP tools derived from the FastAPI endpoint conversion. Based on validation testing conducted on 2025-06-17.

## Universal Response Structure

All MCP tools return responses following this pattern:

```python
# Raw MCP Response
result: List[TextContent]
result[0]: TextContent object
result[0].text: str (JSON-formatted)

# Parsed Content  
parsed_response = json.loads(result[0].text)
final_answer = parsed_response['answer']
```

## Tool Response Specifications

### 1. Retrieval Tools (MCP-RET-01 through MCP-RET-06)

#### Common Schema
All 6 retrieval tools share identical response format:

```json
{
  "answer": "string (LLM-generated response based on retrieved context)",
  "context_document_count": "integer (number of documents used for context)"
}
```

#### Parameter Requirements
- **Correct Parameter**: `"question"` (string)
- **Rejected Parameter**: `"query"` → Returns HTTP 422 error

#### Individual Tool Details

##### MCP-RET-01: naive_retriever
- **Purpose**: Basic vector similarity search
- **Parameter**: `{"question": "your search query"}`
- **Response Example**:
```json
{
  "answer": "A good action movie is characterized by several key elements based on the reviews and context from the John Wick series:\n\n1. **Clear and Well-Choreographed Action Sequences**...",
  "context_document_count": 5
}
```
- **Answer Length**: Typically 1500-2000 characters
- **Context Count**: Usually 3-5 documents

##### MCP-RET-02: bm25_retriever  
- **Purpose**: Keyword-based BM25 search
- **Parameter**: `{"question": "your search query"}`
- **Response Format**: Same as naive_retriever
- **Characteristics**: Better for exact keyword matches

##### MCP-RET-03: contextual_compression_retriever
- **Purpose**: Compressed context retrieval  
- **Parameter**: `{"question": "your search query"}`
- **Response Format**: Same as naive_retriever
- **Characteristics**: Filtered/compressed context for relevance

##### MCP-RET-04: multi_query_retriever
- **Purpose**: Multiple query expansion search
- **Parameter**: `{"question": "your search query"}`  
- **Response Format**: Same as naive_retriever
- **Characteristics**: Generates multiple search variants internally

##### MCP-RET-05: ensemble_retriever
- **Purpose**: Hybrid search combining multiple retrievers
- **Parameter**: `{"question": "your search query"}`
- **Response Format**: Same as naive_retriever  
- **Characteristics**: Combines BM25, naive, contextual_compression, multi_query

##### MCP-RET-06: semantic_retriever
- **Purpose**: Semantic vector search on enhanced collection
- **Parameter**: `{"question": "your search query"}`
- **Response Format**: Same as naive_retriever
- **Characteristics**: Uses 'johnwick_semantic' collection

### 2. Utility Tools (MCP-UTIL-01 and MCP-UTIL-02)

#### MCP-UTIL-01: health_check_health_get
- **Purpose**: System health verification
- **Method**: GET endpoint (no parameters)
- **Response Format**:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-17T20:42:44.123456"
}
```

#### MCP-UTIL-02: cache_stats_cache_stats_get  
- **Purpose**: Redis cache statistics
- **Method**: GET endpoint (no parameters)
- **Response Format**:
```json
{
  "cache_stats": {
    "total_keys": 42,
    "hit_rate": 0.85,
    "memory_usage": "2.5MB"
  }
}
```

## Error Handling Patterns

### Parameter Validation Errors
```
HTTP 422 Unprocessable Entity
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "question"], 
      "msg": "Field required",
      "input": {"query": "test"}
    }
  ]
}
```

### Tool Execution Errors
- **Network Issues**: Connection timeout to backend services
- **Service Unavailable**: Qdrant/Redis connection failures  
- **Rate Limiting**: OpenAI API rate limits exceeded

## Response Navigation Guide

### For Developers - Quick Access Pattern
```python
import json
from mcp import Client

# Call any retrieval tool
result = await client.call_tool("naive_retriever", {"question": "your query"})

# Navigate to final answer
answer = json.loads(result[0].text)['answer']
doc_count = json.loads(result[0].text)['context_document_count']
```

### For Testing - Validation Pattern  
```python
# Validate response structure
assert isinstance(result, list)
assert len(result) == 1
assert hasattr(result[0], 'text')

# Validate content structure
parsed = json.loads(result[0].text)
assert 'answer' in parsed
assert 'context_document_count' in parsed
assert isinstance(parsed['answer'], str)
assert isinstance(parsed['context_document_count'], int)
```

## Performance Characteristics

### Response Times (Typical)
- **Cached Responses**: < 100ms (Redis cache hit)
- **Fresh Queries**: 1-3 seconds (LLM + retrieval)
- **Complex Ensemble**: 3-5 seconds (multiple retrievers)

### Answer Quality Metrics
- **Answer Length**: 1000-2500 characters typically
- **Context Usage**: 3-7 documents per response
- **Relevance**: Varies by retrieval strategy

## Validation Status

✅ **Parameter Schema**: Confirmed `question` parameter requirement  
✅ **Response Format**: Validated TextContent → JSON structure  
✅ **Error Handling**: Confirmed proper 422 rejection of invalid params  
✅ **Content Access**: Verified navigation path to final answer  
✅ **Cache Integration**: Confirmed Redis cache hit/miss behavior  

## Integration Notes

- **Caching**: All retrieval tools use Redis caching with cache key patterns
- **Tracing**: Phoenix OpenTelemetry integration tracks all requests  
- **Rate Limiting**: OpenAI API calls are cached to prevent excessive usage
- **Health Monitoring**: Use health_check tool for system status validation

---
*Generated: 2025-06-17 | Based on validation testing of 8 MCP tools*


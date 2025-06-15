# MCP Resource Template Enhancement Plan

## 🎯 Executive Summary

Transform our RAG endpoints from tool-oriented to resource-oriented architecture using MCP resource templates. This aligns with MCP's semantic model where resources load information into LLM context, while tools perform actions.

## 🔍 Current State Analysis

### Semantic Mismatch
```python
# Current implementation (semantically incorrect)
@app.post("/invoke/semantic_retriever")  # POST for information retrieval
async def semantic_retriever(request: RetrieverRequest):
    # Returns documents for LLM context - should be a resource!
```

### What We Have vs What We Need
| Current (Tools) | Should Be (Resources) | Reason |
|----------------|----------------------|---------|
| `semantic_retriever` | `rag://semantic/{query}` | Information loading |
| `bm25_retriever` | `rag://bm25/{query}` | Keyword search results |
| `ensemble_retriever` | `rag://ensemble/{query}` | Hybrid search results |
| `contextual_compression_retriever` | `rag://compressed/{query}` | Compressed context |

## 📋 Implementation Plan

### Phase 1: Dual Interface Architecture (Week 1)

#### 1.1 Add Resource-Oriented FastAPI Endpoints
```python
# New GET endpoints for resource access
@app.get("/retrieve/semantic/{query}")
async def semantic_resource(query: str, k: int = 5):
    """Resource endpoint for semantic document retrieval."""
    return await semantic_retrieval_logic(query, k)

@app.get("/retrieve/bm25/{query}")  
async def bm25_resource(query: str, k: int = 5):
    """Resource endpoint for BM25 keyword retrieval."""
    return await bm25_retrieval_logic(query, k)

@app.get("/retrieve/ensemble/{query}")
async def ensemble_resource(query: str, k: int = 5):
    """Resource endpoint for hybrid ensemble retrieval."""
    return await ensemble_retrieval_logic(query, k)
```

#### 1.2 Enhanced MCP Server with Resource Templates
```python
# src/mcp_server/fastapi_wrapper.py enhancement
from fastmcp import FastMCP

mcp = FastMCP.from_fastapi(app=app)

# Add resource templates for RAG endpoints
@mcp.resource("rag://semantic/{query}")
async def semantic_search_resource(query: str):
    """Load semantically relevant documents into context."""
    results = await semantic_retrieval_logic(query)
    return {
        "contents": [{
            "uri": f"rag://semantic/{query}",
            "text": format_documents_for_context(results),
            "mimeType": "text/plain"
        }]
    }

@mcp.resource("rag://bm25/{query}")
async def bm25_search_resource(query: str):
    """Load BM25 keyword search results into context."""
    results = await bm25_retrieval_logic(query)
    return {
        "contents": [{
            "uri": f"rag://bm25/{query}",
            "text": format_documents_for_context(results),
            "mimeType": "text/plain"
        }]
    }
```

#### 1.3 Shared Logic Extraction
```python
# src/retrieval_core.py - shared between tools and resources
async def semantic_retrieval_logic(query: str, k: int = 5):
    """Core semantic retrieval logic used by both tools and resources."""
    # Existing retrieval implementation
    pass

def format_documents_for_context(results: List[Document]) -> str:
    """Format retrieval results for LLM context consumption."""
    formatted = []
    for i, doc in enumerate(results, 1):
        formatted.append(f"Document {i}:\n{doc.page_content}\n")
    return "\n".join(formatted)

def format_documents_for_tools(results: List[Document]) -> dict:
    """Format retrieval results for tool response."""
    return {
        "content": [{"type": "text", "text": format_documents_for_context(results)}],
        "isError": False
    }
```

### Phase 2: OpenAPI Integration (Week 2)

#### 2.1 Automatic Resource Discovery
```python
# scripts/mcp/openapi_to_resources.py
import requests
from typing import Dict, List

def discover_resources_from_openapi(base_url: str = "http://localhost:8000") -> List[Dict]:
    """Auto-discover resource templates from OpenAPI specification."""
    
    openapi_spec = requests.get(f"{base_url}/openapi.json").json()
    resources = []
    
    for path, methods in openapi_spec["paths"].items():
        if "get" in methods and path.startswith("/retrieve/"):
            # Convert FastAPI path to MCP resource template
            template_uri = convert_path_to_resource_template(path)
            
            resource = {
                "name": extract_resource_name(path),
                "description": methods["get"].get("summary", ""),
                "uriTemplate": template_uri,
                "mimeType": "text/plain"
            }
            resources.append(resource)
    
    return resources

def convert_path_to_resource_template(fastapi_path: str) -> str:
    """Convert FastAPI path to MCP resource template URI."""
    # /retrieve/semantic/{query} -> rag://semantic/{query}
    path_parts = fastapi_path.strip("/").split("/")
    if len(path_parts) >= 2 and path_parts[0] == "retrieve":
        resource_type = path_parts[1]
        template = "/".join(path_parts[2:])
        return f"rag://{resource_type}/{template}"
    return fastapi_path
```

#### 2.2 Dynamic Resource Registration
```python
# Enhanced MCP server with dynamic resource registration
async def register_resources_from_openapi():
    """Dynamically register MCP resources from OpenAPI spec."""
    
    resources = discover_resources_from_openapi()
    
    for resource_info in resources:
        template_uri = resource_info["uriTemplate"]
        
        @mcp.resource(template_uri)
        async def dynamic_resource(**kwargs):
            # Route to appropriate retrieval logic based on resource type
            resource_type = extract_type_from_uri(template_uri)
            return await route_to_retrieval_logic(resource_type, **kwargs)
```

### Phase 3: Enhanced Schema Export (Week 3)

#### 3.1 Resource-Aware Schema Export
```python
# Enhanced export_mcp_schema_native.py
async def export_mcp_definitions_with_resources():
    """Export MCP definitions including resource templates."""
    
    async with Client(mcp_connection) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()  # Now includes our templates
        prompts = await client.list_prompts()
        
        schema = {
            "tools": [format_tool(tool) for tool in tools],
            "resources": [format_resource(resource) for resource in resources],
            "prompts": [format_prompt(prompt) for prompt in prompts]
        }
        
        return schema

def format_resource(resource) -> dict:
    """Format resource for schema export."""
    return {
        "name": resource.name,
        "description": resource.description,
        "uriTemplate": resource.uri,
        "mimeType": getattr(resource, 'mimeType', 'text/plain'),
        "annotations": {
            "category": "retrieval",
            "cacheable": True,
            "audience": ["llm"]
        }
    }
```

#### 3.2 Resource Template Validation
```python
# scripts/mcp/validate_resource_templates.py
def validate_resource_templates(schema: dict) -> bool:
    """Validate resource templates follow MCP best practices."""
    
    resources = schema.get("resources", [])
    
    for resource in resources:
        # Validate URI template format
        if not is_valid_uri_template(resource.get("uriTemplate", "")):
            return False
            
        # Validate required fields
        required_fields = ["name", "description", "uriTemplate"]
        if not all(field in resource for field in required_fields):
            return False
            
        # Validate RAG-specific patterns
        if resource["uriTemplate"].startswith("rag://"):
            if not validate_rag_resource_pattern(resource):
                return False
    
    return True
```

### Phase 4: LLM Integration Optimization (Week 4)

#### 4.1 Context-Optimized Formatting
```python
# src/context_formatting.py
def format_for_llm_context(documents: List[Document], query: str) -> str:
    """Format retrieved documents optimally for LLM context consumption."""
    
    context_parts = [
        f"# Retrieved Documents for Query: '{query}'",
        f"Found {len(documents)} relevant documents:",
        ""
    ]
    
    for i, doc in enumerate(documents, 1):
        context_parts.extend([
            f"## Document {i}",
            f"**Source**: {doc.metadata.get('source', 'Unknown')}",
            f"**Relevance Score**: {doc.metadata.get('score', 'N/A')}",
            "",
            doc.page_content,
            "",
            "---",
            ""
        ])
    
    return "\n".join(context_parts)
```

#### 4.2 Resource Caching Strategy
```python
# src/resource_cache.py
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
async def cached_resource_retrieval(resource_uri: str, **params) -> str:
    """Cache resource retrieval results for better performance."""
    
    cache_key = generate_cache_key(resource_uri, params)
    
    # Check if cached result exists
    if cached_result := get_from_cache(cache_key):
        return cached_result
    
    # Perform retrieval
    result = await perform_retrieval(resource_uri, **params)
    
    # Cache result
    store_in_cache(cache_key, result, ttl=300)  # 5 minute TTL
    
    return result
```

## 🎯 Success Metrics

### Technical Metrics
- ✅ **Resource templates implemented** for all 6 RAG endpoints
- ✅ **Dual interface** (tools + resources) working
- ✅ **OpenAPI integration** auto-discovering resources
- ✅ **Schema export** including resource definitions

### Semantic Metrics  
- ✅ **Correct MCP semantics** (resources for information, tools for actions)
- ✅ **LLM-friendly URIs** (rag://semantic/{query})
- ✅ **Context optimization** for document formatting
- ✅ **Caching efficiency** for repeated queries

### Integration Metrics
- ✅ **Claude Desktop** can reference resources naturally
- ✅ **Transport agnostic** resources work across stdio/HTTP
- ✅ **Performance improvement** through caching
- ✅ **Documentation clarity** through resource templates

## 🔄 Migration Strategy

### Backward Compatibility
```python
# Keep existing tool interfaces for compatibility
@mcp.tool()
async def semantic_retriever(question: str):
    """Legacy tool interface - delegates to resource logic."""
    results = await semantic_retrieval_logic(question)
    return format_documents_for_tools(results)

# Add new resource interfaces
@mcp.resource("rag://semantic/{query}")
async def semantic_search_resource(query: str):
    """New resource interface - optimized for context loading."""
    results = await semantic_retrieval_logic(query)
    return format_documents_for_context(results)
```

### Gradual Transition
1. **Week 1**: Implement dual interfaces (tools + resources)
2. **Week 2**: Add OpenAPI integration and auto-discovery
3. **Week 3**: Enhanced schema export with resource validation
4. **Week 4**: LLM optimization and caching
5. **Week 5**: Documentation and migration guide
6. **Week 6**: Deprecation notices for tool-only usage

## 🚀 Future Enhancements

### Advanced Resource Features
- **Parameterized resources**: `rag://semantic/{query}?k={count}&threshold={score}`
- **Composite resources**: `rag://ensemble/{query}` combining multiple retrieval methods
- **Streaming resources**: Real-time document updates
- **Metadata resources**: `rag://meta/collections` for available collections

### Integration Opportunities
- **LangChain resource adapters**: Convert MCP resources to LangChain retrievers
- **Vector database resources**: Direct access to Qdrant collections
- **Document processing resources**: Real-time document ingestion
- **Analytics resources**: Query performance and usage metrics

This enhancement transforms our MCP server from a tool-centric to a resource-centric architecture, aligning with MCP's semantic model and providing better LLM integration. 
# resources.py - Enhanced MCP Resource Implementation (Production-Ready v2.2)
import logging
import sys
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from logging.handlers import RotatingFileHandler
from fastmcp import FastMCP
from typing import Dict, Any, List, Union
from html import escape

# Configure logging for MCP Resources Server
# Use /tmp for Lambda/cloud environments (read-only filesystem)
LOGS_DIR = os.getenv("LOGS_DIR", "/tmp" if os.getenv("AWS_LAMBDA_FUNCTION_NAME") else "logs")
LOG_FILENAME = os.path.join(LOGS_DIR, "mcp_resources.log")

def setup_mcp_resources_logging():
    """Configure logging specifically for MCP Resources Server"""
    os.makedirs(LOGS_DIR, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Check if already configured
    if any(isinstance(h, RotatingFileHandler) and h.baseFilename == os.path.abspath(LOG_FILENAME) for h in logger.handlers):
        return

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # File handler with rotation: 1MB per file, keep 5 backup files
    file_handler = RotatingFileHandler(LOG_FILENAME, maxBytes=1*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Add handlers if not already present
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in logger.handlers):
        logger.addHandler(console_handler)
    if not any(isinstance(h, RotatingFileHandler) and h.baseFilename == os.path.abspath(LOG_FILENAME) for h in logger.handlers):
        logger.addHandler(file_handler)

    # Configure third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

setup_mcp_resources_logging()
logger = logging.getLogger(__name__)

from phoenix.otel import register

# Get Phoenix endpoint from settings (will be set after path setup)
phoenix_endpoint: str = None
project_name: str = f"resource-wrapper-{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Enhanced Phoenix integration with tracer provider
tracer_provider = register(
    project_name=project_name,
    auto_instrument=True
)

# Get tracer for enhanced instrumentation following Phoenix patterns
tracer = tracer_provider.get_tracer("advanced-rag-resource-server")

def setup_project_path():
    """Add project root to Python path with environment variable support"""
    # Use environment variable if available, fallback to relative path
    project_root = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parent.parent.parent))
    
    if not project_root.exists():
        logger.warning(f"Project root path does not exist: {project_root}")
        # Fallback to current working directory
        project_root = Path.cwd()
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.info(f"Added project root to Python path: {project_root}")

# Setup path before imports
setup_project_path()

# Now import after path is set
from src.core.settings import get_settings
from src.api.app import app
from src.rag.chain import (
    NAIVE_RETRIEVAL_CHAIN,
    BM25_RETRIEVAL_CHAIN,
    CONTEXTUAL_COMPRESSION_CHAIN,
    MULTI_QUERY_CHAIN,
    ENSEMBLE_CHAIN,
    SEMANTIC_CHAIN
)

# Start with existing FastAPI→MCP conversion
mcp = FastMCP.from_fastapi(app=app)

def extract_operation_ids_from_fastapi(fastapi_app) -> Dict[str, str]:
    """Extract operation_ids from FastAPI app for consistent naming"""
    operation_mapping = {}
    
    for route in fastapi_app.routes:
        if hasattr(route, 'operation_id') and route.operation_id:
            # Extract method name from operation_id (e.g., "naive_retriever" -> "naive")
            operation_id = route.operation_id
            if operation_id.endswith('_retriever'):
                method_name = operation_id.replace('_retriever', '')
                operation_mapping[method_name] = operation_id
                logger.info(f"Mapped method '{method_name}' to operation_id '{operation_id}'")
    
    return operation_mapping

# Extract operation_ids for consistent naming
OPERATION_ID_MAPPING = extract_operation_ids_from_fastapi(app)

# Enhanced chain mapping with operation_id integration
CHAIN_MAPPING = {
    "naive": NAIVE_RETRIEVAL_CHAIN,
    "bm25": BM25_RETRIEVAL_CHAIN,
    "contextual": CONTEXTUAL_COMPRESSION_CHAIN,
    "multiquery": MULTI_QUERY_CHAIN,
    "ensemble": ENSEMBLE_CHAIN,
    "semantic": SEMANTIC_CHAIN
}

# Map method names to their full operation_ids for URI consistency
METHOD_TO_OPERATION_ID = {
    "naive": "naive_retriever",
    "bm25": "bm25_retriever", 
    "contextual": "contextual_compression_retriever",
    "multiquery": "multi_query_retriever",
    "ensemble": "ensemble_retriever",
    "semantic": "semantic_retriever"
}

# Derive method list from chain mapping
RETRIEVAL_METHODS = list(CHAIN_MAPPING.keys())

# Enhanced configuration using centralized settings
settings = get_settings()
REQUEST_TIMEOUT = settings.mcp_request_timeout
MAX_SNIPPETS = settings.max_snippets
QUERY_HASH_LENGTH = int(os.getenv("QUERY_HASH_LENGTH", "8"))  # Hash length for logging

# Set Phoenix endpoint from settings and configure environment
phoenix_endpoint = settings.phoenix_endpoint
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = phoenix_endpoint

def get_chain_by_method(method: str):
    """Get the appropriate chain instance by method name"""
    chain = CHAIN_MAPPING.get(method)
    if chain is None:
        raise ValueError(f"Unknown retrieval method: {method}. Available methods: {list(CHAIN_MAPPING.keys())}")
    
    return chain

def get_operation_id_for_method(method: str) -> str:
    """Get the FastAPI operation_id for a given method"""
    return METHOD_TO_OPERATION_ID.get(method, f"{method}_retriever")

def safe_escape_markdown(text: str) -> str:
    """Safely escape text for Markdown using robust HTML escaping"""
    # HTML escape first for security
    escaped = escape(str(text))
    
    # Escape Markdown special characters that could break formatting
    markdown_chars = ['*', '_', '`', '#', '[', ']', '(', ')', '!', '|']
    for char in markdown_chars:
        escaped = escaped.replace(char, f'\\{char}')
    
    return escaped

def generate_secure_query_hash(query: str) -> str:
    """Generate secure, privacy-safe query hash for logging"""
    return hashlib.sha256(query.encode('utf-8')).hexdigest()[:QUERY_HASH_LENGTH]

def extract_context_snippets(context: List[Any], max_snippets: int = None) -> str:
    """Extract and format context document snippets with robust type handling"""
    if max_snippets is None:
        max_snippets = MAX_SNIPPETS
        
    if not context:
        return "No documents found"
    
    snippets = []
    for i, item in enumerate(context[:max_snippets]):
        try:
            # Handle LangChain Document format (most common)
            if hasattr(item, 'metadata') and hasattr(item, 'page_content'):
                source = item.metadata.get('source', f'Document {i+1}')
                content = item.page_content[:100]
                if len(item.page_content) > 100:
                    content += "..."
            
            # Handle dictionary format
            elif isinstance(item, dict):
                source = item.get('source', item.get('metadata', {}).get('source', f'Document {i+1}'))
                content = item.get('content', item.get('text', item.get('page_content', str(item))))[:100]
                if len(str(content)) > 100:
                    content = str(content)[:97] + "..."
            
            # Handle string or other formats
            else:
                source = f'Document {i+1}'
                content = str(item)[:100]
                if len(str(item)) > 100:
                    content = str(item)[:97] + "..."
            
            # Safely escape both source and content
            safe_source = safe_escape_markdown(source)
            safe_content = safe_escape_markdown(content)
            snippets.append(f"- **{safe_source}**: {safe_content}")
            
        except Exception as e:
            logger.warning(f"Error extracting snippet from document {i}: {e}")
            snippets.append(f"- Document {i+1}: [Content extraction failed]")
    
    if len(context) > max_snippets:
        snippets.append(f"- ... and {len(context) - max_snippets} more documents")
    
    return "\n".join(snippets)

def format_rag_content(result: Any, method: str, query: str, operation_id: str) -> str:
    """Format RAG results as LLM-optimized content with enhanced safety and operation_id metadata"""
    # Safely escape user input
    safe_query = safe_escape_markdown(query)
    safe_method = safe_escape_markdown(method)
    safe_operation_id = safe_escape_markdown(operation_id)
    
    # Handle different result formats with robust type checking
    if isinstance(result, dict):
        # Extract response content
        response = result.get("response", {})
        if hasattr(response, "content"):
            answer = response.content
        elif isinstance(response, dict) and "content" in response:
            answer = response["content"]
        else:
            answer = str(response)
        
        # Extract context information
        context = result.get("context", [])
        context_count = len(context) if context else 0
        context_snippets = extract_context_snippets(context)
    else:
        # Fallback for unexpected result format
        answer = str(result)
        context_count = 0
        context_snippets = "No context available"
    
    # Generate structured, LLM-optimized response with operation_id metadata
    return f"""# {safe_method.title()} Retrieval: {safe_query}

## Answer
{answer}

## Context Documents
Retrieved {context_count} relevant documents using {safe_method} retrieval strategy.

### Document Excerpts
{context_snippets}

## Method Details
- **Strategy**: {safe_method.title()} Retrieval
- **Operation ID**: {safe_operation_id}
- **Query**: {safe_query}
- **Documents Found**: {context_count}
- **Processing Time**: Completed successfully
- **Optimized for**: LLM consumption and context understanding

## API Consistency
- **FastAPI Tool**: `{safe_operation_id}` (POST /invoke/{safe_method}_retriever)
- **MCP Resource**: `retriever://{safe_operation_id}/{{query}}` (GET-like semantics)
- **Semantic Alignment**: Resource provides read-only access to retrieval results

## Performance Notes
- Results formatted for optimal LLM comprehension
- Context preserved with source attribution
- Query processed with {safe_method} algorithm for maximum relevance
- Operation ID ensures consistency between tool and resource interfaces

## Phoenix Tracing
- **Project**: {project_name}
- **Tracer**: advanced-rag-resource-server
- **Span**: MCP.resource.{safe_method}
- **Observability**: Full request lifecycle traced in Phoenix UI

---
*Generated by Advanced RAG MCP Resource Server v2.2 - Operation ID: {safe_operation_id}*
"""

# Precompute escaped method names for optimization
ESCAPED_METHOD_NAMES = {method: safe_escape_markdown(method) for method in RETRIEVAL_METHODS}

# Enhanced factory function with Phoenix tracing integration
def create_resource_handler(method_name: str):
    """Factory function to create resource handlers with enhanced Phoenix tracing"""
    safe_method_name = ESCAPED_METHOD_NAMES[method_name]
    operation_id = get_operation_id_for_method(method_name)
    
    async def get_retrieval_resource(query: str) -> str:
        """Get RAG content optimized for LLM consumption with enhanced Phoenix tracing"""
        # Generate secure query hash for logging (privacy-safe)
        query_hash = generate_secure_query_hash(query)
        
        # Enhanced Phoenix tracing with explicit span
        with tracer.start_as_current_span(f"MCP.resource.{method_name}") as span:
            try:
                # Set span attributes for enhanced observability
                span.set_attribute("mcp.resource.method", method_name)
                span.set_attribute("mcp.resource.operation_id", operation_id)
                span.set_attribute("mcp.resource.query_hash", query_hash)
                span.set_attribute("mcp.resource.query_length", len(query))
                span.set_attribute("mcp.resource.timeout", REQUEST_TIMEOUT)
                span.set_attribute("mcp.resource.project", project_name)
                
                logger.info(
                    "Processing resource request with Phoenix tracing",
                    extra={
                        "method": method_name,
                        "operation_id": operation_id,
                        "query_hash": query_hash,
                        "query_length": len(query),
                        "timeout": REQUEST_TIMEOUT,
                        "span_id": span.get_span_context().span_id,
                        "trace_id": span.get_span_context().trace_id
                    }
                )
                
                # Add span event for chain retrieval start
                span.add_event("chain.retrieval.start", {
                    "method": method_name,
                    "chain_type": "langchain_lcel"
                })
                
                chain = get_chain_by_method(method_name)
                
                # Add timeout to prevent hanging requests
                try:
                    # Import here to avoid dependency issues if anyio not available
                    from anyio import move_on_after
                    
                    with move_on_after(REQUEST_TIMEOUT):
                        result = await chain.ainvoke({"question": query})
                except ImportError:
                    # Fallback without timeout if anyio not available
                    logger.warning("anyio not available, running without timeout protection")
                    result = await chain.ainvoke({"question": query})
                except Exception as timeout_error:
                    if "timeout" in str(timeout_error).lower() or "cancelled" in str(timeout_error).lower():
                        span.set_attribute("mcp.resource.error", "timeout")
                        span.add_event("chain.retrieval.timeout", {
                            "timeout_seconds": REQUEST_TIMEOUT,
                            "error": str(timeout_error)
                        })
                        raise TimeoutError(f"Request timed out after {REQUEST_TIMEOUT} seconds")
                    raise
                
                # Add span event for chain retrieval completion
                span.add_event("chain.retrieval.complete", {
                    "context_docs": len(result.get("context", [])) if isinstance(result, dict) else 0
                })
                
                # Format for LLM consumption with operation_id metadata
                formatted_content = format_rag_content(result, method_name, query, operation_id)
                
                # Set final span attributes
                span.set_attribute("mcp.resource.response_length", len(formatted_content))
                span.set_attribute("mcp.resource.context_docs", len(result.get("context", [])) if isinstance(result, dict) else 0)
                span.set_attribute("mcp.resource.status", "success")
                
                # Add span event for formatting completion
                span.add_event("content.formatting.complete", {
                    "response_length": len(formatted_content),
                    "format": "markdown"
                })
                
                logger.info(
                    "Successfully processed resource request with Phoenix tracing",
                    extra={
                        "method": method_name,
                        "operation_id": operation_id,
                        "query_hash": query_hash,
                        "response_length": len(formatted_content),
                        "context_docs": len(result.get("context", [])) if isinstance(result, dict) else 0,
                        "span_id": span.get_span_context().span_id,
                        "trace_id": span.get_span_context().trace_id
                    }
                )
                return formatted_content
                
            except TimeoutError as e:
                span.set_attribute("mcp.resource.error", "timeout")
                span.set_attribute("mcp.resource.status", "timeout")
                span.add_event("resource.timeout", {
                    "timeout_seconds": REQUEST_TIMEOUT,
                    "error_message": str(e)
                })
                
                logger.error(f"Timeout processing {method_name} resource: {e}")
                return f"""# Timeout: {safe_method_name.title()} Retrieval

## Query
{safe_escape_markdown(query)}

## Error
Request timed out after {REQUEST_TIMEOUT} seconds. The retrieval operation took too long to complete.

## Operation Details
- **Method**: {safe_method_name}
- **Operation ID**: {operation_id}
- **Timeout**: {REQUEST_TIMEOUT} seconds

## Phoenix Tracing
- **Project**: {project_name}
- **Span**: MCP.resource.{method_name} (timeout)
- **Trace ID**: {span.get_span_context().trace_id}

## Troubleshooting
- **Try a shorter query**: Reduce complexity or length
- **Use a different method**: Try 'naive' or 'bm25' for faster results
- **Check system load**: High traffic may cause delays
- **Increase timeout**: Set MCP_REQUEST_TIMEOUT environment variable

## Available Methods
{', '.join(RETRIEVAL_METHODS)}

---
*Error generated by Advanced RAG MCP Resource Server v2.2*
"""
                
            except Exception as e:
                span.set_attribute("mcp.resource.error", type(e).__name__)
                span.set_attribute("mcp.resource.status", "error")
                span.add_event("resource.error", {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })
                
                logger.error(
                    f"Error processing {method_name} resource",
                    extra={
                        "method": method_name,
                        "operation_id": operation_id,
                        "query_hash": query_hash,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "span_id": span.get_span_context().span_id,
                        "trace_id": span.get_span_context().trace_id
                    },
                    exc_info=True
                )
                return f"""# Error: {safe_method_name.title()} Retrieval Failed

## Query
{safe_escape_markdown(query)}

## Error Details
**Type**: {type(e).__name__}  
**Message**: {safe_escape_markdown(str(e))}
**Operation ID**: {operation_id}

## Phoenix Tracing
- **Project**: {project_name}
- **Span**: MCP.resource.{method_name} (error)
- **Trace ID**: {span.get_span_context().trace_id}
- **Error Type**: {type(e).__name__}

## Troubleshooting Guide
1. **Verify query format**: Ensure query is a valid string
2. **Try alternative methods**: Use different retrieval strategies
3. **Check system status**: Verify all services are running
4. **Review logs**: Check server logs for detailed error information
5. **Phoenix UI**: View full trace in Phoenix for detailed analysis

## Available Methods
{', '.join(RETRIEVAL_METHODS)}

## System Information
- **Timeout**: {REQUEST_TIMEOUT} seconds
- **Max Snippets**: {MAX_SNIPPETS}
- **Error ID**: {query_hash}
- **Operation ID**: {operation_id}

---
*Error generated by Advanced RAG MCP Resource Server v2.2*
"""
    
    # Add enhanced docstring with Phoenix tracing information
    get_retrieval_resource.__doc__ = f"""
    Retrieve and format content using {method_name} retrieval strategy with Phoenix tracing.
    
    This resource provides LLM-optimized content retrieval using the {method_name}
    method, returning results in structured Markdown format with context information,
    source attribution, performance metadata, and comprehensive Phoenix observability.
    
    Phoenix Tracing:
        - Project: {project_name}
        - Tracer: advanced-rag-resource-server
        - Span: MCP.resource.{method_name}
        - Attributes: method, operation_id, query_hash, response_length, context_docs
        - Events: chain.retrieval.start, chain.retrieval.complete, content.formatting.complete
    
    Operation ID: {operation_id}
    Corresponds to FastAPI tool: POST /invoke/{method_name}_retriever
    
    Args:
        query (str): The search query to process (max recommended: 500 characters)
        
    Returns:
        str: Formatted Markdown content with:
            - Direct answer to the query
            - Context documents with source attribution
            - Method-specific metadata
            - Operation ID for API consistency
            - Performance and processing notes
            - Phoenix tracing information
            
    Raises:
        TimeoutError: If processing exceeds {REQUEST_TIMEOUT} seconds
        ValueError: If query format is invalid
        
    Example:
        >>> resource = get_retrieval_resource("What makes John Wick popular?")
        >>> print(resource)  # Returns formatted Markdown response with Phoenix tracing metadata
    """
    
    return get_retrieval_resource

# Add system health endpoint with enhanced Phoenix tracing
async def health_check() -> str:
    """System health and status check with enhanced Phoenix tracing"""
    with tracer.start_as_current_span("MCP.resource.health_check") as span:
        try:
            # Set span attributes
            span.set_attribute("mcp.resource.type", "health_check")
            span.set_attribute("mcp.resource.project", project_name)
            
            # Basic health checks
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "2.2.0",
                "available_methods": len(RETRIEVAL_METHODS),
                "configuration": {
                    "request_timeout": REQUEST_TIMEOUT,
                    "max_snippets": MAX_SNIPPETS,
                    "query_hash_length": QUERY_HASH_LENGTH
                },
                "methods": RETRIEVAL_METHODS,
                "operation_id_mapping": METHOD_TO_OPERATION_ID,
                "phoenix_tracing": {
                    "project": project_name,
                    "endpoint": phoenix_endpoint,
                    "tracer": "advanced-rag-resource-server",
                    "auto_instrument": True
                }
            }
            
            # Test chain availability
            chain_status = {}
            for method in RETRIEVAL_METHODS:
                try:
                    chain = get_chain_by_method(method)
                    operation_id = get_operation_id_for_method(method)
                    chain_status[method] = {
                        "status": "available" if chain else "unavailable",
                        "operation_id": operation_id
                    }
                except Exception as e:
                    chain_status[method] = {
                        "status": f"error: {str(e)}",
                        "operation_id": get_operation_id_for_method(method)
                    }
            
            health_status["chain_status"] = chain_status
            
            # Set span attributes for health status
            span.set_attribute("mcp.health.status", "healthy")
            span.set_attribute("mcp.health.available_methods", len(RETRIEVAL_METHODS))
            span.set_attribute("mcp.health.version", "2.2.0")
            
            # Add span event
            span.add_event("health_check.complete", {
                "status": "healthy",
                "methods_count": len(RETRIEVAL_METHODS)
            })
            
            # Format as readable Markdown with enhanced Phoenix information
            return f"""# System Health Check

## Overall Status
✅ **HEALTHY** - All systems operational

## Timestamp
{health_status['timestamp']}

## Configuration
- **Request Timeout**: {REQUEST_TIMEOUT} seconds
- **Max Context Snippets**: {MAX_SNIPPETS}
- **Available Methods**: {len(RETRIEVAL_METHODS)}

## Retrieval Methods Status
{chr(10).join([f"- **{method}**: {status['status']} (Operation ID: {status['operation_id']})" for method, status in chain_status.items()])}

## Operation ID Mapping
{chr(10).join([f"- **{method}** → `{op_id}`" for method, op_id in METHOD_TO_OPERATION_ID.items()])}

## Phoenix Tracing Integration
- **Project**: {project_name}
- **Endpoint**: {phoenix_endpoint}
- **Tracer**: advanced-rag-resource-server
- **Auto Instrument**: ✅ Enabled
- **Span**: MCP.resource.health_check
- **Trace ID**: {span.get_span_context().trace_id}

## API Consistency
- **FastAPI Tools**: Use operation_ids as tool names
- **MCP Resources**: Use operation_ids in URI patterns and metadata
- **Naming Convention**: `{{method}}_retriever` format for all endpoints

## System Information
- **Version**: {health_status['version']}
- **Environment**: Production-Ready with Enhanced Phoenix Tracing
- **Security**: Enhanced with input sanitization
- **Performance**: Optimized with timeouts and caching
- **Consistency**: Operation ID mapping ensures tool/resource alignment
- **Observability**: Full Phoenix tracing with spans, events, and attributes

---
*Health check generated at {health_status['timestamp']} - v2.2.0 with Phoenix Tracing*
"""
            
        except Exception as e:
            span.set_attribute("mcp.health.status", "error")
            span.set_attribute("mcp.health.error", str(e))
            span.add_event("health_check.error", {
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            
            logger.error(f"Health check failed: {e}", exc_info=True)
            return f"""# System Health Check - ERROR

## Status
❌ **UNHEALTHY** - System experiencing issues

## Error
{safe_escape_markdown(str(e))}

## Timestamp
{datetime.now(timezone.utc).isoformat()}

## Phoenix Tracing
- **Project**: {project_name}
- **Span**: MCP.resource.health_check (error)
- **Trace ID**: {span.get_span_context().trace_id}
- **Error Type**: {type(e).__name__}

## Recommended Actions
1. Check server logs for detailed error information
2. Verify all dependencies are installed and accessible
3. Restart the MCP server if issues persist
4. Contact system administrator if problems continue
5. Review Phoenix UI for detailed trace analysis

---
*Error health check generated at {datetime.now(timezone.utc).isoformat()} - v2.2.0*
"""

# Create the MCP server as a global variable for inspector compatibility
logger.info("🚀 Creating Enhanced RAG MCP Resource Server v2.2 with Advanced Phoenix Tracing...")

try:
    # Start with existing FastAPI→MCP conversion
    mcp = FastMCP.from_fastapi(app=app)
    
    # Register native FastMCP resources for each retrieval method using operation_id patterns
    for method in RETRIEVAL_METHODS:
        handler = create_resource_handler(method)
        operation_id = get_operation_id_for_method(method)
        safe_method = ESCAPED_METHOD_NAMES[method]
        
        # Use operation_id in URI pattern for consistency
        resource_uri = f"retriever://{operation_id}/{{query}}"
        
        # Register the resource with comprehensive metadata including operation_id
        mcp.resource(resource_uri)(handler)
        
        logger.info(f"Registered resource template: {resource_uri} (method: {method}, operation_id: {operation_id})")
    
    # Register health check resource
    mcp.resource("system://health")(health_check)
    
    logger.info(
        f"Registered {len(RETRIEVAL_METHODS)} RAG resource templates + 1 health endpoint with Phoenix tracing",
        extra={
            "methods": RETRIEVAL_METHODS,
            "operation_ids": list(METHOD_TO_OPERATION_ID.values()),
            "timeout": REQUEST_TIMEOUT,
            "max_snippets": MAX_SNIPPETS,
            "total_resources": len(RETRIEVAL_METHODS) + 1,
            "version": "2.2.0",
            "phoenix_project": project_name,
            "phoenix_endpoint": phoenix_endpoint,
            "tracer": "advanced-rag-resource-server"
        }
    )
    
except Exception as e:
    logger.error(f"Failed to create MCP server: {e}")
    raise

def main():
    """Entry point for MCP resource server with enhanced Phoenix tracing"""
    logger.info("Starting Advanced RAG MCP Resource Server v2.2 with Enhanced Phoenix Tracing...")
    logger.info(
        "Server configuration with Phoenix integration",
        extra={
            "available_resources": [f'retriever://{get_operation_id_for_method(method)}/{{query}}' for method in RETRIEVAL_METHODS] + ["system://health"],
            "operation_id_mapping": METHOD_TO_OPERATION_ID,
            "request_timeout": REQUEST_TIMEOUT,
            "max_snippets": MAX_SNIPPETS,
            "project_root": os.getenv("PROJECT_ROOT", "auto-detected"),
            "security_features": ["input_sanitization", "timeout_protection", "error_handling"],
            "consistency_features": ["operation_id_integration", "tool_resource_alignment"],
            "phoenix_features": ["enhanced_tracing", "explicit_spans", "span_events", "span_attributes"],
            "version": "2.2.0",
            "phoenix_project": project_name,
            "phoenix_endpoint": phoenix_endpoint,
            "tracer": "advanced-rag-resource-server"
        }
    )
    mcp.run()

if __name__ == "__main__":
    import sys

    # Check for cloud deployment mode (streamable-http transport)
    if len(sys.argv) > 1 and sys.argv[1] == "--transport":
        transport = sys.argv[2] if len(sys.argv) > 2 else "stdio"

        if transport == "streamable-http":
            # Cloud deployment mode with streamable-http
            port = int(os.getenv("MCP_PORT", "8002"))
            host = os.getenv("MCP_HOST", "0.0.0.0")

            logger.info(f"Starting MCP resource server in cloud mode: streamable-http on {host}:{port}")
            mcp.run(transport="streamable-http", port=port, host=host)
        else:
            # Local stdio mode
            logger.info("Starting MCP resource server in local mode: stdio")
            main()
    else:
        # Default: stdio mode for local development
        main()
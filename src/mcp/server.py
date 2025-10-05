# server.py - Primary MCP Server Implementation (v2.2)

import os
from datetime import datetime
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from fastmcp import FastMCP

# Configure logging for MCP Tools Server
# Use /tmp for Lambda/cloud environments (read-only filesystem)
LOGS_DIR = os.getenv("LOGS_DIR", "/tmp" if os.getenv("AWS_LAMBDA_FUNCTION_NAME") else "logs")
LOG_FILENAME = os.path.join(LOGS_DIR, "mcp_tools.log")

def setup_mcp_tools_logging():
    """Configure logging specifically for MCP Tools Server"""
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

setup_mcp_tools_logging()
logger = logging.getLogger(__name__)

from phoenix.otel import register

# Import settings for configuration
from src.core.settings import get_settings

# Unified Phoenix configuration for the entire Advanced RAG system
settings = get_settings()
phoenix_endpoint: str = settings.phoenix_endpoint
# Use unified project name to correlate all traces across FastAPI, MCP Server, and Resources
project_name: str = f"advanced-rag-system-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = phoenix_endpoint

# Enhanced Phoenix integration with tracer provider (following resource_wrapper.py v2.2 patterns)
tracer_provider = register(
    project_name=project_name,
    auto_instrument=True
)

# Get tracer for enhanced MCP server instrumentation
tracer = tracer_provider.get_tracer("advanced-rag-mcp-server")

def create_mcp_server():
    """Create MCP server from FastAPI app using FastMCP.from_fastapi() with enhanced Phoenix tracing"""
    
    # Enhanced MCP server creation with explicit span tracing
    with tracer.start_as_current_span("MCP.server.creation") as span:
        try:
            # Set span attributes for MCP server creation
            span.set_attribute("mcp.server.type", "fastapi_wrapper")
            span.set_attribute("mcp.server.project", project_name)
            span.set_attribute("mcp.server.phoenix_endpoint", phoenix_endpoint)
            span.set_attribute("mcp.server.conversion_method", "FastMCP.from_fastapi")
            
            # Add span event for server creation start
            span.add_event("server.creation.start", {
                "method": "FastMCP.from_fastapi",
                "auto_instrument": True
            })
            
            # Add project root to Python path for imports
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent  # Go up 3 levels: mcp -> src -> project_root
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
                logger.info(f"Added project root to Python path: {project_root}")
                span.set_attribute("mcp.server.project_root", str(project_root))
                span.add_event("path.setup.complete", {
                    "project_root": str(project_root)
                })
            
            # Import the FastAPI app with tracing
            span.add_event("fastapi.import.start")
            from src.api.app import app
            
            # Set span attributes for FastAPI app analysis
            route_count = len(app.routes)
            span.set_attribute("mcp.server.fastapi_routes", route_count)
            span.add_event("fastapi.import.complete", {
                "routes_count": route_count,
                "app_title": getattr(app, 'title', 'Unknown'),
                "app_version": getattr(app, 'version', 'Unknown')
            })
            
            logger.info(f"Successfully imported FastAPI app with {route_count} routes")
            
            # Convert FastAPI app to MCP server using FastMCP.from_fastapi()
            span.add_event("mcp.conversion.start", {
                "source": "FastAPI",
                "target": "MCP",
                "method": "FastMCP.from_fastapi"
            })
            
            # This works as a pure wrapper - no backend services needed during conversion
            mcp = FastMCP.from_fastapi(app=app)
            
            # Set final span attributes for successful creation
            span.set_attribute("mcp.server.status", "created")
            span.set_attribute("mcp.server.ready", True)
            span.add_event("mcp.conversion.complete", {
                "status": "success",
                "server_type": "FastMCP"
            })
            
            logger.info(
                "FastMCP server created successfully from FastAPI app with Phoenix tracing",
                extra={
                    "routes_count": route_count,
                    "project": project_name,
                    "phoenix_endpoint": phoenix_endpoint,
                    "tracer": "advanced-rag-mcp-server",
                    "span_id": span.get_span_context().span_id,
                    "trace_id": span.get_span_context().trace_id
                }
            )
            
            return mcp
            
        except ImportError as e:
            # Enhanced import error handling with Phoenix tracing
            span.set_attribute("mcp.server.error", "import_error")
            span.set_attribute("mcp.server.status", "failed")
            span.add_event("fastapi.import.error", {
                "error_type": "ImportError",
                "error_message": str(e),
                "module": "src.api.app"
            })
            
            logger.error(
                f"Failed to import FastAPI app: {e}",
                extra={
                    "error_type": "ImportError",
                    "project": project_name,
                    "span_id": span.get_span_context().span_id,
                    "trace_id": span.get_span_context().trace_id
                }
            )
            logger.error("Environment variables will only be needed when MCP tools execute")
            raise
            
        except Exception as e:
            # Enhanced general error handling with Phoenix tracing
            span.set_attribute("mcp.server.error", type(e).__name__)
            span.set_attribute("mcp.server.status", "failed")
            span.add_event("server.creation.error", {
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            
            logger.error(
                f"Failed to create MCP server: {e}",
                extra={
                    "error_type": type(e).__name__,
                    "project": project_name,
                    "span_id": span.get_span_context().span_id,
                    "trace_id": span.get_span_context().trace_id
                },
                exc_info=True
            )
            raise

# Create the MCP server using the enhanced approach with Phoenix tracing
logger.info("🚀 Creating Advanced RAG MCP Server with Enhanced Phoenix Tracing...")

try:
    mcp = create_mcp_server()
    
    # Add CQRS-compliant Qdrant Resources
    logger.info("Adding CQRS-compliant Qdrant Resources...")
    
    # Import CQRS resources
    from src.mcp.qdrant_resources import (
        get_collection_info_resource,
        get_document_resource,
        search_collection_resource,
        get_collection_stats_resource,
        list_collections_resource
    )
    
    # Register CQRS Resources following claude_code_instructions.md patterns
    # Resources handle queries (read operations), Tools handle commands (write operations)
    
    # Collection listing resource
    mcp.resource("qdrant://collections")(list_collections_resource)
    
    # Collection information resource
    mcp.resource("qdrant://collections/{collection_name}")(get_collection_info_resource)
    
    # Document retrieval resource
    mcp.resource("qdrant://collections/{collection_name}/documents/{point_id}")(get_document_resource)
    
    # Search resource (with query parameters)
    @mcp.resource("qdrant://collections/{collection_name}/search")
    async def search_resource_with_params(collection_name: str, query: str = "", limit: int = 5) -> str:
        """Search collection with query parameters."""
        if not query:
            return f"Error: query parameter is required for search in collection {collection_name}"
        return await search_collection_resource(collection_name, query, limit)
    
    # Collection statistics resource
    mcp.resource("qdrant://collections/{collection_name}/stats")(get_collection_stats_resource)
    
    logger.info("✅ CQRS Resources registered: collections, search, documents, stats")
    logger.info("✅ MCP Server created successfully with Phoenix observability and CQRS Resources")
    
except Exception as e:
    logger.error(f"❌ Failed to create MCP server: {e}")
    raise

def get_server_health() -> dict:
    """Get comprehensive server health information with Phoenix tracing"""
    with tracer.start_as_current_span("MCP.server.health_check") as span:
        try:
            # Set span attributes for health check
            span.set_attribute("mcp.server.health.type", "comprehensive")
            span.set_attribute("mcp.server.project", project_name)
            
            # Gather health information
            health_info = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "server_type": "FastMCP.from_fastapi",
                "version": "2.2.0",
                "phoenix_integration": {
                    "project": project_name,
                    "endpoint": phoenix_endpoint,
                    "tracer": "advanced-rag-mcp-server",
                    "auto_instrument": True,
                    "enhanced_tracing": True
                },
                "system_info": {
                    "python_path_configured": True,
                    "fastapi_app_imported": True,
                    "mcp_server_ready": True,
                    "cqrs_resources_enabled": True
                },
                "cqrs_resources": {
                    "collections_list": "qdrant://collections",
                    "collection_info": "qdrant://collections/{collection_name}",
                    "document_retrieval": "qdrant://collections/{collection_name}/documents/{point_id}",
                    "search": "qdrant://collections/{collection_name}/search?query={text}&limit={n}",
                    "statistics": "qdrant://collections/{collection_name}/stats"
                }
            }
            
            # Set span attributes for health status
            span.set_attribute("mcp.server.health.status", "healthy")
            span.set_attribute("mcp.server.health.version", "2.2.0")
            span.add_event("health_check.complete", {
                "status": "healthy",
                "phoenix_enabled": True
            })
            
            logger.info(
                "Server health check completed successfully",
                extra={
                    "status": "healthy",
                    "project": project_name,
                    "span_id": span.get_span_context().span_id,
                    "trace_id": span.get_span_context().trace_id
                }
            )
            
            return health_info
            
        except Exception as e:
            # Enhanced error handling for health check
            span.set_attribute("mcp.server.health.status", "error")
            span.set_attribute("mcp.server.health.error", str(e))
            span.add_event("health_check.error", {
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            
            logger.error(
                f"Server health check failed: {e}",
                extra={
                    "error_type": type(e).__name__,
                    "project": project_name,
                    "span_id": span.get_span_context().span_id,
                    "trace_id": span.get_span_context().trace_id
                },
                exc_info=True
            )
            
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__,
                "phoenix_integration": {
                    "project": project_name,
                    "trace_id": span.get_span_context().trace_id
                }
            }

def main():
    """Entry point for MCP server with enhanced Phoenix tracing"""
    with tracer.start_as_current_span("MCP.server.startup") as span:
        try:
            # Set span attributes for server startup
            span.set_attribute("mcp.server.startup.type", "main")
            span.set_attribute("mcp.server.project", project_name)
            span.set_attribute("mcp.server.version", "2.2.0")
            
            logger.info("Starting Advanced RAG MCP Server v2.2 with Enhanced Phoenix Tracing...")
            
            # Add span event for startup
            span.add_event("server.startup.start", {
                "version": "2.2.0",
                "phoenix_project": project_name,
                "tracer": "advanced-rag-mcp-server"
            })
            
            # Get and log health information
            health_info = get_server_health()
            
            logger.info(
                "Server configuration with Phoenix integration",
                extra={
                    "server_type": "FastMCP.from_fastapi",
                    "conversion_method": "zero_duplication",
                    "backend_services": "on_demand",
                    "phoenix_features": [
                        "enhanced_tracing", 
                        "explicit_spans", 
                        "span_events", 
                        "span_attributes",
                        "error_correlation",
                        "health_monitoring"
                    ],
                    "version": "2.2.0",
                    "project": project_name,
                    "phoenix_endpoint": phoenix_endpoint,
                    "tracer": "advanced-rag-mcp-server",
                    "health_status": health_info["status"]
                }
            )
            
            logger.info("FastMCP acts as a wrapper - backend services only needed when tools execute")
            
            # Set span attributes for successful startup
            span.set_attribute("mcp.server.startup.status", "ready")
            span.add_event("server.startup.ready", {
                "status": "ready",
                "health": health_info["status"]
            })
            
            # Start the MCP server
            span.add_event("server.run.start")
            mcp.run()
            
        except Exception as e:
            # Enhanced startup error handling
            span.set_attribute("mcp.server.startup.status", "failed")
            span.set_attribute("mcp.server.startup.error", str(e))
            span.add_event("server.startup.error", {
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            
            logger.error(
                f"Failed to start MCP server: {e}",
                extra={
                    "error_type": type(e).__name__,
                    "project": project_name,
                    "span_id": span.get_span_context().span_id,
                    "trace_id": span.get_span_context().trace_id
                },
                exc_info=True
            )
            raise

if __name__ == "__main__":
    import sys

    # Check for cloud deployment mode (streamable-http transport)
    if len(sys.argv) > 1 and sys.argv[1] == "--transport":
        transport = sys.argv[2] if len(sys.argv) > 2 else "stdio"

        if transport == "streamable-http":
            # Cloud deployment mode with streamable-http
            port = int(os.getenv("MCP_PORT", "8001"))
            host = os.getenv("MCP_HOST", "0.0.0.0")

            logger.info(f"Starting MCP server in cloud mode: streamable-http on {host}:{port}")
            mcp.run(transport="streamable-http", port=port, host=host)
        else:
            # Local stdio mode
            logger.info("Starting MCP server in local mode: stdio")
            main()
    else:
        # Default: stdio mode for local development
        main() 
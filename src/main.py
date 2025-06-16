"""
Main application entry point for the Advanced RAG project.

This module serves as the central entry point that coordinates all components
of the Advanced RAG system:
- Core infrastructure (settings, logging)
- RAG system components
- MCP server functionality  
- FastAPI web interface
- External service integrations

Educational Note: This demonstrates how to structure a main entry point
that can initialize and coordinate multiple subsystems. The modular
organization allows different components to be started independently
or together as needed.
"""

import logging
from typing import Optional

# Import core infrastructure first
from src.core.logging_config import setup_logging
from src.core.settings import get_settings

# Component imports (now available after migration)
from src.api.app import app
from src.mcp.server import create_mcp_server

__version__ = "1.0.0"

logger = logging.getLogger(__name__)


def initialize_application() -> dict:
    """
    Initialize the complete Advanced RAG application.
    
    Returns:
        dict: Initialized components
    """
    logger.info("Initializing Advanced RAG application...")
    
    # Initialize core components
    settings = get_settings()
    logger.info(f"Loaded settings for environment: {settings.environment}")
    
    components = {
        'settings': settings,
        'version': __version__,
        'fastapi_app': app,
        'mcp_server': create_mcp_server()
    }
    
    logger.info("Application initialization complete")
    return components


def main():
    """Main entry point for the application."""
    try:
        # Setup logging first
        setup_logging()
        logger.info("Starting Advanced RAG application...")
        
        # Initialize all components
        components = initialize_application()
        
        logger.info("Advanced RAG application started successfully")
        return components
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


if __name__ == "__main__":
    main() 
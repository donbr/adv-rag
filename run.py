#!/usr/bin/env python
"""
Advanced RAG FastAPI Server Startup

Starts the FastAPI server with 6 retrieval strategies exposed as HTTP endpoints.
Prerequisites: Run complete setup first - see docs/SETUP.md for detailed instructions.

Quick setup check:
- Virtual environment activated (REQUIRED)
- Docker services running: docker-compose ps
- Data ingested: python scripts/ingestion/csv_ingestion_pipeline.py
- API keys configured in .env file

After startup:
- Server: http://localhost:8000
- API docs: http://localhost:8000/docs  
- Health check: http://localhost:8000/health
"""

import uvicorn
import logging
import socket
import sys
import os
from src.api.app import app
from src.core.logging_config import setup_logging

# Ensure logging is set up
if not logging.getLogger().hasHandlers():
    setup_logging()

logger = logging.getLogger(__name__)


def check_port_available(port: int, host: str = "0.0.0.0") -> bool:
    """Check if a port is available for binding"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        # Try to bind to the port
        sock.bind((host, port))
        sock.close()
        return True
    except OSError:
        sock.close()
        return False


if __name__ == "__main__":
    port = 8000
    host = "0.0.0.0"
    
    # Check if port is available
    if not check_port_available(port, host):
        logger.error(f"Port {port} is already in use!")
        logger.info("Options:")
        logger.info("  1. Kill the existing process: python scripts/manage.py stop --tier 4")
        logger.info("  2. Use a different port: PORT=8001 python run.py")
        logger.info("  3. Check what's running: python scripts/status.py")
        
        # Check if PORT environment variable is set
        env_port = os.environ.get("PORT")
        if env_port:
            try:
                port = int(env_port)
                logger.info(f"Trying alternate port {port} from PORT environment variable...")
            except ValueError:
                logger.error(f"Invalid PORT value: {env_port}")
                sys.exit(1)
        else:
            sys.exit(1)
    
    logger.info("Starting Advanced RAG Retriever API server...")
    logger.info(f"API documentation will be available at http://127.0.0.1:{port}/docs")
    
    try:
        uvicorn.run(app, host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested via keyboard interrupt")
    except Exception as e:
        logger.error(f"Error starting server: {e}", exc_info=True)
    finally:
        logger.info("Server has been shut down") 
#!/usr/bin/env python
"""
Run the RAG API server.

This script serves as the main entry point for the Advanced RAG Retriever API.
It initializes the FastAPI application from src.main_api and starts the server.
"""
import uvicorn
import logging
from src.main_api import app
from src import logging_config

# Ensure logging is set up
if not logging.getLogger().hasHandlers():
    logging_config.setup_logging()

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
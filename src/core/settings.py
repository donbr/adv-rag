# settings.py
import os
import logging # For more structured logging
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Initialize logging as the very first thing
# This ensures that even early messages (like dotenv loading status or errors) are logged.
from . import logging_config
logging_config.setup_logging()

from dotenv import load_dotenv

logging.info("Attempting to load environment variables from .env file...")
if load_dotenv():
    logging.info(".env file loaded successfully.")
else:
    logging.info(".env file not found or failed to load. Will rely on OS environment variables.")

class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings (v2 compatible)"""
    
    # Core API Keys
    openai_api_key: str
    openai_model_name: str = "gpt-4.1-mini"  # Required for llm_models.py
    cohere_api_key: Optional[str] = None
    
    # LLM Configuration
    openai_temperature: float = 0.0
    openai_max_retries: int = 3
    openai_request_timeout: int = 60
    
    # Embedding Configuration
    embedding_model_name: str = "text-embedding-3-small"
    
    # Cohere Configuration
    cohere_rerank_model: str = "rerank-english-v3.0"
    
    # External Service Endpoints
    phoenix_endpoint: str = "http://localhost:6006"
    qdrant_url: str = "http://localhost:6333"
    
    # Redis Configuration (Updated for 2024-2025 best practices)
    redis_url: str = "redis://localhost:6379"  # Docker Compose Redis
    redis_cache_ttl: int = 300  # 5 minutes default
    redis_max_connections: int = 20  # Increased pool size for better performance
    redis_socket_keepalive: bool = True
    redis_health_check_interval: int = 30
    
    # MCP Configuration
    mcp_request_timeout: int = 30
    max_snippets: int = 5
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables
    )

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get application settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def get_env_variable(var_name, is_secret=True, default_value=None):
    """Gets an environment variable, logs if not found."""
    value = os.getenv(var_name, default_value)
    if value is None:
        logging.error(f"Environment variable '{var_name}' not found. Please set it in your .env file or system environment.")
        return default_value # Or raise an error if it's absolutely critical and has no default
    # For actual secrets, you might avoid logging the value itself, even at DEBUG
    logging.info(f"Environment variable '{var_name}' was accessed.") # Changed from 'loaded' to 'accessed'
    return value

def setup_env_vars():
    logging.info("Setting up application environment variables...")

    # Get OpenAI API key (Required for core functionality)
    openai_api_key = get_env_variable("OPENAI_API_KEY", is_secret=True)
    if not openai_api_key:
        logging.error("CRITICAL: OPENAI_API_KEY is not set. Core functionality will be impacted.")
        # Depending on strictness, you might raise an error here or allow the app to try and fail later.
    else:
        logging.info("OPENAI_API_KEY is set.")
    os.environ["OPENAI_API_KEY"] = openai_api_key if openai_api_key else ""

    # Get COHERE_API_KEY (Required for CohereRerank)
    cohere_api_key = get_env_variable("COHERE_API_KEY", is_secret=True)
    if not cohere_api_key:
        logging.warning("COHERE_API_KEY is not set. Contextual Compression Retriever (CohereRerank) will not function.")
    else:
        logging.info("COHERE_API_KEY is set.")
    os.environ["COHERE_API_KEY"] = cohere_api_key if cohere_api_key else ""
    logging.info("Application environment variables setup complete.")

if __name__ == "__main__":
    # setup_logging() is already called at the top of the module
    logging.info("Running settings.py as __main__ to check environment variable status...")
    # print("Attempting to load and set up environment variables...") # Now logged
    setup_env_vars()
    logging.info("\nEnvironment variable status check:")

    logging.info(f"OPENAI_API_KEY is set: {bool(os.getenv('OPENAI_API_KEY'))}")
    logging.info(f"COHERE_API_KEY is set: {bool(os.getenv('COHERE_API_KEY'))}")

    if not os.getenv('OPENAI_API_KEY'):
        logging.warning("OPENAI_API_KEY is missing. Key functionalities will fail.")
    if not os.getenv('COHERE_API_KEY'):
        logging.warning("COHERE_API_KEY is missing. CohereRerank will fail.")
    logging.info("Finished settings.py __main__ check.") 
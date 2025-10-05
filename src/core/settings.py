# settings.py
import os
import logging # For more structured logging
from typing import Optional, List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

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
    
    # Core API Keys (Optional for build/inspection, required at runtime)
    openai_api_key: Optional[str] = None
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
    
    # Cache Feature Flag - Enable/disable caching for A/B testing
    cache_enabled: bool = Field(
        default=True,
        description="Enable/disable Redis caching for retrieval strategy comparison"
    )
    
    # MCP Configuration
    mcp_request_timeout: int = 30
    max_snippets: int = 5
    
    # Phoenix Integration Configuration (Task 1.7)
    phoenix_integration_enabled: bool = Field(
        default=True,
        description="Enable Phoenix MCP integration for experiment analysis"
    )
    
    phoenix_base_url: Optional[str] = Field(
        default=None,
        description="Base URL for Phoenix MCP server (auto-detected if None)"
    )
    
    phoenix_api_key: Optional[str] = Field(
        default=None,
        description="API key for Phoenix authentication (if required)"
    )
    
    phoenix_timeout_seconds: float = Field(
        default=30.0,
        description="Default timeout for Phoenix MCP operations"
    )
    
    # Phoenix Error Handling Configuration
    phoenix_retry_max_attempts: int = Field(
        default=3,
        description="Maximum retry attempts for Phoenix operations"
    )
    
    phoenix_retry_base_delay: float = Field(
        default=1.0,
        description="Base delay for exponential backoff in seconds"
    )
    
    phoenix_retry_max_delay: float = Field(
        default=30.0,
        description="Maximum delay for exponential backoff in seconds"
    )
    
    phoenix_retry_exponential_base: float = Field(
        default=2.0,
        description="Exponential base for backoff calculation"
    )
    
    phoenix_retry_jitter: bool = Field(
        default=True,
        description="Enable jitter in retry delays to prevent thundering herd"
    )
    
    # Phoenix Circuit Breaker Configuration
    phoenix_circuit_breaker_enabled: bool = Field(
        default=True,
        description="Enable circuit breaker pattern for Phoenix operations"
    )
    
    phoenix_circuit_breaker_failure_threshold: int = Field(
        default=5,
        description="Number of failures before opening circuit breaker"
    )
    
    phoenix_circuit_breaker_success_threshold: int = Field(
        default=3,
        description="Number of successes to close from half-open state"
    )
    
    phoenix_circuit_breaker_timeout: float = Field(
        default=60.0,
        description="Time in seconds before attempting to close circuit breaker"
    )
    
    # Phoenix Batch Processing Configuration
    phoenix_batch_enabled: bool = Field(
        default=True,
        description="Enable batch processing for Phoenix data synchronization"
    )
    
    phoenix_batch_size: int = Field(
        default=10,
        description="Number of items to process in each batch"
    )
    
    phoenix_batch_timeout_seconds: float = Field(
        default=300.0,
        description="Timeout for batch operations in seconds"
    )
    
    phoenix_batch_progress_interval: int = Field(
        default=5,
        description="Progress reporting interval for batch operations"
    )
    
    phoenix_batch_concurrent_limit: int = Field(
        default=3,
        description="Maximum concurrent batch operations"
    )
    
    # Phoenix Pattern Extraction Configuration
    phoenix_pattern_qa_threshold: float = Field(
        default=0.8,
        description="Minimum QA correctness score for pattern extraction"
    )
    
    phoenix_pattern_rag_threshold: float = Field(
        default=0.7,
        description="Minimum RAG relevance score for pattern extraction"
    )
    
    phoenix_pattern_confidence_threshold: float = Field(
        default=0.75,
        description="Minimum confidence score for pattern validation"
    )
    
    phoenix_pattern_max_patterns_per_experiment: int = Field(
        default=50,
        description="Maximum patterns to extract per experiment"
    )
    
    # Phoenix Data Sync Configuration
    phoenix_sync_enabled: bool = Field(
        default=False,
        description="Enable periodic Phoenix data synchronization"
    )
    
    phoenix_sync_interval_hours: int = Field(
        default=24,
        description="Interval between Phoenix data synchronizations in hours"
    )
    
    phoenix_sync_datasets: Union[str, List[str]] = Field(
        default="johnwick_golden_testset",
        description="List of dataset names to synchronize from Phoenix (comma-separated string or list)"
    )
    
    phoenix_sync_max_age_days: int = Field(
        default=30,
        description="Maximum age of experiments to synchronize in days"
    )
    
    @field_validator('phoenix_sync_datasets', mode='after')
    @classmethod
    def parse_phoenix_sync_datasets(cls, v):
        """Parse phoenix_sync_datasets from comma-separated string or list"""
        if isinstance(v, str):
            # Handle comma-separated string from environment variable
            return [dataset.strip() for dataset in v.split(',') if dataset.strip()]
        elif isinstance(v, list):
            # Already a list, return as-is
            return v
        else:
            # Default to single item list for other types
            return [str(v)] if v else []

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
        env_nested_delimiter="__",
        env_parse_none_str="None"
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
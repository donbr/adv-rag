# settings.py
import os
import logging # For more structured logging

# Initialize logging as the very first thing
# This ensures that even early messages (like dotenv loading status or errors) are logged.
from src import logging_config
logging_config.setup_logging()

from dotenv import load_dotenv

logging.info("Attempting to load environment variables from .env file...")
if load_dotenv():
    logging.info(".env file loaded successfully.")
else:
    logging.info(".env file not found or failed to load. Will rely on OS environment variables.")

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